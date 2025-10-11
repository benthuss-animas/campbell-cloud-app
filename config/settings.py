import streamlit as st

def load_config():
    """Load configuration from Streamlit secrets"""
    try:
        config = {
            "BASE_URL": st.secrets["CAMPBELL_BASE_URL"],
            "USERNAME": st.secrets["CAMPBELL_USERNAME"],
            "PASSWORD": st.secrets["CAMPBELL_PASSWORD"],
            "ORGANIZATION_ID": st.secrets["CAMPBELL_ORGANIZATION_ID"],
            "APP_PASSWORD": st.secrets["APP_PASSWORD"]
        }
        return config
    except KeyError as e:
        st.error(f"Missing required secret: {e}. Please configure secrets in Streamlit Cloud.")
        st.stop()
    except FileNotFoundError:
        st.error("No secrets file found. Please configure secrets in Streamlit Cloud or add .streamlit/secrets.toml locally.")
        st.stop()
