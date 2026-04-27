import json
from config import WORKING_DIR
from functions.get_file_content import get_file_content
from functions.get_files_info import get_files_info
from functions.run_python_file import run_python_file
from functions.write_file import write_file

TOOL_REGISTRY = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
    "run_python_file": run_python_file,
}

working_directory = WORKING_DIR

def call_function(function_name: str, args: dict, verbose: bool = False) -> str:
    """Executes a requested tool call and returns the result as a string."""
    if verbose:
        print(f"Calling function: {function_name}({json.dumps(args)})")
    else:
        print(f"- Calling function: {function_name}")

    func = TOOL_REGISTRY.get(function_name)
    if not func:
        error_msg = f"Error: Unknown function '{function_name}'. Available functions are: {list(TOOL_REGISTRY.keys())}"
        if verbose: print(error_msg)
        return error_msg

    try:
        result = func(working_directory, **args)
        
        if result is None:
            return "Success: Function executed but returned no output."
        return str(result)
        
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        if verbose: print(error_msg)
        return error_msg
