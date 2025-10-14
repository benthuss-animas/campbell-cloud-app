# Campbell Cloud Weather Station - Agent Guidelines

## Running the Application
- **Run Streamlit app**: `streamlit run app.py`
- No formal test framework detected - verify functionality by running the app

## Architecture & Structure
- **Main app**: `app.py` - Streamlit dashboard for Silverton Mountain Weather Station
- **API layer**: `api/campbell_client.py` - Campbell Cloud API client with cached functions
- **Authentication**: 
  - `auth/authentication.py` - Password-protected app access with session state
  - `config/settings.py` - Loads credentials from Streamlit secrets
- **Components**: Modular UI components in `components/`:
  - `current_metrics.py` - Current weather readings display
  - `wind_rose.py` - Wind direction visualization
  - `wind_chart.py` - Wind speed/direction charts
  - `temp_humidity.py` - Temperature and humidity charts
  - `system_status.py` - Station system status
- **Utils**: `utils/formatters.py` and `utils/styles.py` for formatting and CSS
- **Documentation**: `documentation/oas-campbell-cloud-external.yaml` - OpenAPI spec
- **Tests**: `tests/favs.py` - test scripts
- **Data caching**: `@st.cache_data` with TTL: 3000s for tokens, 300s for data

## Code Style & Conventions
- **Language**: Python with Streamlit for web UI
- **Dependencies**: streamlit, requests, plotly, pandas, numpy
- **Imports**: Standard library first (datetime, zoneinfo), then third-party (streamlit, requests, plotly, pandas, numpy)
- **Configuration**: Credentials from Streamlit secrets (not env vars): `CAMPBELL_BASE_URL`, `CAMPBELL_USERNAME`, `CAMPBELL_PASSWORD`, `CAMPBELL_ORGANIZATION_ID`, `APP_PASSWORD`
- **Naming**: snake_case for functions/variables
- **Error handling**: Use `response.raise_for_status()` for API calls, try/except for data processing
- **Types**: No type hints - follow existing convention
- **Comments**: Minimal - docstrings for functions only
- **Timezone**: America/Denver for all timestamps
