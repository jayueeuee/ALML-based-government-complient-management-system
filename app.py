import streamlit as st
import database
import os
import utils

st.set_page_config(
    page_title="AI Grievance System",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

utils.render_sidebar()

# Initialize database and models on startup
with st.spinner("Initializing System..."):
    try:
        database.setup_database()
        os.makedirs('uploads', exist_ok=True)
    except Exception as e:
        pass

# Initialize session state for user
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# If user is logged in, show a welcome and prompt to use sidebar
if st.session_state.logged_in:
    st.title(f"Welcome to AI Grievance System, {st.session_state.user_info.get('name', st.session_state.user_info.get('ward_name', 'User'))}!")
    st.success(f"You are logged in as {st.session_state.user_info['role']}.")
    st.write("Please use the sidebar to navigate to your dashboard.")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
else:
    # Beautiful Home Page UI
    st.title("🏙️ AI/ML Governance Complaint Management System")
    st.markdown("""
    ### Welcome to the future of civic grievance redressal!
    Our AI-powered platform ensures faster, transparent, and more accountable resolution of your city complaints. 
    Submit issues with image proof, and our AI will automatically verify, categorize, and route them to the right authority.
    """)
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Login to your account")
        role = st.selectbox("Login As", ["User", "Sevak", "Admin", "Officer"])
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Sign In", use_container_width=True):
            if role == "Sevak":
                user = database.authenticate_sevak(login_username, login_password)
                if user:
                    st.session_state.logged_in = True
                    user['role'] = 'Sevak'
                    st.session_state.user_info = user
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/2_Nagar_Sevak.py")
                    else:
                        st.rerun()
                else:
                    st.error("Invalid credentials for Sevak.")
            elif role == "Officer":
                user = database.authenticate_officer(login_username, login_password)
                if user:
                    st.session_state.logged_in = True
                    user['role'] = 'Officer'
                    st.session_state.user_info = user
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/6_Officer_Dashboard.py")
                    else:
                        st.rerun()
                else:
                    st.error("Invalid credentials for Officer.")
            else:
                user = database.authenticate_user(login_username, login_password, role)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user
                    if hasattr(st, "switch_page"):
                        if role == "Admin":
                            st.switch_page("pages/3_Admin_Dashboard.py")
                        else:
                            st.switch_page("pages/1_User_Portal.py")
                    else:
                        st.rerun()
                else:
                    st.error(f"Invalid credentials for {role}.")
                    
    with col2:
        st.subheader("New Citizen? Sign Up Here")
        reg_name = st.text_input("Full Name *")
        reg_username = st.text_input("Choose Username *")
        reg_password = st.text_input("Choose Password *", type="password")
        reg_email = st.text_input("Email Address")
        reg_phone = st.text_input("Phone Number")
        reg_address = st.text_area("Home Address")
        
        if st.button("Register & Sign Up", use_container_width=True):
            if reg_name and reg_username and reg_password:
                success = database.register_user(reg_name, reg_username, reg_password, reg_email, reg_phone, reg_address, role="User")
                if success:
                    st.success(f"Registered successfully! Please sign in on the left.")
                else:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.warning("Please fill the mandatory fields (*) to register.")

    st.markdown("---")
    st.markdown("© 2026 AI Governance Systems. All rights reserved.")
