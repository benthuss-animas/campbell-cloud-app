import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
from api.campbell_client import get_historical_datapoints

def display_wind_chart(config, token, datastreams):
    """Display wind speed and gust history chart"""
    st.markdown("---")
    st.subheader("📈 Wind Speed & Gusts History")
    
    time_range = st.radio(
        "Select time range:",
        ["24 Hours", "72 Hours"],
        horizontal=True,
        index=0
    )
    
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
                    
                    fig.add_trace(go.Scatter(
                        x=speed_times,
                        y=speed_values,
                        fill='tozeroy',
                        fillcolor='rgba(76, 175, 80, 0.7)',
                        line=dict(color='rgba(76, 175, 80, 1)', width=1),
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
                    
                    dir_lookup_for_arrows = {dir_times[i]: dir_values[i] for i in range(len(dir_times))}
                    max_speed = max(speed_values + gust_values)
                    
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
                                y=max_speed * 1.05,
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
                    
                    fig.update_layout(
                        xaxis_title=f"Previous {hours} Hours",
                        yaxis_title="Wind Speed (mph)",
                        hovermode='x unified',
                        height=350,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        margin=dict(l=60, r=20, t=20, b=80),
                        xaxis=dict(
                            tickformat='%b %d %I%p',
                            tickangle=-45,
                            range=[min(speed_times), max(speed_times)]
                        ),
                        yaxis=dict(
                            rangemode='tozero'
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, config={
                        'staticPlot': True,
                        'displayModeBar': False
                    })
            else:
                st.error(f"Failed to fetch {hours}-hour wind data.")
    else:
        st.warning("Wind speed, gust, or direction datastream not found.")
