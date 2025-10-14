import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.formatters import degrees_to_cardinal
from api.campbell_client import get_historical_datapoints
from browser_detection import browser_detection_engine

def display_wind_rose(config, token, datastreams):
    """Display 24-hour wind rose chart"""
    if 'browser_info' not in st.session_state:
        browser_info = browser_detection_engine()
        st.session_state.browser_info = browser_info
    else:
        browser_info = st.session_state.browser_info
    
    is_mobile_device = browser_info.get('isMobile', False) or browser_info.get('isTablet', False)
    
    st.markdown("---")
    st.subheader("🧭 Wind Rose")
    
    time_range = st.radio(
        "Select time range:",
        ["24 Hours", "72 Hours"],
        horizontal=True,
        index=0,
        key="wind_rose_time_range"
    )
    
    is_mobile = st.checkbox("Enable touch-friendly mode", value=is_mobile_device, key="wind_rose_mobile_mode", 
                           help="Enable for better experience on mobile devices")
    
    hours = 24 if time_range == "24 Hours" else 72
    
    wind_speed_id = None
    wind_dir_id = None
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Five_Min":
            if field_name == "WS_mph_S_WVT":
                wind_speed_id = ds.get("id")
            elif field_name == "WindDir_D1_WVT":
                wind_dir_id = ds.get("id")
    
    if wind_speed_id and wind_dir_id:
        with st.spinner(f"Generating wind rose from last {hours} hours of data..."):
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (hours * 60 * 60 * 1000)
            
            wind_speed_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                       wind_speed_id, start_time, end_time)
            wind_dir_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                     wind_dir_id, start_time, end_time)
            
            if wind_speed_data and wind_dir_data:
                speeds = []
                directions = []
                
                speed_points = wind_speed_data.get("data", [])
                dir_points = wind_dir_data.get("data", [])
                
                dir_lookup = {point["ts"]: point["value"] for point in dir_points}
                
                for speed_point in speed_points:
                    ts = speed_point["ts"]
                    if ts in dir_lookup:
                        speeds.append(speed_point["value"])
                        directions.append(dir_lookup[ts])
                
                if speeds and directions:
                    dir_bins = np.arange(0, 360, 22.5)
                    dir_labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                                 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                    
                    speed_bins = [0, 5, 15, 25, 100]
                    speed_labels = ['0-5', '5-15', '15-25', '>25']
                    speed_colors = ['#9370DB', '#FFFF00', '#FF0000', '#FF8C00']
                    
                    df = pd.DataFrame({'speed': speeds, 'direction': directions})
                    
                    df['dir_bin'] = pd.cut(df['direction'], bins=np.append(dir_bins, 360), 
                                          labels=dir_labels, include_lowest=True)
                    df['speed_bin'] = pd.cut(df['speed'], bins=speed_bins, 
                                           labels=speed_labels, include_lowest=True)
                    
                    rose_data = df.groupby(['dir_bin', 'speed_bin'], observed=False).size().unstack(fill_value=0)
                    rose_data = (rose_data.T / rose_data.sum().sum() * 100).T
                    
                    fig = go.Figure()
                    
                    for i, speed_label in enumerate(speed_labels):
                        if speed_label in rose_data.columns:
                            fig.add_trace(go.Barpolar(
                                r=rose_data[speed_label],
                                theta=dir_labels,
                                name=f'{speed_label} mph',
                                marker_color=speed_colors[i]
                            ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                ticksuffix='%', 
                                angle=90, 
                                dtick=10,
                                tickfont=dict(size=14, color='#333333')
                            ),
                            angularaxis=dict(direction='clockwise')
                        ),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5
                        ),
                        # height=500,
                        margin=dict(t=0, b=60, l=30, r=30)
                    )
                    
                    st.plotly_chart(fig, config={'staticPlot': is_mobile, 'responsive': True})
                    
                    timestamps = [point["ts"] for point in speed_points if point["ts"] in dir_lookup]
                    if timestamps:
                        start_dt = datetime.fromtimestamp(min(timestamps) / 1000, tz=ZoneInfo("America/Denver"))
                        end_dt = datetime.fromtimestamp(max(timestamps) / 1000, tz=ZoneInfo("America/Denver"))
                        time_range = f"{start_dt.strftime('%m/%d %I:%M%p')} - {end_dt.strftime('%m/%d %I:%M%p')}"
                    else:
                        time_range = "N/A"
                    
                    avg_direction = np.mean(directions)
                    cardinal = degrees_to_cardinal(avg_direction)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Observations", len(speeds))
                        st.caption(time_range)
                    with col2:
                        st.metric("Avg Wind Speed", f"{np.mean(speeds):.1f} mph")
                    with col3:
                        st.metric("Avg Direction", f"{avg_direction:.0f}° ({cardinal})")
                else:
                    st.warning(f"No matching wind data found for the last {hours} hours.")
            else:
                st.error("Failed to fetch historical wind data.")
    else:
        st.warning("Wind speed or direction datastream not found.")
