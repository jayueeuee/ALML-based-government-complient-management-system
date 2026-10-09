import streamlit as st
import database
import pandas as pd
from PIL import Image
from email_service import send_resolution_email, send_officer_assignment_email
import utils

st.set_page_config(page_title="Nagar Sevak Dashboard", page_icon="👨‍💼", layout="wide")
utils.render_sidebar()

try:
    database.setup_database()
except Exception:
    pass

st.title("👨‍💼 Nagar Sevak Dashboard")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the Home Page to access this portal.")
    st.stop()

if st.session_state.user_info.get("role") != "Sevak":
    st.warning("This page is restricted to Nagar Sevaks.")
    st.stop()

sevak_info = st.session_state.user_info
selected_ward = sevak_info.get('ward_name', 'Unknown')
sevak_id = sevak_info.get('id')

col_title, col_logout = st.columns([4, 1])
with col_title:
    st.subheader(f"Welcome, {sevak_info.get('nagar_sevak_name', 'Sevak')} ({selected_ward})")
with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

# Load complaints for this ward
complaints_df = database.get_complaints_df()
ward_complaints = complaints_df[complaints_df['ward'] == selected_ward].copy()

# Quick Stats
if not ward_complaints.empty:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", len(ward_complaints))
    c2.metric("Pending", len(ward_complaints[ward_complaints['status'] == 'Pending']))
    c3.metric("Resolved", len(ward_complaints[ward_complaints['status'] == 'Resolved']))
    c4.metric("High Priority", len(ward_complaints[ward_complaints['priority'] == 'High']))
    suspicious_count = len(ward_complaints[ward_complaints['verification_status'] == 'Suspicious'])
    c5.metric("⚠️ Suspicious", suspicious_count)

st.markdown("---")

# ─── TABS ───
main_tab1, main_tab2, main_tab3 = st.tabs(["📋 All Complaints", "⚠️ Suspicious Complaints", "👮 Manage Officers"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: ALL COMPLAINTS (existing functionality)
# ═══════════════════════════════════════════════════════════════
with main_tab1:
    if ward_complaints.empty:
        st.info("No complaints assigned to this ward yet.")
    else:
        col_cat, col_pri = st.columns(2)
        with col_cat:
            st.write("**Complaints by Category**")
            cat_counts = ward_complaints['category'].value_counts()
            st.bar_chart(cat_counts)
        with col_pri:
            st.write("**Complaints by Priority**")
            pri_counts = ward_complaints['priority'].value_counts()
            st.bar_chart(pri_counts)
        
        st.markdown("---")
        
        # Sort so High Priority is first, then by submission date
        priority_map = {'High': 1, 'Medium': 2, 'Low': 3}
        ward_complaints['priority_rank'] = ward_complaints['priority'].map(priority_map).fillna(4)
        ward_complaints = ward_complaints.sort_values(by=['priority_rank', 'status', 'submission_date'], ascending=[True, True, False])
        
        # Show Top High Priority Complaint Notification
        high_priority_complaints = ward_complaints[(ward_complaints['priority'] == 'High') & (ward_complaints['status'] != 'Resolved')]
        if not high_priority_complaints.empty:
            st.warning("🚨 Attention: You have high priority complaints pending!")
            first_high = high_priority_complaints.iloc[0]
            st.write(f"**Top High Priority Complaint ID:** {first_high['id']}")
            st.write(f"**Category:** {first_high['category']} | **Status:** {first_high['status']}")
            st.write(f"**Description:** {first_high['description']}")
            st.markdown("---")
        
        st.subheader("Assigned Complaints Overview")
        
        display_cols = ['id', 'category', 'priority', 'status', 'verification_status', 'submission_date']
        if 'user_name' in ward_complaints.columns:
            display_cols.append('user_name')
        if 'physical_verification_status' in ward_complaints.columns:
            display_cols.append('physical_verification_status')
        
        st.dataframe(ward_complaints[display_cols].reset_index(drop=True), use_container_width=True)
        
        st.markdown("---")
        st.subheader("View / Update Complaint")
        
        # Search
        search_id = st.text_input("Search Complaint by ID (leave empty to select from list below)")
        
        if search_id:
            choices = [c for c in ward_complaints['id'].tolist() if search_id.upper() in c.upper()]
        else:
            choices = ward_complaints['id'].tolist()
        
        # Selection
        comp_id = st.selectbox("Select Complaint ID", choices)
        
        if comp_id:
            comp_data = ward_complaints[ward_complaints['id'] == comp_id].iloc[0]
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Description:** {comp_data['description']}")
                user_n = comp_data.get('user_name', 'Unknown')
                user_c = comp_data.get('user_contact', 'Unknown')
                st.write(f"**Reported By:** {user_n if pd.notna(user_n) else 'Unknown'} | **Contact:** {user_c if pd.notna(user_c) else 'Unknown'}")
                st.write(f"**Category:** {comp_data['category']} | **Priority:** {comp_data['priority']}")
                st.write(f"**AI Verification:** {comp_data['verification_status']}")
                st.write(f"**Submitted On:** {comp_data['submission_date']}")
                st.write(f"**Current Status:** {comp_data['status']}")
                
                # Show physical verification info if available
                pv_status = comp_data.get('physical_verification_status', None)
                if pv_status and pd.notna(pv_status):
                    if pv_status == 'Physically Confirmed':
                        st.success(f"✅ Physical Verification: {pv_status}")
                    elif pv_status == 'Physically Rejected':
                        st.error(f"❌ Physical Verification: {pv_status}")
                    else:
                        st.info(f"⏳ Physical Verification: {pv_status}")
                    
                    # Show officer details
                    verification = database.get_verification_by_complaint(comp_id)
                    if verification:
                        st.write(f"**Officer:** {verification['officer_name']}")
                        st.write(f"**Officer Remarks:** {verification['officer_remarks']}")
                        if verification.get('photo_proof_path'):
                            try:
                                proof_img = Image.open(verification['photo_proof_path'])
                                st.image(proof_img, caption="Officer's Photo Proof", width=300)
                            except:
                                pass
                
            with col2:
                try:
                    img = Image.open(comp_data['image_path'])
                    st.image(img, caption="User Uploaded Proof", use_container_width=True)
                except:
                    st.warning("Image not found.")
            
            st.markdown("### Update Status")
            new_status = st.radio("Change Status To:", ['Pending', 'Work in Progress', 'Resolved', 'Black Zone'], 
                                  index=['Pending', 'Work in Progress', 'Resolved', 'Black Zone'].index(comp_data['status']) if comp_data['status'] in ['Pending', 'Work in Progress', 'Resolved', 'Black Zone'] else 0)
            comments = st.text_area("Resolution Comments", value=comp_data['sevak_comments'] if pd.notna(comp_data['sevak_comments']) else "")
            proof_file = st.file_uploader("Upload Resolution Proof (Optional)", type=['png', 'jpg', 'jpeg'])
            
            if st.button("Update Complaint"):
                proof_path = comp_data['resolution_proof']
                if pd.isna(proof_path):
                    proof_path = ""
                if proof_file:
                    proof_path = f"uploads/{comp_id}_resolution.jpg"
                    img = Image.open(proof_file)
                    img.save(proof_path)
                
                database.update_complaint_status(comp_id, new_status, comments, proof_path)
                st.success("Complaint updated successfully!")
                
                # Send resolution email to user when status is set to Resolved
                if new_status == "Resolved":
                    user_n = comp_data.get('user_name', 'User')
                    user_c = comp_data.get('user_contact', '')
                    cat = comp_data.get('category', 'N/A')
                    
                    if pd.notna(user_n) and pd.notna(user_c) and user_c:
                        try:
                            send_resolution_email(
                                user_contact=user_c,
                                user_name=user_n,
                                complaint_id=comp_id,
                                category=cat,
                                sevak_comments=comments
                            )
                            st.toast("📧 Resolution email sent to user!", icon="✅")
                        except Exception as e:
                            st.warning(f"Could not send email: {e}")
                    else:
                        st.info("User contact not available — email not sent.")
                
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2: SUSPICIOUS COMPLAINTS
# ═══════════════════════════════════════════════════════════════
with main_tab2:
    suspicious_df = database.get_suspicious_complaints_by_ward(selected_ward)
    officers_df = database.get_officers_by_ward(selected_ward)
    
    if suspicious_df.empty:
        st.success("✅ No suspicious complaints in your ward! All complaints were verified by AI.")
    else:
        st.warning(f"⚠️ {len(suspicious_df)} complaint(s) flagged as suspicious by AI and need physical verification.")
        
        if officers_df.empty:
            st.error("❌ You haven't added any officers yet. Go to the 'Manage Officers' tab to add officers before assigning complaints.")
        
        for idx, comp in suspicious_df.iterrows():
            comp_id = comp['id']
            
            # Check if already assigned
            assignment = database.get_assignment_by_complaint(comp_id)
            verification = database.get_verification_by_complaint(comp_id)
            
            with st.container():
                # Status indicator
                if verification:
                    if verification['verification_result'] == 'Confirmed':
                        status_badge = "✅ Physically Confirmed"
                    else:
                        status_badge = "❌ Physically Rejected"
                elif assignment:
                    status_badge = f"⏳ Assigned to {assignment['officer_name']}"
                else:
                    status_badge = "🔴 Not Assigned"
                
                st.markdown(f"### 📋 {comp_id} — {status_badge}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {comp['description']}")
                    st.write(f"**Category:** {comp['category']} | **Priority:** {comp['priority']}")
                    st.write(f"**AI Verification:** ⚠️ Suspicious")
                    st.write(f"**Submitted On:** {comp['submission_date']}")
                    user_n = comp.get('user_name', 'Unknown')
                    st.write(f"**Reported By:** {user_n if pd.notna(user_n) else 'Unknown'}")
                    
                    # Show AI analysis
                    analysis = comp.get('image_analysis', '')
                    if analysis and pd.notna(analysis) and analysis != '':
                        with st.expander("🤖 AI Analysis Details"):
                            st.code(analysis, language=None)
                    
                    # Show verification result if completed
                    if verification:
                        st.markdown("#### 👮 Officer Verification Result")
                        result_emoji = "✅" if verification['verification_result'] == 'Confirmed' else "❌"
                        st.write(f"**Result:** {result_emoji} {verification['verification_result']}")
                        st.write(f"**Officer:** {verification['officer_name']}")
                        st.write(f"**Remarks:** {verification['officer_remarks']}")
                        st.write(f"**Verified At:** {verification['verified_at']}")
                        if verification.get('photo_proof_path'):
                            try:
                                proof_img = Image.open(verification['photo_proof_path'])
                                st.image(proof_img, caption="Officer's Photo Proof", width=300)
                            except:
                                pass
                
                with col2:
                    try:
                        img = Image.open(comp['image_path'])
                        st.image(img, caption="User Uploaded Proof", use_container_width=True)
                    except:
                        st.warning("Image not found.")
                
                # Assignment section (only if NOT yet assigned and officers exist)
                if not assignment and not verification and not officers_df.empty:
                    st.markdown("#### 🔄 Assign to Officer")
                    officer_options = {f"{row['name']} ({row['username']})": row['id'] for _, row in officers_df.iterrows()}
                    
                    selected_officer_label = st.selectbox(
                        "Select Officer",
                        options=list(officer_options.keys()),
                        key=f"officer_select_{comp_id}"
                    )
                    
                    if st.button("🔄 Assign to Officer", key=f"assign_{comp_id}"):
                        officer_id = officer_options[selected_officer_label]
                        success = database.assign_complaint_to_officer(comp_id, officer_id, sevak_id)
                        if success:
                            st.success(f"Complaint {comp_id} assigned to {selected_officer_label}!")
                            
                            # Send assignment email to officer
                            selected_officer_row = officers_df[officers_df['id'] == officer_id].iloc[0]
                            off_email = selected_officer_row['email']
                            if off_email and pd.notna(off_email):
                                try:
                                    send_officer_assignment_email(
                                        officer_email=off_email,
                                        officer_name=selected_officer_row['name'],
                                        complaint_id=comp_id,
                                        category=comp['category'],
                                        priority=comp['priority'],
                                        description=comp['description'],
                                        lat=comp.get('lat', 'N/A'),
                                        lon=comp.get('lon', 'N/A')
                                    )
                                    st.toast("📧 Assignment email sent to Officer!", icon="✅")
                                except Exception as e:
                                    st.warning(f"Could not send email: {e}")
                                    
                            st.rerun()
                        else:
                            st.error("Failed to assign. Please try again.")
                
                st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# TAB 3: MANAGE OFFICERS
# ═══════════════════════════════════════════════════════════════
with main_tab3:
    st.subheader(f"👮 Officers in {selected_ward}")
    
    officers_df = database.get_officers_by_ward(selected_ward)
    
    if not officers_df.empty:
        display_cols = ['id', 'name', 'username', 'phone', 'email', 'created_at']
        display_cols = [c for c in display_cols if c in officers_df.columns]
        st.dataframe(officers_df[display_cols].reset_index(drop=True), use_container_width=True)
    else:
        st.info("No officers added yet. Add your first officer below.")
    
    st.markdown("---")
    st.subheader("➕ Add New Officer")
    
    with st.form("add_officer_form"):
        off_name = st.text_input("Officer Full Name *")
        off_username = st.text_input("Username *")
        off_password = st.text_input("Password *", type="password")
        off_phone = st.text_input("Phone Number")
        off_email = st.text_input("Email Address")
        st.info(f"📍 This officer will be assigned to **{selected_ward}** (your ward).")
        
        submit_officer = st.form_submit_button("Add Officer", type="primary")
        
        if submit_officer:
            if off_name and off_username and off_password:
                success = database.add_officer(
                    name=off_name,
                    username=off_username,
                    password=off_password,
                    phone=off_phone,
                    email=off_email,
                    ward_name=selected_ward,
                    sevak_id=sevak_id
                )
                if success:
                    st.success(f"Officer '{off_name}' added successfully to {selected_ward}!")
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.warning("Please fill all mandatory fields (*).")
