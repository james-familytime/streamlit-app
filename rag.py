import streamlit as st
import aiohttp
import asyncio
import logging
from urllib.parse import urljoin
from json import loads, JSONDecodeError

# Logger setup
logger = logging.getLogger(__name__)

# Base URL and headers
BASE_URL = "https://staging.rag.familytime.ai/"
FAMILY_ID = "10af0003-6a86-458d-b013-6a05b7eb7f59"
AUTHORIZATION_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM2OTYxNDMwLCJpYXQiOjE3MjgzMjE0MzAsImp0aSI6IjM2YmUyZWQyZjRiMjRiOTA4YWRkNjIyZmIxM2JlMjY3IiwidXNlcl9pZCI6IjRkNTM5YjgxLTVmZGYtNDUyMi1iNDhmLTA5ODQ1ZjY0NTYxZCJ9.jiCTj_IeCWQxMoM8lCxIDj_7OEcmJCWky_0_6oX__uI"

headers = {
    "Authorization": AUTHORIZATION_TOKEN,
    "Content-Type": "application/json",
}

# Asynchronous helper to fetch streaming responses
async def fetch_stream(url: str, payload: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunk = chunk.decode("utf-8")
                        for line in chunk.splitlines():
                            if line.startswith("data:"):
                                sse_data = line[5:].strip()
                                try:
                                    json_data = loads(sse_data)
                                    yield json_data
                                except JSONDecodeError:
                                    logger.error("Failed to decode JSON from SSE data")
            else:
                logger.error(f"Request failed with status {response.status}")
                yield None

# Async function to start a new chat session
async def start_chat(query: str):
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/start/"
    full_url = urljoin(BASE_URL, query_url)
    payload = {"query": query}
    async for json_data in fetch_stream(full_url, payload):
        if json_data:
            chunk_type = json_data.get('chunk_type')
            data = json_data.get('data')
            if chunk_type == "session":
                st.session_state.conversation_id = data
            elif chunk_type == "terminate":
                return
            else:
                yield data

# Async function to continue an existing chat session
async def continue_chat(query: str, conversation_id: str):
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/{conversation_id}/messages/"
    full_url = urljoin(BASE_URL, query_url)
    payload = {"query": query}
    async for json_data in fetch_stream(full_url, payload):
        if json_data:
            chunk_type = json_data.get('chunk_type')
            data = json_data.get('data')
            if chunk_type == "terminate":
                return
            else:
                yield data

# Helper function to display previous messages
def get_previous_messages(conversation_id: str):
    query_url = f"../api/v1/families/{FAMILY_ID}/conversations/{conversation_id}/messages/"
    full_url = urljoin(BASE_URL, query_url)
    # Simulate fetching previous messages for the current conversation
    response = []
    #response = query_rag(url=full_url, method='get')
    return response or []

# Streamlit app title
st.title("FamilyTime RAG Chat")
st.write("This is intended for testing the RAG Chat. Limited data for Nick's family can be queried.")

# Initialize session state for messages and conversation ID
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# Retrieve and display previous messages if conversation ID exists
if st.session_state.conversation_id and not st.session_state.messages:
    st.session_state.messages = get_previous_messages(st.session_state.conversation_id)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input and stream responses
if prompt := st.chat_input("What is up?"):
    # Display user message in chat
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Placeholder for assistant's response
    assistant_response_placeholder = st.empty()

    # Coroutine to handle streaming responses and display them
    async def display_streamed_response():
        responses = []
        response_stream = start_chat(query=prompt)

        # Update the assistant's response progressively
        async for chunk in response_stream:
            responses.append(chunk)
            assistant_response_placeholder.markdown(''.join(responses))

        # Append final response to session state
        st.session_state.messages.append({"role": "assistant", "content": ''.join(responses)})

    # Run the streaming coroutine within Streamlit's async runtime
    asyncio.run(display_streamed_response())