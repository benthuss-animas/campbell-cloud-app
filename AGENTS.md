# Campbell Cloud Weather Station - Agent Guidelines

## Running the Application
- **Run Streamlit app**: `streamlit run app.py`
- **Run CLI tools**: `python projects/main.py` or `python projects/favorites.py`
- No formal test framework detected - verify functionality by running the app

## Architecture & Structure
- **Main app**: `app.py` - Streamlit dashboard displaying Campbell Cloud weather data
- **Projects folder**: Contains CLI scripts (`main.py`, `favorites.py`) for API testing
- **Documentation**: `documentation/oas-campbell-cloud-external.yaml` - OpenAPI spec for Campbell Cloud API
- **API**: Uses Campbell Cloud REST API at `https://us-west-2.campbell-cloud.com/api/v1/`
- **Authentication**: Bearer token auth with 60-minute expiration, cached for 50 minutes
- **Data caching**: Uses `@st.cache_data` with TTL for performance (5-50 minutes)

## Code Style & Conventions
- **Language**: Python with Streamlit for web UI
- **Imports**: Standard library first, then third-party (`streamlit`, `requests`, `plotly`, `pandas`, `numpy`)
- **Authentication**: Credentials loaded from environment variables (`CAMPBELL_USERNAME`, `CAMPBELL_PASSWORD`)
- **Naming**: snake_case for functions/variables, UPPER_CASE for constants
- **Error handling**: Use `response.raise_for_status()` for API calls, fallback values for missing data
- **Types**: No type hints used - follow existing convention
- **Comments**: Minimal - use docstrings for functions, inline comments only where necessary
