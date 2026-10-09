import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import time
from uuid import uuid4
from PIL import Image

import database
import utils
from ai_engine import ai_system
from email_service import send_complaint_email
import pandas as pd

st.set_page_config(page_title="User Dashboard", page_icon="📝", layout="wide")
utils.render_sidebar()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the Home Page to access this portal.")
    st.stop()

if st.session_state.user_info.get("role") != "User":
    st.warning("This page is restricted to Citizens (Users).")
    st.stop()

try:
    database.setup_database()
except Exception:
    pass

st.title("📝 User Dashboard - Submit a Grievance")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Your Details")
    default_name = st.session_state.user_info.get("name", "")
    default_contact = st.session_state.user_info.get("email", "") or st.session_state.user_info.get("phone", "")
    user_name = st.text_input("Name", value=default_name, placeholder="Enter your full name")
    user_contact = st.text_input("Contact Number / Email", value=default_contact, placeholder="Enter phone or email")
    st.subheader("Complaint Details")
    description = st.text_area("Describe the issue in detail")
    uploaded_file = st.file_uploader("Upload Image Proof", type=['png', 'jpg', 'jpeg'])

with col2:
    st.subheader("Location")
    st.write("Click on the map to pinpoint the exact location.")
    # Centered at Nashik for demo
    m = folium.Map(location=[20.0059, 73.7900], zoom_start=13)
    # Add click for marker
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=300, width=500)

lat, lon = None, None
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"Location selected: {lat:.4f}, {lon:.4f}")
else:
    st.info("Please click on the map to select a location.")

def assign_ward(lat, lon):
    # Mock logic to assign ward based on coordinates
    wards_df = database.get_wards_df()
    if len(wards_df) == 0:
        return None, None, None
    # For demo, just randomly pick one or simply pick the first
    import random
    idx = random.randint(0, len(wards_df)-1)
    row = wards_df.iloc[idx]
    return row['ward_name'], row['nagar_sevak_name'], row['email']

if st.button("Submit Complaint"):
    if not user_name:
        st.error("Your name is required.")
    elif not description:
        st.error("Description is required.")
    elif not uploaded_file:
        st.error("Image proof is required.")
    elif not lat or not lon:
        st.error("Location is required. Please click on the map.")
    else:
        with st.spinner("Processing... AI is analyzing the complaint..."):
            complaint_id = f"CMP-{str(uuid4())[:8].upper()}"
            img_path = f"uploads/{complaint_id}.jpg"
            
            image = Image.open(uploaded_file)
            image.save(img_path)
            
            # AI Inference
            category, priority = ai_system.predict_text(description)
            verification, analysis_summary = ai_system.verify_image(img_path, category)
            
            ward, sevak_name, sevak_email = assign_ward(lat, lon)
            
            # Save to DB
            database.insert_complaint(
                complaint_id, description, lat, lon, ward, img_path, 
                verification, category, priority, user_name, user_contact,
                image_analysis=analysis_summary,
                user_id=st.session_state.user_info["id"]
            )
            
            # Send Email
            # if sevak_email:
            #     send_complaint_email(sevak_email, sevak_name, complaint_id, category, priority, description, lat, lon)
                
        st.success(f"Complaint {complaint_id} submitted successfully!")
        
        # Display AI Results
        st.subheader("AI Analysis Results")
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Verification", verification)
        res_col2.metric("Category", category)
        res_col3.metric("Priority", priority)
        
        # Display detailed image analysis
        with st.expander("🔍 Image Analysis Details", expanded=True):
            st.write("**AI Visual Question Answering (BLIP VQA):**")
            st.code(analysis_summary, language=None)
            if verification == "Verified":
                st.success("✅ The uploaded image matches the complaint category.")
            elif verification == "Suspicious":
                st.warning("⚠️ The uploaded image may not match the complaint category.")
            else:
                st.info(f"ℹ️ Verification status: {verification}")
        
        st.info(f"Assigned to: {sevak_name} ({ward})")
