# 🏨 Ali Hall Smart Hostel & Mess Management System
### The Islamia University of Bahawalpur (IUB) &bull; Baghdad-ul-Jadeed Campus

A production-ready, enterprise-grade Python/Django web application custom-tailored for **Ali Hall (Boys Hostel)** under the Directorate of Student Hostels & Hall Council at **The Islamia University of Bahawalpur (IUB)**.

Featuring a modern, responsive UI crafted with **Tailwind CSS** and **Bootstrap 5**, Role-Based Access Control (RBAC), Pakistani banking payment verification, automated Zero Double-Booking bed allocation logic for **300 Rooms and 600 Beds**, and a **Professional Hostel Mess Management System**.

---

## 🏛️ Campus & Hostel Specification
- **Institution:** The Islamia University of Bahawalpur (IUB)
- **Hostel:** Ali Hall (Boys Hostel)
- **Capacity:** Exactly **300 Rooms**, **2 Students per room**, **600 Beds Total**
- **Allocation State:** **580 Occupied Beds**, **Exactly 20 Vacant Beds**
- **Campus:** Baghdad-ul-Jadeed Campus, Bahawalpur, Punjab, Pakistan
- **Governing Body:** Hall Council & Directorate of Student Hostels, IUB
- **Residential Wings & Quota Allocation:**
  - **♿ Quaid Block (Block A) — Ground Floor (Rooms 1 to 100):**
    - **100 Rooms &bull; 200 Beds (`Bed-A`, `Bed-B`)**
    - **Exclusively Reserved for Special Students** (disabled scholars, mobility-impaired, medical needs)
    - **196 Occupied Beds**, **4 Vacant Spaces** (Rooms 99 & 100)
  - **🎓 Iqbal Block (Block B) — First Floor (Rooms 101 to 200):**
    - **100 Rooms &bull; 200 Beds (`Bed-A`, `Bed-B`)**
    - General Merit & Regular Students
    - **192 Occupied Beds**, **8 Vacant Spaces** (Rooms 195–200)
  - **🎓 Sir Syed Block (Block C) — Second Floor (Rooms 201 to 300):**
    - **100 Rooms &bull; 200 Beds (`Bed-A`, `Bed-B`)**
    - General Merit & Regular Students
    - **192 Occupied Beds**, **8 Vacant Spaces** (Rooms 295–300)
- **Currency:** Pakistani Rupee (PKR / Rs.)
- **Payment Methods:** HBL Konnect, 1-Bill, EasyPaisa, JazzCash, HBL / NBP Baghdad-ul-Jadeed Campus Bank Challans

---

## 🌟 Key Functional Modules & Architecture

```
hostal_management/
├── smart_hostel/          # Django Project Configuration (Settings, URLs, WSGI, Context Processors)
├── hostel/                # Hostel Core (300 Rooms, 600 Beds, Allotments, Complaints, Room Changes, Applications)
├── mess/                  # Professional Mess Module (Menus, Attendance, Fees, Expenses)
├── templates/
│   ├── base.html          # Base Layout with Responsive Sidebar & Notification Center
│   ├── accounts/          # Login (with 1-click demo fillers), Register (with photo preview), Profile
│   ├── allocations/       # Room Inventory (300 Rooms matrix/table), Bed Allotments, Room Changes
│   ├── applications/      # Student Admission Applications Roster & Review Dossier
│   ├── complaints/        # Maintenance Tickets (11 Categories, 4 Priority Levels, Staff Assignment)
│   ├── dashboard/         # Role-specific Dashboards: Admin, Warden, Student
│   ├── notifications/     # In-App Notification Center
│   ├── announcements/     # Official Notice Board & Broadcast Circulars
│   ├── students/          # Searchable Student Directory & Full Dossiers
│   ├── wardens/           # Warden Staff Roster & Granular Permissions
│   ├── fees/              # Hostel Fee Vouchers, Payment Proofs, Bulk Generation
│   ├── gatepasses/        # Out-Pass / Leave Applications & Warden Approvals
│   └── mess/              # 7-Day Menu Matrix, Meal Attendance, Mess Accounting, Expenses
├── static/                # Static assets (Custom CSS, JS, Branding)
├── media/                 # Student profile photos, uploaded CNIC/slips, dish pictures
└── manage.py              # Django management script
```

---

## 🏨 Core Hostel Management Features

### 1. 300 Rooms & 600 Beds Room Inventory (`/rooms/`)
- **Natural Room-Wise Sequential Order (1 to 300):** Integer-sorted query preventing alphabetic misordering.
- **Ground Floor Special Students Reservation:**
  - **Rooms 1 to 100** prominently marked with purple wheelchair badges and reservation notice.
  - Dedicated quota filter (`All`, `Special Students Quota (Rooms 1-100)`, `Regular Students (Rooms 101-300)`).
  - Designed for disabled scholars, mobility-impaired residents, and medical accommodations.
- **Complete Resident Details Displayed Room-Wise:**
  - Full resident name (e.g. Ali Hassan, Rizwan Ahmed, Usman Tariq, Bilal Ahmed).
  - Mobile phone number (e.g. `+92-30X-XXXXXXX`).
  - National CNIC / B-Form (e.g. `31202-XXXXXXX-X`).
  - Residential Home Address (across Bahawalpur, Multan, Rahim Yar Khan, Lodhran, etc.).
  - Academic Department, Semester, and Registration Number.
  - Bed code (`Bed-A`, `Bed-B`) and status badge.
- **Strict Capacity & Vacancy Tracking:**
  - Exactly **580 beds allocated** to active verified students.
  - Exactly **20 vacant spaces** available for emergency or incoming allocations.
  - Vacant beds display a green "Vacant Space" badge with a direct 1-click `+ Allot` shortcut.
- **Visual Switcher & Export:**
  - **Table View:** Dense, comprehensive roster showing both Bed-A and Bed-B side-by-side with full contact dossiers.
  - **Grid View:** Responsive cards with photo avatars, quick contact chips, and status badges.
  - **CSV Export:** 1-click download (`/reports/export-rooms/`) of the complete 300-room inventory with resident details.
- Quick 1-click **Maintenance Mode Toggle** for administrators and wardens.

### 2. Student Admission Application Portal (`/applications/`)
- New student self-registration with live avatar preview (`FileReader` JavaScript API).
- Document uploads: CNIC / B-Form, University Admission Fee Challan Slip, and optional verification files.
- Application workflow statuses: `PENDING` $\rightarrow$ `APPROVED` $\rightarrow$ `ALLOCATED` or `REJECTED`.
- Administrator / Warden review dossier (`/applications/<id>/`) with document viewers and feedback notes.
- Only approved applicants can be allocated a bed in the hostel.

### 3. Multi-Tier Student Room-Change Workflow (`/room-changes/`)
- **Step 1 (Student Submission):** Resident selects reason category (`Roommate conflicts`, `Maintenance problems`, `Noise disturbance`, `Safety`, `Medical / Ground floor requirement`, `Other genuine difficulties`), suggests preferred target room, details circumstances, and attaches optional medical proof.
- **Step 2 (Warden Field Review):** Block warden assesses physical room conditions, interviews roommates, and submits recommendation (`RECOMMENDED` / `NOT_RECOMMENDED`) with assessment remarks.
- **Step 3 (Admin Atomic Transfer Execution):** Chief Warden reviews findings, selects available target room and bed, and triggers the transfer.
- **Atomic Zero Double-Booking Swap:** Old bed is automatically freed to `AVAILABLE`, target bed is marked `OCCUPIED`, the active allotment record is updated, the request is marked `COMPLETED`, and an instant notification is dispatched to the student.

### 4. 11-Category Maintenance Complaint Helpdesk (`/complaints/`)
- 11 specialized categories:
  1. Room Maintenance
  2. Electrical
  3. Water / Plumbing
  4. Bathroom / Sanitation
  5. Cleanliness & Janitorial
  6. Furniture & Fixtures
  7. Internet / PERN WiFi
  8. Roommate / Noise Issues
  9. Food / Mess
  10. Security
  11. Other General Concerns
- 4 Priority levels: `LOW`, `MEDIUM`, `HIGH`, `URGENT` (with pulsing badges).
- Automated ticket reference generation: `CMP-YYYYMM-XXXX`.
- Warden / Staff assignment and resolution notes.
- Issue photo upload and supporting file attachments.

### 5. Warden Management & Granular Permissions (`/wardens/`)
- Administrative directory of all wardens and resident tutors.
- Block assignment jurisdiction (e.g. Quaid Block, Iqbal Block, or all blocks).
- Granular permission flags:
  - `Can Manage Allocations`
  - `Can Manage Complaints`
  - `Can Manage Gate Passes`
  - `Can Review Room Changes`

### 6. In-App Notification Center (`/notifications/`)
- Real-time notification badge with unread counter in the top navigation bar.
- Dropdown menu with one-click direct links to tickets, room transfers, or fee vouchers.
- Dedicated notification center page with "Mark All as Read" action.

### 7. Official Notice Board & Announcements (`/announcements/`)
- Categorized circulars: `GENERAL`, `TIMINGS`, `DISCIPLINE`, `MAINTENANCE`, `FEES`, `HOLIDAY`.
- Urgent alert banners and real-time broadcast across student resident portals.

---

## 🍽️ Professional Mess Management Module

- **Executive Dashboard (`/mess/`):** 4-meal daily schedule, participation metrics, and 6-month financial analytics.
- **Student Resident Directory (`/mess/students/`):** Resident roster, contact info, and CSV exports.
- **7-Day Menu Matrix (`/mess/menu/weekly/`):** Complete breakfast, lunch, tea, and dinner menus with serving windows.
- **Per-Meal Attendance (`/mess/attendance/`):** Mark attendance with "Mark All Present/Absent" controls and zero-duplicate database constraints.
- **Mess Fees & Ledgers (`/mess/fees/`):** Monthly fee billing, payments recording, auto-calculated balances, and defaulter tracking.
- **Kitchen Procurement & Expenses (`/mess/expenses/`):** Daily procurement ledger (food, groceries, gas, supplies) and monthly income vs expense audit reports.
- **Student Mess Portal (`/mess/portal/`):** Personal meal schedule, attendance history, and fee vouchers.

---

## 🚀 Setup & Execution Guide

### Step 1: Open PowerShell in Project Directory
```powershell
cd "c:\Users\Dad Mohammad\Desktop\hostal_management"
```

### Step 2: Activate Virtual Environment
```powershell
.\venv\Scripts\activate
```

### Step 3: Run Database Migrations
```powershell
python manage.py migrate
```

### Step 4: Populate Ali Hall 300 Rooms, 600 Beds & Sample Data
```powershell
# 1. Seed 300 Rooms, 600 Beds, Applications, Room Changes, Complaints, Announcements
python manage.py populate_sample_data

# 2. Seed Mess 7-Day Menus, Attendances, Fees, and Kitchen Expenses
python manage.py populate_mess_data
```

### Step 5: Run Full Automated Test Suite (34 Tests)
```powershell
python manage.py test
```
*(All 34 tests will execute with `OK` status)*

### Step 6: Launch Development Server
```powershell
python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username | Password | Full Name & Designation | Primary Portal |
| :--- | :--- | :--- | :--- | :--- |
| **Chief Warden / SuperAdmin** | `admin` | `admin123` | Dr. Muhammad Tariq (Chief Hall Warden) | `/` & `/mess/` |
| **Hostel Warden (Quaid Block)** | `warden_ali_hall` | `warden123` | Hafiz Muhammad Asif (Senior Resident Warden) | `/` & `/mess/` |
| **Hostel Warden (Iqbal Block)** | `warden_iqbal` | `warden123` | Engr. Shahbaz Khan (Block Warden) | `/` & `/mess/` |
| **Student Resident (Ali)** | `student_ali` | `student123` | Ali Hassan (Room 101, Bed-A) | `/` & `/mess/portal/` |
| **Student Resident (Usman)** | `student_usman` | `student123` | Usman Tariq (Room 101, Bed-B) | `/` & `/mess/portal/` |
| **Student Resident (Bilal)** | `student_bilal` | `student123` | Bilal Ahmed (Room 201, Bed-A) | `/` & `/mess/portal/` |
| **Applicant Student (Hamza)** | `student_hamza` | `student123` | Hamza Rehman (Application Approved) | `/profile/` |
| **Applicant Student (Zain)** | `student_zain` | `student123` | Zain Malik (Application Pending) | `/profile/` |

*(Tip: On the login page, you can click any of the 1-click demo buttons to automatically populate credentials!)*

---

## 🌐 Application URL Reference Directory

| Endpoint | Access Level | Description |
| :--- | :--- | :--- |
| `/` | Authenticated | Smart Dashboard router (SuperAdmin, Warden, or Student view) |
| `/profile/` | Authenticated | Student / User Profile with live photo preview and documents |
| `/login/` | Public | University Login Page with 1-click demo credential fillers |
| `/register/` | Public | Student Registration with photo preview and document uploads |
| `/notifications/` | Authenticated | System Notifications Center with unread counter |
| `/applications/` | Admin / Warden | Student Admission Applications roster and filters |
| `/applications/<id>/` | Admin / Warden | Student Application Review Dossier & Approve/Reject actions |
| `/students/` | Admin / Warden | Searchable Student Directory with academic records |
| `/students/<id>/` | Admin / Warden | Comprehensive Student Resident Dossier (Allotments, Tickets, Fees) |
| `/rooms/` | Authenticated | 300 Rooms & 600 Beds Inventory (Grid & Table views) |
| `/rooms/<id>/maintenance-toggle/` | Admin / Warden | Toggle Room Maintenance status |
| `/allocations/` | Admin / Warden | Bed Allotments management & vacate history |
| `/allocations/new/` | Admin / Warden | Allocate Bed with zero double-booking validation |
| `/allocations/<id>/vacate/` | Admin / Warden | Vacate Bed and release back to Available |
| `/room-changes/` | Authenticated | Room-change requests list (Students see own; Staff see block) |
| `/room-changes/request/` | Student | Submit Room-Change Application with reasons and preferred room |
| `/room-changes/<id>/` | Authenticated | Multi-tier review: Warden Recommendation + Admin Bed Swap |
| `/complaints/` | Authenticated | 11-Category Maintenance Complaints roster and filters |
| `/complaints/new/` | Student | Lodge new maintenance ticket with photo and priority |
| `/complaints/<id>/` | Authenticated | Ticket detail, staff assignment, and resolution history |
| `/wardens/` | Admin | Hostel Wardens roster and assigned blocks |
| `/wardens/new/` | Admin | Register new warden account with granular permissions |
| `/wardens/<id>/edit/` | Admin | Edit warden block jurisdiction and permissions |
| `/announcements/` | Authenticated | Notice Board & Official Broadcast Circulars |
| `/announcements/new/` | Admin / Warden | Post new notice or urgent alert |
| `/fees/` | Authenticated | Hostel Fee Vouchers, bank payment slips, and verification |
| `/gatepasses/` | Authenticated | Student Gate Passes / Leave Applications |
| `/mess/` | Authenticated | Professional Mess Dashboard / Student Mess Portal |
| `/mess/menu/weekly/` | Authenticated | 7-Day Monday–Sunday Weekly Dining Matrix |
| `/mess/attendance/` | Admin / Staff | Daily per-meal attendance marking system |
| `/mess/fees/` | Admin / Staff | Mess accounting, payments, and defaulters ledger |
| `/mess/expenses/` | Admin / Staff | Kitchen procurement, groceries, and utility expenses |

---

## 🔒 Security, Validation & Integrity Guarantees

1. **Strict Zero Double-Booking:** Verified both in the `Allotment` model clean method and the atomic database transaction. No bed can be occupied by more than one active student, and no student can hold more than one active bed.
2. **Atomic Bed Swaps:** Room transfer requests perform atomic releases of old beds and occupation of target beds in a single database transaction.
3. **Role-Based Access Control (RBAC):** Students are strictly blocked from administrative endpoints (e.g. applications review, room allocation, warden creation) and restricted to their personal data.
4. **Pillow Photo Validation:** Profile pictures, problem photos, and dish images are safely processed with Pillow.
5. **Full Test Suite:** 34 comprehensive tests verifying models, views, forms, atomic transfers, double-booking prevention, and permission checks.
