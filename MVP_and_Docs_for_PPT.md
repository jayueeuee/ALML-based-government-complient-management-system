# AI Governance Complaint Management System - Presentation Content

Use the following content to build your PowerPoint presentation. It covers the MVP definition, how AI is utilized, and a comparison between traditional methods and your innovative solution.

---

## 1. Minimum Viable Product (MVP) Definition

Our MVP is a unified **AI-powered Civic Grievance Platform** designed to connect citizens with their local authorities efficiently. 

**Key Features of the MVP:**
- **Citizen Portal (User):** A web-based interface for citizens to lodge complaints by providing a text description and uploading image evidence.
- **Automated AI Processing:** Immediate, backend AI processing that categorizes the complaint (e.g., Pothole, Water Supply), assigns a priority level, and verifies the authenticity of the uploaded image against the text claim.
- **Authority Dashboard (Nagar Sevak):** A localized dashboard for civic officials to view assigned, verified complaints and update their resolution status.
- **Admin Oversight:** A high-level view for administrators to track Service Level Agreement (SLA) breaches (Black Zones) and overall grievance resolution metrics via interactive maps and charts.

---

## 2. Where AI is Used in Our Project

Our system leverages artificial intelligence at the very first touchpoint to automate triage and reduce manual verification efforts. 

### A. NLP for Text Classification (Scikit-Learn)
- **Category Prediction:** When a user types a description of their issue, our custom NLP model analyzes the text to automatically categorize the issue into specific departments (e.g., Road/Pothole, Water Supply, Garbage/Sanitation).
- **Priority Assignment:** The same NLP engine assesses the severity of the text description to automatically assign a priority tier (High, Medium, Low), ensuring critical issues are flagged immediately.

### B. Computer Vision & VQA for Image Verification (HuggingFace ViLT)
- **Fake/Irrelevant Image Detection:** We use a Visual Question Answering (VQA) model (`ViLT-b32`). Once the NLP model predicts a category (e.g., "Pothole"), the VQA model dynamically asks the image specific questions (e.g., *"Is there a pothole in this image?"*). 
- **Automated Verification:** If the image answers align with the category, the AI marks the complaint as **"Verified"**. If the image is unrelated (e.g., a selfie uploaded instead of a pothole), the AI flags it as **"Suspicious"**, filtering out spam and fake complaints before they reach human officials.

---

## 3. Old Methods vs. Our Innovative Solution

### The Old / Traditional Method
- **Manual Data Entry & Routing:** Citizens fill out lengthy forms, and a human operator reads, interprets, and manually assigns the ticket to the correct department.
- **High Spam & Fake Complaints:** Pranksters or frustrated users upload fake images or irrelevant complaints, wasting the time of field inspectors who travel to the location only to find nothing.
- **Slow Response Times:** Because categorization and verification are manual, critical issues (like open live wires or severe water pipe bursts) sit in the queue waiting to be read.
- **Lack of Transparency:** Citizens submit a complaint into a "black hole" and have no way of tracking if an official is actually working on it.

### Our Project's New & Innovative Benefits
- **Zero Human Triage (AI Routing):** AI instantly categorizes and prioritizes the complaint the millisecond it is submitted, routing it to the correct "Nagar Sevak" without human bottleneck.
- **Pre-emptive Spam Filtering:** The AI Vision model acts as a digital inspector. By correlating the image with the text via VQA, it automatically weeds out fake complaints and flags suspicious entries.
- **SLA Tracking & Black Zones:** If an official ignores a high-priority verified complaint, the system maps it as a "Black Zone," forcing accountability and drawing Admin attention to neglected areas.
- **E-Commerce Style Tracking:** Citizens get real-time status updates (Submitted -> AI Verified -> In Progress -> Resolved), building trust between the public and the government.

---

## 4. Technology Stack (What We Used to Build This)

Here is a breakdown of the core technologies and frameworks used to build the platform:

### 🖥️ Frontend & UI
- **Streamlit:** Used to build the entire web interface (User Portal, Admin Dashboard, and Nagar Sevak dashboards) rapidly using Python.
- **Plotly:** For rendering interactive data visualizations and analytics charts in the Admin dashboard.

### ⚙️ Backend & Logic
- **Python 3:** The core programming language running the application logic, routing, and AI integration.
- **MySQL (`mysql-connector-python`):** Relational database used to securely store users, authorities, complaints data, and tracking statuses.

### 🧠 Artificial Intelligence & Machine Learning
- **Scikit-Learn (Python):** Used to train and run the NLP (Natural Language Processing) models (`category_model.pkl`, `priority_model.pkl`) that predict text categories and prioritize complaints.
- **Hugging Face Transformers (`transformers`):** Used to load and execute the pre-trained **ViLT (Vision-and-Language Transformer)** model (`vilt-b32-finetuned-vqa`) for Visual Question Answering (VQA) image verification.
- **PyTorch (`torch`):** The deep learning backend framework required to run the Hugging Face vision models efficiently.

### 🗺️ Mapping & Geospatial Data
- **Folium & Streamlit-Folium:** Used to generate interactive maps for the Admin dashboard (e.g., plotting complaint locations and SLA "Black Zones").
- **GeoPandas & Pandas:** Used for handling geospatial data points and general data manipulation from the database.
