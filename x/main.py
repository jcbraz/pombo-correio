# from dataclasses import dataclass


# @dataclass
# class XPublisher:
#     pass

import os

import requests

url = "https://api.twitter.com/2/tweets"

headers = {
    "Authorization": f"Bearer {os.environ['X_BEARER_KEY']}",
    "Content-Type": "application/json",
}

payload = {
    "text": "Hello from the X API via Python!"  # Replace with your post content
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())
