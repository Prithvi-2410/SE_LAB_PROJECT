# Loan Approval System (College PBL Individual Project)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-15%20Passed-brightgreen.svg)]()
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)]()

A full-stack, secure, web-based prototype developed for a College Problem-Based Learning (PBL) software engineering curriculum. The system demonstrates server-side validation, document upload handling, configurable institutional eligibility assessment, and mathematical EMI calculation with transactional SQLite persistence.

> **Academic Prototype Notice:** This system is built strictly for educational demonstration. Sample eligibility rules and EMI calculations illustrate institutional underwriting workflows and must never be represented as live bank policies or actual loan approval decisions. Real sensitive credentials (such as Aadhaar, PAN, or bank credentials) are never requested or stored.

---

## 1. System Architecture & Modules

The system is organized into two core functional modules:

### Module 1: Loan Application and Document Upload
- **Responsive Application Form:** Collects applicant identity and financial parameters (Full Name, Age, Monthly Income, Credit Score, Loan Amount, Interest Rate, and Tenure).
- **Server-Side Validation:** Rigid verification of boundaries (e.g., standard credit score range 300–900, human age limits 18–100, positive currency amounts).
- **Safe Document Upload:**
  - Allowed file types: `PDF`, `JPG`, `JPEG`, `PNG`.
  - Maximum upload size strictly capped at **5 MB** (`MAX_CONTENT_LENGTH`).
  - Secure, collision-resistant storage via UUID-prefixed filenames (`uuid4().hex[:12] + "_" + secure_filename`).
  - Stored inside an isolated `uploads/` directory with no public execution permissions.
  - Transactional error safety: Automatic rollback and removal of uploaded files if the database persistence step encounters an error.
- **Unique Application Identifier:** Every valid submission receives an alphanumeric reference code (e.g. `APP-20261011-A8F3K9`).
- **Database Storage:** Automatic SQLite schema creation using parameterized SQL queries to prevent SQL injection.

### Module 2: Loan Eligibility and EMI Calculation
- **Configurable Demonstration Rules:**
  - **Age:** 21 – 60 years.
  - **Monthly Income:** &ge; ₹25,000.
  - **Credit Score:** &ge; 650 (CIBIL benchmark).
  - **Max Loan Limit:** &le; 10&times; monthly income.
- **Clear Separation:** Malformed input triggers immediate **Validation Errors** (HTTP 400), whereas well-formed submissions that violate underwriting guidelines produce an **Ineligible Result** with explicit policy explanations.
- **Accurate EMI Calculation:**
  $$\text{EMI} = \frac{P \times r \times (1 + r)^n}{(1 + r)^n - 1}$$
  - $P$ = Principal loan amount
  - $r$ = Monthly interest rate ($\text{Annual Rate} / 12 / 100$)
  - $n$ = Number of monthly installments
  - **Zero-Interest Support:** Separate calculation path ($EMI = P / n$) for interest-free promotional schemes.
  - Calculates and displays Monthly EMI, Total Repayment, and Total Interest Payable rounded to two decimal places.

---

## 2. Technology Stack

- **Backend:** Python 3.13 / 3.11, Flask 3.1, Werkzeug
- **Frontend:** Semantic HTML5, CSS3 (Modern Responsive Flexbox/Grid, Inter typography), Vanilla JavaScript (live EMI calculator and file pre-validation)
- **Database:** SQLite 3 (transactional, parameterized)
- **Testing:** Python `unittest` and `pytest`
- **Project Tracking:** Jira (Project Key: `KAN`)

---

## 3. Project Directory Structure

```
LoanApprovalSystem/
│
├── app.py                     # Flask application factory, routes, validation, and calculations
├── requirements.txt           # Core application and testing dependencies
├── README.md                  # Comprehensive technical documentation
├── PROJECT_PROGRESS.md        # Jira tracking, actual timeline, and test verification log
├── .gitignore                 # Excludes venv, uploads, db instances, and cache
│
├── templates/
│   ├── index.html             # Landing page with hero section & eligibility rules
│   ├── application.html       # Application form with live EMI calculator sidebar
│   └── result.html            # Outcome banner, eligibility reasons & repayment summary
│
├── static/
│   ├── style.css              # Custom responsive stylesheet
│   └── script.js              # Live EMI calculations and client-side upload checks
│
├── tests/
│   └── test_app.py            # 15 automated test cases (unit & integration)
│
├── uploads/                   # Secure storage for uploaded documents (gitignored)
│   └── .gitkeep
│
└── instance/                  # Local SQLite database directory (gitignored)
    ├── .gitkeep
    └── loan.db                # Auto-initialized SQLite database
```

---

## 4. Setup and Installation

### Step 1: Navigate to Project Directory
```powershell
cd LoanApprovalSystem
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on Windows (Command Prompt)
.\venv\Scripts\activate.bat

# Activate on Linux / macOS
source venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 5. Running the Application

To start the local development server:
```powershell
python app.py
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

- **Home Page:** `http://127.0.0.1:5000/`
- **Application Form:** `http://127.0.0.1:5000/apply`
- **Result Page:** Accessible upon submitting an application (e.g. `http://127.0.0.1:5000/result/APP-YYYYMMDD-XXXXXX`)

---

## 6. Automated Testing

The project includes an isolated test suite that runs against a temporary database and temporary upload directory, ensuring your local working database is never modified during tests.

### Running Tests with pytest:
```powershell
pytest tests/test_app.py -v
```

### Running Tests with Python unittest:
```powershell
python -m unittest discover tests
```

### Verified Test Cases:
| # | Test Name | Purpose / Assertion | Result |
|---|-----------|---------------------|--------|
| 1 | `test_home_page_loads` | Confirms landing page loads with HTTP 200 | **PASSED** |
| 2 | `test_application_form_loads` | Confirms loan application form loads with HTTP 200 | **PASSED** |
| 3 | `test_valid_application_submission` | Verifies end-to-end form submission, redirect, and persistence | **PASSED** |
| 4 | `test_missing_required_fields` | Validates rejection of empty required form fields (HTTP 400) | **PASSED** |
| 5 | `test_invalid_age` | Verifies boundary validation on underage/overage input (<18 or >100) | **PASSED** |
| 6 | `test_low_monthly_income_eligibility_rejection` | Verifies underwriting rejection when income < ₹25,000 | **PASSED** |
| 7 | `test_invalid_credit_score` | Enforces standard credit score range (300 to 900) | **PASSED** |
| 8 | `test_eligibility_rejection_loan_multiplier` | Rejects applications exceeding 10x monthly income | **PASSED** |
| 9 | `test_unsupported_document_extension` | Blocks unsupported extensions (.exe, .txt, etc.) | **PASSED** |
| 10 | `test_empty_document_submission` | Prevents upload of 0-byte corrupted files | **PASSED** |
| 11 | `test_file_larger_than_5mb` | Enforces 5 MB upload ceiling | **PASSED** |
| 12 | `test_emi_with_normal_interest_rate` | Mathematically verifies EMI, total repayment, and total interest | **PASSED** |
| 13 | `test_emi_with_zero_interest` | Tests zero-interest promotional repayment formula | **PASSED** |
| 14 | `test_database_persistence` | Direct SQLite inspection of stored records and UUID filenames | **PASSED** |
| 15 | `test_correct_calculation_of_total_repayment_and_interest` | Verifies mathematical consistency of EMI amortizations | **PASSED** |

---

## 7. Security and Reliability Safeguards

1. **Upload Sanitation & Collision Resistance:** Original filenames are sanitized using `werkzeug.utils.secure_filename` and prepended with random 12-character UUID hashes to prevent filesystem collisions and path traversal attacks.
2. **Execution Prevention:** Documents are stored outside the public `static/` directory and are never served or executed directly.
3. **Database Integrity:** SQLite queries use parameterized placeholders (`?`) to neutralize SQL injection vulnerabilities.
4. **Transaction Cleanup:** If any failure occurs during database insertion, partial uploaded files are automatically unlinked and cleaned up.
5. **Data Privacy:** Sensitive identity documents (e.g. Aadhaar, PAN) and financial credentials are never collected.

---

## 8. Academic Demonstration Notes & Limitations

- **Demonstration Scope:** Underwriting decisions are simulated via configurable rules and do not integrate real-time credit bureaus (CIBIL/Experian).
- **Environment:** Designed for local development and academic evaluation. In enterprise deployment, a dedicated WSGI server (Gunicorn/Waitress) and a PostgreSQL database cluster would be configured.
