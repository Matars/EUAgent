"""
OpenAI function tool definitions for the EU database assistant.
"""
from functions import query_eu_regulations, get_eu_statistics, find_eu_institution
from schema_utils import function_to_schema, get_function_descriptions, enhance_schema

# Get detailed descriptions for better documentation
function_descriptions = get_function_descriptions()

# Generate OpenAI function schemas from our functions
schemas = [
    function_to_schema(query_eu_regulations),
    function_to_schema(get_eu_statistics),
    function_to_schema(find_eu_institution)
]

# Enhance schemas with detailed descriptions
enhanced_schemas = [
    enhance_schema(schema, function_descriptions) for schema in schemas
]

# Add parameter descriptions
enhanced_schemas[0]["function"]["parameters"]["properties"]["topic"]["description"] = (
    "The topic to search for (e.g., agriculture, privacy)"
)
enhanced_schemas[0]["function"]["parameters"]["properties"]["domain"]["description"] = (
    "Optional specific domain within the topic"
)

enhanced_schemas[1]["function"]["parameters"]["properties"]["country"]["description"] = (
    "The EU country to get statistics for"
)
enhanced_schemas[1]["function"]["parameters"]["properties"]["metric"]["description"] = (
    "Optional metric (population, gdp, eu_contribution, etc)"
)

enhanced_schemas[2]["function"]["parameters"]["properties"]["name"]["description"] = (
    "Optional name of the institution to search for"
)
enhanced_schemas[2]["function"]["parameters"]["properties"]["location"]["description"] = (
    "Optional location to find institutions in"
)

# Define tools for the model
OPENAI_TOOLS = enhanced_schemas
