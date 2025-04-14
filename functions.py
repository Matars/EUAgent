"""
Europeana API functions for the Streamlit application.
"""
import os
import requests
from typing import Optional

# Europeana API base URL
EUROPEANA_API_BASE = "https://api.europeana.eu/record/v2/search.json"
EUROPEANA_API_KEY = os.getenv("EUROPEANA_API_KEY")


def query_eu_regulations(topic: str, domain: Optional[str] = None) -> str:
    """
    Search for EU regulations related to a specific topic in Europeana.

    Args:
        topic: The topic to search for
        domain: Optional specific domain within the topic

    Returns:
        A string with the search results
    """
    # Build query parameters
    params = {
        "query": topic,
        "wskey": EUROPEANA_API_KEY,
        "rows": 5  # Limit to 5 results
    }

    # Add domain as a refinement if provided
    if domain:
        params["qf"] = f"what:{domain}"

    # Make request to Europeana API
    try:
        response = requests.get(EUROPEANA_API_BASE, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        data = response.json()

        if data.get("success", False) and data.get("itemsCount", 0) > 0:
            # Format the results
            results = [
                f"Title: {item.get('title', ['Unknown'])[0]}\n"
                f"Description: {item.get('dcDescription', ['No description'])[0] if 'dcDescription' in item else 'No description'}\n"
                f"Source: {item.get('dataProvider', ['Unknown'])[0]}\n"
                f"URL: {item.get('guid', 'No link')}\n"
                for item in data.get("items", [])
            ]

            return (
                f"Found {data.get('itemsCount')} EU documents about '{topic}'"
                f"{f' in domain {domain}' if domain else ''}:\n\n" +
                "\n\n".join(results)
            )
        else:
            return f"No EU regulations found for '{topic}'{f' in domain {domain}' if domain else ''}."

    except requests.RequestException as e:
        return f"Error accessing Europeana API: {str(e)}"


def get_eu_statistics(country: str, metric: Optional[str] = None) -> str:
    """
    Search for statistics related to an EU country in Europeana.

    Args:
        country: The EU country to get statistics for
        metric: Optional specific metric to look for

    Returns:
        A string with the search results
    """
    # Build query parameters
    query = f"\"{country}\" AND (statistics OR data OR figures)"
    if metric:
        query += f" AND {metric}"

    params = {
        "query": query,
        "wskey": EUROPEANA_API_KEY,
        "rows": 5,  # Limit to 5 results
        "profile": "standard"  # Get standard metadata
    }

    # Make request to Europeana API
    try:
        response = requests.get(EUROPEANA_API_BASE, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        data = response.json()

        if data.get("success", False) and data.get("itemsCount", 0) > 0:
            # Format the results
            results = [
                f"Title: {item.get('title', ['Unknown'])[0]}\n"
                f"Description: {item.get('dcDescription', ['No description'])[0] if 'dcDescription' in item else 'No description'}\n"
                f"Source: {item.get('dataProvider', ['Unknown'])[0]}\n"
                f"URL: {item.get('guid', 'No link')}\n"
                for item in data.get("items", [])
            ]

            result_text = (
                f"Found {data.get('itemsCount')} statistical documents about '{country}'"
                f"{f' related to {metric}' if metric else ''}:\n\n" +
                "\n\n".join(results)
            )
            return result_text
        else:
            search_desc = f"'{country}'{f' related to {metric}' if metric else ''}"
            return f"No statistical information found for {search_desc}."

    except requests.RequestException as e:
        return f"Error accessing Europeana API: {str(e)}"


def find_eu_institution(name: Optional[str] = None, location: Optional[str] = None) -> str:
    """
    Search for information about EU institutions in Europeana.

    Args:
        name: Optional name of the institution to search for
        location: Optional location to find institutions in

    Returns:
        A string with the search results
    """
    # Build query parameters
    if name and location:
        query = f"\"{name}\" AND \"{location}\" AND (institution OR organization OR authority)"
    elif name:
        query = f"\"{name}\" AND (institution OR organization OR authority OR agency OR body)"
    elif location:
        query = f"\"{location}\" AND (institution OR organization OR EU OR European Union)"
    else:
        query = "\"European Union\" AND (institution OR organization OR authority OR agency OR body)"

    params = {
        "query": query,
        "wskey": EUROPEANA_API_KEY,
        "rows": 5,  # Limit to 5 results
        "profile": "standard"  # Get standard metadata
    }

    # Make request to Europeana API
    try:
        response = requests.get(EUROPEANA_API_BASE, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        data = response.json()

        if data.get("success", False) and data.get("itemsCount", 0) > 0:
            # Format the results
            results = [
                f"Title: {item.get('title', ['Unknown'])[0]}\n"
                f"Description: {item.get('dcDescription', ['No description'])[0] if 'dcDescription' in item else 'No description'}\n"
                f"Source: {item.get('dataProvider', ['Unknown'])[0]}\n"
                f"URL: {item.get('guid', 'No link')}\n"
                for item in data.get("items", [])
            ]

            search_desc = []
            if name:
                search_desc.append(f"institution '{name}'")
            if location:
                search_desc.append(f"location '{location}'")

            search_text = " in ".join(
                search_desc) if search_desc else "EU institutions"

            result_text = (
                f"Found {data.get('itemsCount')} documents about {search_text}:\n\n" +
                "\n\n".join(results)
            )
            return result_text
        else:
            search_desc = []
            if name:
                search_desc.append(f"institution '{name}'")
            if location:
                search_desc.append(f"location '{location}'")

            search_text = " in ".join(
                search_desc) if search_desc else "EU institutions"
            return f"No information found for {search_text}."

    except requests.RequestException as e:
        return f"Error accessing Europeana API: {str(e)}"
