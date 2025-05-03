"""
Main Streamlit application for the EU Database Assistant using Europeana API.
"""

import streamlit as st
import openai
import json
import os
import logging
from dotenv import load_dotenv

from functions import search_europeana, get_europeana_record, search_europeana_entities, get_europeana_entity
from tools import OPENAI_TOOLS

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()

# Create OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up the Streamlit interface
st.title("Europeana Database Assistant")
st.write("Ask questions about EU Cultural Heritage using Europeana's APIs.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # System message will be used by OpenAI but not displayed
    st.session_state.system_message = {
        "role": "system",
        "content": (
            "You are an AI assistant for Europeana, the EU digital cultural heritage platform. "
            "Follow these guidelines for function calling:\n\n"
            "1. For searching cultural heritage objects (artworks, books, etc.):\n"
            "   - Use search_europeana for general searches\n"
            "   - Use get_europeana_record when users ask for detailed metadata about specific items\n"
            "   - When search results include record IDs and users ask for more details, call get_europeana_record\n\n"
            "2. For searching contextual entities (people, places, concepts, etc.):\n"
            "   - Use search_europeana_entities when users ask about cultural figures, historical periods, "
            "geographical locations, or artistic movements\n"
            "   - Use get_europeana_entity when users ask for detailed information about specific entities\n\n"
            "3. Combine approaches when appropriate:\n"
            "   - After finding relevant entities, you might search for related cultural objects\n"
            "   - When discussing objects, you might provide contextual entity information\n"
            "4. Always prefer specific functions (get_*) when you have exact identifiers\n"
            "5. For broad exploratory queries, start with search functions"
        )
    }

# Display only user and assistant messages (excluding system messages)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


def process_response(response):
    """
    Process the response from the OpenAI API, including any tool calls.
    """
    message = response.choices[0].message

    if hasattr(message, "tool_calls") and message.tool_calls:
        with st.chat_message("assistant"):
            st.write("Searching Europeana database...")

        TOOL_FUNCTIONS = {
            "search_europeana": search_europeana,
            "get_europeana_record": get_europeana_record,
            "search_europeana_entities": search_europeana_entities,
            "get_europeana_entity": get_europeana_entity
        }

        tool_results = []
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            logging.info(f"Assistant called function: {tool_name} with arguments: {function_args}")

            if tool_name in TOOL_FUNCTIONS:
                try:
                    function_response = TOOL_FUNCTIONS[tool_name](**function_args)
                except Exception as e:
                    function_response = f"Error while executing function '{tool_name}': {str(e)}"
                    logging.error(function_response)

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response
                })
            else:
                error_msg = f"Tool '{tool_name}' not implemented."
                logging.warning(error_msg)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_msg
                })

        # Include system message in the API call but not in displayed messages
        messages_for_api = [st.session_state.system_message] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages if m["role"] in ["user", "assistant"]
        ] + [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": message.tool_calls
            }
        ] + tool_results

        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            tools=OPENAI_TOOLS
        )

        return final_response.choices[0].message

    return message


# Prompt input from the user
prompt_text = "Ask anything about Europeana..."
if prompt := st.chat_input(prompt_text):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Thinking..."):
        # Include system message in the API call but not in displayed messages
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[st.session_state.system_message] + [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
            ],
            tools=OPENAI_TOOLS
        )

    assistant_message = process_response(response)

    # Append final message and show it
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message.content}
    )
    with st.chat_message("assistant"):
        st.write(assistant_message.content)

# Sidebar with app info
with st.sidebar:
    st.header("About This App")
    st.write("""
        This app demonstrates OpenAI function calling with Europeana data.
        Try questions like:
        - "Show me Dutch paintings from 17th century"
        - "Give me images related to European Parliament"
        - "Find information about Vincent van Gogh"
        - "Tell me about the Renaissance period"
    """)
    st.divider()
    st.subheader("Powered by Europeana API")
    st.write("Searches cultural heritage items and entities from EU institutions and collections.")
    st.divider()
    st.subheader("Requires .env")
    st.info("You need both an OpenAI and Europeana API key in your .env file.")