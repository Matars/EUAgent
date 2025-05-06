"""
Europeana API functions for the Streamlit application.
"""
import os
import requests
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Europeana API KEY
EUROPEANA_API_KEY = os.getenv("EUROPEANA_SECRET_API_KEY")

## Search API
def search_europeana(query: str, type: str = "TEXT", limit: int = 5) -> str:
    """
    General-purpose Europeana search function.

    Args:
        query: Search query string
        type: Media type filter (e.g., TEXT, IMAGE, VIDEO)
        limit: Number of results to return

    Returns:
        A formatted string of search results or an error message
    """
    logging.info(f"Searching Europeana for query='{query}', type='{type}', limit={limit}")
    
    url = "https://api.europeana.eu/record/v2/search.json"
    params = {
        "wskey": EUROPEANA_API_KEY,
        "query": query,
        "rows": limit,
        "qf": f"TYPE:{type.upper()}",
        "profile": "standard"
    }

    try:
        response = requests.get(url, params=params)
        logging.debug(f"Request URL: {response.url}")
        response.raise_for_status()
        data = response.json()

        if data.get("success") and data.get("itemsCount", 0) > 0:
            logging.info(f"Found {data['itemsCount']} items.")
            results = []
            for item in data.get("items", []):
                title = item.get("title", ["Unknown"])[0]
                description = item.get("dcDescription", ["No description"])[0] if "dcDescription" in item else "No description"
                source = item.get("dataProvider", ["Unknown"])[0]
                link = item.get("guid", "No link")
                preview = item.get("edmPreview", [None])[0]  # Small image preview

                preview_md = f"![Preview]({preview})" if preview else ""
                result = (
                    f"{preview_md}\n\n"
                    f"**Title:** {title}\n"
                    f"**Description:** {description}\n"
                    f"**Source:** {source}\n"
                    f"**URL:** {link}"
                )
                results.append(result)

            return f"Found {data['itemsCount']} results for '{query}' (type: {type}):\n\n" + "\n\n---\n\n".join(results)
        else:
            logging.warning(f"No results found for query: '{query}' (type: {type})")
            return f"No results found for '{query}' (type: {type})."

    except requests.RequestException as e:
        logging.error(f"Europeana API request error: {e}")
        return f"Error accessing Europeana API: {str(e)}"



## Record API
def get_europeana_record(record_id: str) -> str:
    """
    Retrieve a detailed Europeana record by ID. Returns comprehensive metadata including:
    - Title, creator, description, date
    - Image/viewing URLs (high quality, thumbnail, IIIF manifest)
    - Rights information and license
    - Provider and collection information
    - Technical metadata for images
    """
    # Normalize the record ID
    if record_id.startswith("http"):
        # Extract ID from URL like https://www.europeana.eu/item/9200579/b99e9hec
        record_id = "/" + record_id.split("item/")[-1]
    elif not record_id.startswith("/"):
        record_id = "/" + record_id

    url = f"https://api.europeana.eu/record/v2{record_id}.json"
    params = {"wskey": EUROPEANA_API_KEY, "profile": "full"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            return f"Record '{record_id}' not found."

        obj = data.get("object", {})
        europeana_agg = obj.get("europeanaAggregation", {})
        proxies = obj.get("proxies", [])
        aggregations = obj.get("aggregations", [{}])[0] if obj.get("aggregations") else {}

        # Extract metadata from both Europeana and provider proxies
        europeana_proxy = next((p for p in proxies if p.get("europeanaProxy")), None)
        provider_proxy = next((p for p in proxies if not p.get("europeanaProxy")), None)

        # Get basic metadata
        title = provider_proxy.get("dcTitle", {}).get("def", ["Unknown"])[0] if provider_proxy else "Unknown"
        creator = provider_proxy.get("dcCreator", {}).get("def", ["Unknown"])[0] if provider_proxy else "Unknown"
        description = provider_proxy.get("dcDescription", {}).get("en", ["No description"])[0] if provider_proxy else "No description"
        date = provider_proxy.get("dctermsCreated", {}).get("def", ["Unknown date"])[0] if provider_proxy else "Unknown date"
        rights = aggregations.get("edmRights", {}).get("def", ["Unknown"])[0] if aggregations else "Unknown"
        
        # Get provider information
        provider = "Unknown"
        country = "Unknown"
        if obj.get("organizations"):
            org = obj.get("organizations")[0]
            provider = org.get("prefLabel", {}).get("en", ["Unknown"])[0]
            country = org.get("country", "Unknown")

        # Get image/viewing URLs
        viewing_url = aggregations.get("edmIsShownAt", "Not available")
        image_url = aggregations.get("edmIsShownBy", "Not available")
        thumbnail_url = europeana_agg.get("edmPreview", "Not available")
        manifest_url = next(
            (res.get("about") for res in aggregations.get("webResources", [])
            if res.get("rdfType") == "http://iiif.io/api/presentation/3#Manifest"
        ), None)

        # Get technical metadata for images
        image_metadata = {}
        for res in aggregations.get("webResources", []):
            if res.get("ebucoreHasMimeType", "").startswith("image/"):
                image_metadata = {
                    "width": res.get("ebucoreWidth"),
                    "height": res.get("ebucoreHeight"),
                    "size": f"{round(res.get('ebucoreFileByteSize', 0)/1024):.1f} KB",
                    "mime_type": res.get("ebucoreHasMimeType"),
                    "colors": res.get("edmComponentColor", [])[:5] 
                }
                break

        # Format the output
        result = [
            f"**Title:** {title}",
            f"**Creator:** {creator}",
            f"**Description:** {description}",
            f"**Date:** {date}",
            f"**Type:** {obj.get('type', 'Unknown')}",
            f"**Rights:** {rights}",
            "",
            "**Provider Information:**",
            f"- Institution: {provider}",
            f"- Country: {country}",
            "",
            "**Access Links:**",
            f"- [View on Europeana]({europeana_agg.get('edmLandingPage', 'Not available')})",
            f"- [View on Provider Site]({viewing_url})" if viewing_url != "Not available" else "",
            f"- [IIIF Manifest]({manifest_url})" if manifest_url else "",
            "",
            "**Image Information:**",
            f"- [High Resolution Image]({image_url})" if image_url != "Not available" else "",
            f"- Thumbnail: {thumbnail_url}",
            f"- Dimensions: {image_metadata.get('width', '?')}×{image_metadata.get('height', '?')} pixels",
            f"- Size: {image_metadata.get('size', 'Unknown')}",
            f"- Format: {image_metadata.get('mime_type', 'Unknown')}",
            f"- Dominant colors: {', '.join(image_metadata.get('colors', []))}" if image_metadata.get("colors") else ""
        ]

        return "\n".join(filter(None, result))  # Remove empty lines

    except requests.RequestException as e:
        return f"Error accessing Europeana Record API: {str(e)}"
    
## Entity API
def search_europeana_entities(
    query: str,
    type: str = "all",
    scope: str = None,
    lang: str = "en",
    limit: int = 5
) -> str:
    """
    Search for entities (people, places, concepts, timespans, organizations) in Europeana's Entity API.
    
    Args:
        query: Search query string
        type: Entity type (agent, place, concept, timespan, organization, all)
        scope: Restrict to entities referenced in Europeana ('europeana')
        lang: Language code for results (default: en)
        limit: Number of results to return (max 100)
        
    Returns:
        A formatted string of entity search results or error message
    """
    url = "https://api.europeana.eu/entity/search"
    params = {
        "wskey": EUROPEANA_API_KEY,
        "query": query,
        "type": type,
        "pageSize": min(limit, 100),  # API max is 100
        "lang": lang,
        "profile": "facets"
    }
    
    if scope:
        params["scope"] = scope

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            return f"No entities found for '{query}' (type: {type})"

        results = []
        for item in data.get("items", [])[:limit]:
            entity_type = item.get("type", "entity").lower()
            pref_label = item.get("prefLabel", {}).get(lang, ["Unnamed"])[0]
            entity_id = item.get("id", "").split("/")[-1]
            
            result = (
                f"**Type:** {entity_type.capitalize()}\n"
                f"**Name:** {pref_label}\n"
                f"**ID:** {entity_id}\n"
                f"**Europeana URI:** {item.get('id')}"
            )
            
            # Add alternative labels if available
            if "altLabel" in item:
                alt_labels = item["altLabel"].get(lang, [])
                if alt_labels:
                    result += f"\n**Also known as:** {', '.join(alt_labels)}"
            
            results.append(result)

        return f"Found {len(data['items'])} entities for '{query}':\n\n" + "\n\n".join(results)

    except requests.RequestException as e:
        return f"Error accessing Europeana Entity API: {str(e)}"


def get_europeana_entity(
    entity_id: str,
    entity_type: str,
    lang: str = "en"
) -> str:
    """
    Retrieve detailed metadata about a specific Europeana entity (person, place, concept, etc.).
    
    Args:
        entity_id: The Europeana entity ID (e.g. '59904' for agent/59904)
        entity_type: The entity type (agent, place, concept, timespan, organization)
        lang: Preferred language for labels (default: en)
        
    Returns:
        A formatted string with detailed entity information or error message
    """
    valid_types = ["agent", "place", "concept", "timespan", "organization"]
    if entity_type not in valid_types:
        return f"Invalid entity type. Must be one of: {', '.join(valid_types)}"

    url = f"https://api.europeana.eu/entity/{entity_type}/{entity_id}.json"
    params = {
        "wskey": EUROPEANA_API_KEY,
        "profile": "external",
        "lang": lang
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract core metadata
        pref_label = data.get("prefLabel", {}).get(lang, ["Unnamed"])[0]
        entity_type = data.get("type", "entity").lower()
        
        result = [
            f"**Type:** {entity_type.capitalize()}",
            f"**Name:** {pref_label}",
            f"**Europeana URI:** {data.get('id')}",
            ""
        ]

        # Add alternative names
        if "altLabel" in data:
            alt_labels = data["altLabel"].get(lang, [])
            if alt_labels:
                result.append(f"**Also known as:** {', '.join(alt_labels)}")
                result.append("")

        # Add descriptions
        if "note" in data:
            notes = data["note"].get(lang, [])
            if notes:
                result.append("**Descriptions:**")
                result.extend(f"- {note}" for note in notes)
                result.append("")

        # Add biographical/historical info for agents
        if entity_type == "agent" and "biographicalInformation" in data:
            bio_info = data["biographicalInformation"].get(lang, [])
            if bio_info:
                result.append("**Biographical Information:**")
                result.extend(f"- {info}" for info in bio_info)
                result.append("")

        # Add date info for timespans
        if entity_type == "timespan" and "begin" in data and "end" in data:
            result.append(f"**Time Period:** {data['begin']} to {data['end']}")
            result.append("")

        # Add geographical coordinates for places
        if entity_type == "place" and "lat" in data and "long" in data:
            result.append(f"**Coordinates:** {data['lat']}, {data['long']}")
            result.append("")

        # Add related entities
        relation_types = {
            "broader": "Broader Concepts",
            "narrower": "Narrower Concepts",
            "related": "Related Entities",
            "exactMatch": "Equivalent Entities"
        }

        for rel_type, label in relation_types.items():
            if rel_type in data:
                relations = []
                for rel in data[rel_type]:
                    rel_label = rel.get("prefLabel", {}).get(lang, ["Unnamed"])[0]
                    relations.append(f"{rel_label} ({rel.get('id')})")
                
                if relations:
                    result.append(f"**{label}:**")
                    result.extend(f"- {rel}" for rel in relations)
                    result.append("")

        return "\n".join(result)

    except requests.RequestException as e:
        return f"Error accessing Europeana Entity API: {str(e)}"