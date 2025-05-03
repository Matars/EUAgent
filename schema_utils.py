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
            "Use this function to search Europeana's digital archive for cultural heritage items "
            "when the user asks general questions or wants to discover items. "
            "Examples: 'Show me Dutch paintings', 'Find images of the Eiffel Tower'."
        ),
        "get_europeana_record": (
            "Use this function when the user asks for detailed metadata about a specific item "
            "or when you need comprehensive information about a known Europeana record. "
            "This function requires a Europeana record ID. "
            "Examples: 'Show me the full metadata for record 90402/RP_P_1984_87', "
            "'Give me all details about this artwork'."
        ),
        "search_europeana_entities": (
            "Use this function to search for entities (people, places, concepts, time periods, organizations) "
            "in Europeana's Entity API. Useful when the user asks about cultural figures, historical periods, "
            "or geographical locations. Examples: 'Find information about Vincent van Gogh', "
            "'What places are associated with Art Nouveau?'"
        ),
        "get_europeana_entity": (
            "Use this function to get detailed information about a specific Europeana entity "
            "(person, place, concept, time period, or organization). Requires the entity ID and type. "
            "Examples: 'Get details about entity agent/59904', "
            "'Tell me more about the Art Nouveau concept'"
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
