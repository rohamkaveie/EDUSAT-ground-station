import requests

url = 'https://www.aparat.com/home'
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Success!")
    # Get the response content in JSON format
    data = response.json()
    print(data)
else:
    print(f"Failed with status code: {response.status_code}")

