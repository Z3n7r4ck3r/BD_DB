import streamlit as st

def toast_notification(message: str, type: str = "info"):
    st.toast(message)

def loading_spinner(text: str):
    return st.spinner(text)

def confirmation_modal(title: str, message: str):
    st.warning(f"{title}: {message}")

def progress_bar(value: int, max_value: int):
    st.progress(value / max_value)

def status_badge(status: str, color: str):
    st.markdown(f"<span style='background-color:{color};padding:0.2em 0.5em;border-radius:4px;'>{status}</span>", unsafe_allow_html=True)

def metric_card(title: str, value: str, delta: str = ""):
    st.metric(title, value, delta)
