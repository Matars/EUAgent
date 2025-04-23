"""
OpenAI function tool definitions for the Europeana search AI agent.
"""
from functions import search_europeana
from schema_utils import function_to_schema, get_function_descriptions, enhance_schema

# Generate schema and descriptions
function_descriptions = get_function_descriptions()
schema = function_to_schema(search_europeana)
enhanced_schema = enhance_schema(schema, function_descriptions)

# Safely ensure the nested structure exists
enhanced_schema.setdefault("function", {}).setdefault("parameters", {}).setdefault("properties", {})

# Add descriptions
enhanced_schema["function"]["parameters"]["properties"].setdefault("query", {})[
    "description"
] = "The search query string (e.g., 'Dutch paintings 17th century', 'European Parliament')"

enhanced_schema["function"]["parameters"]["properties"].setdefault("type", {})[
    "description"
] = "Media type to filter results: TEXT, IMAGE, VIDEO, SOUND, or 3D"

enhanced_schema["function"]["parameters"]["properties"].setdefault("limit", {})[
    "description"
] = "Number of results to return (default: 5)"

# Add enum values for "type"
enhanced_schema["function"]["parameters"]["properties"]["type"]["enum"] = [
    "TEXT", "IMAGE", "VIDEO", "SOUND", "3D"
]

# Register the tool
OPENAI_TOOLS = [enhanced_schema]
