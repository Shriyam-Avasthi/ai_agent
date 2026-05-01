import inspect
import json
import logging

from config import LOGGER_ID, WORKING_DIR
from functions.edit_file import edit_file
from functions.expand_block import expand_block
from functions.get_file_skeleton import get_file_skeleton
from functions.list_directory import list_directory
from functions.manage_scratchpad import manage_scratchpad
from functions.run_python_file import run_python_file
from functions.write_file import write_file

TOOL_REGISTRY = {
    "write_file": write_file,
    "run_python_file": run_python_file,
    "manage_scratchpad": manage_scratchpad,
    "edit_file": edit_file,
    "expand_block": expand_block,
    "get_file_skeleton": get_file_skeleton,
    "list_directory": list_directory,
}

working_directory = WORKING_DIR
logger = logging.getLogger(LOGGER_ID)


def call_function(function_name: str, args: dict) -> str:
    logger.info(f"Calling function: {function_name}")
    logger.debug(f"Function Args: {json.dumps(args)}")

    func = TOOL_REGISTRY.get(function_name)
    if not func:
        error_msg = f"Error: Unknown function '{function_name}'. Available functions are: {list(TOOL_REGISTRY.keys())}"
        logger.error(error_msg)
        return error_msg

    try:
        sig = inspect.signature(func)
        if "working_dir" in sig.parameters:
            args["working_dir"] = working_directory
        elif "working_directory" in sig.parameters:
            args["working_directory"] = working_directory

        result = func(**args)

        if result is None:
            msg = "Success: Function executed but returned no output."
            logger.debug(msg)
            return msg

        logger.debug(
            f'Function "{function_name}" returned successfully.\nCall result:{str(result)}'
        )
        return str(result)

    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        logger.exception(error_msg)
        return error_msg
