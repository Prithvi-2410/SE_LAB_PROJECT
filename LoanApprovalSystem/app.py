"""
Loan Approval System
Educational Demonstration Prototype
Flask Backend with SQLite, Server-Side Validation, Eligibility Assessment, and EMI Calculation.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    g
)

# Configurable Demonstration Eligibility Rules
DEFAULT_ELIGIBILITY_RULES = {
    'min_age': 21,
    'max_age': 60,
    'min_monthly_income': 25000.0,
    'min_credit_score': 650,
    'max_loan_to_income_ratio': 10.0,
}

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename: str) -> bool:
    """Check if the provided filename has an approved extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> dict:
    """
    Calculate monthly EMI, total repayment, and total interest.
    
    Formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    Where:
    - P = principal
    - r = monthly interest rate (annual_interest_rate / 12 / 100)
    - n = tenure in months
    
    Special case:
    If annual_interest_rate == 0:
    EMI = P / n
    """
    principal = float(principal)
    annual_rate = float(annual_interest_rate)
    n = int(tenure_months)

    if n <= 0:
        raise ValueError("Tenure must be greater than zero months.")
    if principal <= 0:
        raise ValueError("Principal loan amount must be positive.")
    if annual_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    if annual_rate == 0.0:
        monthly_emi = round(principal / n, 2)
        total_repayment = round(principal, 2)
        total_interest = 0.0
    else:
        monthly_rate = (annual_rate / 100.0) / 12.0
        factor = (1.0 + monthly_rate) ** n
        emi = (principal * monthly_rate * factor) / (factor - 1.0)
        monthly_emi = round(emi, 2)
        total_repayment = round(monthly_emi * n, 2)
        total_interest = round(total_repayment - principal, 2)

    return {
        'monthly_emi': monthly_emi,
        'total_repayment': total_repayment,
        'total_interest': total_interest
    }


def evaluate_eligibility(
    age: int,
    monthly_income: float,
    credit_score: int,
    loan_amount: float,
    rules: dict = None
) -> tuple[bool, list[str]]:
    """
    Evaluate loan eligibility based on configurable demonstration rules.
    Returns (is_eligible, reasons).
    """
    if rules is None:
        rules = DEFAULT_ELIGIBILITY_RULES

    reasons = []

    # Rule 1: Age boundary
    if age < rules['min_age'] or age > rules['max_age']:
        reasons.append(
            f"Applicant age ({age}) is outside the acceptable range of "
            f"{rules['min_age']} to {rules['max_age']} years."
        )

    # Rule 2: Minimum monthly income
    if monthly_income < rules['min_monthly_income']:
        reasons.append(
            f"Monthly income (₹{monthly_income:,.2f}) is below the minimum "
            f"threshold of ₹{rules['min_monthly_income']:,.2f}."
        )

    # Rule 3: Credit score
    if credit_score < rules['min_credit_score']:
        reasons.append(
            f"Credit score ({credit_score}) does not satisfy the minimum "
            f"qualifying score of {rules['min_credit_score']}."
        )

    # Rule 4: Loan amount to income ratio
    max_loan = monthly_income * rules['max_loan_to_income_ratio']
    if loan_amount > max_loan:
        reasons.append(
            f"Requested loan amount (₹{loan_amount:,.2f}) exceeds the maximum "
            f"permissible limit of ₹{max_loan:,.2f} "
            f"({int(rules['max_loan_to_income_ratio'])}x monthly income)."
        )

    if not reasons:
        return True, ["Applicant meets all configurable demonstration eligibility criteria."]
    return False, reasons


def validate_application_form(form_data: dict, files: dict) -> tuple[dict, dict]:
    """
    Validate all submitted application form fields and uploaded file.
    Returns (validated_data, errors).
    """
    errors = {}
    validated = {}

    # Full Name
    full_name = form_data.get('full_name', '').strip()
    if not full_name:
        errors['full_name'] = "Full name is required."
    elif len(full_name) < 2 or len(full_name) > 100:
        errors['full_name'] = "Full name must be between 2 and 100 characters."
    elif not all(c.isalpha() or c in " .'-" for c in full_name):
        errors['full_name'] = "Full name contains invalid characters."
    else:
        validated['full_name'] = full_name

    # Age (Validation verifies plausible human age 18-100; eligibility assesses 21-60)
    raw_age = form_data.get('age', '').strip()
    try:
        age = int(raw_age)
        if age < 18 or age > 100:
            errors['age'] = "Age must be a valid number between 18 and 100."
        else:
            validated['age'] = age
    except (ValueError, TypeError):
        errors['age'] = "Please enter a valid whole number for age."

    # Monthly Income
    raw_income = form_data.get('monthly_income', '').strip()
    try:
        income = float(raw_income)
        if income <= 0:
            errors['monthly_income'] = "Monthly income must be greater than zero."
        elif income > 100_000_000:
            errors['monthly_income'] = "Monthly income exceeds realistic limits."
        else:
            validated['monthly_income'] = income
    except (ValueError, TypeError):
        errors['monthly_income'] = "Please enter a valid positive number for monthly income."

    # Credit Score (Credit bureau standard: 300 to 900)
    raw_credit = form_data.get('credit_score', '').strip()
    try:
        credit = int(raw_credit)
        if credit < 300 or credit > 900:
            errors['credit_score'] = "Credit score must be between 300 and 900."
        else:
            validated['credit_score'] = credit
    except (ValueError, TypeError):
        errors['credit_score'] = "Please enter a valid whole number for credit score (300-900)."

    # Loan Amount
    raw_loan = form_data.get('loan_amount', '').strip()
    try:
        loan = float(raw_loan)
        if loan <= 0:
            errors['loan_amount'] = "Loan amount must be greater than zero."
        elif loan > 100_000_000:
            errors['loan_amount'] = "Loan amount exceeds maximum limit of ₹10,00,00,000."
        else:
            validated['loan_amount'] = loan
    except (ValueError, TypeError):
        errors['loan_amount'] = "Please enter a valid positive number for loan amount."

    # Annual Interest Rate
    raw_rate = form_data.get('interest_rate', '').strip()
    try:
        rate = float(raw_rate)
        if rate < 0:
            errors['interest_rate'] = "Interest rate cannot be negative."
        elif rate > 100:
            errors['interest_rate'] = "Interest rate cannot exceed 100%."
        else:
            validated['interest_rate'] = rate
    except (ValueError, TypeError):
        errors['interest_rate'] = "Please enter a valid interest rate (0% or higher)."

    # Tenure in Months
    raw_tenure = form_data.get('tenure_months', '').strip()
    try:
        tenure = int(raw_tenure)
        if tenure < 1 or tenure > 360:
            errors['tenure_months'] = "Tenure must be between 1 and 360 months (up to 30 years)."
        else:
            validated['tenure_months'] = tenure
    except (ValueError, TypeError):
        errors['tenure_months'] = "Please enter a valid tenure in months (1-360)."

    # Document Upload Validation
    doc = files.get('document')
    if not doc or doc.filename == '':
        errors['document'] = "Supporting document upload is required."
    elif not allowed_file(doc.filename):
        errors['document'] = "Unsupported document format. Allowed types: PDF, JPG, JPEG, PNG."
    else:
        # Check size if available via stream/content-length
        doc.seek(0, os.SEEK_END)
        size = doc.tell()
        doc.seek(0)
        if size == 0:
            errors['document'] = "Uploaded document cannot be empty (0 bytes)."
        elif size > MAX_UPLOAD_SIZE_BYTES:
            errors['document'] = "Document exceeds the maximum permissible size of 5 MB."
        else:
            validated['document'] = doc

    return validated, errors


def get_db(db_path: str):
    """Obtain a SQLite database connection with row-factory."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def init_db(db_path: str):
    """Initialize database tables with parameterized schema."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            monthly_income REAL NOT NULL,
            credit_score INTEGER NOT NULL,
            loan_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            tenure_months INTEGER NOT NULL,
            document_filename TEXT NOT NULL,
            document_original_name TEXT NOT NULL,
            is_eligible INTEGER NOT NULL,
            eligibility_reason TEXT NOT NULL,
            monthly_emi REAL NOT NULL,
            total_repayment REAL NOT NULL,
            total_interest REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_app(test_config=None) -> Flask:
    """Application factory for the Loan Approval System."""
    app = Flask(__name__, instance_relative_config=True)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'loan-approval-system-dev-secret-2026'),
        DATABASE=os.path.join(app.instance_path, 'loan.db'),
        UPLOAD_FOLDER=os.path.join(basedir, 'uploads'),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE_BYTES,
    )

    if test_config:
        app.config.update(test_config)

    # Ensure required runtime folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize SQLite database
    init_db(app.config['DATABASE'])

    @app.errorhandler(413)
    def file_too_large(error):
        flash("The uploaded file exceeds the 5 MB maximum allowed size.", "danger")
        return redirect(url_for('apply_loan'))

    @app.route('/')
    def index():
        return render_template('index.html', rules=DEFAULT_ELIGIBILITY_RULES)

    @app.route('/apply', methods=['GET', 'POST'])
    def apply_loan():
        if request.method == 'GET':
            return render_template('application.html', form_data={}, errors={})

        # POST submission
        validated_data, errors = validate_application_form(request.form, request.files)
        if errors:
            return render_template(
                'application.html',
                form_data=request.form,
                errors=errors
            ), 400

        # Process valid application
        doc = validated_data['document']
        original_name = secure_filename(doc.filename) or "document.bin"
        unique_prefix = uuid.uuid4().hex[:12]
        stored_filename = f"{unique_prefix}_{original_name}"
        saved_file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)

        # Generate unique application ID
        today_str = datetime.now().strftime('%Y%m%d')
        app_suffix = uuid.uuid4().hex[:6].upper()
        application_id = f"APP-{today_str}-{app_suffix}"

        # Evaluate eligibility
        is_eligible, reasons = evaluate_eligibility(
            age=validated_data['age'],
            monthly_income=validated_data['monthly_income'],
            credit_score=validated_data['credit_score'],
            loan_amount=validated_data['loan_amount']
        )
        eligibility_reason_text = " | ".join(reasons)

        # Calculate EMI
        emi_details = calculate_emi(
            principal=validated_data['loan_amount'],
            annual_interest_rate=validated_data['interest_rate'],
            tenure_months=validated_data['tenure_months']
        )

        # Save document and record transaction in SQLite
        try:
            doc.save(saved_file_path)

            conn = get_db(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO loan_applications (
                    application_id, full_name, age, monthly_income, credit_score,
                    loan_amount, interest_rate, tenure_months, document_filename,
                    document_original_name, is_eligible, eligibility_reason,
                    monthly_emi, total_repayment, total_interest, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                validated_data['full_name'],
                validated_data['age'],
                validated_data['monthly_income'],
                validated_data['credit_score'],
                validated_data['loan_amount'],
                validated_data['interest_rate'],
                validated_data['tenure_months'],
                stored_filename,
                original_name,
                1 if is_eligible else 0,
                eligibility_reason_text,
                emi_details['monthly_emi'],
                emi_details['total_repayment'],
                emi_details['total_interest'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()
            conn.close()

        except Exception as exc:
            # Clean up partial uploaded file if DB operation fails
            if os.path.exists(saved_file_path):
                try:
                    os.remove(saved_file_path)
                except OSError:
                    pass
            flash("An unexpected error occurred while saving your application. Please try again.", "danger")
            return render_template(
                'application.html',
                form_data=request.form,
                errors={'general': "Unable to persist application. Partial files cleaned up."}
            ), 500

        return redirect(url_for('loan_result', application_id=application_id))

    @app.route('/result/<application_id>')
    def loan_result(application_id: str):
        conn = get_db(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loan_applications WHERE application_id = ?", (application_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            abort(404)

        application = dict(row)
        # Parse reason list
        application['reasons_list'] = [r.strip() for r in application['eligibility_reason'].split(' | ') if r.strip()]

        return render_template('result.html', app_data=application)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
