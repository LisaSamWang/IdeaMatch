import streamlit as st
import pandas as pd
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import streamlit as st
import json
from google.oauth2 import service_account
import googleapiclient.discovery

# Fetch idea submissions data from Google Sheets
def fetch_google_sheets_data():
    try:
        # Define the scope
        # scope = [
        #     "https://spreadsheets.google.com/feeds",
        #     "https://www.googleapis.com/auth/spreadsheets",
        #     "https://www.googleapis.com/auth/drive.file",
        #     "https://www.googleapis.com/auth/drive"
        # ]

        # # Load credentials from json
        # creds = ServiceAccountCredentials.from_json_keyfile_name(
        #     "ideamatch-402003-87cc447222eb.json", scope)
        google_creds = json.loads(st.secrets["google"]["creds"])

        # Use credentials to access Google Sheets API
        creds = service_account.Credentials.from_service_account_info(google_creds, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
        # Authorize client
        client = gspread.authorize(creds)

        # Open the Google Sheets and get data
        sheet = client.open("testform").sheet1
        # Fetch data records
        data = sheet.get_all_records()

        # Check if data is empty
        if not data:
            st.warning("No data available in the sheet.")
            return pd.DataFrame()
        
        # Convert data to DataFrame
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Failed to fetch data from Google Sheets: {str(e)}")
        return pd.DataFrame()
    
# Streamlit UI: Questionnaire Page
def questionnaire():
    st.title("Find Your Ideal Team")
    with st.form("questionnaire"):
        preferred_industry = st.text_input("Preferred Industry Space")
        non_preferred_industry = st.text_input("Non-Preferred Industry Space")
        background = st.text_input("Background/Program")
        seriousness = st.selectbox("How serious are you?", ["Just passing", "Want an actual startup", "Want a good grade", "Average is fine"])
        additional_info = st.text_area("Any Additional Information")
        submit = st.form_submit_button("Submit")
        if submit:
            # Store the user responses in the session state
            st.session_state.user_responses = {
                'preferred_industry': [preferred_industry],
                'non_preferred_industry': [non_preferred_industry],
                'background': background,
                'seriousness': seriousness
            }
            st.success("Questionnaire Submitted!")

# Matching Function
def match_user_to_ideas(user, idea_submissions):
    seriousness_map = {"Just passing": 1, "Average is fine": 2, "Want a good grade": 3, "Want an actual startup": 4}
    idea_submissions['seriousness'] = idea_submissions['seriousness'].map(seriousness_map)
    user['seriousness'] = seriousness_map[user['seriousness']]
    
    idea_submissions = idea_submissions[~idea_submissions['industry_space'].isin(user['non_preferred_industry'])]
    idea_submissions = idea_submissions[idea_submissions['team_members'] < 5]
    
    idea_submissions['idea_space_match'] = idea_submissions['industry_space'].isin(user['preferred_industry']).astype(int)
    idea_submissions['seriousness_score'] = abs(idea_submissions['seriousness'] - user['seriousness'])
    idea_submissions['background_match'] = (idea_submissions['desired_background'] == user['background']).astype(int)
    
    idea_submissions['total_score'] = (
        idea_submissions['idea_space_match'] * 3 +
        idea_submissions['seriousness_score'] * 2 +
        idea_submissions['background_match'] * 1
    )
    
    sorted_ideas = idea_submissions.sort_values(by='total_score', ascending=False)
    return sorted_ideas

# Streamlit UI: Matches Page with user data from session state
def view_matches():
    st.title("Your Matches")
    idea_submissions = fetch_google_sheets_data()
    
    if hasattr(st.session_state, "user_responses"):  # Check if user_responses exists in the session state
        user = st.session_state.user_responses
        matched_ideas = match_user_to_ideas(user, idea_submissions)
        st.dataframe(matched_ideas[['idea_title', 'industry_space', 'seriousness', 'desired_background', 'contact_info']])
    else:
        st.warning("No user data available for matching. Please fill out the questionnaire first.")

# Streamlit UI: Dashboard Page
def dashboard():
    st.title("Dashboard")
    idea_submissions = fetch_google_sheets_data()
    fig = px.histogram(idea_submissions, x="industry_space")
    st.plotly_chart(fig)

# Navigation
page = st.sidebar.selectbox("Choose a page:", ["Questionnaire", "View Matches", "Dashboard"])
if page == "Questionnaire":
    questionnaire()
elif page == "View Matches":
    view_matches()
elif page == "Dashboard":
    dashboard()
