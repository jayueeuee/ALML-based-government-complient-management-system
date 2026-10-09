import streamlit as st
import database
import pandas as pd
from PIL import Image
import utils

st.set_page_config(page_title="Officer Dashboard", page_icon="👮", layout="wide")
utils.render_sidebar()

try:
    database.setup_database()
except Exception:
    pass

st.title("👮 Field Officer Dashboard")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the Home Page to access this portal.")
    st.stop()

if st.session_state.user_info.get("role") != "Officer":
    st.warning("This page is restricted to Field Officers.")
    st.stop()

officer_info = st.session_state.user_info
officer_id = officer_info['id']
officer_ward = officer_info['ward_name']

col_title, col_logout = st.columns([4, 1])
with col_title:
    st.subheader(f"Welcome, {officer_info.get('name', 'Officer')} ({officer_ward})")
with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

# Load assigned complaints
assigned_df = database.get_officer_assignments(officer_id)

if assigned_df.empty:
    st.info("No complaints have been assigned to you yet.")
    st.stop()

# Quick Stats
c1, c2, c3 = st.columns(3)
c1.metric("Total Assigned", len(assigned_df))
c2.metric("Pending", len(assigned_df[assigned_df['assignment_status'] == 'Assigned']))
c3.metric("Completed", len(assigned_df[assigned_df['assignment_status'] == 'Completed']))

st.markdown("---")

# Separate pending and completed
pending_df = assigned_df[assigned_df['assignment_status'] == 'Assigned']
completed_df = assigned_df[assigned_df['assignment_status'] == 'Completed']

tab1, tab2 = st.tabs([f"⏳ Pending Verification ({len(pending_df)})", f"✅ Completed ({len(completed_df)})"])

with tab1:
    if pending_df.empty:
        st.success("All assigned complaints have been verified!")
    else:
        for idx, comp in pending_df.iterrows():
            comp_id = comp['id']
            with st.container():
                st.markdown(f"### 📋 {comp_id}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {comp['description']}")
                    st.write(f"**Category:** {comp['category']} | **Priority:** {comp['priority']}")
                    st.write(f"**AI Verification:** ⚠️ {comp['verification_status']}")
                    st.write(f"**Submitted On:** {comp['submission_date']}")
                    st.write(f"**Location:** {comp.get('lat', 'N/A')}, {comp.get('lon', 'N/A')}")
                    user_n = comp.get('user_name', 'Unknown')
                    st.write(f"**Reported By:** {user_n if pd.notna(user_n) else 'Unknown'}")
                    
                    # Show AI analysis if available
                    analysis = comp.get('image_analysis', '')
                    if analysis and pd.notna(analysis) and analysis != '':
                        with st.expander("🤖 AI Image Analysis"):
                            st.code(analysis, language=None)
                            
                with col2:
                    try:
                        img = Image.open(comp['image_path'])
                        st.image(img, caption="User Uploaded Proof", use_container_width=True)
                    except:
                        st.warning("Image not found.")
                
                st.markdown("#### 🔎 Physical Verification Form")
                
                ver_result = st.radio(
                    "Verification Result",
                    ["Confirmed", "Rejected"],
                    key=f"ver_{comp_id}",
                    horizontal=True,
                    help="Confirmed = complaint is genuine | Rejected = complaint is fake/invalid"
                )
                
                remarks = st.text_area(
                    "Officer Remarks",
                    placeholder="Describe what you found at the location...",
                    key=f"rem_{comp_id}"
                )
                
                proof_file = st.file_uploader(
                    "📷 Upload Photo Proof (taken at location)",
                    type=['png', 'jpg', 'jpeg'],
                    key=f"proof_{comp_id}"
                )
                
                if st.button("✅ Submit Verification", key=f"submit_{comp_id}", type="primary"):
                    if not remarks:
                        st.error("Please add your remarks about the physical verification.")
                    elif not proof_file:
                        st.error("Please upload a photo proof from the location.")
                    else:
                        # Save the proof photo
                        proof_path = f"uploads/{comp_id}_officer_proof.jpg"
                        proof_img = Image.open(proof_file)
                        proof_img.save(proof_path)
                        
                        # Submit verification
                        success = database.submit_physical_verification(
                            complaint_id=comp_id,
                            officer_id=officer_id,
                            assignment_id=int(comp['assignment_id']),
                            result=ver_result,
                            remarks=remarks,
                            photo_path=proof_path
                        )
                        
                        if success:
                            st.success(f"✅ Complaint {comp_id} verification submitted as '{ver_result}'!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to submit verification. Please try again.")
                
                st.markdown("---")

with tab2:
    if completed_df.empty:
        st.info("No completed verifications yet.")
    else:
        for idx, comp in completed_df.iterrows():
            comp_id = comp['id']
            verification = database.get_verification_by_complaint(comp_id)
            
            with st.container():
                st.markdown(f"### 📋 {comp_id}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {comp['description']}")
                    st.write(f"**Category:** {comp['category']} | **Priority:** {comp['priority']}")
                    
                    if verification:
                        result_emoji = "✅" if verification['verification_result'] == 'Confirmed' else "❌"
                        st.write(f"**Your Verdict:** {result_emoji} {verification['verification_result']}")
                        st.write(f"**Your Remarks:** {verification['officer_remarks']}")
                        st.write(f"**Verified At:** {verification['verified_at']}")
                
                with col2:
                    if verification and verification.get('photo_proof_path'):
                        try:
                            proof_img = Image.open(verification['photo_proof_path'])
                            st.image(proof_img, caption="Your Photo Proof", use_container_width=True)
                        except:
                            st.info("Proof image not available.")
                    
                    try:
                        img = Image.open(comp['image_path'])
                        st.image(img, caption="Original User Photo", use_container_width=True)
                    except:
                        pass
                
                st.markdown("---")
