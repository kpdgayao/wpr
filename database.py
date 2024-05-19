import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def save_data(data):
    supabase.table("wpr_data").insert(data).execute()

def load_data():
    result = supabase.table("wpr_data").select("*").execute()
    data = result.data
    df = pd.DataFrame(data)
    return df

def display_data():
    df = load_data()
    st.dataframe(df)