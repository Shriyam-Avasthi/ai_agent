import json
import os
import sys
import time
from typing import Any

import litellm

from call_function import call_function
from config import PROXY_URL, WORKING_DIR
from functions.get_file_content import schema_get_file_content
from functions.get_files_info import schema_get_files_info
from functions.manage_scratchpad import schema_manage_scratchpad
from functions.run_python_file import schema_run_python_file
from functions.write_file import schema_write_file
from hierarchicalContextManager import HierarchicalContextManager

litellm.drop_params = True


def main():
    verbose_flag = False

    if len(sys.argv) < 2:
        print("Prompt is missing!")
        sys.exit(1)

    if (len(sys.argv) == 3) and (sys.argv[2] == "--verbose"):
        verbose_flag = True
    prompt = sys.argv[1]

    system_prompt = f""" You are a helpful AI coding agent. You are currently in the "{WORKING_DIR}" directory.

    When a user asks a question or makes a request, you should use your provided tools to gather information before answering.
    
    You have the following tools:
        1. write_file
        2. get_file_content
        3. run_python_file
        4. get_files_info
        5. manage_scratchpad

    CRITICAL NOTE:
        1. Be cautious about the tool call syntax and don't hallucinate on the tools. The only tools available are the ones explicitly given to you.
    """
    # messages = [
    #     types.Content(role="user", parts=[types.Part(text=prompt)]),
    # ]

    context = HierarchicalContextManager(WORKING_DIR)
    context.set_core_prompts(system_prompt, prompt)

    # load_dotenv()
    # gemini_api_key = os.environ.get("GEMINI_API_KEY")
    # client = genai.Client(api_key=api_key)

    available_functions = [
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
        schema_manage_scratchpad,
    ]

    # config = types.GenerateContentConfig(
    #     tools=[available_functions], system_instruction=system_prompt
    # )

    max_iters = 200
    for i in range(0, max_iters):

        # response = client.models.generate_content(
        #     model="gemini-2.5-flash",
        #     contents=messages,
        #     config=config,
        # )

        try:
            response = litellm.completion(
                model="openai/orchestrator",  # Or whichever model you are routing to
                api_base=PROXY_URL,
                api_key="sk-dummy-key",
                messages=context.get_messages_for_api(),
                tools=available_functions,
                tool_choice="auto",
                stream=False,
            )
        except Exception as e:
            print(f"Proxy Connection Error: {e}")
            break

        assistant_message = response.choices[0].message  # type: ignore
        #
        # messages.append(assistant_message.model_dump(exclude_none=True))
        msg_dict = assistant_message.model_dump(exclude_none=True)
        msg_dict.pop("provider_specific_fields", None)
        msg_dict.pop("reasoning_content", None)

        context.add_message(msg_dict)

        # 4. Check if the model wants to call tools
        if assistant_message.tool_calls is not None:

            if verbose_flag:
                print("Model requested tool calls...")

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                if function_name is None:
                    continue
                # The arguments come back as a JSON string, you must parse them
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    function_args = {}

                result_string = call_function(
                    function_name, function_args, verbose_flag
                )

                context.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": str(result_string),
                    }
                )

        else:
            # If there are no tool calls, the model has finished its final answer
            print("Final Answer:\n", assistant_message.content)
            break

        time.sleep(1)

        # if response is None or response.usage_metadata is None:
        #     print("Response is malformed!!")
        #     return
        #
        # if verbose_flag:
        #     print(f"User prompt: {prompt}")
        #     print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        #     print(f"Response tokens: {
        #         response.usage_metadata.candidates_token_count}")
        #
        # if response.candidates:
        #     for candidate in response.candidates:
        #         if candidate is None or candidate.content is None:
        #             continue
        #         messages.append(candidate.content)
        #
        # if response.function_calls:
        #     for function_call in response.function_calls:
        #         result = call_function(function_call, verbose_flag)
        #         messages.append(result)
        # else:
        #     print(response.text)
        #     return


main()
