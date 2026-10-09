import streamlit as st
import database
import utils

st.set_page_config(page_title="Feedback", page_icon="⭐", layout="wide")
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

st.title("⭐ Complaint Resolution Feedback")

# Read complaint_id from URL query parameter
query_params = st.query_params
complaint_id = query_params.get("complaint_id", "")

if not complaint_id:
    st.subheader("Submit Feedback")
    st.write("Enter your Complaint ID below to submit feedback.")
    complaint_id = st.text_input("Complaint ID", placeholder="e.g. CMP-A1B2C3D4")
    
if not complaint_id:
    st.info("Please provide a Complaint ID to submit feedback. You can find it in the resolution email you received.")
    st.stop()

# Fetch complaint details
complaint = database.get_complaint_by_id(complaint_id)

if not complaint:
    st.error(f"Complaint '{complaint_id}' not found. Please check the ID and try again.")
    st.stop()

# Check if complaint is resolved
if complaint.get('status') != 'Resolved':
    st.warning(f"Complaint {complaint_id} is currently **{complaint.get('status', 'Unknown')}**. Feedback can only be submitted for resolved complaints.")
    st.stop()

# Check if feedback already submitted
existing_feedback = database.get_feedback_df()
if not existing_feedback.empty and complaint_id in existing_feedback['complaint_id'].values:
    st.success("✅ Thank you! You have already submitted feedback for this complaint.")
    
    prev = existing_feedback[existing_feedback['complaint_id'] == complaint_id].iloc[0]
    st.write(f"**Your Rating:** {'⭐' * int(prev['rating'])}")
    if prev.get('comment'):
        st.write(f"**Your Comment:** {prev['comment']}")
    st.stop()

# Display complaint details
st.markdown("---")
st.subheader("📋 Complaint Details")

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Complaint ID:** {complaint_id}")
    st.write(f"**Category:** {complaint.get('category', 'N/A')}")
    st.write(f"**Priority:** {complaint.get('priority', 'N/A')}")
with col2:
    st.write(f"**Status:** ✅ {complaint.get('status', 'N/A')}")
    st.write(f"**Submitted On:** {complaint.get('submission_date', 'N/A')}")
    st.write(f"**Ward:** {complaint.get('ward', 'N/A')}")

st.write(f"**Description:** {complaint.get('description', 'N/A')}")

if complaint.get('sevak_comments'):
    st.info(f"**Resolution Comments:** {complaint['sevak_comments']}")

# Feedback form
st.markdown("---")
st.subheader("📝 Rate Our Service")

st.write("How satisfied are you with the resolution of your complaint?")

rating = st.radio(
    "Your Rating",
    options=[5, 4, 3, 2, 1],
    format_func=lambda x: f"{'⭐' * x} ({x}/5)" + (
        " — Excellent" if x == 5 else
        " — Good" if x == 4 else
        " — Average" if x == 3 else
        " — Poor" if x == 2 else
        " — Very Poor"
    ),
    index=0,
    horizontal=False
)

comment = st.text_area(
    "Additional Comments (Optional)",
    placeholder="Tell us more about your experience...",
    max_chars=500
)

if st.button("Submit Feedback", type="primary"):
    try:
        database.insert_feedback(complaint_id, rating, comment)
        st.balloons()
        st.success("🎉 Thank you for your feedback! Your response has been recorded.")
        st.write(f"**Your Rating:** {'⭐' * rating}")
        if comment:
            st.write(f"**Your Comment:** {comment}")
    except Exception as e:
        st.error(f"Failed to submit feedback: {e}")
