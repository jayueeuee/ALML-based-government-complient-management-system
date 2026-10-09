# AI Governance Complaint Management System 🏙️

Welcome to the **AI Governance Complaint Management System**, an intelligent, AI-powered platform designed to streamline and automate the reporting, verification, and resolution of civic issues and grievances.

## 🚀 Features

- **User Portal**: Submit complaints with text descriptions and image proofs. The AI automatically verifies the image, categorizes the issue, and prioritizes the complaint before routing it to the concerned authority.
- **AI & Physical Verification**: Ensures authenticity of complaints using AI image verification and multi-stage physical verification steps.
- **Nagar Sevak Dashboard**: A dedicated dashboard for local authorities and officials to manage and resolve their assigned complaints.
- **Admin Dashboard**: Comprehensive analytics, maps, and tracking of SLA (Service Level Agreement) breaches (highlighting "Black Zones" where issues are delayed).
- **Complaint Tracking**: Users can track their submitted complaints in real-time, just like tracking an e-commerce order.
- **Feedback System**: Rate the resolution of the complaint and share experiences to improve civic services.

## 🛠️ Technology Stack

- **Frontend/UI**: Streamlit
- **Backend/Logic**: Python
- **Database**: MySQL (`mysql-connector-python`)
- **AI/ML**: `scikit-learn`, `transformers`, `torch` (for image verification and text prediction)
- **Data Visualization & Mapping**: `pandas`, `plotly`, `folium`, `streamlit-folium`, `geopandas`

## ⚙️ Installation & Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <your-github-repo-url>
   cd <repository-folder>
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory for local development. Set `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` for your MySQL database. Never commit `.env` or put credentials in source files.

5. **Run the Application**:
   ```bash
   streamlit run app.py
   ```
   The application will be accessible at `http://localhost:8501`.

## Publish a Public Test (Streamlit Community Cloud)

1. Create a GitHub repository and push the application code. Keep `.env`, `uploads/`, and `__pycache__/` out of Git; `.gitignore` excludes them.
2. Create a hosted MySQL database. Streamlit Community Cloud cannot connect to MySQL running on your computer. Create the database/schema with your provider before deploying, and use a database account limited to that schema.
3. In Streamlit Community Cloud, deploy `app.py` from the GitHub repository and add these values under the app's **Settings > Secrets**. Use the connection details supplied by your database provider.

   ```toml
   MYSQL_HOST = "your-mysql-host"
   MYSQL_PORT = "3306"
   MYSQL_USER = "your-database-user"
   MYSQL_PASSWORD = "your-database-password"
   MYSQL_DATABASE = "your-database-name"
   BOOTSTRAP_ADMIN_USERNAME = "choose-an-admin-username"
   BOOTSTRAP_ADMIN_PASSWORD = "choose-a-strong-admin-password"
   SENDER_EMAIL = "your-sender-address"
   SENDER_PASSWORD = "your-email-app-password"
   ```

   `SENDER_EMAIL` and `SENDER_PASSWORD` are optional; add them only if email notifications are needed. The bootstrap admin is created only when both admin settings are present. Sign in as that admin to add Nagar Sevak and officer accounts. Do not share the admin credentials with testers.
4. Test citizen registration, complaint submission, tracking, and staff workflows using non-sensitive sample data.

The app stores uploaded complaint photos on the server's local filesystem. Those files may be lost when a hosted app restarts or redeploys; use durable object storage before relying on the public deployment for real complaints. Treat all complaint details and images as sensitive, and do not upload real personal data to a test deployment.

## 📁 Project Structure

- `app.py`: Main Streamlit application entry point.
- `database.py`: Handles database connections and operations.
- `ai_engine.py`: Contains the AI/ML logic for categorization and verification.
- `email_service.py`: Handles email notifications.
- `pages/`: Contains the individual dashboard and portal pages (User, Admin, Nagar Sevak, etc.).
- `models/`: Directory for storing pre-trained AI models.
- `requirements.txt`: Python dependencies.
