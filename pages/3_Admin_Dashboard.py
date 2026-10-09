import streamlit as st
import database
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import utils

st.set_page_config(page_title="Admin Analytics", page_icon="📈", layout="wide")
utils.render_sidebar()

try:
    database.setup_database()
except Exception:
    pass

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the Home Page to access this portal.")
    st.stop()

if st.session_state.user_info.get("role") not in ["Admin", "Officer"]:
    st.warning("This page is restricted to Administrators and Officers.")
    st.stop()

st.title("📈 Data Science & Analytics Dashboard")

# Run Escalation check
escalated_count = database.escalate_black_zone_complaints(days_threshold=3)
if escalated_count > 0:
    st.toast(f"{escalated_count} new complaints escalated to Black Zone!")

df = database.get_complaints_df()

if df.empty:
    st.info("No data available yet.")
    st.stop()

# --- KPI Row ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Complaints", len(df))
c2.metric("Verified (AI)", len(df[df['verification_status'] == 'Verified']))
c3.metric("Resolved", len(df[df['status'] == 'Resolved']))
c4.metric("High Priority", len(df[df['priority'] == 'High']))

bz_count = len(df[df['status'] == 'Black Zone'])
c5.metric("⛔ Black Zone", bz_count, delta=f"{bz_count} Overdue", delta_color="inverse")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Category Distribution")
    cat_counts = df['category'].value_counts().reset_index()
    cat_counts.columns = ['Category', 'Count']
    fig_cat = px.bar(cat_counts, x='Category', y='Count', color='Category', 
                     title="Complaints by Category")
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.subheader("Priority Distribution")
    pri_counts = df['priority'].value_counts().reset_index()
    pri_counts.columns = ['Priority', 'Count']
    fig_pri = px.pie(pri_counts, values='Count', names='Priority', 
                     title="Complaints by Priority", color='Priority',
                     color_discrete_map={'High':'red', 'Medium':'orange', 'Low':'green'})
    st.plotly_chart(fig_pri, use_container_width=True)

st.markdown("---")
st.subheader("📍 Geospatial Hotspot Analysis")

map_center = [df['lat'].mean(), df['lon'].mean()] if not df['lat'].isnull().all() else [20.0059, 73.7900]
m = folium.Map(location=map_center, zoom_start=12)

# Add Markers
for idx, row in df.iterrows():
    if pd.notna(row['lat']) and pd.notna(row['lon']):
        color = 'red' if row['priority'] == 'High' else ('orange' if row['priority'] == 'Medium' else 'green')
        if row['status'] == 'Black Zone':
            color = 'black'
            
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=8,
            popup=f"ID: {row['id']}<br>Cat: {row['category']}<br>Pri: {row['priority']}<br>Stat: {row['status']}",
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)

st_folium(m, width=1200, height=400)

st.markdown("---")
st.subheader("⛔ Black Zone (Escalated Complaints)")

bz_df = df[df['status'] == 'Black Zone']
if bz_df.empty:
    st.success("No complaints in Black Zone!")
else:
    st.error(f"{len(bz_df)} complaints have breached the SLA and require immediate attention.")
    display_cols_bz = ['id', 'category', 'ward', 'submission_date', 'priority', 'verification_status']
    if 'user_name' in bz_df.columns:
        display_cols_bz.append('user_name')
    st.dataframe(bz_df[display_cols_bz])

st.markdown("---")
st.subheader("👨‍💼 Admin Actions: Users & Nagar Sevaks")

tab1, tab2, tab3 = st.tabs(["Nagar Sevak Work Status", "Add New Nagar Sevak", "Reset Passwords"])

with tab1:
    wards_df = database.get_wards_df()
    if not wards_df.empty:
        # Calculate stats per ward
        ward_stats = df.groupby('ward').agg(
            Total_Complaints=('id', 'count'),
            Pending=('status', lambda x: (x == 'Pending').sum()),
            Resolved=('status', lambda x: (x == 'Resolved').sum()),
            Black_Zone=('status', lambda x: (x == 'Black Zone').sum())
        ).reset_index()
        
        merged_stats = pd.merge(wards_df, ward_stats, left_on='ward_name', right_on='ward', how='left').fillna(0)
        
        # Display as integer
        for col in ['Total_Complaints', 'Pending', 'Resolved', 'Black_Zone']:
            if col in merged_stats.columns:
                merged_stats[col] = merged_stats[col].astype(int)
                
        st.dataframe(merged_stats[['ward_name', 'nagar_sevak_name', 'Total_Complaints', 'Pending', 'Resolved', 'Black_Zone']])
    else:
        st.info("No Nagar Sevaks found.")

with tab2:
    with st.form("add_ward_form"):
        new_ward_name = st.text_input("Ward Name")
        new_sevak_name = st.text_input("Nagar Sevak Name")
        new_email = st.text_input("Email")
        new_username = st.text_input("Username (Ward ID)")
        new_password = st.text_input("Password", type="password")
        
        submit_btn = st.form_submit_button("Add Nagar Sevak")
        
        if submit_btn:
            if new_ward_name and new_sevak_name and new_email and new_username and new_password:
                try:
                    database.add_ward(new_ward_name, new_sevak_name, new_email, new_username, new_password)
                    st.success(f"Nagar Sevak {new_sevak_name} added successfully for {new_ward_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding Nagar Sevak: {e}")
            else:
                st.error("Please fill all fields.")

with tab3:
    st.write("Reset password for any Citizen or Nagar Sevak account.")
    with st.form("reset_password_form"):
        target_account_type = st.radio("Account Type", ["Citizen/User", "Nagar Sevak"])
        target_username = st.text_input("Target Username")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        
        reset_btn = st.form_submit_button("Reset Password")
        
        if reset_btn:
            if not target_username or not new_pass:
                st.error("Please provide both username and new password.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match!")
            else:
                is_sevak = target_account_type == "Nagar Sevak"
                success = database.reset_password(target_username, new_pass, is_sevak)
                if success:
                    st.success(f"Password for '{target_username}' reset successfully!")
                else:
                    st.error(f"Failed to reset password. Username '{target_username}' may not exist.")

# ─────────────────────────────────────────────────────────
# Feedback Analytics Section
# ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📝 User Feedback Analytics")

feedback_df = database.get_feedback_df()

if feedback_df.empty:
    st.info("No feedback received yet.")
else:
    # Join feedback with complaints to get ward info
    feedback_merged = pd.merge(
        feedback_df, 
        df[['id', 'ward', 'category', 'description', 'user_name']],
        left_on='complaint_id', 
        right_on='id', 
        how='left',
        suffixes=('_fb', '_comp')
    )
    
    # Join with wards to get sevak names
    wards_df_fb = database.get_wards_df()
    if not wards_df_fb.empty:
        feedback_merged = pd.merge(
            feedback_merged,
            wards_df_fb[['ward_name', 'nagar_sevak_name']],
            left_on='ward',
            right_on='ward_name',
            how='left'
        )
    else:
        feedback_merged['nagar_sevak_name'] = 'Unknown'
    
    # KPI Row
    fb_c1, fb_c2, fb_c3 = st.columns(3)
    fb_c1.metric("Total Feedback", len(feedback_merged))
    avg_rating = feedback_merged['rating'].mean()
    fb_c2.metric("Average Rating", f"{'⭐' * round(avg_rating)} ({avg_rating:.1f}/5)")
    fb_c3.metric("Unique Complaints", feedback_merged['complaint_id'].nunique())
    
    # Per-Ward/Sevak Summary Table
    st.markdown("#### 📊 Feedback by Ward / Nagar Sevak")
    
    ward_feedback_stats = feedback_merged.groupby(['ward', 'nagar_sevak_name']).agg(
        Avg_Rating=('rating', 'mean'),
        Total_Feedback=('rating', 'count'),
        Min_Rating=('rating', 'min'),
        Max_Rating=('rating', 'max')
    ).reset_index()
    
    ward_feedback_stats['Avg_Rating'] = ward_feedback_stats['Avg_Rating'].round(2)
    ward_feedback_stats = ward_feedback_stats.rename(columns={
        'ward': 'Ward',
        'nagar_sevak_name': 'Nagar Sevak'
    })
    
    st.dataframe(ward_feedback_stats, use_container_width=True)
    
    # Bar chart: Average rating per Nagar Sevak
    if len(ward_feedback_stats) > 0:
        fig_fb = px.bar(
            ward_feedback_stats, 
            x='Nagar Sevak', 
            y='Avg_Rating',
            color='Avg_Rating',
            color_continuous_scale=['red', 'orange', 'yellow', 'lightgreen', 'green'],
            range_color=[1, 5],
            title="Average Rating per Nagar Sevak",
            labels={'Avg_Rating': 'Average Rating (1-5)'}
        )
        fig_fb.update_layout(yaxis_range=[0, 5])
        st.plotly_chart(fig_fb, use_container_width=True)
    
    # Individual Feedback List (filterable by ward)
    st.markdown("#### 💬 Individual Feedback")
    
    ward_filter = st.selectbox(
        "Filter by Ward", 
        options=["All"] + sorted(feedback_merged['ward'].dropna().unique().tolist()),
        key="feedback_ward_filter"
    )
    
    display_fb = feedback_merged.copy()
    if ward_filter != "All":
        display_fb = display_fb[display_fb['ward'] == ward_filter]
    
    # Format rating as stars
    display_fb['Rating'] = display_fb['rating'].apply(lambda x: '⭐' * int(x) if pd.notna(x) else 'N/A')
    
    display_cols_fb = ['complaint_id', 'Rating', 'comment', 'submitted_at', 'ward', 'nagar_sevak_name', 'category']
    display_cols_fb = [c for c in display_cols_fb if c in display_fb.columns]
    
    display_fb = display_fb.sort_values('submitted_at', ascending=False)
    st.dataframe(
        display_fb[display_cols_fb].rename(columns={
            'complaint_id': 'Complaint ID',
            'comment': 'Comment',
            'submitted_at': 'Submitted At',
            'ward': 'Ward',
            'nagar_sevak_name': 'Nagar Sevak',
            'category': 'Category'
        }),
        use_container_width=True
    )
