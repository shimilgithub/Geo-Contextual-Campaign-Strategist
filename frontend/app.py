import streamlit as st
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_backend.agent import run_campaign_agent

st.set_page_config(page_title="InMarket Geo-Strategist", layout="centered")

if "latitude" not in st.session_state:
    st.session_state.latitude = 35.7796
if "longitude" not in st.session_state:
    st.session_state.longitude = -78.6382
if "campaign_goal" not in st.session_state:
    st.session_state.campaign_goal = "Promote a new iced coffee blend in the local area."
if "agent_response" not in st.session_state:
    st.session_state.agent_response = ""

st.title("📍 Geo-Contextual Campaign Strategist")
st.write("Use the sidebar to enter coordinates and your campaign goal. Then press the button to trigger the external agent.")

with st.sidebar:
    st.header("Campaign Inputs")
    st.session_state.latitude = st.number_input(
        "Latitude",
        value=st.session_state.latitude,
        format="%.6f",
        key="latitude_input",
    )
    st.session_state.longitude = st.number_input(
        "Longitude",
        value=st.session_state.longitude,
        format="%.6f",
        key="longitude_input",
    )
    st.session_state.campaign_goal = st.text_area(
        "Campaign Goal",
        value=st.session_state.campaign_goal,
        height=150,
        key="campaign_goal_input",
    )

st.subheader("Run the Marketing Agent")
if st.button("Execute Agent"):
    with st.spinner("Running the external campaign agent..."):
        prompt = (
            f"Use latitude={st.session_state.latitude} and longitude={st.session_state.longitude}. "
            f"Campaign goal: {st.session_state.campaign_goal}. "
            "Check the weather and nearby cafe density, then provide a marketing strategy."
        )
        st.session_state.agent_response = run_campaign_agent(prompt)

if st.session_state.agent_response:
    st.markdown("### Agent Output")
    st.markdown(st.session_state.agent_response)
