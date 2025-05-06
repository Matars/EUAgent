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
            "2. Use get_europeana_record when users ask for detailed metadata about specific items\n"
            "   - When search results include record IDs and users ask for more details, call get_europeana_record\n\n"
            "3. For searching contextual entities (people, places, concepts, etc.):\n"
            "   - Use search_europeana_entities when users ask about cultural figures, historical periods, "
            "geographical locations, or artistic movements\n"
            "   - Use get_europeana_entity when users ask for detailed information about specific entities\n\n"
            "4. Combine approaches when appropriate:\n"
            "   - After finding relevant entities, you might search for related cultural objects\n"
            "   - When discussing objects, you might provide contextual entity information\n"
            "5. Always prefer specific functions (get_*) when you have exact identifiers\n"
            "6. For broad exploratory queries, start with search functions"
        )
    }

# Display only user and assistant messages (excluding system messages)
for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
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
                    # Ensure we have a valid response
                    if not function_response or function_response.strip() == "":
                        function_response = f"No results found for {tool_name} with these parameters"
                    logging.info(f"Function response: {function_response}")  # Log the actual response
                except Exception as e:
                    function_response = f"Error while executing function '{tool_name}': {str(e)}"
                    logging.error(function_response)

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(function_response)
                })
            else:
                error_msg = f"Tool '{tool_name}' not implemented."
                logging.warning(error_msg)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_msg
                })

        # Prepare messages for API including system message but not displaying it
        messages_for_api = [
            st.session_state.system_message,
            *[
                {"role": m["role"], "content": str(m["content"]) if m["content"] is not None else ""}
                for m in st.session_state.messages 
                if m["role"] in ["user", "assistant"]
            ],
            {
                "role": "assistant",
                "content": "",  # Never use null content
                "tool_calls": message.tool_calls
            },
            *tool_results
        ]

        try:
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_for_api,
                tools=OPENAI_TOOLS
            )
            
            # Return the message content only if it exists
            if final_response.choices[0].message.content:
                return final_response.choices[0].message
            else:
                # If no content, return the first tool response if available
                if tool_results and tool_results[0]['content']:
                    return openai.types.chat.ChatCompletionMessage(
                        role="assistant",
                        content=tool_results[0]['content']
                    )
                return openai.types.chat.ChatCompletionMessage(
                    role="assistant",
                    content="I found some information but couldn't format it properly. Here are the raw results."
                )
            
        except Exception as e:
            logging.error(f"Error in final response: {str(e)}")
            return openai.types.chat.ChatCompletionMessage(
                role="assistant",
                content="There was an error processing your request. Please try again."
            )

    # Handle case where message has no content
    if not message.content:
        return openai.types.chat.ChatCompletionMessage(
            role="assistant",
            content="I couldn't generate a response. Please try rephrasing your question."
        )
        
    return message

# Prompt input from the user
prompt_text = "Ask anything about Europeana..."
if prompt := st.chat_input(prompt_text):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Thinking..."):
        try:
            # Prepare messages ensuring no null content
            api_messages = [
                st.session_state.system_message,
                *[
                    {"role": msg["role"], "content": str(msg["content"]) if msg["content"] is not None else ""}
                    for msg in st.session_state.messages
                ]
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=api_messages,
                tools=OPENAI_TOOLS
            )
            
            assistant_message = process_response(response)
            
            # Ensure we always have content to display
            if assistant_message.content:
                st.session_state.messages.append({
                    "role": assistant_message.role,
                    "content": assistant_message.content
                })
                with st.chat_message("assistant"):
                    st.write(assistant_message.content)
            else:
                error_msg = "Sorry, I couldn't process your request. Please try again."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.write(error_msg)
                
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.write(error_msg)
            logging.error(f"API Error: {str(e)}")
            
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