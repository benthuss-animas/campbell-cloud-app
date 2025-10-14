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
    wind_dir_datastream_id = None
    temp_datastream_id = None
    
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
                elif field_name == "WindDir_D1_WVT":
                    wind_dir_datastream_id = ds.get("id")
                elif field_name == "AirTF_Avg":
                    temp_datastream_id = ds.get("id")
    
    peak_gust_1h = None
    peak_gust_24h = None
    peak_gust_72h = None
    temp_high_24h = None
    temp_low_24h = None
    
    if temp_datastream_id:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time_24h = end_time - (24 * 60 * 60 * 1000)
        temp_history_24h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                      temp_datastream_id, start_time_24h, end_time)
        if temp_history_24h and temp_history_24h.get("data"):
            temp_points = temp_history_24h["data"]
            if temp_points:
                max_point = max(temp_points, key=lambda x: x["value"])
                min_point = min(temp_points, key=lambda x: x["value"])
                temp_high_24h = {
                    "value": max_point["value"],
                    "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                }
                temp_low_24h = {
                    "value": min_point["value"],
                    "timestamp": datetime.fromtimestamp(min_point["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                }
    
    if gust_datastream_id and wind_dir_datastream_id:
        end_time = int(datetime.now().timestamp() * 1000)
        
        start_time_1h = end_time - (2 * 60 * 60 * 1000)
        gust_history_1h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                     gust_datastream_id, start_time_1h, end_time, limit=12)
        dir_history_1h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                    wind_dir_datastream_id, start_time_1h, end_time, limit=12)
        if gust_history_1h and gust_history_1h.get("data") and dir_history_1h and dir_history_1h.get("data"):
            gust_points = gust_history_1h["data"]
            dir_points = dir_history_1h["data"]
            if gust_points and dir_points:
                max_point = max(gust_points, key=lambda x: x["value"])
                dir_lookup = {p["ts"]: p["value"] for p in dir_points}
                peak_gust_1h = {
                    "value": max_point["value"],
                    "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000, tz=ZoneInfo("America/Denver")),
                    "direction": dir_lookup.get(max_point["ts"])
                }
        
        start_time_24h = end_time - (24 * 60 * 60 * 1000)
        gust_history_24h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                      gust_datastream_id, start_time_24h, end_time)
        dir_history_24h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                     wind_dir_datastream_id, start_time_24h, end_time)
        if gust_history_24h and gust_history_24h.get("data") and dir_history_24h and dir_history_24h.get("data"):
            gust_points = gust_history_24h["data"]
            dir_points = dir_history_24h["data"]
            if gust_points and dir_points:
                max_point = max(gust_points, key=lambda x: x["value"])
                dir_lookup = {p["ts"]: p["value"] for p in dir_points}
                peak_gust_24h = {
                    "value": max_point["value"],
                    "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000, tz=ZoneInfo("America/Denver")),
                    "direction": dir_lookup.get(max_point["ts"])
                }
        
        start_time_72h = end_time - (72 * 60 * 60 * 1000)
        gust_history_72h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                      gust_datastream_id, start_time_72h, end_time)
        dir_history_72h = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"], 
                                                     wind_dir_datastream_id, start_time_72h, end_time)
        if gust_history_72h and gust_history_72h.get("data") and dir_history_72h and dir_history_72h.get("data"):
            gust_points = gust_history_72h["data"]
            dir_points = dir_history_72h["data"]
            if gust_points and dir_points:
                max_point = max(gust_points, key=lambda x: x["value"])
                dir_lookup = {p["ts"]: p["value"] for p in dir_points}
                peak_gust_72h = {
                    "value": max_point["value"],
                    "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000, tz=ZoneInfo("America/Denver")),
                    "direction": dir_lookup.get(max_point["ts"])
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
    
    if peak_gust_1h:
        direction_text = ""
        if peak_gust_1h.get("direction") is not None:
            cardinal = degrees_to_cardinal(peak_gust_1h["direction"])
            direction_text = f'<p style="color: #422006; font-size: 16px; font-weight: bold; margin: 4px 0 0 0;">{peak_gust_1h["direction"]:.0f}° ({cardinal})</p>'
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #facc15 0%, #eab308 100%);"><p class="metric-label" style="color: #422006;">1-Hour Peak Gust</p><h2 class="metric-value">{peak_gust_1h["value"]:.1f} mph</h2>{direction_text}<p style="color: #422006; font-size: 11px; margin: 8px 0 0 0;">{peak_gust_1h["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if peak_gust_24h:
        direction_text = ""
        if peak_gust_24h.get("direction") is not None:
            cardinal = degrees_to_cardinal(peak_gust_24h["direction"])
            direction_text = f'<p style="color: #fed7aa; font-size: 16px; font-weight: bold; margin: 4px 0 0 0;">{peak_gust_24h["direction"]:.0f}° ({cardinal})</p>'
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);"><p class="metric-label" style="color: #fed7aa;">24-Hour Peak Gust</p><h2 class="metric-value">{peak_gust_24h["value"]:.1f} mph</h2>{direction_text}<p style="color: #fed7aa; font-size: 11px; margin: 8px 0 0 0;">{peak_gust_24h["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if peak_gust_72h:
        direction_text = ""
        if peak_gust_72h.get("direction") is not None:
            cardinal = degrees_to_cardinal(peak_gust_72h["direction"])
            direction_text = f'<p style="color: #fecaca; font-size: 16px; font-weight: bold; margin: 4px 0 0 0;">{peak_gust_72h["direction"]:.0f}° ({cardinal})</p>'
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);"><p class="metric-label" style="color: #fecaca;">72-Hour Peak Gust</p><h2 class="metric-value">{peak_gust_72h["value"]:.1f} mph</h2>{direction_text}<p style="color: #fecaca; font-size: 11px; margin: 8px 0 0 0;">{peak_gust_72h["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "RH" in current_measurements:
        data = current_measurements["RH"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);"><p class="metric-label" style="color: #a5f3fc;">Humidity</p><h2 class="metric-value">{data["value"]:.0f}%</h2><p style="color: #a5f3fc; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if "AirTF_Avg" in current_measurements:
        data = current_measurements["AirTF_Avg"]
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);"><p class="metric-label" style="color: #e9d5ff;">Temperature</p><h2 class="metric-value">{data["value"]:.1f}°F</h2><p style="color: #e9d5ff; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if temp_low_24h:
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);"><p class="metric-label" style="color: #e0f2fe;">24-Hour Low</p><h2 class="metric-value">{temp_low_24h["value"]:.1f}°F</h2><p style="color: #e0f2fe; font-size: 11px; margin: 8px 0 0 0;">{temp_low_24h["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    if temp_high_24h:
        grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);"><p class="metric-label" style="color: #fce7f3;">24-Hour High</p><h2 class="metric-value">{temp_high_24h["value"]:.1f}°F</h2><p style="color: #fce7f3; font-size: 11px; margin: 8px 0 0 0;">{temp_high_24h["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
    
    grid_html += '</div>'
    
    st.html(grid_html)
