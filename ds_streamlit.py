import streamlit as st
import requests
from requests_toolbelt import MultipartEncoder

def call_api_toolbelt(url, fields):
    """
    Sends a POST request to the specified URL using requests-toolbelt's MultipartEncoder.
    The `fields` parameter should be a dictionary of form fields. For file fields, use a tuple:
    (filename, file_obj, content_type).
    """
    try:
        m = MultipartEncoder(fields=fields)
        headers = {'Content-Type': m.content_type}
        response = requests.post(url, data=m, headers=headers)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred when calling {url}: {http_err}"
    except Exception as err:
        return f"An error occurred when calling {url}: {err}"

def display_product_recommendation(result):
    """
    Displays the assistant response and recommended products from the API result.
    The `recommended_products` is expected to be a list of dicts with keys 'name' and 'description'.
    If the list is empty, only the assistant response is displayed.
    """
    if isinstance(result, dict):
        assistant_response = result.get("assistant_response", "")
        recommended_products = result.get("recommended_products", [])
        st.write("**Assistant Response:**")
        st.write(assistant_response)
        if recommended_products:
            st.write("**Recommended Products:**")
            for product in recommended_products:
                name = product.get("name", "N/A")
                description = product.get("description", "N/A")
                st.write(f"**Name:** {name}")
                st.write(f"**Description:** {description}")
                st.write("---")
    else:
        st.write(result)

def main():
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Select an option", [
        "Product Recommendation with Query",
        "Product Recommendation with Handwritten Query",
        "Production Recommendation with Image",
        "Load Pinecone Dataset",
        "Scrape and Train"
    ])

    # Define your API endpoints (replace these with your actual endpoints)
    endpoints = {
        "Product Recommendation with Query": "https://api.example.com/product-recommendation-query",
        "Product Recommendation with Handwritten Query": "https://api.example.com/product-recommendation-handwritten",
        "Production Recommendation with Image": "https://api.example.com/production-recommendation-image",
        "Load Pinecone Dataset": "https://api.example.com/load-pinecone-dataset",
        "Scrape and Train": "https://api.example.com/scrape-and-train"
    }

    # Page 1: Product Recommendation with Query
    if menu == "Product Recommendation with Query":
        st.header("Product Recommendation with Query")
        with st.form(key="query_form"):
            user_query = st.text_input("Enter your query:")
            submit_query = st.form_submit_button("Submit Query")
            if submit_query:
                fields = {"query": user_query}
                result = call_api_toolbelt(endpoints["Product Recommendation with Query"], fields)
                st.write("**API Response:**")
                display_product_recommendation(result)

    # Page 2: Product Recommendation with Handwritten Query
    elif menu == "Product Recommendation with Handwritten Query":
        st.header("Product Recommendation with Handwritten Query")
        handwritten_file = st.file_uploader("Upload your handwritten query file", type=["png", "jpg", "jpeg", "pdf", "txt"])
        if handwritten_file is not None:
            st.write("File uploaded:", handwritten_file.name)
            with st.form(key="handwritten_form"):
                submit_handwritten = st.form_submit_button("Submit Handwritten Query")
                if submit_handwritten:
                    # Determine a default content type based on file extension.
                    content_type = "application/octet-stream"
                    if handwritten_file.name.lower().endswith(".txt"):
                        content_type = "text/plain"
                    elif handwritten_file.name.lower().endswith(".pdf"):
                        content_type = "application/pdf"
                    elif handwritten_file.name.lower().endswith(("png", "jpg", "jpeg")):
                        content_type = "image/jpeg"  # Adjust as needed for png

                    fields = {
                        "filename": handwritten_file.name,
                        "content": (handwritten_file.name, handwritten_file, content_type)
                    }
                    result = call_api_toolbelt(endpoints["Product Recommendation with Handwritten Query"], fields)
                    st.write("**API Response:**")
                    display_product_recommendation(result)

    # Page 3: Production Recommendation with Image
    elif menu == "Production Recommendation with Image":
        st.header("Production Recommendation with Image")
        image_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if image_file is not None:
            st.image(image_file, caption="Uploaded Image", use_column_width=True)
            with st.form(key="image_form"):
                submit_image = st.form_submit_button("Submit Image")
                if submit_image:
                    content_type = "image/jpeg"
                    if image_file.name.lower().endswith(".png"):
                        content_type = "image/png"
                    fields = {
                        "filename": image_file.name,
                        "content": (image_file.name, image_file, content_type)
                    }
                    result = call_api_toolbelt(endpoints["Production Recommendation with Image"], fields)
                    st.write("**API Response:**")
                    display_product_recommendation(result)

    # Page 4: Load Pinecone Dataset
    elif menu == "Load Pinecone Dataset":
        st.header("Load Pinecone Dataset")
        if st.button("Load Dataset"):
            fields = {}
            result = call_api_toolbelt(endpoints["Load Pinecone Dataset"], fields)
            st.write("**API Response:**")
            st.write(result)

    # Page 5: Scrape and Train
    elif menu == "Scrape and Train":
        st.header("Scrape and Train")
        with st.form(key="scrape_form"):
            url_input = st.text_input("Enter URL for scraping:")
            submit_scrape = st.form_submit_button("Scrape and Train")
            if submit_scrape:
                fields = {"url": url_input}
                result = call_api_toolbelt(endpoints["Scrape and Train"], fields)
                st.write("**API Response:**")
                st.write(result)

if __name__ == "__main__":
    main()