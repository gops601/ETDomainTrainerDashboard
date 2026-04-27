# Training Data Access Dashboard

A comprehensive, role-based Flask application designed to manage, track, and filter training session data across different domains and organizational units.

## Features

- **Role-Based Access Control**:
  - **System Admin**: Full access to manage users, organizational units (OUs), training types, and view all system-wide training data.
  - **Domain Lead**: A specialized role that provides team-level dashboard access. Domain Leads can view and manage data specific to their assigned domain (e.g., ET, AI, Cyber, DM). They can also submit their own training entries.
  - **Trainer**: Can submit daily/weekly training logs detailing the number of participants, duration, and training mode.
- **Dynamic Dashboards**: Dashboards feature advanced filtering by date, OU, Training Type, and Domain.
- **Secure Authentication**: Utilizing `Flask-Login` and `Flask-Bcrypt` for secure user sessions and password hashing.
- **Dockerized Ready**: Fully equipped with a `Dockerfile`, `docker-compose.yml`, and `.dockerignore` for easy containerized deployment.

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy (ORM)
- **Database**: MySQL (PyMySQL driver)
- **Frontend**: HTML5, CSS3 (Vanilla), Jinja2 Templating
- **Security**: Flask-Bcrypt, Flask-Login

## Prerequisites

- Python 3.9+
- MySQL Server 8.0+
- (Optional) Docker & Docker Compose for containerized deployment

## Local Setup

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd Trainigdataaccessdashboard
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and define the following variables:
   ```env
   SECRET_KEY=your_secure_random_key
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_HOST=localhost
   MYSQL_DB=training_dashboard
   ```

5. **Initialize the Database**:
   The application will automatically create the required tables and insert a default Admin user upon its first run.
   
6. **Run the Application**:
   ```bash
   python app.py
   ```
   The app will be accessible at `http://127.0.0.1:5001`.

## Docker Deployment

This application is ready to be deployed using Docker.

1. Build the Docker image:
   ```bash
   docker build -t training-dashboard .
   ```
2. Or use `docker-compose` if you have a `docker-compose.yml` configured with a MySQL database service.

## Default Credentials

Upon first run, the system creates a default admin account. Please change this password immediately after logging in.

- **Email**: `admin@example.com`
- **Password**: `admin123`

When an Admin or Domain Lead creates a new Trainer, their default password is set to `Trainer@ict`. The user will be forced to change it upon their first login.
