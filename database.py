import base64
import hashlib
import hmac
import os
import secrets

import mysql.connector
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from datetime import datetime

load_dotenv()

PASSWORD_HASH_ITERATIONS = 600_000


def _setting(name, default=None):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value if value not in (None, "") else os.getenv(name, default)


def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_HASH_ITERATIONS)
    encoded_salt = base64.urlsafe_b64encode(salt).decode()
    encoded_digest = base64.urlsafe_b64encode(digest).decode()
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${encoded_salt}${encoded_digest}"


def _verify_password(password, stored_password):
    if not stored_password:
        return False, False
    if not stored_password.startswith("pbkdf2_sha256$"):
        matches = hmac.compare_digest(password, stored_password)
        return matches, matches
    try:
        _, iterations, encoded_salt, encoded_digest = stored_password.split("$", 3)
        salt = base64.urlsafe_b64decode(encoded_salt)
        expected_digest = base64.urlsafe_b64decode(encoded_digest)
        actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual_digest, expected_digest), False
    except (ValueError, TypeError):
        return False, False


def _verify_and_upgrade_password(cursor, table, user, password):
    is_valid, needs_upgrade = _verify_password(password, user.get("password"))
    if is_valid and needs_upgrade:
        cursor.execute(
            f"UPDATE {table} SET password = %s WHERE id = %s",
            (_hash_password(password), user["id"]),
        )
    return is_valid


def get_db_connection():
    host = _setting("MYSQL_HOST", "localhost")
    is_local_host = host in ("localhost", "127.0.0.1")
    user = _setting("MYSQL_USER", "root" if is_local_host else None)
    password = _setting("MYSQL_PASSWORD", "root" if is_local_host else None)
    if not user or password is None:
        raise ValueError("Set MYSQL_USER and MYSQL_PASSWORD for the hosted database.")

    connection_options = {
        "host": host,
        "port": int(_setting("MYSQL_PORT", "3306")),
        "user": user,
        "password": password,
        "database": _setting("MYSQL_DATABASE", "grievance_db"),
    }
    ssl_ca = _setting("MYSQL_SSL_CA")
    if ssl_ca:
        connection_options["ssl_ca"] = ssl_ca
    return mysql.connector.connect(**connection_options)

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table (for User, Admin, Officer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(50),
        address TEXT
    )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
        cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(50)")
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
    except Exception:
        pass
    
    # Wards Table (for Sevak)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wards (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ward_name VARCHAR(255) NOT NULL UNIQUE,
        nagar_sevak_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        username VARCHAR(255),
        password VARCHAR(255)
    )
    """)
    
    # Complaints Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id VARCHAR(50) PRIMARY KEY,
        description TEXT NOT NULL,
        lat FLOAT,
        lon FLOAT,
        ward VARCHAR(255),
        image_path VARCHAR(500),
        verification_status VARCHAR(50),
        category VARCHAR(100),
        priority VARCHAR(50),
        status VARCHAR(50) DEFAULT 'Pending',
        submission_date DATETIME,
        escalated BOOLEAN DEFAULT FALSE,
        resolution_proof VARCHAR(500),
        sevak_comments TEXT,
        user_name VARCHAR(255),
        user_contact VARCHAR(255),
        image_analysis TEXT,
        user_id INT
    )
    """)
    try:
        cursor.execute("ALTER TABLE complaints ADD COLUMN user_id INT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE complaints ADD COLUMN physical_verification_status VARCHAR(50) DEFAULT NULL")
    except Exception:
        pass
    
    # Officers Table (Field Officers added by Sevak, bound to a ward)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS officers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        phone VARCHAR(50),
        email VARCHAR(255),
        ward_name VARCHAR(255) NOT NULL,
        sevak_id INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)
    
    # Officer Assignments Table (Sevak assigns suspicious complaints to officers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS officer_assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        complaint_id VARCHAR(50) NOT NULL,
        officer_id INT NOT NULL,
        assigned_by INT NOT NULL,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'Assigned'
    )
    """)
    
    # Physical Verifications Table (Officer submits verification with photo proof)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS physical_verifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        complaint_id VARCHAR(50) NOT NULL,
        officer_id INT NOT NULL,
        assignment_id INT NOT NULL,
        verification_result VARCHAR(50) NOT NULL,
        officer_remarks TEXT,
        photo_proof_path VARCHAR(500),
        verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        lat FLOAT,
        lon FLOAT
    )
    """)
    
    # Feedback Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id INT AUTO_INCREMENT PRIMARY KEY,
        complaint_id VARCHAR(50),
        rating INT,
        comment TEXT,
        submitted_at DATETIME,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
    )
    """)
    
    bootstrap_username = _setting("BOOTSTRAP_ADMIN_USERNAME")
    bootstrap_password = _setting("BOOTSTRAP_ADMIN_PASSWORD")
    if bootstrap_username and bootstrap_password:
        cursor.execute("SELECT id FROM users WHERE username = %s", (bootstrap_username,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO users (name, username, password, role) VALUES (%s, %s, %s, 'Admin')",
                ("System Admin", bootstrap_username, _hash_password(bootstrap_password)),
            )
        
    conn.commit()
    cursor.close()
    conn.close()

def insert_complaint(complaint_id, desc, lat, lon, ward, img_path, v_status, category, priority, user_name, user_contact, image_analysis="", user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO complaints (id, description, lat, lon, ward, image_path, verification_status, category, priority, submission_date, user_name, user_contact, image_analysis, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (complaint_id, desc, lat, lon, ward, img_path, v_status, category, priority, datetime.now(), user_name, user_contact, image_analysis, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_complaints_df():
    conn = get_db_connection()
    query = "SELECT * FROM complaints"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_complaints_by_user(user_id):
    """Fetch complaints submitted by a specific account."""
    conn = get_db_connection()
    query = "SELECT * FROM complaints WHERE user_id = %s ORDER BY submission_date DESC"
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

def get_wards_df():
    conn = get_db_connection()
    query = "SELECT * FROM wards"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def update_complaint_status(complaint_id, status, comments="", proof=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE complaints SET status=%s, sevak_comments=%s, resolution_proof=%s WHERE id=%s"
    cursor.execute(query, (status, comments, proof, complaint_id))
    conn.commit()
    cursor.close()
    conn.close()

def escalate_black_zone_complaints(days_threshold=3):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Mark complaints as escalated if Pending for more than threshold days
    # Using simple date math for MySQL
    query = f"""
    UPDATE complaints 
    SET escalated = TRUE, status = 'Black Zone' 
    WHERE status = 'Pending' AND DATEDIFF(NOW(), submission_date) >= %s
    """
    cursor.execute(query, (days_threshold,))
    updated_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return updated_rows

def add_ward(ward_name, sevak_name, email, username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO wards (ward_name, nagar_sevak_name, email, username, password)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (ward_name, sevak_name, email, username, _hash_password(password)))
    conn.commit()
    cursor.close()
    conn.close()

def insert_feedback(complaint_id, rating, comment=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO feedback (complaint_id, rating, comment, submitted_at)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (complaint_id, rating, comment, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()

def get_feedback_df():
    conn = get_db_connection()
    query = "SELECT * FROM feedback"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM complaints WHERE id = %s"
    cursor.execute(query, (complaint_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def register_user(name, username, password, email, phone, address, role="User"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (name, username, password, role, email, phone, address) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (name, username, _hash_password(password), role, email, phone, address))
        conn.commit()
        success = True
    except mysql.connector.IntegrityError:
        success = False # Username exists
    cursor.close()
    conn.close()
    return success

def authenticate_user(username, password, role):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE username = %s AND role = %s"
    cursor.execute(query, (username, role))
    user = cursor.fetchone()
    if user and _verify_and_upgrade_password(cursor, "users", user, password):
        conn.commit()
    else:
        user = None
    cursor.close()
    conn.close()
    return user

def authenticate_sevak(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM wards WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    if user and _verify_and_upgrade_password(cursor, "wards", user, password):
        conn.commit()
    else:
        user = None
    cursor.close()
    conn.close()
    return user

def reset_password(username, new_password, is_sevak=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    table = "wards" if is_sevak else "users"
    try:
        query = f"UPDATE {table} SET password = %s WHERE username = %s"
        cursor.execute(query, (_hash_password(new_password), username))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception:
        success = False
    cursor.close()
    conn.close()
    return success

# ─────────────────────────────────────────────────────────
# Officer Management Functions
# ─────────────────────────────────────────────────────────

def add_officer(name, username, password, phone, email, ward_name, sevak_id):
    """Sevak adds a new field officer under their ward."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO officers (name, username, password, phone, email, ward_name, sevak_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, username, _hash_password(password), phone, email, ward_name, sevak_id))
        conn.commit()
        success = True
    except mysql.connector.IntegrityError:
        success = False  # Username already exists
    cursor.close()
    conn.close()
    return success

def get_officers_by_ward(ward_name):
    """Get all officers assigned to a specific ward."""
    conn = get_db_connection()
    query = "SELECT * FROM officers WHERE ward_name = %s AND is_active = TRUE"
    df = pd.read_sql(query, conn, params=(ward_name,))
    conn.close()
    return df

def authenticate_officer(username, password):
    """Officer login authentication."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM officers WHERE username = %s AND is_active = TRUE"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    if user and _verify_and_upgrade_password(cursor, "officers", user, password):
        conn.commit()
    else:
        user = None
    cursor.close()
    conn.close()
    return user

# ─────────────────────────────────────────────────────────
# Complaint Assignment Functions
# ─────────────────────────────────────────────────────────

def assign_complaint_to_officer(complaint_id, officer_id, sevak_id):
    """Sevak assigns a suspicious complaint to an officer for physical verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO officer_assignments (complaint_id, officer_id, assigned_by, assigned_at, status)
        VALUES (%s, %s, %s, %s, 'Assigned')
        """
        cursor.execute(query, (complaint_id, officer_id, sevak_id, datetime.now()))
        # Update complaint physical verification status
        cursor.execute(
            "UPDATE complaints SET physical_verification_status = 'Pending Officer Verification' WHERE id = %s",
            (complaint_id,)
        )
        conn.commit()
        success = True
    except Exception:
        success = False
    cursor.close()
    conn.close()
    return success

def get_officer_assignments(officer_id):
    """Get all complaints assigned to a specific officer (with complaint details)."""
    conn = get_db_connection()
    query = """
    SELECT oa.id as assignment_id, oa.status as assignment_status, oa.assigned_at,
           c.*
    FROM officer_assignments oa
    JOIN complaints c ON oa.complaint_id = c.id
    WHERE oa.officer_id = %s
    ORDER BY oa.assigned_at DESC
    """
    df = pd.read_sql(query, conn, params=(officer_id,))
    conn.close()
    return df

def get_assignment_by_complaint(complaint_id):
    """Get the officer assignment for a specific complaint."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT oa.*, o.name as officer_name
    FROM officer_assignments oa
    JOIN officers o ON oa.officer_id = o.id
    WHERE oa.complaint_id = %s
    ORDER BY oa.assigned_at DESC LIMIT 1
    """
    cursor.execute(query, (complaint_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# ─────────────────────────────────────────────────────────
# Physical Verification Functions
# ─────────────────────────────────────────────────────────

def submit_physical_verification(complaint_id, officer_id, assignment_id, result, remarks, photo_path, lat=None, lon=None):
    """Officer submits physical verification result with photo proof."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO physical_verifications (complaint_id, officer_id, assignment_id, verification_result, officer_remarks, photo_proof_path, verified_at, lat, lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (complaint_id, officer_id, assignment_id, result, remarks, photo_path, datetime.now(), lat, lon))
        
        # Update the officer assignment status to Completed
        cursor.execute("UPDATE officer_assignments SET status = 'Completed' WHERE id = %s", (assignment_id,))
        
        # Update complaint's physical verification status
        pv_status = "Physically Confirmed" if result == "Confirmed" else "Physically Rejected"
        cursor.execute("UPDATE complaints SET physical_verification_status = %s WHERE id = %s", (pv_status, complaint_id))
        
        # If confirmed, update verification_status to Verified
        if result == "Confirmed":
            cursor.execute("UPDATE complaints SET verification_status = 'Verified' WHERE id = %s", (complaint_id,))
        
        conn.commit()
        success = True
    except Exception:
        success = False
    cursor.close()
    conn.close()
    return success

def get_verification_by_complaint(complaint_id):
    """Get the physical verification result for a complaint."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT pv.*, o.name as officer_name
    FROM physical_verifications pv
    JOIN officers o ON pv.officer_id = o.id
    WHERE pv.complaint_id = %s
    ORDER BY pv.verified_at DESC LIMIT 1
    """
    cursor.execute(query, (complaint_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_suspicious_complaints_by_ward(ward_name):
    """Get all suspicious complaints for a specific ward."""
    conn = get_db_connection()
    query = "SELECT * FROM complaints WHERE ward = %s AND verification_status = 'Suspicious' ORDER BY submission_date DESC"
    df = pd.read_sql(query, conn, params=(ward_name,))
    conn.close()
    return df
