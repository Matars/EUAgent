"""
OpenAI function tool definitions for the Europeana search AI agent.
"""
from functions import search_europeana, get_europeana_record, search_europeana_entities, get_europeana_entity
from schema_utils import function_to_schema, get_function_descriptions, enhance_schema

# Generate schema and descriptions
function_descriptions = get_function_descriptions()

# Setup search_europeana schema
search_schema = function_to_schema(search_europeana)
enhanced_search_schema = enhance_schema(search_schema, function_descriptions)

# Initialize properties if they don't exist
enhanced_search_schema.setdefault("function", {}).setdefault("parameters", {}).setdefault("properties", {})

# Update descriptions and parameters
enhanced_search_schema["function"]["description"] = (
    "Search Europeana's digital archive when the user wants to discover items or asks general questions. "
    "Use this for initial searches, not for detailed metadata about known items. Returns record IDs that "
    "can be used with get_europeana_record for more details."
)

enhanced_search_schema["function"]["parameters"]["properties"].setdefault("query", {})[
    "description"
] = "The search query string (e.g., 'Dutch paintings 17th century', 'European Parliament')"

enhanced_search_schema["function"]["parameters"]["properties"].setdefault("type", {})[
    "description"
] = "Media type to filter results: TEXT, IMAGE, VIDEO, SOUND, or 3D"

enhanced_search_schema["function"]["parameters"]["properties"].setdefault("limit", {})[
    "description"
] = "Number of results to return (default: 5)"

# Add enum values for "type"
enhanced_search_schema["function"]["parameters"]["properties"]["type"]["enum"] = [
    "TEXT", "IMAGE", "VIDEO", "SOUND", "3D"
]

# Setup get_europeana_record schema
record_schema = function_to_schema(get_europeana_record)
enhanced_record_schema = enhance_schema(record_schema, function_descriptions)

# Initialize properties if they don't exist
enhanced_record_schema.setdefault("function", {}).setdefault("parameters", {}).setdefault("properties", {})

# Update descriptions and parameters
enhanced_record_schema["function"]["description"] = (
    "Get comprehensive metadata about a specific Europeana item when the user asks for detailed information "
    "or when you have a record ID. This returns rich metadata including title, creator, description, date, "
    "rights information, images, and more. Always use this when the user asks for details about a specific item."
)

enhanced_record_schema["function"]["parameters"]["properties"].setdefault("record_id", {})[
    "description"
] = (
    "The Europeana record ID (GUID) to retrieve. Can be in these formats:\n"
    "- Full URL: 'https://www.europeana.eu/item/9200579/b99e9hec'\n"
    "- Path format: '/9200579/b99e9hec'\n"
    "- ID only: '9200579/b99e9hec'\n"
    "The function will automatically normalize the ID format."
)

# Add examples to help the model understand when to use this function
enhanced_record_schema["function"]["parameters"]["properties"]["record_id"]["examples"] = [
    "9200579/b99e9hec",
    "/9200333/BibliographicResource_3000117298548",
    "https://www.europeana.eu/item/9200396/9C6B5C6E4C7B8D9A1B2C3D4E5F6G7H8"
]

# Update tools.py

# ... (keep existing imports and setup)

# Add new entity schemas
entity_search_schema = function_to_schema(search_europeana_entities)
enhanced_entity_search_schema = enhance_schema(entity_search_schema, function_descriptions)

# Initialize and enhance properties
enhanced_entity_search_schema.setdefault("function", {}).setdefault("parameters", {}).setdefault("properties", {})

enhanced_entity_search_schema["function"]["parameters"]["properties"].setdefault("query", {})[
    "description"
] = "The search query for entities (e.g., 'Vincent van Gogh', 'Art Nouveau', 'Paris')"

enhanced_entity_search_schema["function"]["parameters"]["properties"].setdefault("type", {})[
    "description"
] = "Entity type to filter: agent, place, concept, timespan, organization, or all"

enhanced_entity_search_schema["function"]["parameters"]["properties"].setdefault("scope", {})[
    "description"
] = "Optional scope filter (use 'europeana' to limit to entities referenced in Europeana)"

enhanced_entity_search_schema["function"]["parameters"]["properties"].setdefault("lang", {})[
    "description"
] = "Preferred language for results (2-letter ISO code, default: en)"

enhanced_entity_search_schema["function"]["parameters"]["properties"].setdefault("limit", {})[
    "description"
] = "Number of results to return (default: 5, max: 100)"

# Add enum values for type
enhanced_entity_search_schema["function"]["parameters"]["properties"]["type"]["enum"] = [
    "agent", "place", "concept", "timespan", "organization", "all"
]

# Setup get_europeana_entity schema
entity_schema = function_to_schema(get_europeana_entity)
enhanced_entity_schema = enhance_schema(entity_schema, function_descriptions)

# Initialize and enhance properties
enhanced_entity_schema.setdefault("function", {}).setdefault("parameters", {}).setdefault("properties", {})

enhanced_entity_schema["function"]["parameters"]["properties"].setdefault("entity_id", {})[
    "description"
] = "The Europeana entity ID (e.g. '59904' for agent/59904)"

enhanced_entity_schema["function"]["parameters"]["properties"].setdefault("entity_type", {})[
    "description"
] = "The entity type: agent, place, concept, timespan, or organization"

enhanced_entity_schema["function"]["parameters"]["properties"].setdefault("lang", {})[
    "description"
] = "Preferred language for metadata (2-letter ISO code, default: en)"

# Add enum values for entity_type
enhanced_entity_schema["function"]["parameters"]["properties"]["entity_type"]["enum"] = [
    "agent", "place", "concept", "timespan", "organization"
]

# Register the tools (Always update OPENAI_TOOLS to include new functions)
OPENAI_TOOLS = [
    enhanced_search_schema,
    enhanced_record_schema,
    enhanced_entity_search_schema,
    enhanced_entity_schema
]