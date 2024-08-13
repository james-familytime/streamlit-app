import streamlit as st
import requests
import logging

logger = logging.getLogger(__name__)

# Base URL
base_url = "http://localhost:8000" 
query_endpoint = f"{base_url}/api/schools/query"

# Title of the web app
st.title("RAG Chat Interface")
st.write("Chat with the public data of a school")

# Input fields
#family_id = st.text_input("Enter Family ID:")
school_id = st.text_input("Enter School ID:")
user_input = st.text_area("Enter your query:")

result = None

# Placeholder for displaying LLM responses
message_window = st.empty()

# Button to submit the query
if st.button("Submit"):    
    if school_id and user_input:
        payload = {
            "user_query": user_input,
            "school_id": school_id
        }

        try:
            response = requests.post(url=query_endpoint, json=payload)
            if 200 <= response.status_code < 400:
                logger.info(f"result: {response}")                
                result = response.json().get("answer", "No result found")
                
                if result:
                    message_window.markdown(f"**LLM Response** \n\n{result}")

            else:
                message_window.markdown(f"Error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            results = f"Request failed: {str(e)}"
    else:
        message_window.markdown("Please fill in all the fields.")
