import requests
from datetime import datetime

# Configuration
BASE_URL = "https://us-west-2.campbell-cloud.com"
USERNAME = ""
PASSWORD = ""
ORGANIZATION_ID = ""

def get_access_token():
    url = f"{BASE_URL}/api/v1/tokens"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "client_id": "cloud",
        "grant_type": "password"
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_datastreams(token):
    url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/datastreams"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_latest_datapoint(token, datastream_id):
    url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/datastreams/{datastream_id}/datapoints/last"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"brief": "true"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("=== Campbell Cloud - SM Favorite Measurements ===\n")
    
    # Authenticate
    token = get_access_token()
    
    # Get datastreams
    datastreams = get_datastreams(token)
    
    # Define favorite measurements
    favorites = {
        "Five_Min": ["WS_mph_S_WVT", "WS_mph_Max", "WindDir_D1_WVT", "AirTF_Avg", "RH"],
        "Twelve_Hours": ["BattV_Min", "PTemp_C_Max"],
        "Twenty_Four_Hours": ["WS_mph_Max", "WS_mph_Avg", "WindDir_D1_WVT"]
    }
    
    # Collect favorite data
    favorite_data = []
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name in favorites and field_name in favorites[table_name]:
            latest = get_latest_datapoint(token, ds.get("id"))
            if latest and latest.get("data"):
                favorite_data.append({
                    "field": field_name,
                    "table": table_name,
                    "latest": latest["data"][0]
                })
    
    # Display favorites
    if favorite_data:
        for item in favorite_data:
            timestamp = datetime.fromtimestamp(item["latest"]["ts"] / 1000)
            print(f"{item['field']} ({item['table']})")
            print(f"  Value: {item['latest']['value']}")
            print(f"  Time: {timestamp}")
            print()
    else:
        print("No favorite measurements found.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
