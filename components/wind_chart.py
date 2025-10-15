import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
from api.campbell_client import get_historical_datapoints
from browser_detection import browser_detection_engine

def display_wind_chart(config, token, datastreams):
    """Display wind speed and gust history chart"""
    if 'browser_info' not in st.session_state:
        browser_info = browser_detection_engine()
        st.session_state.browser_info = browser_info
    else:
        browser_info = st.session_state.browser_info
    
    is_mobile_device = browser_info.get('isMobile', False) or browser_info.get('isTablet', False)
    
    st.markdown("---")
    st.subheader("📈 Wind Speed & Gusts History")
    
    time_range = st.radio(
        "Select time range:",
        ["24 Hours", "72 Hours"],
        horizontal=True,
        index=0,
        key="wind_time_range"
    )
    
    is_mobile = st.checkbox("Enable touch-friendly mode", value=is_mobile_device, key="wind_chart_mobile_mode", 
                           help="Enable for better experience on mobile devices")
    
    hours = 24 if time_range == "24 Hours" else 72
    
    wind_speed_id = None
    wind_gust_id = None
    wind_dir_id = None
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Five_Min":
            if field_name == "WS_mph_S_WVT":
                wind_speed_id = ds.get("id")
            elif field_name == "WS_mph_Max":
                wind_gust_id = ds.get("id")
            elif field_name == "WindDir_D1_WVT":
                wind_dir_id = ds.get("id")
    
    if wind_speed_id and wind_gust_id and wind_dir_id:
        with st.spinner(f"Loading {hours} hours of wind data..."):
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (hours * 60 * 60 * 1000)
            
            speed_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                  wind_speed_id, start_time, end_time)
            gust_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                 wind_gust_id, start_time, end_time)
            dir_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                wind_dir_id, start_time, end_time)
            
            if speed_data and gust_data and dir_data:
                speed_points = speed_data.get("data", [])
                gust_points = gust_data.get("data", [])
                dir_points = dir_data.get("data", [])
                
                if not speed_points or not gust_points:
                    st.error("No data points found in response.")
                else:
                    speed_times = [datetime.fromtimestamp(p['ts']/1000, tz=ZoneInfo("America/Denver")) for p in speed_points]
                    speed_values = [p['value'] for p in speed_points]
                    
                    gust_times = [datetime.fromtimestamp(p['ts']/1000, tz=ZoneInfo("America/Denver")) for p in gust_points]
                    gust_values = [p['value'] for p in gust_points]
                    
                    dir_times = [datetime.fromtimestamp(p['ts']/1000, tz=ZoneInfo("America/Denver")) for p in dir_points]
                    dir_values = [p['value'] for p in dir_points]
                    
                    fig = go.Figure()
                    
                    avg_wind_speed = np.mean(speed_values)
                    
                    fig.add_trace(go.Scatter(
                        x=speed_times,
                        y=speed_values,
                        fill='tozeroy',
                        fillcolor='rgba(76, 175, 80, 0.7)',
                        line=dict(color='rgba(76, 175, 80, 1)', width=2, shape='spline'),
                        name='Wind Speed',
                        hovertemplate='%{y:.1f} mph<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=gust_times,
                        y=gust_values,
                        mode='markers',
                        marker=dict(color='orange', size=4),
                        name='Wind Gusts',
                        hovertemplate='%{y:.1f} mph<extra></extra>'
                    ))
                    
                    fig.add_hline(
                        y=avg_wind_speed,
                        line_dash="dash",
                        line_color="rgba(38, 87, 40, 0.8)",
                        line_width=2,
                        annotation_text=f"Avg {avg_wind_speed:.0f}mph",
                        annotation_position="right"
                    )
                    
                    dir_lookup_for_arrows = {dir_times[i]: dir_values[i] for i in range(len(dir_times))}
                    max_gust = max(gust_values)
                    y_max = max(max_gust + 10, 55)
                    
                    arrow_interval = max(1, len(speed_points) // 30)
                    for i in range(0, len(speed_points), arrow_interval):
                        time_val = speed_times[i]
                        
                        if time_val in dir_lookup_for_arrows:
                            direction = dir_lookup_for_arrows[time_val]
                            arrow_angle = (direction + 180) % 360
                            arrow_length = 25
                            
                            angle_rad = np.radians(arrow_angle)
                            dx = -arrow_length * np.sin(angle_rad)
                            dy = arrow_length * np.cos(angle_rad)
                            
                            fig.add_annotation(
                                x=time_val,
                                y=y_max * 0.95,
                                ax=dx,
                                ay=dy,
                                xref='x',
                                yref='y',
                                axref='pixel',
                                ayref='pixel',
                                showarrow=True,
                                arrowhead=2,
                                arrowsize=1,
                                arrowwidth=2,
                                arrowcolor='#00CED1',
                                standoff=0
                            )
                    
                    layout_config = {
                        'xaxis_title': f"Previous {hours} Hours",
                        'yaxis_title': "Wind Speed (mph)",
                        'hovermode': 'x unified',
                        'showlegend': True,
                        'legend': dict(
                            orientation="h",
                            yanchor="top",
                            y=1.08,
                            xanchor="right",
                            x=1
                        ),
                        'margin': dict(l=60, r=60, t=20, b=80),
                        'xaxis': dict(
                            tickformat='%b %d %I%p',
                            tickangle=-45,
                            range=[min(speed_times), max(speed_times)],
                            nticks=10
                        ),
                        'yaxis': dict(
                            range=[0, y_max]
                        )
                    }
                    
                    if is_mobile:
                        layout_config['height'] = 350
                    
                    fig.update_layout(**layout_config)
                    
                    st.plotly_chart(fig, config={'staticPlot': is_mobile, 'responsive': True})
                    
                    with st.expander("📊 View Raw Data"):
                        df = pd.DataFrame({
                            'Time': [t.strftime('%Y-%m-%d %I:%M %p') for t in speed_times],
                            'Wind Speed (mph)': speed_values,
                            'Wind Gust (mph)': [gust_values[gust_times.index(t)] if t in gust_times else None for t in speed_times],
                            'Wind Direction (°)': [dir_values[dir_times.index(t)] if t in dir_times else None for t in speed_times]
                        })
                        df = df.iloc[::-1].reset_index(drop=True)
                        st.dataframe(df, width="stretch", height=400)
            else:
                st.error(f"Failed to fetch {hours}-hour wind data.")
    else:
        st.warning("Wind speed, gust, or direction datastream not found.")
