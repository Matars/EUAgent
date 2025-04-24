"""
Utility functions for converting Python functions to OpenAI function schemas.
"""
import inspect
from typing import Dict


def function_to_schema(func) -> dict:
    """
    Convert a Python function to an OpenAI function schema.

    Args:
        func: The Python function to convert

    Returns:
        dict: An OpenAI function calling schema
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            error_msg = (
                f"Unknown type annotation {param.annotation} "
                f"for parameter {param.name}: {str(e)}"
            )
            raise KeyError(error_msg)
        parameters[param.name] = {"type": param_type}

    # IMPORTANT: Include ALL parameters in required (even optional ones)
    # This is needed for function calling with OpenAI
    required = list(parameters.keys())

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def get_function_descriptions() -> Dict[str, str]:
    return {
        "search_europeana": (
            "Search Europeana's vast digital archive of European cultural heritage items. "
            "You can search for documents, images, videos, and more using any query string."
        )
    }



def enhance_schema(schema: dict, function_desc: Dict[str, str]) -> dict:
    """
    Enhance a function schema with more detailed descriptions.

    Args:
        schema: The generated schema from function_to_schema
        function_desc: Dictionary mapping function names to descriptions

    Returns:
        dict: Enhanced schema with better descriptions
    """
    func_name = schema["function"]["name"]
    if func_name in function_desc:
        schema["function"]["description"] = function_desc[func_name]

    return schema
