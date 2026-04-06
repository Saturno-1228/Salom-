import urllib.request
import os

os.makedirs('assets/icons', exist_ok=True)
url = "https://cdn-icons-png.flaticon.com/512/992/992651.png"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response, open('assets/icons/plus.png', 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print("Plus icon downloaded.")
except Exception as e:
    print(f"Error: {e}")
