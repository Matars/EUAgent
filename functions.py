"""
Europeana API functions for the Streamlit application.
"""
import os
import requests
import logging
from typing import Optional

# Europeana API base URL
EUROPEANA_API_BASE = "https://api.europeana.eu/record/v2/search.json"
EUROPEANA_API_KEY = os.getenv("EUROPEANA_API_KEY")

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
    
    params = {
        "query": query,
        "wskey": EUROPEANA_API_KEY,
        "rows": limit,
        "qf": f"TYPE:{type.upper()}",
        "profile": "standard"
    }

    try:
        response = requests.get(EUROPEANA_API_BASE, params=params)
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