import requests

url = "https://existing-entryway-demise.ngrok-free.dev/ocr"

files = {
    "image": open("test.png", "rb")
}

response = requests.post(url, files=files)

print(response.json())