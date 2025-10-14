import streamlit as st

def apply_custom_css():
    """Apply custom CSS styles to the Streamlit app"""
    st.markdown("""
    <style>
        h3#24-hour-wind-rose {
            margin-bottom:-2rem;
        }        
        h1 {
            font-size: 1.8rem !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .main > div {
            padding-top: 0 !important;
        }
        .block-container {
            padding-top: 4rem !important;
        }
        button[kind="secondary"] {
            padding: 0.25rem 0.5rem;
            min-height: unset;
        }
        button[kind="secondary"] p {
            font-size: 0.8rem !important;
        }
        .modebar {
            margin-top: -20px !important;
        }
        @media (max-width: 768px) {
            h2 {
                margin-bottom: 0.5rem !important;
            }
            .stPlotlyChart {
                margin-top: -1rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def get_metric_card_css():
    """Get CSS for metric cards"""
    return """
    <style>
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 15px;
        margin-bottom: 20px;
    }
    @media (max-width: 768px) {
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
        }
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
    """
