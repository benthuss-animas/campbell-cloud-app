import streamlit as st
import hashlib

def check_password(app_password):
    """Returns True if user entered correct password"""
    current_hash = hashlib.sha256(app_password.encode()).hexdigest()[:16]
    
    if "authenticated" not in st.session_state:
        stored_hash = st.query_params.get("auth", "")
        st.session_state.authenticated = stored_hash == current_hash
    
    if not st.session_state.authenticated:
        st.title("Authentication Required")
        password_input = st.text_input("Enter password:", type="password", key="password_input")
        
        if st.button("Login"):
            if password_input == app_password:
                st.session_state.authenticated = True
                st.query_params["auth"] = current_hash
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True
