import streamlit as st
import requests
import logging
import time
from typing import List, Dict
from urllib.parse import urljoin


logger = logging.getLogger(__name__)

# Base URL
BASE_URL = "https://api.familytime.ai/"

PROVIDER_IDS = ["62960448-5de8-46cb-ab27-5a030d596c65", "8f0cc0ab-4566-449b-989c-1c14ce61b386"]
FAMILY_ID = "10af0003-6a86-458d-b013-6a05b7eb7f59"

AUTHORIZATION_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM0NzI3ODQzLCJpYXQiOjE3MjYwODc4NDMsImp0aSI6IjhhYjUxNWZlMWNmZjQ5ZmZiMmYyMjY3NTMwYjM4NmI4IiwidXNlcl9pZCI6ImM0M2Q0Y2ZlLTk4MGItNDIzNS04YTVkLTdlNTcwZTdkODk2YSJ9.j1rRR9qutl9YmKHZ11fxGg4K1iFi7Np90mV4k0ptwWk"

headers = {
    "Authorization": AUTHORIZATION_TOKEN
}

# Streamed response emulator
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.1)

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

def continue_chat(query: str, conversation_id: str) -> str:
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/{conversation_id}/messages/"
    full_url = urljoin(BASE_URL, query_url)

    payload = {
        "query": query,
        "provider_ids": PROVIDER_IDS
    }

    response = query_rag(
        url=full_url,
        payload=payload
    )

    if response and response.get('content'):
        return response.get('content')
    else:
        return "Sorry, temporary service downtime. Retry later."


def start_chat(query: str) -> str:
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/start/"
    full_url = urljoin(BASE_URL, query_url)

    payload = {
        "query": query,
        "provider_ids": PROVIDER_IDS
    }

    response = query_rag(
        url=full_url,
        payload=payload
    )

    if response and response.get('content'):
        content = response.get('content')
        # Store conversation_id in session state
        st.session_state.conversation_id = response.get('conversation_id')
        return content
    else:
        return "Sorry, temporary service downtime. Retry later."


# Title of the web app
st.title("FamilyTime RAG Chat")
st.write("Disclaimer: This is intended for testing the RAG CHAT. \nOnly limited data for Nick's family can be queried")

# Initialize chat history and conversation_id in session state
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

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.conversation_id:
        response = continue_chat(query=prompt, conversation_id=st.session_state.conversation_id)
    else:
        response = start_chat(query=prompt)

    # Display assistant response in chat message container
    if response:
        with st.chat_message("assistant"):
            st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
