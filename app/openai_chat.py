# openai_chat.py
import openai
import streamlit as st
import os

def initialize_openai():
    if "OPENAI_API_KEY" in st.secrets["openai"]:
        openai.api_key = st.secrets["openai"]["api_key"]
        print('open api key...', openai.api_key)
    else:
        # openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = ""
    if not openai.api_key:
        st.error("OpenAI API key not found. Please set it in the environment variables or Streamlit secrets.")
        st.stop()

def get_chatgpt_response(messages):
    """
    Sends the conversation history to OpenAI and returns the assistant's reply.

    :param messages: List of message dicts with 'role' and 'content'
    :return: Assistant's reply as a string
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or another model like "gpt-3.5-turbo"
            messages=messages,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        assistant_reply = response.choices[0].message['content'].strip()
        return assistant_reply
    except Exception as e:
        st.error(f"Error communicating with OpenAI: {e}")
        return "Sorry, I couldn't process that."