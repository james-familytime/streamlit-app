import requests
from json import loads, JSONDecodeError

def main():
    query: str = "Hi"
    authorization: str = (
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM2NTM0Mjg1LCJpYXQiOjE3Mjc4OTQyODUsImp0aSI6IjBjNTc2ZWYwNjBjNDQ3ZDU5ZWIyYjc2YjgxMWExZTc2IiwidXNlcl9pZCI6ImJiZjAwZDk5LTFiMjYtNGE4Ny1iMzJiLTE5MTk5NjkwYTQ0NSJ9.L3IGuNPq95wchYEjE2Q3zwNIuCPJM56W8G30gjp-VSM"
    )
    url = "http://localhost:8080/api/v1/families/676b3695-d133-45fe-b60f-6f159c06b275/conversations/start/"

    headers = {
        "Authorization": authorization
    }

    try:
        response = requests.post(
            url,
            json={'query': query},
            headers=headers,
            stream=True,  # Since we are receiving streamed SSE
        )

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
                                if chunk_type == "error":
                                    print(f"Error: {data}")
                                elif chunk_type == "session":
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

if __name__ == "__main__":
    main()