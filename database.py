import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def save_data(data):
    supabase.table("wpr_data").insert(data).execute()

def load_data():
    result = supabase.table("wpr_data").select("*").execute()
    data = result.data
    return data

def display_data():
    data = load_data()
    st.table(data)