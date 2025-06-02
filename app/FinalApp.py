
import streamlit as st
from database import SessionLocal, User
from security import hash_password, verify_password
from sqlalchemy.exc import IntegrityError
from openai_chat import initialize_openai, get_chatgpt_response
# from chat_interface import chat_interface_total
from chat_interface import chat_interface_total
# Main Function


# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''
    st.session_state['name'] = ''



def register():
    st.header("Register")
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if not all([name, username, email, password, password_confirm]):
            st.error("Please fill out all fields.")
            return
        if password != password_confirm:
            st.error("Passwords do not match.")
            return

        # Hash the password
        hashed_password = hash_password(password)

        # Create a new user instance
        new_user = User(
            username=username,
            name=name,
            email=email,
            password=hashed_password
        )

        # Add the user to the database
        session = SessionLocal()
        try:
            session.add(new_user)
            session.commit()
            st.success("Registration successful! You can now log in.")
        except IntegrityError:
            session.rollback()
            st.error("Username or email already exists.")
        finally:
            session.close()


def login():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not all([username, password]):
            st.error("Please enter both username and password.")
            return

        session = SessionLocal()
        user = session.query(User).filter(User.username == username).first()
        session.close()

        if user and verify_password(password, user.password):
            st.success(f"Welcome, {user.name}!")
            # Set session state
            st.session_state['authenticated'] = True
            st.session_state['username'] = user.username
            st.session_state['name'] = user.name
        else:
            st.error("Invalid username or password.")


def logout():
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''
    st.session_state['name'] = ''
    st.success("You have been logged out.")


def main():
    # Sidebar Navigation
    st.sidebar.title("User Access  👈")
    if st.session_state['authenticated']:
        st.sidebar.write(f"**Logged in as:** {st.session_state['name']}")
        if st.sidebar.button("Logout"):
            logout()
        page = st.sidebar.radio("Go to", ["Dashboard"])
    else:
        page = st.sidebar.radio("Go to", ["Login", "Register"])

    # Main Content
    if page == "Register":
        register()
    elif page == "Login":
        login()
    elif page == "Dashboard":
        if st.session_state['authenticated']:
            st.title("Chat Dashboard 🐼")
            st.write(f"Welcome to your dashboard, {st.session_state['name']}!")
            # Add Chat Interface here
            uploaded_file = st.sidebar.file_uploader("Upload File")
            chat_interface_total(uploaded_file)
        else:
            st.error("You must be logged in to access the dashboard.")
            st.warning("Please log in first.")


if __name__ == "__main__":
    main()