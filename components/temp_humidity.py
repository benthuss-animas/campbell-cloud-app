import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from zoneinfo import ZoneInfo
from api.campbell_client import get_historical_datapoints
from streamlit import runtime

def display_temp_humidity_chart(config, token, datastreams):
    """Display temperature and humidity history chart"""
    st.markdown("---")
    st.subheader("🌡️ Temperature & Humidity History")
    
    temp_time_range = st.radio(
        "Select time range:",
        ["24 Hours", "72 Hours"],
        horizontal=True,
        index=0,
        key="temp_time_range"
    )
    
    temp_hours = 24 if temp_time_range == "24 Hours" else 72
    
    temp_id = None
    humidity_id = None
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Five_Min":
            if field_name == "AirTF_Avg":
                temp_id = ds.get("id")
            elif field_name == "RH":
                humidity_id = ds.get("id")
    
    if temp_id and humidity_id:
        with st.spinner(f"Loading {temp_hours} hours of temperature & humidity data..."):
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (temp_hours * 60 * 60 * 1000)
            
            temp_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                 temp_id, start_time, end_time)
            humidity_data = get_historical_datapoints(config["BASE_URL"], token, config["ORGANIZATION_ID"],
                                                     humidity_id, start_time, end_time)
            
            if temp_data and humidity_data:
                temp_points = temp_data.get("data", [])
                humidity_points = humidity_data.get("data", [])
                
                if temp_points and humidity_points:
                    temp_times = [datetime.fromtimestamp(p['ts']/1000, tz=ZoneInfo("America/Denver")) for p in temp_points]
                    temp_values = [p['value'] for p in temp_points]
                    
                    humidity_times = [datetime.fromtimestamp(p['ts']/1000, tz=ZoneInfo("America/Denver")) for p in humidity_points]
                    humidity_values = [p['value'] for p in humidity_points]
                    
                    temp_range = max(temp_values) - min(temp_values)
                    temp_padding = temp_range * 4
                    temp_min = min(temp_values) - temp_padding
                    temp_max = max(temp_values) + temp_padding
                    
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    fig.add_trace(
                        go.Scatter(
                            x=temp_times,
                            y=temp_values,
                            mode='lines+markers',
                            name='Temperature',
                            line=dict(color='#FF0000', width=2),
                            marker=dict(size=4),
                            hovertemplate='%{y:.1f} °F<extra></extra>'
                        ),
                        secondary_y=False
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=humidity_times,
                            y=humidity_values,
                            mode='lines+markers',
                            name='Humidity',
                            line=dict(color='#87CEEB', width=2),
                            marker=dict(size=4),
                            hovertemplate='%{y:.0f}%<extra></extra>'
                        ),
                        secondary_y=True
                    )
                    
                    fig.add_hline(
                        y=32,
                        line_dash="dash",
                        line_color="blue",
                        line_width=2,
                        secondary_y=False
                    )
                    
                    fig.update_layout(
                        xaxis_title=f"Previous {temp_hours} Hours",
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
                            range=[min(temp_times), max(temp_times)],
                            nticks=10
                        )
                    )
                    
                    fig.update_yaxes(title_text="Temperature (°F)", range=[temp_min, temp_max], secondary_y=False)
                    fig.update_yaxes(title_text="Humidity (%)", range=[0, 100], secondary_y=True)
                    
                    try:
                        session_info = runtime.get_instance()._session_mgr.list_active_sessions()[0]
                        is_mobile = session_info.client.request.headers.get("User-Agent", "").lower()
                        is_mobile = any(x in is_mobile for x in ["mobile", "android", "iphone", "ipad"])
                    except:
                        is_mobile = False
                    
                    st.plotly_chart(fig, use_container_width=True, config={
                        'staticPlot': is_mobile,
                        'displayModeBar': False
                    })
                else:
                    st.error("No data points found.")
            else:
                st.error(f"Failed to fetch {temp_hours}-hour temperature/humidity data.")
    else:
        st.warning("Temperature or humidity datastream not found.")
