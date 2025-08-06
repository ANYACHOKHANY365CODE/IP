import requests

ip = "106.222.228.3"  # Replace with real visitor IP
response = requests.get(f"https://ipinfo.io/{ip}/json")
data = response.json()
print(data)
