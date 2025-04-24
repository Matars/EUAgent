"""
Main Streamlit application for the EU Database Assistant using Europeana API.
"""
import streamlit as st
import openai
import json
import os
from dotenv import load_dotenv

from functions import search_europeana
from tools import OPENAI_TOOLS

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("EU Database Assistant")
st.write("Ask questions about EU topics using the Europeana API.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


def process_response(response):
    message = response.choices[0].message

    if message.tool_calls:
        with st.chat_message("assistant"):
            st.write("Searching Europeana database...")

        tool_results = []
        for tool_call in message.tool_calls:
            function_args = json.loads(tool_call.function.arguments)

            function_response = search_europeana(
                function_args.get("query", ""),
                function_args.get("type", "TEXT"),
                function_args.get("limit", 5)
            )

            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_response
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
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message.content}
    )
    with st.chat_message("assistant"):
        st.write(assistant_message.content)

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
