"""
Main Streamlit application for the EU Database Assistant using Europeana API.
"""
import streamlit as st
import openai
import json
import os
from dotenv import load_dotenv

# Import our modules
from functions import (
    query_eu_regulations, get_eu_statistics, find_eu_institution
)
from tools import OPENAI_TOOLS

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# App title and description
st.title("EU Database Assistant")
st.write("Ask questions about EU regulations, statistics, or institutions powered by Europeana API.")

# Initialize or get chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


def process_response(response):
    """Process the OpenAI API response and handle function calls."""
    message = response.choices[0].message

    # Check if the model wants to call a function
    if message.tool_calls:
        # Display thinking state
        with st.chat_message("assistant"):
            st.write("Searching Europeana database...")

        # We'll need this to build our API messages
        tool_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in message.tool_calls
            ]
        }

        # Add the assistant message with tool calls to UI history
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Querying Europeana database..."
        })

        # Process each tool call
        tool_results = []
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Call the appropriate function
            function_response = ""
            if function_name == "query_eu_regulations":
                function_response = query_eu_regulations(
                    function_args.get("topic"),
                    function_args.get("domain")
                )
            elif function_name == "get_eu_statistics":
                function_response = get_eu_statistics(
                    function_args.get("country"),
                    function_args.get("metric")
                )
            elif function_name == "find_eu_institution":
                function_response = find_eu_institution(
                    function_args.get("name"),
                    function_args.get("location")
                )

            # Add to our tool results for API
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_response
            })

        # Prepare messages for the follow-up completion
        messages_for_api = []

        # Add all user and assistant messages before our tool calls
        for msg in st.session_state.messages:
            if msg["role"] in ["user", "assistant"]:
                messages_for_api.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Now add the tool_calls message and tool responses
        messages_for_api.append(tool_message)
        messages_for_api.extend(tool_results)

        # Get the final response from the model with all the tool results
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            tools=OPENAI_TOOLS
        )

        # Return the final response
        return final_response.choices[0].message

    # If no function call, just return the message
    return message


# User input
prompt_text = "Ask about EU regulations, statistics, or institutions..."
if prompt := st.chat_input(prompt_text):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get response from OpenAI
    with st.spinner("Thinking..."):
        messages_for_api = []
        for msg in st.session_state.messages:
            if msg["role"] == "user" or msg["role"] == "assistant":
                messages_for_api.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            tools=OPENAI_TOOLS
        )

    # Process the response
    assistant_message = process_response(response)

    # Display assistant response
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message.content}
    )
    with st.chat_message("assistant"):
        st.write(assistant_message.content)

# Add a sidebar with information
with st.sidebar:
    st.header("About This App")
    st.write("""
    This app demonstrates OpenAI's function calling capabilities to query
    the Europeana API database.
    
    The AI assistant can retrieve:
    - EU regulations and documents
    - Statistics about EU countries
    - Information about EU institutions
    
    Try asking questions like:
    - "What are the EU regulations on digital services?"
    - "Find statistics about Germany's economy"
    - "Tell me about the European Commission"
    """)

    st.divider()

    # Information about Europeana
    st.subheader("Powered by Europeana API")
    st.write("""
    This application uses the [Europeana API](https://pro.europeana.eu/page/apis) 
    to access cultural heritage collections from thousands of European institutions.
    
    The Europeana platform provides access to millions of digitized items including
    books, music, artworks, and more from European museums, galleries, libraries and archives.
    """)

    st.divider()

    # Display information about the auto-schema generation
    st.subheader("Technical Details")
    st.write("""
    This app uses:
    
    1. Automatic schema generation to convert Python functions to OpenAI function schemas
    2. Europeana Search API for fetching real data about the EU
    3. OpenAI function calling to determine when to query the Europeana API
    """)

    # API key information
    st.subheader("API Keys Required")
    st.info("""
    This application requires:
    - An OpenAI API key
    - A Europeana API key
    
    Make sure to add both to your .env file.
    """)
