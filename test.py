import requests

url = "http://127.0.0.1:5000/api/chat"
data = {"message": "bangalore weather tomorrow"}

r = requests.post(url, json=data)
print(r.json())
