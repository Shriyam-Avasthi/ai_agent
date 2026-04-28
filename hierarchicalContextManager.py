import copy
import os

import litellm
import tiktoken

from config import PROXY_URL


class HierarchicalContextManager:
    def __init__(
        self,
        working_directory: str,
        max_total_tokens: int = 60000,
        max_active_tokens: int = 40000,
    ):
        self.encoder = tiktoken.encoding_for_model("gpt-4o")
        self.max_total_tokens = max_total_tokens
        self.max_active_tokens = max_active_tokens

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
        except Exception:
            return {
                "role": "system",
                "content": "=== AGENT SCRATCHPAD ===\n[Error reading scratchpad]\n=============",
            }

    def set_core_prompts(self, system_content, user_content):
        self.system_prompt = {"role": "system", "content": system_content}
        self.initial_user_query = {"role": "user", "content": user_content}

    def add_message(self, message):
        self.active_messages.append(copy.deepcopy(message))
        self._manage_context()

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

        active_tokens = sum(self.count_tokens(str(m)) for m in self.active_messages)
        if active_tokens > self.max_active_tokens:
            self._summarize_and_evict()

    def _summarize_and_evict(self, num_turns_to_evict=4):
        # A turn usually consists of an Assistant message and a Tool/User response.
        # We evict in pairs to keep tool calls and their outputs together.
        messages_to_evict = int(num_turns_to_evict * 2)

        if len(self.active_messages) <= messages_to_evict:
            return

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
        except Exception as e:
            print(f"Warning: Summarization failed: {e}")
            # Fallback: Just append a note rather than crashing
            self.rolling_summary += (
                "\n[Note: Some intermediate steps were truncated due to length limits.]"
            )

    def get_messages_for_api(self):
        core = [self.system_prompt, self.initial_user_query]
        scratchpad = [self.get_agent_scratchpad()]
        summary_msg = [
            {"role": "system", "content": f"HISTORY SUMMARY:\n{self.rolling_summary}"}
        ]
        final_payload = core + scratchpad + summary_msg + self.active_messages
        return final_payload
