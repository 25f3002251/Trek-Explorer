# Trek-Explorer
# Trek Explorer — Trekking Management Application

A web-based Trekking Management Application developed using Flask and SQLite. The application provides separate functionality for Admins, Trek Staff, and Users, including trek management, staff assignment, trek booking, participant management, and booking history.

## Features

### Admin

* Admin login with a pre-created administrator account
* View total treks, users, staff, and bookings
* Create, edit, and delete treks
* Assign staff members to treks
* Approve staff registrations
* View and search treks
* View and manage staff members
* Blacklist and unblacklist staff
* View booking and trekking records

### Trek Staff

* Staff registration and admin approval
* Staff login
* View assigned treks
* View trek participants
* Manage assigned trek information
* Start and complete treks
* View participant and booking information
* Staff can manage only treks assigned to them

### User

* User registration and login
* Browse available treks
* Search treks by location and difficulty
* View trek details and available slots
* Book treks
* Cancel bookings
* Rebook a trek after cancellation
* View active bookings
* View trekking history
* Prevent duplicate active bookings
* Prevent booking when a trek is full or unavailable

## Technologies Used

* **Python** — application programming language
* **Flask** — web application framework
* **Flask-SQLAlchemy / SQLAlchemy** — database ORM and database operations
* **SQLite** — relational database
* **Jinja2** — HTML templating through Flask
* **HTML5** — webpage structure
* **Bootstrap 5** — basic responsive interface styling
* **Git/GitHub** — version control and project submission

## Project Structure

```text
Trek-Explorer/
│
├── app.py
├── models.py
├── README.md
├── .gitignore
│
├── static/
│   └── css/
│       └── style.css
│
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── register.html
    ├── error.html
    ├── admin_dashboard.html
    ├── ...
    └── user_trek_details.html
```

## Database

The application uses SQLite with SQLAlchemy ORM.

The main database entities are:

* **User** — stores users, staff, and administrator accounts.
* **Trek** — stores trek information, assigned staff, dates, capacity, and status.
* **Booking** — stores the relationship between users and treks, including booking date and booking status.

The main relationships are:

```text
User 1 ──────── * Booking * ──────── 1 Trek
                                      │
                                      │
                                      1
                                   Staff/User
```

Booking statuses include:

* `Booked`
* `Cancelled`
* `Completed`

Trek statuses include states such as:

* `Open`
* `Full`
* `Ongoing`
* `Completed`

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/25f3002251/Trek-Explorer.git
cd Trek-Explorer
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install the required packages

```bash
pip install flask flask-sqlalchemy werkzeug
```

### 4. Run the application

```bash
python app.py
```

The Flask development server will start locally. Open the address shown in the terminal in a web browser.

## Administrator Account

The administrator account is created automatically when the application is initialized.

Default administrator credentials:

```text
Email: admin@trek.com
Password: admin123
```

The administrator does not use the normal registration process.

## Running the Application

After starting the application:

1. Register as a User or Trek Staff member.
2. Log in using the registered credentials.
3. Trek Staff accounts require administrator approval before login.
4. The administrator can create treks and assign approved staff members.
5. Users can browse and book available treks.
6. Staff members can manage their assigned treks and participants.
7. Completed bookings are retained as trekking history.

## Booking Rules

The application includes validation to:

* Prevent booking a trek that is not open.
* Prevent booking when all available slots are occupied.
* Prevent duplicate active bookings for the same user and trek.
* Allow users to rebook after cancelling a booking.
* Prevent users from cancelling a booking after the trek has started.
* Automatically mark active bookings as completed when the assigned staff member completes the trek.

## Version Control

The project is maintained using Git and GitHub. Git commits were created for the project milestones, including:

* Milestone 0 — GitHub Repository Setup
* Milestone 1 — Database Models and Schema
* Milestone 2 — Authentication and Role-Based Access
* Milestone 3 — Admin Dashboard and Management
* Milestone 4 — Trek Staff Dashboard and Trek Management
* Milestone 5 — User Dashboard and Trek Booking System
* Milestone 6 — Trek Booking History and Trek Status Tracking

## Project

GitHub Repository:https://github.com/25f3002251/Trek-Explorer

https://github.com/25f3002251/Trek-Explorer
