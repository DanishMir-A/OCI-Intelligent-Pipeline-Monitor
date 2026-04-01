import streamlit as st


BLUEVERSE_SECRET_KEYS = ("BEARER_TOKEN", "API_URL", "SPACE_NAME", "FLOW_ID")


def load_blueverse_config():
    """Return BlueVerse config values plus any missing required keys."""
    config = {}
    missing = []

    for key in BLUEVERSE_SECRET_KEYS:
        value = st.secrets.get(key)
        if value:
            config[key] = value
        else:
            missing.append(key)

    return config, missing
