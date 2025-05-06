import re
import json
import streamlit as st
import sqlite3
import pandas as pd
import math


# read sqlite database
conn = sqlite3.connect('universities_sampled.db')
sql = 'SELECT * FROM universities'
df = pd.read_sql(sql, conn)
conn.close()


st.set_page_config(layout="wide")
st.title('University Search Database')
search_query = st.text_input("Search universities (e.g., country, city, university, study, level, fees)", key='omni_search', placeholder="Enter search term...")
col1, col2, col3, col4 = st.columns(4)
country_filter = col1.selectbox('Country', options=['All'] + sorted(df['country'].unique()), key='country_filter')
city_filter = col2.selectbox('City', options=['All'] + sorted(df[(country_filter == 'All') | (df["country"] == country_filter)]['city'].dropna().unique()), key='city_filter')
level_filter = col3.selectbox('Program Level', options=['All'] + sorted(df['level'].unique()), key='level_filter')
fees_categories = ['Below €5,000', '€5,000 - €10,000', '€10,000 - €20,000', '€20,000 - €30,000', 'Above €30,000']
fee_filter = col4.selectbox('Fees', options=['All'] + sorted(df['fees_category'].dropna().unique().tolist(), key=lambda x: fees_categories.index(x)), key='fee_filter')

# Filter data
filtered_df = df.copy()
if search_query:
    search_query = search_query.lower()
    filtered_df = filtered_df[
        filtered_df[['country', 'city', 'university', 'study', 'level', 'fees_category']]
        .astype(str)
        .apply(lambda x: x.str.lower())
        .apply(lambda x: x.str.contains(search_query, case=False, na=False))
        .any(axis=1)
    ]
filtered_df = filtered_df[
    ((country_filter == 'All') | (filtered_df["country"] == country_filter)) &
    ((city_filter == 'All') | (filtered_df["city"] == city_filter)) &
    ((level_filter == 'All') | (filtered_df["level"] == level_filter)) &
    ((fee_filter == 'All') | (filtered_df["fees_category"] == fee_filter))
].reset_index()

# Show Results
st.subheader("Results")

if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# Page navigation
col_prev, col_page, col_next, _, col_size= st.columns([1, 2, 1, 2, 1])
page_size = col_size.selectbox("Results per page", options=[5, 10, 20, 50], index=1, key='page_size', label_visibility='collapsed')
total_rows = len(filtered_df)
total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1

if col_prev.button("Previous"):
    st.session_state.current_page = max(1, st.session_state.current_page - 1)
if col_next.button("Next"):
    st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
col_page.write(f"Page {st.session_state.current_page} of {total_pages} (Total results: {total_rows})")


start_idx = (st.session_state.current_page - 1) * page_size
end_idx = min(start_idx + page_size, total_rows)


@st.dialog("Detail")
def detail(row):
    st.write(f'Partner: {row['partner']}')
    st.write(f'Country: {row['country']}')
    if row['city']:
        st.write(f'City: {row['city']}')
    st.write(f'University: [{row['university']}]({row['url']})')
    if row['faculty']:
        st.write(f'Faculty: {row['faculty']}')
    st.write(f'Study: {row['study']}')
    st.write(f'Level: {row['level']}')
    if row['degree_duration'] > 0:
        st.write(f'Duration: {int(row['degree_duration'])} months')
    if row['fees_std'] > 0:
        st.write(f'Fees: €{row['fees_std']:,.0f}' + (f"({row['fees']:,.0f} {row['currency']})" if row['currency'] != 'EUR' else ''))
    if row['app_fees_std'] > 0:
        st.write(f'App Fees: €{row['app_fees_std']:,.0f}' + (f"({row['app_fees']:,.0f} {row['currency']})" if row['currency'] != 'EUR' else ''))


for idx, row in filtered_df.iloc[start_idx:end_idx].iterrows():
    with st.container(border=True):
        col_univ, col_study, col_button = st.columns([1, 1, 1])
        col_univ.write(f'University: [{row['university']}]({row['url']})')
        col_study.write(f'Study: {row['study']}')
        if col_button.button("Detail", key=idx):
            detail(row)
