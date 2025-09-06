import streamlit as st
from bd_app.components import auth as auth_component

st.set_page_config(page_title="BD Database App")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    st.title("BD Database App")
    auth_component.logout_button()
    st.write("Welcome!")
else:
    auth_component.login_form()
