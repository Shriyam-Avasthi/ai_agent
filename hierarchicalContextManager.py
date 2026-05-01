import copy
import logging
import os
import json

import litellm
import tiktoken

from config import LOGGER_ID, PROXY_URL

logger = logging.getLogger(LOGGER_ID)


class HierarchicalContextManager:
    def __init__(
        self,
        working_directory: str,
        max_total_tokens: int = 60000,
        max_active_tokens: int = 40000,
        verbose: bool = False,
    ):
        self.encoder = tiktoken.encoding_for_model("gpt-4o")
        self.max_total_tokens = max_total_tokens
        self.max_active_tokens = max_active_tokens
        self.verbose = verbose

        self.working_directory = working_directory
        self.scratchpad_path = os.path.join(working_directory, ".agent_scratchpad.txt")
        # Ensure it exists
        open(self.scratchpad_path, "a").close()

        # Crucial memory. Should be always visible.
        self.system_prompt = {}
        self.initial_user_query = {}

        # Long term memory.
        self.rolling_summary: str = (
            "No previous context. This is the start of the task."
        )

        # Short term memory.
        self.active_messages = []

        logger.debug(
            f"HierarchicalContextManager initialized. Max active tokens: {self.max_active_tokens}"
        )

    def _sanitize_msg(self, msg):
        allowed_keys = {"role", "content", "tool_calls", "tool_call_id", "name"}
        return {k: v for k, v in msg.items() if k in allowed_keys}

    def count_tokens(self, text):
        return len(self.encoder.encode(str(text)))

    def get_agent_scratchpad(self) -> dict:
        try:
            with open(self.scratchpad_path, "r") as f:
                content = f.read().strip()

            if not content:
                content = "[Scratchpad is empty]"

            return {
                "role": "system",
                "content": f"=== AGENT SCRATCHPAD (ACTIVE WORKING MEMORY) ===\n{content}\n=================================================",
            }
        except Exception as e:
            logger.warning(f"Failed to read agent scratchpad: {e}")
            return {
                "role": "system",
                "content": "=== AGENT SCRATCHPAD ===\n[Error reading scratchpad]\n=============",
            }

    def set_core_prompts(self, system_content, user_content):
        self.system_prompt = {"role": "system", "content": system_content}
        self.initial_user_query = {"role": "user", "content": user_content}
        logger.info("Core system and user prompts set.")
        logger.debug(f"System Prompt: {self.system_prompt}")
        logger.debug(f"User Query: {self.initial_user_query}")

    def add_message(self, message):
        self.active_messages.append(copy.deepcopy(message))
        self._manage_context()
        logger.debug(
            f"Appended new message to active context. Role: {message.get('role')}"
        )
        self._dump_conversation_state()

    def _manage_context(self):
        # Keep last 6 messages and truncate earlier ones.
        # NOTE: this is not the most foolproof plan. For example there could be error logs which are too long.
        # Truncating them shouldn't be the first priority
        if len(self.active_messages) > 6:
            for i in range(len(self.active_messages) - 6):
                msg = self.active_messages[i]
                if (
                    msg.get("role") == "tool"
                    and self.count_tokens(msg.get("content", "")) > 1000
                ):
                    msg["content"] = (
                        "[TOOL OUTPUT TRUNCATED DUE TO AGE. The agent should rely on its notes/memory for this information.]"
                    )
                    logger.debug(
                        f"Truncated large tool output at index {i} due to age."
                    )

                elif (
                    msg.get("role") == "assistant"
                    and self.count_tokens(msg.get("content", "")) > 500
                ):
                    msg["content"] = "[ASSISTANT THOUGHT TRUNCATED TO SAVE SPACE.]"

        active_tokens = active_tokens = sum(
            self.count_tokens(str(self._sanitize_msg(m))) for m in self.active_messages
        )
        active_tokens += self.count_tokens(self.system_prompt)
        logger.debug(
            f"Current active token count: {active_tokens} / {self.max_active_tokens}"
        )

        if active_tokens > self.max_active_tokens:
            self._summarize_and_evict()

    def _summarize_and_evict(self, num_turns_to_evict=4):
        # A turn usually consists of an Assistant message and a Tool/User response.
        # We evict in pairs to keep tool calls and their outputs together.
        messages_to_evict = int(num_turns_to_evict * 2)

        if len(self.active_messages) <= messages_to_evict:
            return

        logger.info(
            f"Token limit exceeded. Evicting and summarizing the oldest {messages_to_evict} messages."
        )

        evicted = self.active_messages[:messages_to_evict]
        self.active_messages = self.active_messages[messages_to_evict:]

        evicted_text = "\n".join(
            [
                f"{m.get('role').upper()}: {str(m.get('content', m.get('tool_calls', '')))}"
                for m in evicted
            ]
        )

        summary_prompt = f"""You are maintaining the long-term memory for an autonomous coding agent.
        
        CURRENT MEMORY:
        {self.rolling_summary}
        
        NEW RECENT ACTIONS TO INTEGRATE:
        {evicted_text}
        
        INSTRUCTIONS:
        Update the CURRENT MEMORY with the new actions. 
        - Keep it concise and chronological.
        - Preserve EXACT file paths, variable names, and bugs discovered.
        - DO NOT list failed thoughts; focus on concrete facts learned and actions taken.
        - Return ONLY the updated memory text.
        """

        try:
            response = litellm.completion(
                model="openai/lightweight-helper",
                api_base=PROXY_URL,
                api_key="sk-dummy-key",
                messages=[{"role": "user", "content": summary_prompt}],
                stream=False,
            )
            self.rolling_summary = response.choices[0].message.content  # type: ignore
            logger.debug(
                f"Successfully generated new rolling summary: \n{self.rolling_summary}"
            )

        except Exception as e:
            logger.error(
                "Summarization API call failed. Applying fallback note.", exc_info=True
            )

            # Fallback: Just append a note rather than crashing
            self.rolling_summary += (
                "\n[Note: Some intermediate steps were truncated due to length limits.]"
            )

    def _dump_conversation_state(self):
        log_path = os.path.join(self.working_directory, "conversation_log.md")
        
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("# Active Agent Conversation\n\n")
                f.write("*This file is auto-generated and overwritten during the agent's run.*\n\n---\n\n")
                
                full_context = self.get_messages_for_api(sanitize_messages=False, logging_enabled=False)
                
                for msg in full_context:
                    role = str(msg.get("role", "UNKNOWN")).upper()
                    content = msg.get("content", "")
                    tool_calls = msg.get("tool_calls", None)
                    
                    f.write(f"### {role}\n\n")
                    
                    if content:
                        if role in ["TOOL", "SYSTEM"]:
                            f.write("```text\n")
                            f.write(f"{content}\n")
                            f.write("```\n\n")
                        else:
                            # Assistant and User messages usually contain their own markdown
                            f.write(f"{content}\n\n")
                    
                    if tool_calls:
                        f.write("**Tool Calls Requested:**\n```json\n")
                        try:
                            if isinstance(tool_calls, str):
                                parsed = json.loads(tool_calls)
                                f.write(json.dumps(parsed, indent=2))
                            else:
                                f.write(json.dumps(tool_calls, indent=2))
                        except Exception:
                            f.write(str(tool_calls))
                        f.write("\n```\n\n")

                    for key, value in msg.items():
                        if key not in ["role", "content", "tool_calls"] and value:
                            f.write(f"**Hidden Field (`{key}`):**\n```text\n")
                            if isinstance(value, (dict, list)):
                                f.write(json.dumps(value, indent=2))
                            else:
                                f.write(str(value))
                            f.write("\n```\n\n")
                    
        except Exception as e:
            logger.error(f"Failed to write conversation log: {e}")

    def get_messages_for_api(self, sanitize_messages=True, logging_enabled=True):
        core = [self.system_prompt, self.initial_user_query]
        scratchpad = [self.get_agent_scratchpad()]
        summary_msg = [
            {"role": "system", "content": f"HISTORY SUMMARY:\n{self.rolling_summary}"}
        ]
        if sanitize_messages: 
            sanitized_messages = [self._sanitize_msg(m) for m in self.active_messages]
            
            final_payload = core + scratchpad + summary_msg + sanitized_messages
        else:
            final_payload = core + scratchpad + summary_msg + self.active_messages
        
        if logging_enabled:
            logger.debug(
                f"Assembled final API payload with {len(final_payload)} total messages."
            )
        return final_payload
