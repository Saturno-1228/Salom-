import requests
import os

icons = {
    "send.png": "https://img.icons8.com/ios-filled/50/ffffff/paper-plane.png",
}

for name, url in icons.items():
    print(f"Downloading {name}...")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        with open(os.path.join("assets/icons", name), "wb") as f:
            f.write(response.content)
    else:
        print(f"Failed to download {name}: {response.status_code}")
