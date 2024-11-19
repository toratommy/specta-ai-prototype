# Simple authentication for login

import streamlit as st

def authenticate(username, password):
    credentials = st.secrets["credentials"]
    return username == credentials["username"] and password == credentials["password"]
