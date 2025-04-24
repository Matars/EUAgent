"""
Europeana API functions for the Streamlit application.
"""
import os
import requests
from typing import Optional

# Europeana API base URL
EUROPEANA_API_BASE = "https://api.europeana.eu/record/v2/search.json"
EUROPEANA_API_KEY = os.getenv("EUROPEANA_API_KEY")


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
    params = {
        "query": query,
        "wskey": EUROPEANA_API_KEY,
        "rows": limit,
        "qf": f"TYPE:{type.upper()}",
        "profile": "standard"
    }

    try:
        response = requests.get(EUROPEANA_API_BASE, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and data.get("itemsCount", 0) > 0:
            results = [
                f"Title: {item.get('title', ['Unknown'])[0]}\n"
                f"Description: {item.get('dcDescription', ['No description'])[0] if 'dcDescription' in item else 'No description'}\n"
                f"Source: {item.get('dataProvider', ['Unknown'])[0]}\n"
                f"URL: {item.get('guid', 'No link')}\n"
                for item in data.get("items", [])
            ]
            return f"Found {data['itemsCount']} results for '{query}' (type: {type}):\n\n" + "\n\n".join(results)
        else:
            return f"No results found for '{query}' (type: {type})."

    except requests.RequestException as e:
        return f"Error accessing Europeana API: {str(e)}"