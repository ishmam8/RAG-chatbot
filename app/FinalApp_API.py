import streamlit as st
from database import SessionLocal, User
from security import hash_password, verify_password
from sqlalchemy.exc import IntegrityError
from openai_chat import initialize_openai, get_chatgpt_response
# from chat_interface import chat_interface_total
from chat_interface import chat_interface_total
# Main Function
import streamlit as st
import requests


# Backend API URL
API_URL = "http://54.85.84.7/auth/"


# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''
    st.session_state['name'] = ''


def register():
    # st.header("Register")
    st.header("👷 Register for AI Chatbot 🤖🌍🏗️")
    st.markdown("Create an account to start interacting with your AI Assistant.")
    st.markdown(
        """
        <style>
            .stApp, section.stMain {
                height: 1000px;
            }
        </style>        
        """,unsafe_allow_html = True)


    # name = st.text_input("Full Name")
    name = st.text_input("name")
    email = st.text_input("email")
    password = st.text_input("password", type="password")
    # password_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if not all([name,  email, password]):
            st.error("Please fill out all fields.")
            return
        # if password != password_confirm:
        #     st.error("Passwords do not match.")
        #     return

        # Send registration data to FastAPI
        data = {
            "name": name,
            # "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(f"{API_URL}signup", json=data)
        if response.status_code == 200:
            st.success("Registration successful! You can now log in.")
        elif response.status_code == 400:
            st.error(response.json().get("detail", "Registration failed."))
        else:
            st.error("An error occurred. Please try again later.")

def login():
    # st.header("Login")
    # username = st.text_input("Username")
    st.header("🔑 Login to Your AI Chatbot 🤖🏠💬")
    st.markdown("Log in to access your dashboard and start chatting.")
    st.markdown(
        """
        <style>
            .stApp, section.stMain {
                height: 1000px;
            }
        </style>        
        """,unsafe_allow_html = True)
    email = st.text_input("email")
    password = st.text_input("password", type="password")

    if st.button("Login"):
        if not all([email, password]):
            st.error("Please enter both username and password.")
            return

        # Send login data to FastAPI
        data = {
            "email": email,
            "password": password
        }

        response = requests.post(f"{API_URL}login", json=data)

        if response.status_code == 200:
            user_data = response.json()
            # print('user data...', user_data)
            # st.success(f"Welcome back, {data['email']}!")
            st.success(f"Welcome back, My Friends!")
            st.session_state['authenticated'] = True
            # st.session_state['username'] = user_data['username']
            # st.session_state['name'] = user_data['name']
        elif response.status_code == 401:
            st.error("Invalid username or password.")
        else:
            st.error("An error occurred. Please try again later.")



def logout():
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''
    st.session_state['name'] = ''
    st.success("You have been logged out.")


def main():
    # st.sidebar.title("User Access 👈")
    # st.sidebar.image("https://bobthebuilder.ai/", caption="Construction AI Assistant",
    #                  use_column_width=True)  # Replace with logo
    st.sidebar.title("User Access 👈")
    st.sidebar.image("chat_robot_access.png",
                     caption="Construction AI Assistant",
                     use_column_width=True)  # Make sure the file path matches your environment
    st.markdown(
        """
        <style>
            .stApp, section.stMain {
                height: 1000px;
            }
        </style>        
        """,unsafe_allow_html = True)

    # Main content
    st.title("Welcome to BobtheBuilder 👷!")
    # st.write("This assistant is here to help with your construction-related queries.")
    if st.session_state['authenticated']:
        st.sidebar.write(f"**Logged in as:** {st.session_state['name']}")
        if st.sidebar.button("Logout"):
            logout()
        page = st.sidebar.radio("Go to", ["Dashboard"])
    else:
        page = st.sidebar.radio("Go to", ["Register", "Login"])

    if page == "Register":
        register()
    elif page == "Login":
        login()
    elif page == "Dashboard":
        if st.session_state['authenticated']:
            st.header("AI Chat Robot Dashboard 🤖")
            # st.write(f"Welcome to your dashboard, {st.session_state['name']}!")
            uploaded_file = st.sidebar.file_uploader("Upload File")
            chat_interface_total(uploaded_file)
        else:
            st.error("You must be logged in to access the dashboard.")
            st.warning("Please log in first.")

if __name__ == "__main__":
    main()