import streamlit as st
import os


BLUEVERSE_SECRET_KEYS = ("BEARER_TOKEN", "API_URL", "SPACE_NAME", "FLOW_ID")


def load_blueverse_config():
    """Return BlueVerse config values plus any missing required keys."""
    config = {}
    missing = []

    for key in BLUEVERSE_SECRET_KEYS:
        value = st.secrets.get(key) or os.getenv(key)
        if value:
            config[key] = value
        else:
            missing.append(key)

    return config, missing
