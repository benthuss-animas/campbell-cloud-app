import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

@st.cache_data(ttl=3000)
def get_access_token(base_url, username, password):
    """Authenticate and get access token"""
    url = f"{base_url}/api/v1/tokens"
    payload = {
        "username": username,
        "password": password,
        "client_id": "cloud",
        "grant_type": "password"
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]

@st.cache_data(ttl=300)
def get_datastreams(base_url, token, organization_id):
    """Get all datastreams for the organization"""
    url = f"{base_url}/api/v1/organizations/{organization_id}/datastreams"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    fetch_time = datetime.now(ZoneInfo("America/Denver")).strftime('%I:%M:%S %p')
    return {"data": response.json(), "fetched_at": fetch_time}

@st.cache_data(ttl=300)
def get_latest_datapoint(base_url, token, organization_id, datastream_id):
    """Get the latest datapoint for a specific datastream"""
    url = f"{base_url}/api/v1/organizations/{organization_id}/datastreams/{datastream_id}/datapoints/last"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"brief": "true"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data(ttl=300)
def get_historical_datapoints(base_url, token, organization_id, datastream_id, start_epoch, end_epoch, limit=15000):
    """Get historical datapoints for a specific datastream"""
    url = f"{base_url}/api/v1/organizations/{organization_id}/datastreams/{datastream_id}/datapoints"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "startEpoch": start_epoch,
        "endEpoch": end_epoch,
        "brief": "true",
        "limit": limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None
