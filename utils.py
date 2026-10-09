import streamlit as st

def render_sidebar():
    # Hide the default Streamlit sidebar menu
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    with st.sidebar:
        st.title("🏙️ Navigation")
        
        if not st.session_state.get("logged_in"):
            if st.button("🏠 Home / Login", use_container_width=True):
                st.switch_page("app.py")
        else:
            role = st.session_state.user_info.get("role")
            
            st.markdown(f"**Logged in as: {role}**")
            st.divider()
            
            if role == "User":
                if st.button("📝 Submit Complaint", use_container_width=True):
                    st.switch_page("pages/1_User_Portal.py")
                if st.button("📦 My Complaints", use_container_width=True):
                    st.switch_page("pages/5_My_Complaints.py")
                if st.button("⭐ Feedback", use_container_width=True):
                    st.switch_page("pages/4_Feedback.py")
                    
            elif role == "Sevak":
                if st.button("👨‍💼 Sevak Dashboard", use_container_width=True):
                    st.switch_page("pages/2_Nagar_Sevak.py")
                    
            elif role == "Officer":
                if st.button("👮 Officer Dashboard", use_container_width=True):
                    st.switch_page("pages/6_Officer_Dashboard.py")
                    
            elif role == "Admin":
                if st.button("📈 Admin Dashboard", use_container_width=True):
                    st.switch_page("pages/3_Admin_Dashboard.py")
            
            st.divider()
            if st.button("Log Out", use_container_width=True, type="primary"):
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.switch_page("app.py")
