import streamlit as st
from bd_app.services import auth


def login_form():
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user = auth.authenticate_user(email, password)
        if user:
            token = auth.create_access_token({"sub": user.email})
            st.session_state["token"] = token
            st.session_state["authenticated"] = True
            st.success("Logged in")
        else:
            st.error("Invalid credentials")


def logout_button():
    if st.button("Logout"):
        st.session_state.clear()
        st.success("Logged out")


def auth_check():
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get("authenticated"):
                st.warning("Please log in")
                login_form()
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator


def role_check(required_role: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_email = auth.verify_token(st.session_state.get("token", "")).get("sub") if st.session_state.get("token") else None
            user = auth._fake_users.get(user_email) if user_email else None
            if not user or user.role != required_role:
                st.error("Unauthorized")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator


def register_form():
    st.info("User registration is restricted to administrators in this demo.")
