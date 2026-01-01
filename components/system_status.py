import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from api.campbell_client import get_latest_datapoint

def display_system_status(config, token, datastreams):
    """Display battery and system status"""
    battery_voltage = None
    panel_temp = None
    radio_strength = None
    battery_timestamp = None
    temp_timestamp = None
    radio_timestamp = None
    all_status_data = []
    
    for ds in datastreams:
        metadata = ds.get("metadata", {})
        table_name = metadata.get("table", "")
        field_name = metadata.get("field", "")
        
        if table_name == "Hourly" and field_name == "BattV_Min":
            latest = get_latest_datapoint(config["BASE_URL"], token, config["ORGANIZATION_ID"], ds.get("id"))
            if latest and latest.get("data"):
                value = latest["data"][0]["value"]
                timestamp = datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                all_status_data.append({
                    'Field': field_name,
                    'Value': value,
                    'Timestamp': timestamp,
                    'Table': table_name
                })
                battery_voltage = value
                battery_timestamp = timestamp
        
        elif table_name == "Twelve_Hours" and field_name == "PTemp_C_Max":
            latest = get_latest_datapoint(config["BASE_URL"], token, config["ORGANIZATION_ID"], ds.get("id"))
            if latest and latest.get("data"):
                value = latest["data"][0]["value"]
                timestamp = datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                all_status_data.append({
                    'Field': field_name,
                    'Value': value,
                    'Timestamp': timestamp,
                    'Table': table_name
                })
                panel_temp = value
                temp_timestamp = timestamp
        
        elif table_name == "RadioDiagnostics" and field_name == "RadioStrength":
            latest = get_latest_datapoint(config["BASE_URL"], token, config["ORGANIZATION_ID"], ds.get("id"))
            if latest and latest.get("data"):
                value = latest["data"][0]["value"]
                timestamp = datetime.fromtimestamp(latest["data"][0]["ts"] / 1000, tz=ZoneInfo("America/Denver"))
                all_status_data.append({
                    'Field': field_name,
                    'Value': value,
                    'Timestamp': timestamp,
                    'Table': table_name
                })
                radio_strength = value
                radio_timestamp = timestamp
    
    if battery_voltage is not None or panel_temp is not None or radio_strength is not None:
        st.markdown("---")
        st.subheader("🔋 System Status")
        
        col1, col2, col3 = st.columns(3)
        
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
        
        with col3:
            if radio_strength is not None:
                st.metric(
                    label="Radio Strength",
                    value=f"{radio_strength}",
                    help=f"Updated: {radio_timestamp.strftime('%I:%M:%S %p')}"
                )
        
        current_time = datetime.now(ZoneInfo("America/Denver"))
        
        if battery_timestamp:
            battery_age_hours = (current_time - battery_timestamp).total_seconds() / 3600
            if battery_age_hours < 1:
                battery_age_text = f"{int(battery_age_hours * 60)} minutes old"
            else:
                battery_age_text = f"{battery_age_hours:.1f} hours old"
            st.caption(f"🔋 Battery updated: {battery_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')} ({battery_age_text}) - Hourly table")
        
        if temp_timestamp:
            temp_age_hours = (current_time - temp_timestamp).total_seconds() / 3600
            if temp_age_hours < 1:
                temp_age_text = f"{int(temp_age_hours * 60)} minutes old"
            else:
                temp_age_text = f"{temp_age_hours:.1f} hours old"
            st.caption(f"🌡️ Panel temp updated: {temp_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')} ({temp_age_text}) - 12-Hour table")
        
        if radio_timestamp:
            radio_age_hours = (current_time - radio_timestamp).total_seconds() / 3600
            if radio_age_hours < 1:
                radio_age_text = f"{int(radio_age_hours * 60)} minutes old"
            else:
                radio_age_text = f"{radio_age_hours:.1f} hours old"
            st.caption(f"📡 Radio updated: {radio_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')} ({radio_age_text}) - RadioDiagnostics table")
        
        if all_status_data:
            with st.expander("📊 View All System Data"):
                df = pd.DataFrame(all_status_data)
                df['Value'] = df['Value'].astype(str)
                df['Timestamp'] = df['Timestamp'].apply(lambda t: t.strftime('%Y-%m-%d %I:%M %p'))
                st.dataframe(df, width="stretch", height=400)
