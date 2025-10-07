import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

# Configuration
BASE_URL = os.getenv("CAMPBELL_BASE_URL")
USERNAME = os.getenv("CAMPBELL_USERNAME")
PASSWORD = os.getenv("CAMPBELL_PASSWORD")
ORGANIZATION_ID = os.getenv("CAMPBELL_ORGANIZATION_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not all([BASE_URL, USERNAME, PASSWORD, ORGANIZATION_ID, APP_PASSWORD]):
    st.error("⚠️ Missing required environment variables. Please check your .env file.")
    st.stop()

def check_password():
    """Returns True if user entered correct password"""
    current_hash = hashlib.sha256(APP_PASSWORD.encode()).hexdigest()[:16]
    
    if "authenticated" not in st.session_state:
        stored_hash = st.query_params.get("auth", "")
        st.session_state.authenticated = stored_hash == current_hash
    
    if not st.session_state.authenticated:
        st.title("🔐 Authentication Required")
        password_input = st.text_input("Enter password:", type="password", key="password_input")
        
        if st.button("Login"):
            if password_input == APP_PASSWORD:
                st.session_state.authenticated = True
                st.query_params["auth"] = current_hash
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

@st.cache_data(ttl=3000)  # Cache for 50 minutes (token expires in 60)
def get_access_token():
    """Authenticate and get access token"""
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_datastreams(token):
    """Get all datastreams for the organization"""
    url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/datastreams"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    fetch_time = datetime.now().strftime('%I:%M:%S %p')
    return {"data": response.json(), "fetched_at": fetch_time}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_datapoint(token, datastream_id):
    """Get the latest datapoint for a specific datastream"""
    url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/datastreams/{datastream_id}/datapoints/last"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"brief": "true"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_historical_datapoints(token, datastream_id, start_epoch, end_epoch, limit=15000):
    """Get historical datapoints for a specific datastream"""
    url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/datastreams/{datastream_id}/datapoints"
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

# Page config
st.set_page_config(
    page_title="Silverton Mountain Weather",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if not check_password():
    st.stop()

# Sidebar menu
with st.sidebar:
    st.header("⚙️ Menu")
    
    # Refresh & Clear Cache button
    if st.button("🔄 Refresh & Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Custom Links section
    st.header("🔗 Quick Links")
    st.markdown("### Weather Resources")
    st.markdown("- [Campbell Cloud](https://campbellcloud.com)")
    st.markdown("- [NOAA Weather](https://weather.gov)")
    st.markdown("- [Windy.com](https://windy.com)")
    
    st.markdown("### Data & Reports")
    st.markdown("- [Export Data](#)")
    st.markdown("- [Historical Reports](#)")
    
    st.markdown("---")
    st.caption("v1.0 • Built by Chauncey")

# Title
st.title("Silverton Mountain Weather Station")

# Auto-refresh option
auto_refresh = st.checkbox("⚡ Auto-refresh every 5 minutes", value=False)

if auto_refresh:
    st.empty()
    import time
    time.sleep(300)
    st.rerun()

st.markdown("---")

# Show loading spinner
with st.spinner("Fetching data from Campbell Cloud..."):
    try:
        # Authenticate
        token = get_access_token()
        
        # Define favorite measurements
        favorites = {
            "Five_Min": ["WS_mph_S_WVT", "WS_mph_Max", "WindDir_D1_WVT", "AirTF_Avg", "RH"],
            "Twelve_Hours": ["BattV_Min", "PTemp_C_Max"],
            "Twenty_Four_Hours": ["WS_mph_Max", "WS_mph_Avg", "WindDir_D1_WVT"]
        }
        
        # Get datastreams
        datastreams_response = get_datastreams(token)
        datastreams = datastreams_response["data"]
        fetch_time = datastreams_response["fetched_at"]
        
        # Show cache status
        current_time = datetime.now()
        try:
            fetch_dt = datetime.strptime(fetch_time, '%I:%M:%S %p').replace(
                year=current_time.year, 
                month=current_time.month, 
                day=current_time.day
            )
            age_seconds = (current_time - fetch_dt).total_seconds()
            if age_seconds < 10:
                st.info(f"🆕 Data fetched fresh from API at {fetch_time}")
            else:
                st.success(f"⚡ Using cached data (fetched at {fetch_time})")
        except:
            st.info(f"📊 Data timestamp: {fetch_time}")
        
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
        

        
        # Display Current Measurements
        st.subheader("🌤️ Current Measurements")
        
        # Helper function to convert degrees to cardinal direction
        def degrees_to_cardinal(degrees):
            directions_list = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                              'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            index = int((degrees + 11.25) / 22.5) % 16
            return directions_list[index]
        
        # Extract current measurements from Five_Min table
        current_measurements = {}
        gust_datastream_id = None
        
        for ds in datastreams:
            metadata = ds.get("metadata", {})
            table_name = metadata.get("table", "")
            field_name = metadata.get("field", "")
            
            if table_name == "Five_Min" and field_name in ["WS_mph_Max", "WS_mph_S_WVT", "WindDir_D1_WVT", "AirTF_Avg", "RH"]:
                latest = get_latest_datapoint(token, ds.get("id"))
                if latest and latest.get("data"):
                    current_measurements[field_name] = {
                        "value": latest["data"][0]["value"],
                        "timestamp": datetime.fromtimestamp(latest["data"][0]["ts"] / 1000)
                    }
                    
                    # Store gust datastream ID for 24-hour peak
                    if field_name == "WS_mph_Max":
                        gust_datastream_id = ds.get("id")
        
        # Get 24-hour peak gust
        peak_gust = None
        if gust_datastream_id:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (24 * 60 * 60 * 1000)
            
            gust_history = get_historical_datapoints(token, gust_datastream_id, start_time, end_time)
            if gust_history and gust_history.get("data"):
                gust_points = gust_history["data"]
                if gust_points:
                    max_point = max(gust_points, key=lambda x: x["value"])
                    peak_gust = {
                        "value": max_point["value"],
                        "timestamp": datetime.fromtimestamp(max_point["ts"] / 1000)
                    }
        
        # CSS for card styling with CSS Grid (always 2 columns)
        st.markdown("""
        <style>
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .metric-card {
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100px;
        }
        .metric-label {
            margin: 0 0 8px 0;
            font-size: 13px;
            font-weight: 500;
        }
        .metric-value {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 28px;
            font-weight: bold;
            color: #fff;
            line-height: 1.2;
            text-align: center;
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Build grid HTML (ordered for logical grouping)
        grid_html = '<div class="metrics-grid">'
        
        # Row 1: Wind Speed & Gust
        if "WS_mph_S_WVT" in current_measurements:
            data = current_measurements["WS_mph_S_WVT"]
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #475569 0%, #334155 100%);"><p class="metric-label" style="color: #cbd5e1;">Wind Speed</p><h2 class="metric-value">{data["value"]:.1f} mph</h2><p style="color: #cbd5e1; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        if "WS_mph_Max" in current_measurements:
            data = current_measurements["WS_mph_Max"]
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0369a1 0%, #075985 100%);"><p class="metric-label" style="color: #bae6fd;">Gust</p><h2 class="metric-value">{data["value"]:.1f} mph</h2><p style="color: #bae6fd; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        # Row 2: Wind Direction & Peak Gust
        if "WindDir_D1_WVT" in current_measurements:
            data = current_measurements["WindDir_D1_WVT"]
            direction = data['value']
            cardinal = degrees_to_cardinal(direction)
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);"><p class="metric-label" style="color: #93c5fd;">Wind Direction</p><h2 class="metric-value">{direction:.0f}° ({cardinal})</h2><p style="color: #93c5fd; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        if peak_gust:
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);"><p class="metric-label" style="color: #fed7aa;">24-Hour Peak Gust</p><h2 class="metric-value">{peak_gust["value"]:.1f} mph</h2><p style="color: #fed7aa; font-size: 11px; margin: 8px 0 0 0;">{peak_gust["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        # Row 3: Humidity & Temperature
        if "RH" in current_measurements:
            data = current_measurements["RH"]
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);"><p class="metric-label" style="color: #a5f3fc;">Humidity</p><h2 class="metric-value">{data["value"]:.0f}%</h2><p style="color: #a5f3fc; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        if "AirTF_Avg" in current_measurements:
            data = current_measurements["AirTF_Avg"]
            grid_html += f'<div class="metric-card" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);"><p class="metric-label" style="color: #fecaca;">Temperature</p><h2 class="metric-value">{data["value"]:.1f}°F</h2><p style="color: #fecaca; font-size: 11px; margin: 8px 0 0 0;">{data["timestamp"].strftime("%b %d %I:%M %p")}</p></div>'
        
        grid_html += '</div>'
        
        # Use st.html to render without Streamlit wrapper elements
        st.html(grid_html)
        
        # Group favorites by table (for remaining sections)
        tables = {}
        for item in favorite_data:
            table = item["table"]
            if table not in tables:
                tables[table] = []
            tables[table].append(item)
        
        # Wind Rose Section
        st.markdown("---")
        st.subheader("24-Hour Wind Rose")
        
        # Find wind speed and direction datastream IDs
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
            with st.spinner("Generating wind rose from last 24 hours of data..."):
                # Calculate time range (last 24 hours)
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago
                
                # Fetch historical data
                wind_speed_data = get_historical_datapoints(token, wind_speed_id, start_time, end_time)
                wind_dir_data = get_historical_datapoints(token, wind_dir_id, start_time, end_time)
                
                if wind_speed_data and wind_dir_data:
                    # Extract data points
                    speeds = []
                    directions = []
                    
                    speed_points = wind_speed_data.get("data", [])
                    dir_points = wind_dir_data.get("data", [])
                    
                    # Create timestamp lookup for wind direction
                    dir_lookup = {point["ts"]: point["value"] for point in dir_points}
                    
                    # Match speed and direction by timestamp
                    for speed_point in speed_points:
                        ts = speed_point["ts"]
                        if ts in dir_lookup:
                            speeds.append(speed_point["value"])
                            directions.append(dir_lookup[ts])
                    
                    if speeds and directions:
                        import pandas as pd
                        import numpy as np
                        
                        # Create wind rose using plotly
                        try:
                            import plotly.graph_objects as go
                            
                            # Define direction bins (16 directions)
                            dir_bins = np.arange(0, 360, 22.5)
                            dir_labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                                         'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                            
                            # Define speed bins
                            speed_bins = [0, 5, 15, 25, 100]
                            speed_labels = ['0-5', '5-15', '15-25', '>25']
                            speed_colors = ['#9370DB', '#FFFF00', '#FF0000', '#FF8C00']
                            
                            # Create DataFrame
                            df = pd.DataFrame({'speed': speeds, 'direction': directions})
                            
                            # Bin the data
                            df['dir_bin'] = pd.cut(df['direction'], bins=np.append(dir_bins, 360), 
                                                   labels=dir_labels, include_lowest=True)
                            df['speed_bin'] = pd.cut(df['speed'], bins=speed_bins, 
                                                    labels=speed_labels, include_lowest=True)
                            
                            # Create wind rose data
                            rose_data = df.groupby(['dir_bin', 'speed_bin'], observed=False).size().unstack(fill_value=0)
                            rose_data = (rose_data.T / rose_data.sum().sum() * 100).T
                            
                            # Create polar bar chart
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
                                    yanchor="top",
                                    y=-0.05,
                                    xanchor="center",
                                    x=0.5
                                ),
                                height=550,
                                margin=dict(t=20, b=80, l=20, r=20)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Helper function to convert degrees to cardinal direction
                            def degrees_to_cardinal(degrees):
                                directions_list = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                                                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                                index = int((degrees + 11.25) / 22.5) % 16
                                return directions_list[index]
                            
                            # Calculate time range
                            timestamps = [point["ts"] for point in speed_points if point["ts"] in dir_lookup]
                            if timestamps:
                                start_dt = datetime.fromtimestamp(min(timestamps) / 1000)
                                end_dt = datetime.fromtimestamp(max(timestamps) / 1000)
                                time_range = f"{start_dt.strftime('%m/%d %I:%M%p')} - {end_dt.strftime('%m/%d %I:%M%p')}"
                            else:
                                time_range = "N/A"
                            
                            avg_direction = np.mean(directions)
                            cardinal = degrees_to_cardinal(avg_direction)
                            
                            # Stats (reduced spacing)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Observations", len(speeds))
                                st.caption(time_range)
                            with col2:
                                st.metric("Avg Wind Speed", f"{np.mean(speeds):.1f} mph")
                            with col3:
                                st.metric("Avg Direction", f"{avg_direction:.0f}° ({cardinal})")
                        
                        except ImportError:
                            st.error("Please install plotly: pip install plotly")
                    else:
                        st.warning("No matching wind data found for the last 24 hours.")
                else:
                    st.error("Failed to fetch historical wind data.")
        else:
            st.warning("Wind speed or direction datastream not found.")
        
        # Wind Chart Section
        st.markdown("---")
        st.subheader("📈 Wind Speed & Gusts History")
        
        # Time range selector
        time_range = st.radio(
            "Select time range:",
            ["24 Hours", "72 Hours"],
            horizontal=True,
            index=0
        )
        
        hours = 24 if time_range == "24 Hours" else 72
        
        # Find wind speed, gust, and direction datastream IDs
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
                # Calculate time range
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = end_time - (hours * 60 * 60 * 1000)
                
                # Fetch historical data
                speed_data = get_historical_datapoints(token, wind_speed_id, start_time, end_time)
                gust_data = get_historical_datapoints(token, wind_gust_id, start_time, end_time)
                dir_data = get_historical_datapoints(token, wind_dir_id, start_time, end_time)
                
                if speed_data and gust_data and dir_data:
                    import pandas as pd
                    import numpy as np
                    
                    try:
                        import plotly.graph_objects as go
                        
                        # Extract data
                        speed_points = speed_data.get("data", [])
                        gust_points = gust_data.get("data", [])
                        dir_points = dir_data.get("data", [])
                        
                        if not speed_points or not gust_points:
                            st.error("No data points found in response.")
                        else:
                            # Create lists for plotting
                            speed_times = [datetime.fromtimestamp(p['ts']/1000) for p in speed_points]
                            speed_values = [p['value'] for p in speed_points]
                            
                            gust_times = [datetime.fromtimestamp(p['ts']/1000) for p in gust_points]
                            gust_values = [p['value'] for p in gust_points]
                            
                            dir_times = [datetime.fromtimestamp(p['ts']/1000) for p in dir_points]
                            dir_values = [p['value'] for p in dir_points]
                            
                            # Create the figure
                            fig = go.Figure()
                            
                            # Add wind speed as filled area (green)
                            fig.add_trace(go.Scatter(
                                x=speed_times,
                                y=speed_values,
                                fill='tozeroy',
                                fillcolor='rgba(76, 175, 80, 0.7)',
                                line=dict(color='rgba(76, 175, 80, 1)', width=1),
                                name='Wind Speed',
                                hovertemplate='%{y:.1f} mph<extra></extra>'
                            ))
                            
                            # Add wind gusts as scatter (orange)
                            fig.add_trace(go.Scatter(
                                x=gust_times,
                                y=gust_values,
                                mode='markers',
                                marker=dict(color='orange', size=4),
                                name='Wind Gusts',
                                hovertemplate='%{y:.1f} mph<extra></extra>'
                            ))
                            
                            # Add direction arrows (sampled)
                            arrow_interval = max(1, len(speed_points) // 30)  # ~30 arrows
                            for i in range(0, len(speed_points), arrow_interval):
                                if i < len(dir_points):
                                    direction = dir_values[i]
                                    speed_val = speed_values[i]
                                    time_val = speed_times[i]
                                    
                                    # Wind direction is where wind is COMING FROM (meteorological convention)
                                    # 0° = North, 90° = East, 180° = South, 270° = West
                                    # Arrow points FROM origin direction (tail) TO data point (head)
                                    # For vertical chart: North (0°) = tail above, South (180°) = tail below
                                    
                                    arrow_length = 3.0  # mph units
                                    # cos(0°)=1 (north, tail above), cos(180°)=-1 (south, tail below)
                                    dy = arrow_length * np.cos(np.radians(direction))
                                    
                                    fig.add_annotation(
                                        x=time_val,
                                        y=speed_val,  # Arrow head at data point
                                        ax=time_val,
                                        ay=speed_val + dy,  # Arrow tail offset by direction
                                        xref='x',
                                        yref='y',
                                        axref='x',
                                        ayref='y',
                                        showarrow=True,
                                        arrowhead=2,
                                        arrowsize=1.5,
                                        arrowwidth=1.5,
                                        arrowcolor='#00CED1',
                                        standoff=0
                                    )
                        
                            # Update layout
                            fig.update_layout(
                                xaxis_title=f"Previous {hours} Hours",
                                yaxis_title="Wind Speed (mph)",
                                hovermode='x unified',
                                height=400,
                                showlegend=True,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                xaxis=dict(
                                    tickformat='%b %d %I%p',
                                    tickangle=-45
                                ),
                                yaxis=dict(
                                    rangemode='tozero'
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                    except ImportError:
                        st.error("Please install plotly: pip install plotly")
                else:
                    st.error(f"Failed to fetch {hours}-hour wind data.")
        else:
            st.warning("Wind speed, gust, or direction datastream not found.")
        
        # Temperature & Humidity Chart Section
        st.markdown("---")
        st.subheader("🌡️ Temperature & Humidity History")
        
        # Time range selector
        temp_time_range = st.radio(
            "Select time range:",
            ["24 Hours", "72 Hours"],
            horizontal=True,
            index=0,
            key="temp_time_range"
        )
        
        temp_hours = 24 if temp_time_range == "24 Hours" else 72
        
        # Find temperature and humidity datastream IDs
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
                # Calculate time range
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = end_time - (temp_hours * 60 * 60 * 1000)
                
                # Fetch historical data
                temp_data = get_historical_datapoints(token, temp_id, start_time, end_time)
                humidity_data = get_historical_datapoints(token, humidity_id, start_time, end_time)
                
                if temp_data and humidity_data:
                    try:
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots
                        
                        # Extract data
                        temp_points = temp_data.get("data", [])
                        humidity_points = humidity_data.get("data", [])
                        
                        if temp_points and humidity_points:
                            # Create lists
                            temp_times = [datetime.fromtimestamp(p['ts']/1000) for p in temp_points]
                            temp_values = [p['value'] for p in temp_points]
                            
                            humidity_times = [datetime.fromtimestamp(p['ts']/1000) for p in humidity_points]
                            humidity_values = [p['value'] for p in humidity_points]
                            
                            # Create figure with secondary y-axis
                            fig = make_subplots(specs=[[{"secondary_y": True}]])
                            
                            # Add temperature trace (red, left axis)
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
                            
                            # Add humidity trace (light blue, right axis)
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
                            
                            # Update layout
                            fig.update_layout(
                                xaxis_title=f"Previous {temp_hours} Hours",
                                hovermode='x unified',
                                height=400,
                                showlegend=True,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                xaxis=dict(
                                    tickformat='%b %d %I%p',
                                    tickangle=-45
                                )
                            )
                            
                            # Set y-axes titles
                            fig.update_yaxes(title_text="Temperature (°F)", secondary_y=False)
                            fig.update_yaxes(title_text="Humidity (%)", secondary_y=True)
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.error("No data points found.")
                    
                    except ImportError:
                        st.error("Please install plotly: pip install plotly")
                else:
                    st.error(f"Failed to fetch {temp_hours}-hour temperature/humidity data.")
        else:
            st.warning("Temperature or humidity datastream not found.")
        
        # Display Twelve_Hours at bottom with enhanced battery display
        if "Twelve_Hours" in tables:
            st.markdown("---")
            st.subheader("🔋 System Status")
            
            # Extract battery and temp data
            battery_voltage = None
            panel_temp = None
            battery_timestamp = None
            temp_timestamp = None
            
            for item in tables["Twelve_Hours"]:
                if item["field"] == "BattV_Min":
                    battery_voltage = item["latest"]["value"]
                    battery_timestamp = datetime.fromtimestamp(item["latest"]["ts"] / 1000)
                elif item["field"] == "PTemp_C_Max":
                    panel_temp = item["latest"]["value"]
                    temp_timestamp = datetime.fromtimestamp(item["latest"]["ts"] / 1000)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if battery_voltage is not None:
                    # Determine battery status and color
                    if battery_voltage >= 12.5:
                        status = "Healthy"
                        color = "#00FF00"  # Green
                        message = "Battery is at a healthy state of charge."
                        delta_color = "normal"
                    elif battery_voltage >= 12.1:
                        status = "Partially Discharged"
                        color = "#FFA500"  # Orange
                        message = "Battery should be recharged as soon as possible."
                        delta_color = "inverse"
                    else:
                        status = "Discharged"
                        color = "#FF0000"  # Red
                        message = "⚠️ Battery is fully discharged! Recharge immediately to prevent damage."
                        delta_color = "inverse"
                    
                    st.metric(
                        label=f"Battery Voltage ({status})",
                        value=f"{battery_voltage:.2f} V",
                        help=f"Updated: {battery_timestamp.strftime('%I:%M:%S %p')}"
                    )
                    
                    # Battery gauge
                    voltage_percent = min(100, max(0, (battery_voltage - 11.5) / (12.8 - 11.5) * 100))
                    st.markdown(f"""
                    <div style="background-color: #333; border-radius: 10px; padding: 5px; margin-top: -10px;">
                        <div style="background: linear-gradient(to right, {color}, {color}); 
                                    width: {voltage_percent}%; 
                                    height: 30px; 
                                    border-radius: 8px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    color: white;
                                    font-weight: bold;">
                            {voltage_percent:.0f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(message)
            
            with col2:
                if panel_temp is not None:
                    st.metric(
                        label="Panel Temperature (Max)",
                        value=f"{panel_temp:.1f} °C",
                        help=f"Updated: {temp_timestamp.strftime('%I:%M:%S %p')}"
                    )
                    # Convert to Fahrenheit
                    temp_f = (panel_temp * 9/5) + 32
                    st.caption(f"= {temp_f:.1f} °F")
            
            # Add timestamp footer
            if battery_timestamp or temp_timestamp:
                latest_timestamp = battery_timestamp or temp_timestamp
                current_time = datetime.now()
                age_hours = (current_time - latest_timestamp).total_seconds() / 3600
                
                if age_hours < 1:
                    age_text = f"{int(age_hours * 60)} minutes old"
                else:
                    age_text = f"{age_hours:.1f} hours old"
                
                st.caption(f"📅 Last updated: {latest_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')} ({age_text})")
    
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.exception(e)

# Footer
st.markdown("---")
st.caption("Data from Campbell Cloud API • Built by Chauncey")
