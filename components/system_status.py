import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from api.campbell_client import get_latest_datapoint

def display_system_status(config, token, datastreams):
    """Display battery and system status"""
    battery_voltage = None
    panel_temp = None
    battery_timestamp = None
    temp_timestamp = None
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Twelve_Hours":
            latest = get_latest_datapoint(config["BASE_URL"], token, config["ORGANIZATION_ID"], ds.get("id"))
            if latest and latest.get("data"):
                if field_name == "BattV_Min":
                    battery_voltage = latest["data"][0]["value"]
                    battery_timestamp = datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                elif field_name == "PTemp_C_Max":
                    panel_temp = latest["data"][0]["value"]
                    temp_timestamp = datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
    
    if battery_voltage is not None or panel_temp is not None:
        st.markdown("---")
        st.subheader("🔋 System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if battery_voltage is not None:
                if battery_voltage >= 12.5:
                    status = "Healthy"
                    color = "#00FF00"
                    message = "Battery is at a healthy state of charge."
                elif battery_voltage >= 12.1:
                    status = "Partially Discharged"
                    color = "#FFA500"
                    message = "Battery should be recharged as soon as possible."
                else:
                    status = "Discharged"
                    color = "#FF0000"
                    message = "⚠️ Battery is fully discharged! Recharge immediately to prevent damage."
                
                st.metric(
                    label=f"Battery Voltage ({status})",
                    value=f"{battery_voltage:.2f} V",
                    help=f"Updated: {battery_timestamp.strftime('%I:%M:%S %p')}"
                )
                
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
                temp_f = (panel_temp * 9/5) + 32
                st.caption(f"= {temp_f:.1f} °F")
        
        if battery_timestamp or temp_timestamp:
            latest_timestamp = battery_timestamp or temp_timestamp
            current_time = datetime.now(ZoneInfo("America/Denver"))
            age_hours = (current_time - latest_timestamp).total_seconds() / 3600
            
            if age_hours < 1:
                age_text = f"{int(age_hours * 60)} minutes old"
            else:
                age_text = f"{age_hours:.1f} hours old"
            
            st.caption(f"📅 Last updated: {latest_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')} ({age_text})")
