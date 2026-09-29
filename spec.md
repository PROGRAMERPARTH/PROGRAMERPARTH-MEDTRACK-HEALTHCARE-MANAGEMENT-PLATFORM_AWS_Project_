# MASTER PROMPT — BUILD MEDTRACK HEALTHCARE MANAGEMENT PLATFORM

## 1. ROLE

Act as a **senior full-stack architect, AWS cloud engineer, UI/UX designer, cybersecurity engineer, and healthcare application developer**.

Build a production-style cloud healthcare management platform called **MedTrack**.

The application must be:

* User-friendly
* Responsive
* Secure
* Fast
* Accessible
* Scalable
* Modular
* Easy to maintain
* Suitable for real-world demonstration
* Suitable for deployment on AWS
* Suitable for a college cloud/healthcare project demonstration

Do not build a basic CRUD application. Build a polished healthcare management product with a clear separation between **Patient**, **Doctor**, and **Administrator** workflows.

---

# 2. PRODUCT VISION

MedTrack is a centralized healthcare management platform that improves communication and coordination between patients and doctors.

The platform should allow patients to:

* Create an account
* Securely log in
* Complete their profile
* Search for doctors
* View doctor profiles
* Book appointments
* View upcoming appointments
* Cancel/reschedule appointments
* Receive appointment notifications
* Submit diagnosis/medical reports
* View their medical history
* Track diagnosis/report status
* Communicate important appointment information

Doctors should be able to:

* Securely log in
* Manage their professional profile
* View upcoming appointments
* Accept/reject appointment requests
* View patient information relevant to treatment
* Review submitted diagnosis reports
* Add diagnosis notes
* Update medical records
* Manage appointment status
* Receive notifications

Administrators should be able to:

* Manage users
* Manage doctors
* Monitor appointments
* Monitor system activity
* Manage access control
* View system statistics
* Monitor application health

---

# 3. IMPORTANT HEALTHCARE SAFETY PRINCIPLE

MedTrack is a **healthcare management and communication platform**, not an autonomous medical diagnosis system.

Do NOT make the application claim that it can replace a doctor.

Do NOT generate definitive medical diagnoses from symptoms.

Medical information should be treated as sensitive information.

Display appropriate messaging such as:

> "MedTrack helps manage healthcare information and appointments. It does not replace professional medical advice."

---

# 4. TECHNOLOGY STACK

Use the following architecture.

## Backend

* Python
* Flask
* Flask Blueprints
* RESTful API architecture
* Boto3
* Gunicorn

## Frontend

Prefer:

* HTML5
* CSS3
* JavaScript
* Bootstrap or Tailwind CSS

The UI should be modern and responsive.

Use reusable components wherever possible.

## Database

Use:

* Amazon DynamoDB

Suggested logical entities:

* Users
* Patients
* Doctors
* Appointments
* MedicalRecords
* DiagnosisReports
* Notifications
* AuditLogs

Do not unnecessarily create relational-style joins.

Design DynamoDB access patterns intentionally.

---

# 5. AWS ARCHITECTURE

Design the application around:

### Amazon EC2

Used for hosting the Flask application.

Production setup:

Internet
↓
Route 53
↓
Nginx
↓
Gunicorn
↓
Flask
↓
Boto3
↓
DynamoDB / SNS

### AWS DynamoDB

Store application data.

### AWS IAM

Use IAM roles and least-privilege permissions.

IMPORTANT:

Do NOT create an IAM user for every application patient or doctor.

Instead:

* Application users are stored in the application authentication system.
* EC2 uses an IAM role.
* AWS permissions are assigned to infrastructure/service roles.
* Application-level authorization determines what patients/doctors can access.

This distinction must be clearly implemented.

### AWS SNS

Use SNS for:

* Appointment confirmation
* Appointment reminder
* Appointment cancellation
* Appointment status updates
* Diagnosis/report submission notifications

### AWS CloudWatch

Use CloudWatch for:

* Application logs
* EC2 monitoring
* Error monitoring
* Performance monitoring

### AWS VPC

Deploy EC2 inside a properly configured VPC.

Use:

* Security groups
* Private/public subnet architecture where appropriate
* Restricted inbound access
* HTTPS-ready architecture

### Amazon Route 53

Use Route 53 for domain/DNS management.

---

# 6. USER ROLES

Implement three roles.

## PATIENT

Patient permissions:

* Register
* Login
* Logout
* Manage profile
* Search doctors
* View doctors
* Book appointment
* View appointments
* Cancel appointment
* Reschedule appointment
* Upload reports
* View own medical records
* View own diagnosis reports
* View notifications

Patients must NEVER access another patient's medical records.

---

## DOCTOR

Doctor permissions:

* Login
* Manage profile
* Set specialization
* Set availability
* View assigned/upcoming appointments
* Accept/reject appointments
* View relevant patient records
* Review submitted reports
* Add diagnosis notes
* Update medical records
* Mark appointment completed
* Send/update patient-facing information
* View notifications

Doctors must only access patients associated with their appointments/treatment context.

---

## ADMIN

Admin permissions:

* Login
* View system dashboard
* Manage users
* Manage doctors
* Manage patients
* View appointment statistics
* Monitor reports
* Manage account status
* Review audit logs
* Monitor application activity

Admin should not unnecessarily expose complete medical information unless required by an explicitly authorized administrative workflow.

---

# 7. AUTHENTICATION

Implement secure authentication.

Requirements:

* Registration
* Login
* Logout
* Password hashing
* Session management
* Secure cookies
* Session timeout
* Role-based authorization
* Input validation
* CSRF protection
* Rate limiting for authentication endpoints
* Secure password policy

Never store plaintext passwords.

Never expose passwords through logs.

Never expose sensitive medical information in URLs.

---

# 8. PATIENT REGISTRATION

Registration form should include:

* Full name
* Email
* Mobile number
* Date of birth
* Gender
* Address
* Emergency contact
* Password
* Confirm password

After registration:

1. Validate input.
2. Hash password.
3. Create unique PatientID.
4. Store patient information.
5. Create audit event.
6. Redirect to patient dashboard.

Do not collect unnecessary sensitive information.

---

# 9. DOCTOR PROFILE

Doctor profile should contain:

* DoctorID
* Name
* Profile photo
* Specialization
* Qualification
* Experience
* Hospital/clinic
* Consultation mode
* Consultation fee
* Available days
* Available time slots
* Verification status
* Contact information where appropriate

Example specialties:

* General Physician
* Cardiologist
* Dermatologist
* Pediatrician
* Neurologist
* Orthopedic
* Dentist
* Psychiatrist

Do not fabricate real doctors.

Use clearly marked demo data for testing.

---

# 10. DOCTOR DISCOVERY

Create a doctor search interface.

Patients should be able to filter doctors by:

* Specialization
* Availability
* Consultation mode
* Experience
* Location

Doctor cards should display:

* Photo
* Name
* Specialization
* Experience
* Availability
* Verification status
* "View Profile"
* "Book Appointment"

Make this interface extremely simple.

---

# 11. APPOINTMENT BOOKING

Create a smooth appointment booking workflow.

Flow:

Patient selects doctor
↓
View availability
↓
Select date
↓
Select time slot
↓
Enter appointment reason
↓
Review booking
↓
Confirm appointment
↓
Generate AppointmentID
↓
Store appointment
↓
Send notification
↓
Show confirmation

Appointment states:

* Requested
* Confirmed
* Rejected
* Cancelled
* Rescheduled
* Completed
* No-show

Prevent:

* Double booking
* Booking unavailable slots
* Booking past dates
* Invalid appointment states

---

# 12. APPOINTMENT DASHBOARD

Patient dashboard should contain:

### Upcoming Appointment

Display:

* Doctor
* Specialization
* Date
* Time
* Appointment status
* Appointment ID
* Appointment type

Actions:

* View details
* Reschedule
* Cancel

### Previous Appointments

Display appointment history.

Use filters:

* Upcoming
* Completed
* Cancelled

---

# 13. DOCTOR DASHBOARD

Doctor dashboard should contain:

### Today's Appointments

Display:

* Patient name
* Appointment time
* Appointment status
* Reason
* Report availability

### Pending Requests

Provide:

* Accept
* Reject
* View details

### Patient Records

Doctors should be able to access patient medical information only when authorized by the application workflow.

---

# 14. MEDICAL HISTORY

Create a clean medical history interface.

Patient timeline:

Appointment
↓
Diagnosis/Notes
↓
Medical Report
↓
Prescription/Recommendation
↓
Follow-up

Display information chronologically.

Each record should contain:

* RecordID
* PatientID
* DoctorID
* AppointmentID
* Date
* Diagnosis/clinical notes
* Treatment notes
* Follow-up information
* Attached report reference

Avoid exposing sensitive information unnecessarily.

---

# 15. DIAGNOSIS REPORT SUBMISSION

Patients should be able to submit reports.

Upload interface:

* Report title
* Report type
* Description
* Report date
* File upload
* Related appointment

Examples:

* Blood Test
* X-Ray
* MRI
* CT Scan
* Prescription
* Previous Diagnosis
* Other Medical Document

The UI should clearly show:

> "Upload only documents relevant to your healthcare consultation."

Validate:

* File size
* File type
* File name
* Authentication
* Ownership

Do not store uploaded medical files directly inside DynamoDB.

For production architecture, use secure object storage such as Amazon S3 and store only metadata/reference information in DynamoDB.

---

# 16. NOTIFICATION CENTER

Create a notification bell in the application header.

Notification types:

* Appointment booked
* Appointment confirmed
* Appointment rejected
* Appointment cancelled
* Appointment rescheduled
* Appointment reminder
* Report submitted
* Report reviewed
* Medical record updated

Notification UI:

Unread notification count
↓
Notification dropdown
↓
Notification list
↓
Mark as read

Use SNS for appropriate external notifications.

---

# 17. PATIENT DASHBOARD UI

Create a modern dashboard.

Top navigation:

MedTrack logo | Dashboard | Appointments | Doctors | Medical Records | Reports | Notifications | Profile

Dashboard sections:

### Welcome Card

"Good morning, [Patient Name]"

### Next Appointment

Doctor
Date
Time
Status

### Quick Actions

* Book Appointment
* Upload Report
* Medical History
* Find Doctor

### Health Activity

Show:

* Total appointments
* Completed consultations
* Pending appointments
* Reports submitted

### Recent Activity

Timeline of recent healthcare-management activities.

---

# 18. DOCTOR DASHBOARD UI

Navigation:

Dashboard | Appointments | Patients | Medical Records | Reports | Notifications | Profile

Dashboard:

* Today's appointments
* Pending requests
* Completed consultations
* Reports awaiting review
* Recent patients
* Quick actions

Use cards, tables, badges, and timeline components.

---

# 19. ADMIN DASHBOARD

Create a professional administration panel.

KPIs:

* Total Patients
* Total Doctors
* Today's Appointments
* Pending Appointments
* Completed Appointments
* Reports Submitted

Charts:

* Appointment trends
* User registration trends
* Appointment status distribution

Tables:

* Recent registrations
* Recent appointments
* System activity

---

# 20. UI/UX DESIGN SYSTEM

The UI should look like a modern healthcare SaaS product.

Design principles:

* Clean
* Minimal
* Professional
* Trustworthy
* Accessible
* Spacious
* Mobile responsive

Use a healthcare-oriented visual language.

Avoid:

* Excessive animations
* Flashy gradients
* Crowded dashboards
* Tiny text
* Too many colors
* Confusing navigation

Use:

* Clear cards
* Rounded components
* Consistent spacing
* Clear typography
* Status badges
* Icons
* Empty states
* Loading states
* Error states
* Success confirmations

---

# 21. RESPONSIVE DESIGN

The application must work on:

* Desktop
* Laptop
* Tablet
* Mobile

Mobile navigation should convert into a clean hamburger/bottom navigation system.

Appointment booking must remain easy on mobile.

Medical records should be readable without horizontal scrolling.

---

# 22. ACCESSIBILITY

Follow accessibility principles.

Implement:

* Proper labels
* Keyboard navigation
* High contrast
* Accessible buttons
* ARIA where appropriate
* Error messages
* Focus states
* Readable font sizes

Do not rely only on color to communicate status.

Example:

Confirmed ✓
Pending ⏳
Cancelled ×

---

# 23. DYNAMODB DATA MODEL

Design DynamoDB around access patterns.

Suggested entities:

### Users

Fields:

UserID
Role
Email
PasswordHash
Status
CreatedAt
UpdatedAt

### Patients

PatientID
UserID
Name
DOB
Gender
Phone
EmergencyContact
CreatedAt

### Doctors

DoctorID
UserID
Name
Specialization
Qualification
Experience
Availability
VerificationStatus

### Appointments

AppointmentID
PatientID
DoctorID
AppointmentDate
AppointmentTime
Status
Reason
CreatedAt
UpdatedAt

### MedicalRecords

RecordID
PatientID
DoctorID
AppointmentID
RecordDate
ClinicalNotes
TreatmentNotes
FollowUp

### Reports

ReportID
PatientID
DoctorID
AppointmentID
FileReference
ReportType
Description
Status
UploadedAt

### Notifications

NotificationID
UserID
Type
Title
Message
ReadStatus
CreatedAt

### AuditLogs

LogID
ActorID
Action
ResourceType
ResourceID
Timestamp
IP/metadata where appropriate

Use timestamps in UTC.

---

# 24. SECURITY REQUIREMENTS

Treat healthcare data as highly sensitive.

Implement:

* Least privilege
* Role-based authorization
* Password hashing
* Secure sessions
* HTTPS-ready configuration
* CSRF protection
* Input sanitization
* Output escaping
* Rate limiting
* Secure HTTP headers
* Error handling
* Audit logging
* Access validation
* File validation
* No sensitive data in logs
* No secrets inside source code

Use environment variables for:

* AWS configuration
* Flask secret key
* SNS configuration
* Other credentials/configuration

Never hardcode AWS access keys.

Prefer IAM roles over static AWS credentials when running on EC2.

---

# 25. IAM ARCHITECTURE

Implement AWS IAM according to least privilege.

Create an EC2 IAM role with only required permissions.

Example conceptual permissions:

DynamoDB:

* Read/write required tables only

SNS:

* Publish to required SNS topics only

CloudWatch:

* Required logging/monitoring permissions

S3:

* Only required bucket/object operations if report storage is implemented

Do not grant:

AdministratorAccess

unless absolutely necessary for initial infrastructure setup, and do not use administrator privileges for the running application.

---

# 26. CLOUDWATCH

Configure monitoring for:

* EC2 CPU utilization
* Memory where supported/configured
* Application logs
* Flask errors
* Gunicorn errors
* Nginx errors
* Failed authentication attempts
* Important application events

Create meaningful log messages without exposing:

* Passwords
* Medical reports
* Authentication tokens
* Sensitive personal information

---

# 27. ROUTE 53 AND DOMAIN

Prepare the application for a custom domain.

Architecture:

Domain
↓
Route 53
↓
EC2
↓
Nginx
↓
Gunicorn
↓
Flask

Prepare configuration for HTTPS using a proper TLS certificate.

---

# 28. EC2 DEPLOYMENT

Target environment:

Amazon Linux

Deployment flow:

Developer
↓
GitHub
↓
EC2
↓
Virtual Environment
↓
Gunicorn
↓
Nginx
↓
Flask

Provide:

* requirements.txt
* .env.example
* application configuration
* Gunicorn configuration
* Nginx configuration
* deployment instructions
* startup/service configuration
* health check endpoint

Example:

GET /health

Response:

{
"status": "healthy"
}

---

# 29. APPLICATION STRUCTURE

Use a clean Flask structure.

Example:

medtrack/
│
├── app/
│   ├── **init**.py
│   ├── config.py
│   │
│   ├── auth/
│   ├── patient/
│   ├── doctor/
│   ├── admin/
│   ├── appointments/
│   ├── medical_records/
│   ├── reports/
│   ├── notifications/
│   │
│   ├── templates/
│   ├── static/
│   ├── services/
│   ├── utils/
│   └── models/
│
├── tests/
├── scripts/
├── requirements.txt
├── .env.example
├── run.py
├── gunicorn.conf.py
├── README.md
└── deployment/

Use Flask Blueprints to keep modules independent.

---

# 30. ERROR HANDLING

Create friendly error pages.

Required:

* 400
* 401
* 403
* 404
* 429
* 500

Example:

Instead of:

"Internal Server Error"

show:

"Something went wrong. Please try again."

Provide:

* Back to Dashboard
* Try Again

Do not expose stack traces to users in production.

---

# 31. LOADING AND EMPTY STATES

Every important asynchronous operation must have a loading state.

Examples:

"Loading appointments..."

"Uploading report..."

"Booking appointment..."

For empty data:

"No upcoming appointments"

Then show:

"Find a Doctor"

For no medical records:

"No medical records available yet."

---

# 32. VALIDATION

Frontend and backend validation must both exist.

Validate:

* Email
* Phone
* Password
* Dates
* Appointment availability
* File uploads
* Required fields
* User permissions

Never trust frontend validation alone.

---

# 33. AUDIT LOGGING

Log security-sensitive events:

* Login
* Logout
* Failed login
* Appointment creation
* Appointment cancellation
* Medical record creation/update
* Report upload
* Permission denial
* Admin actions

Do not store sensitive medical content inside audit logs.

---

# 34. API DESIGN

Create clean API endpoints.

Examples:

POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout

GET /api/doctors
GET /api/doctors/<id>

POST /api/appointments
GET /api/appointments
PUT /api/appointments/<id>
DELETE /api/appointments/<id>

GET /api/medical-records
POST /api/medical-records

POST /api/reports
GET /api/reports

GET /api/notifications
PUT /api/notifications/<id>/read

GET /api/health

Apply authentication and authorization to every protected endpoint.

---

# 35. SEARCH AND FILTERING

Implement useful filtering.

Patients:

Search doctors by specialization/name/availability.

Doctors:

Filter appointments by:

* Today
* Upcoming
* Completed
* Cancelled
* Pending

Admins:

Filter:

* Users
* Doctors
* Appointments
* Reports
* Status

---

# 36. DEMO DATA

Create realistic but completely fictional demo data.

Example:

Patients:

* Aarav Sharma
* Ananya Patil

Doctors:

* Dr. Rohan Mehta — General Physician
* Dr. Priya Kulkarni — Dermatologist
* Dr. Aditya Shah — Cardiologist

Clearly mark demo accounts where necessary.

Never use real patient medical information.

---

# 37. TESTING

Create automated tests for:

### Authentication

* Registration
* Login
* Logout
* Invalid password
* Unauthorized access

### Appointments

* Create appointment
* Prevent double booking
* Cancel appointment
* Reschedule appointment
* Invalid date

### Authorization

Verify:

Patient cannot access another patient's records.

Patient cannot access doctor dashboard.

Doctor cannot access unrelated patient records.

Regular user cannot access admin routes.

### Reports

* Upload validation
* Unauthorized report access
* Invalid file type

### Notifications

* Appointment confirmation
* Appointment cancellation
* Report submission

---

# 38. PERFORMANCE

Optimize for:

* DynamoDB efficient queries
* Pagination
* Minimal database calls
* Cached static resources
* Efficient frontend rendering
* Optimized images
* Async notification handling where appropriate

Do not scan DynamoDB tables unnecessarily.

Prefer Query operations using appropriate keys.

---

# 39. USER EXPERIENCE FLOW

The complete patient journey should feel like:

Landing Page
↓
Register/Login
↓
Patient Dashboard
↓
Find Doctor
↓
Doctor Profile
↓
Select Date & Time
↓
Confirm Appointment
↓
Appointment Confirmation
↓
Notification
↓
Consultation
↓
Doctor Updates Medical Record
↓
Patient Receives Notification
↓
Patient Views Medical History

Doctor journey:

Login
↓
Doctor Dashboard
↓
View Appointment Request
↓
Accept Appointment
↓
View Patient Information
↓
Consult Patient
↓
Review Reports
↓
Add Medical Record
↓
Complete Appointment
↓
Patient Notification

---

# 40. LANDING PAGE

Create a professional landing page.

Hero:

## "Healthcare Management, Simplified."

Subtitle:

"MedTrack connects patients and doctors through secure appointment management, medical records, reports, and real-time notifications."

Buttons:

* Find a Doctor
* Login
* Register

Sections:

### Why MedTrack?

* Easy Appointment Booking
* Secure Medical Records
* Doctor–Patient Coordination
* Real-Time Notifications
* Cloud-Powered Infrastructure

### How It Works

1. Create Account
2. Find Doctor
3. Book Appointment
4. Manage Healthcare Records

### Security

Explain:

* Secure authentication
* Role-based access
* AWS cloud infrastructure
* Controlled data access

---

# 41. DASHBOARD DESIGN RULE

Do not overwhelm users.

The first screen after login should answer:

### Patient

"What do I need to know or do today?"

### Doctor

"What appointments or patient actions need my attention?"

### Admin

"What is happening in the system?"

Prioritize actionable information.

---

# 42. NOTIFICATION UX

Use both:

### In-app notification

For immediate application updates.

### AWS SNS

For configured external notifications such as:

* Email
* SMS where configured

Do not send notifications for every minor database event.

Notifications should be meaningful.

---

# 43. SECURITY-FIRST DATA ACCESS

Before returning any medical record:

1. Verify authentication.
2. Identify current user.
3. Verify role.
4. Verify resource ownership/relationship.
5. Verify authorization.
6. Retrieve record.
7. Return minimum necessary information.

Never rely on:

/medical-records/123

being protected merely because the URL is difficult to guess.

---

# 44. FINAL UI QUALITY CHECK

Before considering the project complete, verify:

* No broken links
* No placeholder buttons
* No dead pages
* No console errors
* No unhandled exceptions
* Responsive design
* Proper validation
* Accessible navigation
* Working login/logout
* Working appointment workflow
* Working medical history
* Working report submission
* Working notifications
* Working role permissions
* Proper error states
* Loading states
* Empty states

---

# 45. DELIVERABLES

Produce:

1. Complete Flask application
2. Responsive frontend
3. DynamoDB data model
4. AWS IAM configuration guidance
5. EC2 deployment configuration
6. VPC architecture guidance
7. SNS notification implementation
8. CloudWatch monitoring configuration
9. Route 53 configuration guidance
10. Nginx configuration
11. Gunicorn configuration
12. Environment configuration
13. API documentation
14. Database/access-pattern documentation
15. Test cases
16. README
17. Deployment guide
18. Architecture diagram
19. Security documentation
20. Demo credentials/data

---

# 46. DEVELOPMENT STRATEGY

Do NOT attempt to create everything as one huge uncontrolled implementation.

Build incrementally.

### Phase 1 — Foundation

* Flask setup
* Project structure
* Configuration
* Authentication
* Database connection

### Phase 2 — Patient

* Patient profile
* Doctor discovery
* Appointment booking
* Patient dashboard

### Phase 3 — Doctor

* Doctor dashboard
* Appointment management
* Patient records
* Diagnosis/report workflow

### Phase 4 — Notifications

* SNS
* In-app notifications
* Appointment notifications

### Phase 5 — Security

* IAM
* Authorization
* Audit logging
* Secure configuration

### Phase 6 — Cloud Deployment

* VPC
* EC2
* Nginx
* Gunicorn
* Route 53
* CloudWatch

### Phase 7 — Testing

* Functional testing
* Security testing
* Authorization testing
* Performance testing
* UI testing

---

# 47. IMPORTANT IMPLEMENTATION RULES

Do not:

* Hardcode credentials
* Store plaintext passwords
* Give EC2 AdministratorAccess
* Allow patients to access other patients' records
* Allow doctors unrestricted access to all patients
* Put medical information in URLs
* Expose stack traces
* Trust frontend authorization
* Use DynamoDB scans unnecessarily
* Create unnecessary IAM users
* Use real patient data
* Claim the application provides professional medical diagnosis

Do:

* Use least privilege
* Use IAM roles
* Hash passwords
* Validate all inputs
* Authorize every protected resource
* Log security events
* Use HTTPS-ready deployment
* Keep secrets in environment/secret management
* Design DynamoDB around access patterns
* Make the UI simple
* Make the application mobile responsive
* Provide meaningful error and empty states

---

# 48. SUCCESS CRITERIA

The project is successful when a new user can open MedTrack and intuitively understand what to do without training.

A patient should be able to complete:

Register → Login → Find Doctor → Book Appointment → Receive Confirmation → Upload Report → View Medical History

without confusion.

A doctor should be able to complete:

Login → View Appointments → Review Patient → Review Report → Add Medical Record → Complete Appointment

without unnecessary navigation.

The final application should look and behave like a **modern cloud healthcare management SaaS platform**, while remaining understandable enough to demonstrate every major AWS and Flask concept used in the project.

---

# FINAL INSTRUCTION TO THE AI BUILDER

Build MedTrack as a complete, modular, secure, production-style healthcare management platform.

Prioritize:

**Security → Usability → Correctness → Accessibility → Performance → Scalability → Visual polish.**

When making architectural decisions, explain the reasoning briefly and choose the simplest reliable solution.

Do not implement fake functionality behind buttons.

Every visible major feature should have a working backend workflow.

If an AWS service cannot be fully configured in the current development environment, implement a clean service abstraction and provide a clear AWS configuration path rather than pretending the integration works.

The final result should be suitable for:

* College project demonstration
* AWS cloud project evaluation
* Healthcare IT portfolio
* Cloud developer portfolio
* Flask backend demonstration
* AWS architecture demonstration
* Technical interview discussion
