import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo

from config.settings import load_config
from auth.authentication import check_password
from api.campbell_client import get_access_token, get_datastreams
from utils.styles import apply_custom_css
from components.current_metrics import display_current_metrics
from components.wind_rose import display_wind_rose
from components.wind_chart import display_wind_chart
from components.temp_humidity import display_temp_humidity_chart
from components.system_status import display_system_status

st.set_page_config(
    page_title="Silverton Mountain Weather Station",
    page_icon="img/apple-touch-icon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
    # menu_items={
    #     'About': "Silverton Mountain Weather Station • Built by Chauncey"
    # }
)

config = load_config()

if not check_password(config["APP_PASSWORD"]):
    st.stop()

with st.sidebar:
    st.header("⚙️ Menu")
    
    if st.button("🔄 Refresh & Clear Cache", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
    
    st.markdown("---")
    
    st.header("🔗 Quick Links")
    st.markdown("### Weather Resources")
    st.markdown("- [Campbell Cloud](https://campbellcloud.com)")
    st.markdown("- [NOAA Weather](https://weather.gov)")
    st.markdown("- [Windy.com](https://windy.com)")
    
    st.markdown("### Data & Reports")
    st.markdown("- [Export Data](#)")
    st.markdown("- [Historical Reports](#)")

apply_custom_css()

st.title("Silverton Mountain Weather Station (12,280')")

if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = False

st.markdown(f"""
<style>
.stButton > button {{
    width: 100%;
}}
.stButton {{
    margin-top: 0px !important;
}}
div[data-testid="column"]:nth-child(2) .stButton > button {{
    {"background-color: #28a745; color: white;" if st.session_state.auto_refresh_enabled else ""}
}}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([0.15, 0.15, 0.7])
with col1:
    if st.button("🔄 Refresh & Clear Cache", width="stretch"):
        st.cache_data.clear()
        st.rerun()
with col2:
    button_label = "✅ Auto-refresh (ON)" if st.session_state.auto_refresh_enabled else "🔄 Auto-refresh every 5 min"
    if st.button(button_label, width="stretch", key="auto_refresh_btn"):
        st.session_state.auto_refresh_enabled = not st.session_state.auto_refresh_enabled
        st.rerun()

if st.session_state.auto_refresh_enabled:
    count = st_autorefresh(interval=300000, limit=144, debounce=True, key="data_refresher")
    if count >= 144:
        st.session_state.auto_refresh_enabled = False
        st.rerun()

with st.spinner("Fetching data from Campbell Cloud..."):
    try:
        token = get_access_token(config["BASE_URL"], config["USERNAME"], config["PASSWORD"])
        
        datastreams_response = get_datastreams(config["BASE_URL"], token, config["ORGANIZATION_ID"])
        datastreams = datastreams_response["data"]
        fetch_time = datastreams_response["fetched_at"]
        
        current_time = datetime.now(ZoneInfo("America/Denver"))
        try:
            fetch_dt = datetime.strptime(fetch_time, '%I:%M:%S %p').replace(
                year=current_time.year, 
                month=current_time.month, 
                day=current_time.day,
                tzinfo=ZoneInfo("America/Denver")
            )
            age_seconds = (current_time - fetch_dt).total_seconds()
            if age_seconds < 10:
                st.info(f"🆕 Data fetched fresh from API at {fetch_time}")
            else:
                st.success(f"⚡ Using cached data (fetched at {fetch_time})")
        except:
            st.info(f"📊 Data timestamp: {fetch_time}")
        
        display_current_metrics(config, token, datastreams)
        display_wind_rose(config, token, datastreams)
        display_wind_chart(config, token, datastreams)
        display_temp_humidity_chart(config, token, datastreams)
        display_system_status(config, token, datastreams)
    
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.exception(e)

st.markdown("---")
st.caption("Data from Campbell Cloud API • <a href='https://animasdigital.com' target='_blank'>Built by Chauncey</a> • v1.2.1", unsafe_allow_html=True)
