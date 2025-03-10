import streamlit as st
import requests
import aiohttp
import nest_asyncio
from urllib.parse import urljoin
import asyncio
from json import loads, JSONDecodeError
import logging

# Set up logging (optional)
logger = logging.getLogger(__name__)

# Enable nested event loops for async calls within Streamlit.
nest_asyncio.apply()

# --- Endpoint URLs (adjust as needed) ---
FT_DATA_BASE_URL = "https://staging.api.familytime.ai"
RAG_BASE_URL = "https://staging.rag.familytime.ai"
USER_ID = "09e2770e-73d7-4993-aec9-945b50a2a5d8"
AUTHORIZATION = (
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0NTQ5MDM3LCJpYXQiOjE3MzU5MDkwMzcsImp0aSI6ImMwNDRmNzk2ODZkYzQ4OTdiNmVhYmM5YjQyZjM2YTg1IiwidXNlcl9pZCI6IjA5ZTI3NzBlLTczZDctNDk5My1hZWM5LTk0NWI1MGEyYTVkOCJ9.gYBEVvei-mYANA8oPdOCEC6SbDB81AuJzkA6L5orwtA"
)
FAMILY_ID = "96b6c6be-710e-4126-9041-8b83eeb4b29d"
GET_MESSAGES_URL = urljoin(FT_DATA_BASE_URL, "../api/v1/families/{family_id}/conversations/{conversation_id}/messages/")
START_CONVERSATION_URL = urljoin(RAG_BASE_URL, f"../api/v1/families/{FAMILY_ID}/conversations/start/")
CONTINUE_CONVERSATION_URL = urljoin(RAG_BASE_URL, "../api/v1/families/{family_id}/conversations/{conversation_id}/continue/")
HEADERS = {
    "Authorization": AUTHORIZATION,
    "Content-Type": "application/json",
}

supported_models = {
    "GPT-4o": "openai:gpt-4o",
    "GPT-4o-mini": "openai:gpt-4o-mini",
}

supported_versions = {
    "Agentic RAG": "3",
    "Traditional RAG": "2",
}

suported_vectorstores = {
    "Qdrant": "qdrant",
    "Pinecone": "pinecone",
}

# --- Sidebar ---
with st.sidebar:
    with st.expander("Configuration", expanded=False):
        llm_model = st.selectbox("Choose LLM Model", list(supported_models.keys()))
        chat_app_version = st.selectbox("Chat App Version", list(supported_versions.keys()))
        vectorstore = st.selectbox("Vector Store", list(suported_vectorstores.keys()))
        web_search_enabled = st.checkbox("Enable Web Search", value=True)
    
    # New Conversation button placed below the Configuration expander.
    if st.button("New Conversation"):
        st.session_state.current_conversation_id = None
        st.session_state.current_messages = []
        st.session_state.has_sent_message = False
        st.rerun()

# --- Async Function for fetching messages ---
async def fetch_messages(conversation_id):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        url = GET_MESSAGES_URL.format(family_id=FAMILY_ID, conversation_id=conversation_id)
        async with session.get(url) as resp:
            data = await resp.json()
            results = data.get("results", [])
            messages = []
            for msg in results:
                user_msg = msg.get("user_query")
                assistant_msg = msg.get("answer")
                if user_msg:
                    messages.append({"role": "user", "message": user_msg})
                if assistant_msg:
                    messages.append({"role": "assistant", "message": assistant_msg})
            return messages

# --- Synchronous Streaming Generator using requests ---
def get_streaming_generator(query, config, endpoint):
    with requests.post(endpoint, json=config, headers=HEADERS, stream=True, timeout=180) as response:
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                for line in chunk.splitlines():
                    if line.startswith("data:"):
                        sse_data = line[5:].strip()
                        try:
                            json_data = loads(sse_data)
                            chunk_type = json_data.get("chunk_type")
                            
                            if chunk_type == "session":
                                # Update the session with the conversation ID returned from the assistant response.
                                st.session_state.current_conversation_id = json_data.get("data")
                            elif chunk_type in ("error", "llm_data"):
                                yield json_data.get('data')
                        except JSONDecodeError:
                            logger.error("Failed to decode JSON from SSE data")

def get_streamed_response(query, config, endpoint):
    return st.write_stream(get_streaming_generator(query, config, endpoint))

# Display conversation messages using a dedicated placeholder.
def display_conversation_messages(current_messages, info_placeholder):
    if not current_messages and not st.session_state.get("has_sent_message", False):
        info_placeholder.info("New messages will be displayed here")
    else:
        info_placeholder.empty()
        for message in current_messages:
            if message["role"] == "user":
                with st.chat_message("User"):
                    st.markdown(message["message"])
            else:
                with st.chat_message("Assistant"):
                    st.markdown(message["message"])

# --- Session State Initialization ---
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None  # None indicates new conversation mode
if "current_messages" not in st.session_state:
    st.session_state.current_messages = []  # List of messages
if "has_sent_message" not in st.session_state:
    st.session_state.has_sent_message = False  # Flag for user interaction

# --- Main Chat Interface ---
st.title("RAG Chat Application")
st.write("This is a simple chat interface for the RAG Chat application using Nick's family data.")
st.write("---")

# Create a placeholder for conversation messages (including info message).
message_placeholder = st.empty()
display_conversation_messages(st.session_state.current_messages, message_placeholder)

# Chat input: Wait for a new user message.
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.has_sent_message = True
    message_placeholder.empty()
    
    with st.chat_message("User"):
        st.markdown(user_input)
    st.session_state.current_messages.append({"role": "user", "message": user_input})
    
    config = {
        "llm_model": supported_models[llm_model],
        "version": supported_versions[chat_app_version],
        "vectorstore": suported_vectorstores[vectorstore],
        "enable_web_search": web_search_enabled,
        "user_id": USER_ID,
        "query": user_input
    }
    if st.session_state.current_conversation_id is None:
        endpoint = START_CONVERSATION_URL
    else:
        endpoint = CONTINUE_CONVERSATION_URL.format(family_id=FAMILY_ID, conversation_id=st.session_state.current_conversation_id)
        config["history"] = st.session_state.current_messages[:-1]
    
    with st.chat_message("Assistant"):
        info_placeholder = st.empty()
        info_placeholder.info("LLM is thinking...")
        response = get_streamed_response(user_input, config, endpoint)
        info_placeholder.empty()
    
    st.session_state.current_messages.append({"role": "assistant", "message": response})