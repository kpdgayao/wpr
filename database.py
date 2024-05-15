import pandas as pd
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid

def save_data(data):
    try:
        df = pd.read_csv("wpr_data.csv")
        df = df.append(data, ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([data])
    
    df.to_csv("wpr_data.csv", index=False)

def load_data():
    try:
        df = pd.read_csv("wpr_data.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "Team", "Week Number", "Year", "Completed Tasks", "Number of Completed Tasks",
                                   "Pending Tasks", "Number of Pending Tasks", "Dropped Tasks", "Number of Dropped Tasks",
                                   "Productivity Rating", "Productivity Suggestions", "Productivity Details",
                                   "Productive Time", "Productive Place"])
    return df

def display_data():
    df = load_data()
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options)