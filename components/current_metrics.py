import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.formatters import degrees_to_cardinal
from utils.styles import get_metric_card_css
from api.campbell_client import get_latest_datapoint, get_historical_datapoints

def display_current_metrics(config, token, datastreams):
    """Display current weather measurements"""
    st.subheader("🌤️ Current Measurements")
    
    current_measurements = {}
    gust_datastream_id = None
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Five_Min" and field_name in ["WS_mph_Max", "WS_mph_S_WVT", "WindDir_D1_WVT", "AirTF_Avg", "RH"]:
            latest = get_latest_datapoint(config["BASE_URL"], token, config["ORGANIZATION_ID"], ds.get("id"))
            if latest and latest.get("data"):
                current_measurements[field_name] = {
                    "value": latest["data"][0]["value"],
                    "timestamp": datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                }
                
                if field_name == "WS_mph_Max":
                    gust_datastream_id = ds.get("id")
    
    peak_gust = None
    if gust_datastream_id:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (24 * 60 * 60 * 1000)
        
        gust_history = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                 gust_datastream_id, start_time, end_time)
        if gust_history and gust_history.get("data"):
            gust_points = gust_history["data"]
            if gust_points:
                max_point = max(gust_points, key=lambda x: x["value"])
                peak_gust = {
                    "value": max_point["value"],
                    "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                }
    
    st.markdown(get_metric_card_css(), unsafe_allow_html=True)
    
    grid_html = '<div class="metrics-grid">'
    
    if "WS_mph_S_WVT" in current_measurements:
        data = current_measurements["WS_mph_S_WVT"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #475569 0%, #334155 100%);"><p class="metric-label" style="color: #cbd5e1;">Wind Speed</p><h2 class="metric-value">{data["value"]:.1f} mph</h2><p style="color: #cbd5e1; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "WS_mph_Max" in current_measurements:
        data = current_measurements["WS_mph_Max"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0369a1 0%, #075985 100%);"><p class="metric-label" style="color: #bae6fd;">Gust</p><h2 class="metric-value">{data["value"]:.1f} mph</h2><p style="color: #bae6fd; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "WindDir_D1_WVT" in current_measurements:
        data = current_measurements["WindDir_D1_WVT"]
        direction = data['value']
        cardinal = degrees_to_cardinal(direction)
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);"><p class="metric-label" style="color: #93c5fd;">Wind Direction</p><h2 class="metric-value">{direction:.0f}° ({cardinal})</h2><p style="color: #93c5fd; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if peak_gust:
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);"><p class="metric-label" style="color: #fed7aa;">24-Hour Peak Gust</p><h2 class="metric-value">{peak_gust["value"]:.1f} mph</h2><p style="color: #fed7aa; font-size: 11px; margin: 8px 0 0 0;">{peak_gust["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "RH" in current_measurements:
        data = current_measurements["RH"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);"><p class="metric-label" style="color: #a5f3fc;">Humidity</p><h2 class="metric-value">{data["value"]:.0f}%</h2><p style="color: #a5f3fc; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "AirTF_Avg" in current_measurements:
        data = current_measurements["AirTF_Avg"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);"><p class="metric-label" style="color: #fecaca;">Temperature</p><h2 class="metric-value">{data["value"]:.1f}°F</h2><p style="color: #fecaca; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    grid_html += '</div>'
    
    st.html(grid_html)
