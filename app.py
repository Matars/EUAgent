"""
Main Streamlit application for the EU Database Assistant using Europeana API.
"""

import streamlit as st
import openai
import json
import os
import logging
from dotenv import load_dotenv

from functions import search_europeana, get_europeana_record
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

# Maintain session messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are an AI agent for Europeana, the EU digital cultural heritage platform. "
                "Use search_europeana for general searches and discovery. "
                "Use get_europeana_record when the user asks for detailed metadata about specific items. "
                "When search results include record IDs and the user asks for more details, call get_europeana_record."
            )
        }
    ]

# Display previous messages
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
            "get_europeana_record": get_europeana_record
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

        messages_for_api = [
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
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
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
    """)
    st.divider()
    st.subheader("Powered by Europeana API")
    st.write("Searches cultural heritage items from EU institutions and collections.")
    st.divider()
    st.subheader("Requires .env")
    st.info("You need both an OpenAI and Europeana API key in your .env file.")
