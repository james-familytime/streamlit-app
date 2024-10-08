import streamlit as st
import requests
import logging
import time
from typing import List, Dict
from urllib.parse import urljoin
from json import loads, JSONDecodeError
logger = logging.getLogger(__name__)

# Base URL
BASE_URL = "http://localhost:9000/"


FAMILY_ID = "10af0003-6a86-458d-b013-6a05b7eb7f59"

AUTHORIZATION_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM2OTYxNDMwLCJpYXQiOjE3MjgzMjE0MzAsImp0aSI6IjM2YmUyZWQyZjRiMjRiOTA4YWRkNjIyZmIxM2JlMjY3IiwidXNlcl9pZCI6IjRkNTM5YjgxLTVmZGYtNDUyMi1iNDhmLTA5ODQ1ZjY0NTYxZCJ9.jiCTj_IeCWQxMoM8lCxIDj_7OEcmJCWky_0_6oX__uI"

headers = {
    "Authorization": AUTHORIZATION_TOKEN
}

def query_rag(url, payload: dict | None = None, method: str = "post") -> Dict | None:
    response: dict | None = None
    try:
        if method == "post":
            response = requests.post(
                url=url,
                json=payload,
                headers=headers,
            )
        else:
            response = requests.get(
                url=url,
                headers=headers
            )

        if response and response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.critical(f"Something went wrong due to error: {e}")
        return None

def get_previous_messages(conversation_id: str) -> List[Dict]:
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/{conversation_id}/messages/"
    full_url = urljoin(BASE_URL, query_url)

    response = query_rag(
        url=full_url,
        method='get'
    )

    if response:
        return response
    else:
        return []

# Use generators for streaming responses
def continue_chat(query: str, conversation_id: str):
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/{conversation_id}/messages/"
    full_url = urljoin(BASE_URL, query_url)

    payload = {
        "query": query,
    }

    try:
        response = requests.post(
            full_url,
            json=payload,
            headers=headers,
            stream=True,  # Only necessary for large responses
        )

        # Check if the request was successful (status code 200 OK)
        if response.status_code == 200:
            # Process the response stream
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:  # Filter out keep-alive chunks
                    # SSE typically comes with `data:` prefix, extract the JSON after `data:`
                    for line in chunk.splitlines():
                        if line.startswith("data:"):
                            try:
                                # Remove the "data:" prefix and strip any extra spaces
                                sse_data = line[5:].strip()
                                
                                # Load the JSON data
                                json_data = loads(sse_data)
                                
                                # Access chunk_type and data fields
                                chunk_type = json_data.get('chunk_type', None)
                                data = json_data.get('data', None)
                                
                                # Handle the decoded data based on chunk_type
                                if chunk_type != "session" and chunk_type != "terminate":
                                     yield data
                                elif chunk_type == "session":
                                    st.session_state.conversation_id = data.get('id')
                                elif chunk_type == "terminate":
                                    print("Session terminated")
                                else:
                                    print(f"Unknown chunk_type: {chunk_type}, Data: {data}")

                            except JSONDecodeError:
                                print("Failed to decode JSON from SSE data")
        else:
            print(f"Request failed with status code {response.status_code}")
            print(response.text)  # To see the error message from the server
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def start_chat(query: str):
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/start/"
    full_url = urljoin(BASE_URL, query_url)

    payload = {
        "query": query,
    }

    try:
        response = requests.post(
            full_url,
            json=payload,
            headers=headers,
            stream=True,  # Only necessary for large responses
        )

        # Check if the request was successful (status code 200 OK)
        if response.status_code == 200:
            # Process the response stream
            for chunk in response.iter_content(chunk_size=500, decode_unicode=True):
                if chunk:  # Filter out keep-alive chunks
                    # SSE typically comes with `data:` prefix, extract the JSON after `data:`
                    for line in chunk.splitlines():
                        if line.startswith("data:"):
                            try:
                                # Remove the "data:" prefix and strip any extra spaces
                                sse_data = line[5:].strip()
                                
                                # Load the JSON data
                                json_data = loads(sse_data)
                                
                                # Access chunk_type and data fields
                                chunk_type = json_data.get('chunk_type', None)
                                data = json_data.get('data', None)
                                
                                # Handle the decoded data based on chunk_type
                                if chunk_type != "session" and chunk_type != "sources" and chunk_type != "terminate":
                                     yield data
                                elif chunk_type == "session":
                                    st.session_state.conversation_id = data
                                    print(f"Session data: {data}")
                                elif chunk_type == "terminate":
                                    print("Session terminated")
                                else:
                                    print(f"Unknown chunk_type: {chunk_type}, Data: {data}")

                            except JSONDecodeError:
                                print("Failed to decode JSON from SSE data")
        else:
            print(f"Request failed with status code {response.status_code}")
            print(response.text)  # To see the error message from the server

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


# Streamlit app title
st.title("FamilyTime RAG Chat")
st.write("Disclaimer: This is intended for testing the RAG CHAT. \nOnly limited data for Nick's family can be queried")

# Initialize session state for messages and conversation ID
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# Retrieve previous messages if conversation_id exists
if st.session_state.conversation_id and not st.session_state.messages:
    st.session_state.messages = get_previous_messages(st.session_state.conversation_id)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input and stream responses
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container progressively
    with st.chat_message("assistant"):
        if st.session_state.conversation_id:
            response_stream = continue_chat(query=prompt, conversation_id=st.session_state.conversation_id)
        else:
            response_stream = start_chat(query=prompt)

        # Use write_stream() to handle the streamed response
        st.write_stream(response_stream)

        # Store assistant response in session state for chat history
        st.session_state.messages.append({"role": "assistant", "content": ''.join(response_stream)})