import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def _get_setting(name, default=None):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name, default)


def send_complaint_email(sevak_email, sevak_name, complaint_id, category, priority, description, lat, lon):
    smtp_server = "smtp.gmail.com"
    smtp_port =  587
    sender_email = _get_setting("SENDER_EMAIL")
    sender_pwd = _get_setting("SENDER_PASSWORD")
    
    if not sender_email or not sender_pwd:
        print("SMTP Credentials not configured. Simulating email send...")
        print(f"--- MOCK EMAIL TO {sevak_email} ---")
        print(f"Subject: New Complaint Assigned: {complaint_id}")
        print(f"Body: You have a {priority} priority complaint in {category}.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sevak_email
    msg['Subject'] = f"New Grievance Assigned [Priority: {priority}] - ID: {complaint_id}"
    
    body = f"""
    Hello {sevak_name},
    
    A new complaint has been assigned to your ward.
    
    Complaint ID: {complaint_id}
    Category: {category}
    Priority: {priority}
    
    Description:
    {description}
    
    Location: Lat {lat}, Lon {lon}
    
    Please log in to the Nagar Sevak Dashboard to update the status.
    You must respond within 3 days to avoid escalation to the Black Zone.
    
    Regards,
    AI Grievance Management System
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_pwd)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {sevak_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_escalation_email(admin_email, complaint_id, sevak_name):
    print(f"--- ESCALATION EMAIL TO {admin_email} ---")
    print(f"Subject: BLACK ZONE ALERT - {complaint_id}")
    print(f"Body: The complaint {complaint_id} assigned to {sevak_name} has breached the SLA.")

def send_officer_assignment_email(officer_email, officer_name, complaint_id, category, priority, description, lat, lon):
    """Send an email to the field officer when they are assigned a suspicious complaint."""
    smtp_server = "smtp.gmail.com"
    smtp_port =  587
    sender_email = _get_setting("SENDER_EMAIL")
    sender_pwd = _get_setting("SENDER_PASSWORD")
    
    if not sender_email or not sender_pwd:
        print(f"--- MOCK EMAIL TO OFFICER {officer_email} ---")
        print(f"Subject: Physical Verification Required - ID: {complaint_id}")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = officer_email
    msg['Subject'] = f"Physical Verification Required [Priority: {priority}] - ID: {complaint_id}"
    
    body = f"""
    Hello {officer_name},
    
    You have been assigned a suspicious complaint for physical verification.
    
    Complaint ID: {complaint_id}
    Category: {category}
    Priority: {priority}
    
    Description:
    {description}
    
    Location Coordinates: Lat {lat}, Lon {lon}
    
    Please log in to the Field Officer Dashboard to submit your verification result and upload photo proof.
    
    Regards,
    AI Grievance Management System
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_pwd)
        server.send_message(msg)
        server.quit()
        print(f"Officer assignment email sent successfully to {officer_email}")
    except Exception as e:
        print(f"Failed to send officer assignment email: {e}")


def send_resolution_email(user_contact, user_name, complaint_id, category, sevak_comments=""):
    """Send an email to the user when their complaint is resolved, with a feedback link."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = _get_setting("SENDER_EMAIL")
    sender_pwd = _get_setting("SENDER_PASSWORD")
    
    app_base_url = _get_setting(
        "APP_BASE_URL",
        "https://alml-based-government-complient-management-system-dhr8ybbvkc9y.streamlit.app",
    )
    feedback_url = f"{app_base_url.rstrip('/')}/Feedback?{urlencode({'complaint_id': complaint_id})}"
    
    subject = f"Your Complaint {complaint_id} has been Resolved! ✅"
    
    body = f"""
    Dear {user_name},
    
    We are happy to inform you that your complaint has been verified and resolved.
    
    ─────────────────────────────────────
    Complaint ID   : {complaint_id}
    Category       : {category}
    Status         : ✅ Resolved
    ─────────────────────────────────────
    
    Resolution Comments from Nagar Sevak:
    {sevak_comments if sevak_comments else 'No additional comments.'}
    
    ─────────────────────────────────────
    
    We value your feedback! Please take a moment to rate our service:
    
    👉 Submit Feedback: {feedback_url}
    
    Your feedback helps us improve our services and hold our officers accountable.
    
    Thank you for using the AI Grievance Management System.
    
    Regards,
    AI Grievance Management System
    """
    
    # Check if user_contact looks like an email
    if not user_contact or '@' not in str(user_contact):
        print(f"--- MOCK RESOLUTION EMAIL (contact '{user_contact}' is not an email) ---")
        print(f"To: {user_name} ({user_contact})")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return
    
    if not sender_email or not sender_pwd:
        print(f"--- MOCK RESOLUTION EMAIL TO {user_contact} ---")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_contact
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_pwd)
        server.send_message(msg)
        server.quit()
        print(f"Resolution email sent successfully to {user_contact}")
    except Exception as e:
        print(f"Failed to send resolution email: {e}")
