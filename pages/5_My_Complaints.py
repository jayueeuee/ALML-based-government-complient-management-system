import streamlit as st
import database
import pandas as pd
from PIL import Image
from datetime import datetime
from textwrap import dedent
import utils

st.set_page_config(page_title="My Complaints", page_icon="📦", layout="wide")
utils.render_sidebar()

try:
    database.setup_database()
except Exception:
    pass

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the Home Page to access this portal.")
    st.stop()

if st.session_state.user_info.get("role") != "User":
    st.warning("This page is restricted to Citizens (Users).")
    st.stop()

st.title("📦 My Complaints")
st.write("Track your submitted complaints — just like tracking your orders!")

# ─────────────────────────────────────────────────────────
# Status pipeline steps (e-commerce style)
# ─────────────────────────────────────────────────────────
STATUS_STEPS = [
    {"key": "Submitted", "icon": "📝", "label": "Submitted"},
    {"key": "Verified",  "icon": "🔍", "label": "AI Verified"},
    {"key": "Officer Verified", "icon": "👮", "label": "Officer Verified"},
    {"key": "Work in Progress", "icon": "🔧", "label": "Work in Progress"},
    {"key": "Resolved",  "icon": "✅", "label": "Resolved"},
]

# Black Zone is a special state shown separately
BLACK_ZONE_STEP = {"key": "Black Zone", "icon": "⛔", "label": "Escalated (Black Zone)"}

def get_step_index(status, verification_status, physical_verification_status=None):
    """Map complaint status to a step index in the pipeline."""
    if status == "Resolved":
        return 4
    elif status == "Work in Progress":
        return 3
    elif status == "Black Zone":
        return -1  # special
    else:
        # Check physical verification status for suspicious complaints
        if physical_verification_status and physical_verification_status in ['Physically Confirmed', 'Physically Rejected']:
            return 2
        # Pending — check if AI verified
        if verification_status == "Verified":
            return 1
        return 0

def render_tracking_bar(current_step, is_black_zone=False):
    """Render an e-commerce style order tracking progress bar using HTML/CSS."""
    
    if is_black_zone:
        # Special escalated state
        st.markdown(dedent("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; padding: 24px; margin: 12px 0; border: 2px solid #e74c3c;">
            <div style="text-align: center;">
                <span style="font-size: 40px;">⛔</span>
                <h3 style="color: #e74c3c; margin: 8px 0 4px 0;">Escalated — Black Zone</h3>
                <p style="color: #bbb; margin: 0;">This complaint has breached the SLA and has been escalated for immediate attention.</p>
            </div>
        </div>
        """), unsafe_allow_html=True)
        return
    
    steps_html = ""
    for i, step in enumerate(STATUS_STEPS):
        if i <= current_step:
            # Completed or current step
            circle_bg = "#27ae60" if i < current_step else "#2980b9"
            circle_border = circle_bg
            label_color = "#ffffff"
            line_color = "#27ae60"
            opacity = "1"
        else:
            # Future step
            circle_bg = "transparent"
            circle_border = "#555"
            label_color = "#888"
            line_color = "#333"
            opacity = "0.5"
        
        # Connector line (not for the last step)
        line_html = ""
        if i < len(STATUS_STEPS) - 1:
            completed_line_color = "#27ae60" if i < current_step else "#333"
            line_html = f'<div style="flex: 1; height: 4px; background: {completed_line_color}; margin: 0 4px; border-radius: 2px; align-self: center;"></div>'
        
        check_or_icon = "✓" if i < current_step else step["icon"]
        
        steps_html += dedent(f"""
        <div style="display: flex; flex-direction: column; align-items: center; opacity: {opacity}; min-width: 90px;">
            <div style="width: 48px; height: 48px; border-radius: 50%; background: {circle_bg}; border: 3px solid {circle_border}; 
                        display: flex; align-items: center; justify-content: center; font-size: 20px; color: white;
                        box-shadow: {f'0 0 12px {circle_bg}40' if i <= current_step else 'none'};">
                {check_or_icon}
            </div>
            <span style="color: {label_color}; font-size: 12px; font-weight: {'700' if i == current_step else '400'}; margin-top: 8px; text-align: center;">
                {step['label']}
            </span>
        </div>
        {line_html}
        """)
    
    st.markdown(dedent(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; padding: 24px 32px; margin: 12px 0; border: 1px solid #2d3748;">
        <div style="display: flex; align-items: flex-start; justify-content: center;">
            {steps_html}
        </div>
    </div>
    """).lstrip(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# Auto-Load User Complaints
# ─────────────────────────────────────────────────────────
st.markdown("---")

user_info = st.session_state.user_info
user_complaints = database.get_complaints_by_user(user_info["id"])

if user_complaints.empty:
    st.info("You haven't submitted any complaints yet. Head over to the User Dashboard to submit your first grievance!")

# ─────────────────────────────────────────────────────────
# Display Complaints (E-commerce Order Style)
# ─────────────────────────────────────────────────────────
if not user_complaints.empty:
    st.markdown("---")
    st.subheader(f"📋 Your Complaints ({len(user_complaints)})")
    
    for idx, comp in user_complaints.iterrows():
        comp_id = comp['id']
        status = comp.get('status', 'Pending')
        verification = comp.get('verification_status', 'Unknown')
        category = comp.get('category', 'N/A')
        priority = comp.get('priority', 'N/A')
        description = comp.get('description', '')
        submission_date = comp.get('submission_date', '')
        ward = comp.get('ward', 'N/A')
        sevak_comments = comp.get('sevak_comments', '')
        image_path = comp.get('image_path', '')
        image_analysis = comp.get('image_analysis', '')
        physical_v_status = comp.get('physical_verification_status', None)
        if pd.isna(physical_v_status):
            physical_v_status = None
        
        is_black_zone = status == "Black Zone"
        current_step = get_step_index(status, verification, physical_v_status)
        
        # Priority badge color
        pri_colors = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#27ae60"}
        pri_color = pri_colors.get(priority, "#888")
        
        # Status badge
        status_colors = {
            "Pending": "#f39c12", "Work in Progress": "#3498db",
            "Resolved": "#27ae60", "Black Zone": "#e74c3c"
        }
        status_color = status_colors.get(status, "#888")
        
        # Card container
        with st.container():
            # Header row: ID + badges
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); border-radius: 12px; padding: 20px; margin-bottom: 8px; border: 1px solid #2d3748;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="font-size: 20px; font-weight: 700; color: #e2e8f0;">📦 {comp_id}</span>
                        <span style="color: #888; font-size: 13px; margin-left: 12px;">
                            {f"Ordered on {submission_date}" if submission_date else ""}
                        </span>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span style="background: {pri_color}22; color: {pri_color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid {pri_color}44;">
                            {priority} Priority
                        </span>
                        <span style="background: {status_color}22; color: {status_color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid {status_color}44;">
                            {status}
                        </span>
                        <span style="background: #8e44ad22; color: #8e44ad; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #8e44ad44;">
                            {category}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Tracking bar
            render_tracking_bar(current_step, is_black_zone)
            
            # Expandable details
            with st.expander(f"📄 View Details — {comp_id}", expanded=False):
                det_col1, det_col2 = st.columns([2, 1])
                
                with det_col1:
                    st.markdown(f"**📝 Description:**")
                    st.write(description)
                    
                    st.markdown(f"**📍 Ward:** {ward}")
                    st.markdown(f"**🔍 AI Verification:** {verification}")
                    
                    if image_analysis and pd.notna(image_analysis) and image_analysis != "":
                        st.markdown(f"**🤖 AI Image Analysis:**")
                        st.info(image_analysis)
                    
                    if sevak_comments and pd.notna(sevak_comments) and sevak_comments != "":
                        st.markdown(f"**💬 Resolution Comments:**")
                        st.success(sevak_comments)
                    
                    # Show physical verification info for suspicious complaints
                    if physical_v_status:
                        pv_data = database.get_verification_by_complaint(comp_id)
                        if pv_data:
                            result_emoji = "✅" if pv_data['verification_result'] == 'Confirmed' else "❌"
                            st.markdown(f"**👮 Officer Verification:** {result_emoji} {pv_data['verification_result']}")
                            st.write(f"**Officer:** {pv_data['officer_name']}")
                            st.write(f"**Remarks:** {pv_data['officer_remarks']}")
                            if pv_data.get('photo_proof_path'):
                                try:
                                    proof_img = Image.open(pv_data['photo_proof_path'])
                                    st.image(proof_img, caption="Officer's Verification Photo", width=300)
                                except:
                                    pass
                        elif physical_v_status == 'Pending Officer Verification':
                            st.info("⏳ An officer has been assigned to physically verify this complaint.")
                    
                    if status == "Resolved":
                        feedback_url = f"/Feedback?complaint_id={comp_id}"
                        st.markdown(f"[⭐ Submit Feedback]({feedback_url})")
                
                with det_col2:
                    if image_path and pd.notna(image_path):
                        try:
                            img = Image.open(image_path)
                            st.image(img, caption="Uploaded Proof", use_container_width=True)
                        except Exception:
                            st.info("Image not available.")
                    
                    # Timeline
                    st.markdown("**📅 Timeline:**")
                    timeline_items = [f"📝 Submitted: {submission_date}"]
                    
                    if current_step >= 1 or is_black_zone:
                        timeline_items.append(f"🔍 AI Verified: {verification}")
                    if current_step >= 2 and physical_v_status:
                        timeline_items.append(f"👮 Officer Verified: {physical_v_status}")
                    if current_step >= 3:
                        timeline_items.append("🔧 Work in Progress")
                    if current_step >= 4:
                        timeline_items.append("✅ Resolved")
                    if is_black_zone:
                        timeline_items.append("⛔ Escalated to Black Zone")
                    
                    for item in timeline_items:
                        st.write(f"  {item}")
            
            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
