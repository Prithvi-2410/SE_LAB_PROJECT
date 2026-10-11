"""
Automated Test Suite for Loan Approval System
Includes Unit Tests, Integration Tests, Validation & Upload Security Tests.
"""

import io
import os
import shutil
import tempfile
import unittest
import sqlite3

from app import (
    create_app,
    calculate_emi,
    evaluate_eligibility,
    allowed_file,
    DEFAULT_ELIGIBILITY_RULES,
    MAX_UPLOAD_SIZE_BYTES
)


class LoanApprovalSystemTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated test environment with temporary database and uploads."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, 'test_loan.db')
        self.test_uploads = os.path.join(self.test_dir, 'test_uploads')

        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.test_db,
            'UPLOAD_FOLDER': self.test_uploads,
            'SECRET_KEY': 'test-secret-key-loan-pbl',
        })
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up temporary test artifacts."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. Home page loads
    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Loan Approval System", response.data)
        self.assertIn(b"Start Application", response.data)

    # 2. Application form loads
    def test_application_form_loads(self):
        response = self.client.get('/apply')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Loan Application Form", response.data)
        self.assertIn(b"Full Name", response.data)
        self.assertIn(b"Monthly Income", response.data)

    # 3. Valid application submission
    def test_valid_application_submission(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 fake pdf data"), 'id_proof.pdf')
        data = {
            'full_name': 'Aarav Sharma',
            'age': '28',
            'monthly_income': '50000',
            'credit_score': '750',
            'loan_amount': '200000',
            'interest_rate': '10.5',
            'tenure_months': '24',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application Eligible", response.data)
        self.assertIn(b"Aarav Sharma", response.data)
        self.assertIn(b"APP-", response.data)

    # 4. Missing required fields
    def test_missing_required_fields(self):
        data = {
            'full_name': '',
            'age': '',
            'monthly_income': '',
            'credit_score': '',
            'loan_amount': '',
            'interest_rate': '',
            'tenure_months': ''
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Full name is required", response.data)
        self.assertIn(b"Please enter a valid whole number for age", response.data)

    # 5. Invalid age
    def test_invalid_age(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 test"), 'proof.pdf')
        data = {
            'full_name': 'Invalid Age User',
            'age': '15',  # Outside valid input range (18-100)
            'monthly_income': '40000',
            'credit_score': '700',
            'loan_amount': '100000',
            'interest_rate': '9.0',
            'tenure_months': '12',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Age must be a valid number between 18 and 100", response.data)

    # 6. Low monthly income (Eligibility rejection)
    def test_low_monthly_income_eligibility_rejection(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 income proof"), 'income.pdf')
        data = {
            'full_name': 'Sunita Rao',
            'age': '30',
            'monthly_income': '18000',  # Below Rs. 25,000 threshold
            'credit_score': '720',
            'loan_amount': '50000',
            'interest_rate': '10.0',
            'tenure_months': '12',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application Not Eligible", response.data)
        self.assertIn(b"below the minimum threshold", response.data)

    # 7. Invalid credit score format
    def test_invalid_credit_score(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 dummy"), 'id.pdf')
        data = {
            'full_name': 'Test User',
            'age': '29',
            'monthly_income': '40000',
            'credit_score': '150',  # Outside valid bureau range 300-900
            'loan_amount': '100000',
            'interest_rate': '9.0',
            'tenure_months': '12',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Credit score must be between 300 and 900", response.data)

    # 8. Eligibility rejection (Loan to income multiplier)
    def test_eligibility_rejection_loan_multiplier(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 dummy"), 'id.pdf')
        data = {
            'full_name': 'Rahul Verma',
            'age': '32',
            'monthly_income': '30000',
            'credit_score': '750',
            'loan_amount': '500000',  # 500,000 > 10 * 30,000 (300,000)
            'interest_rate': '11.0',
            'tenure_months': '36',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application Not Eligible", response.data)
        self.assertIn(b"exceeds the maximum permissible limit", response.data)

    # 9. Unsupported document extension
    def test_unsupported_document_extension(self):
        dummy_file = (io.BytesIO(b"malicious script content"), 'script.exe')
        data = {
            'full_name': 'Sneha Patel',
            'age': '27',
            'monthly_income': '45000',
            'credit_score': '710',
            'loan_amount': '150000',
            'interest_rate': '8.5',
            'tenure_months': '24',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Unsupported document format", response.data)

    # 10. Empty document submission
    def test_empty_document_submission(self):
        empty_file = (io.BytesIO(b""), 'empty.pdf')
        data = {
            'full_name': 'Sneha Patel',
            'age': '27',
            'monthly_income': '45000',
            'credit_score': '710',
            'loan_amount': '150000',
            'interest_rate': '8.5',
            'tenure_months': '24',
            'document': empty_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Uploaded document cannot be empty", response.data)

    # 11. File larger than 5 MB
    def test_file_larger_than_5mb(self):
        oversized_content = b"0" * (MAX_UPLOAD_SIZE_BYTES + 1024)  # 5 MB + 1 KB
        oversized_file = (io.BytesIO(oversized_content), 'large_document.pdf')
        data = {
            'full_name': 'Big File User',
            'age': '30',
            'monthly_income': '60000',
            'credit_score': '750',
            'loan_amount': '200000',
            'interest_rate': '8.0',
            'tenure_months': '24',
            'document': oversized_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertTrue(response.status_code in [400, 302, 413])
        # Verify it wasn't saved in database
        conn = sqlite3.connect(self.test_db)
        count = conn.execute("SELECT count(*) FROM loan_applications WHERE full_name = 'Big File User'").fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    # 12. EMI with normal interest rate (Standard Formula Verification)
    def test_emi_with_normal_interest_rate(self):
        # Principal = 100,000, Annual Rate = 12% (1% monthly), Tenure = 12 months
        # Expected EMI: 100000 * 0.01 * (1.01^12) / (1.01^12 - 1) = 8884.88
        res = calculate_emi(principal=100000.0, annual_interest_rate=12.0, tenure_months=12)
        self.assertEqual(res['monthly_emi'], 8884.88)
        self.assertEqual(res['total_repayment'], 106618.56)
        self.assertEqual(res['total_interest'], 6618.56)

    # 13. EMI with zero interest rate
    def test_emi_with_zero_interest(self):
        res = calculate_emi(principal=120000.0, annual_interest_rate=0.0, tenure_months=12)
        self.assertEqual(res['monthly_emi'], 10000.0)
        self.assertEqual(res['total_repayment'], 120000.0)
        self.assertEqual(res['total_interest'], 0.0)

    # 14. Database persistence and parameterized storage
    def test_database_persistence(self):
        dummy_file = (io.BytesIO(b"%PDF-1.4 db test"), 'statement.pdf')
        data = {
            'full_name': 'Kavita Krishnan',
            'age': '35',
            'monthly_income': '70000',
            'credit_score': '780',
            'loan_amount': '350000',
            'interest_rate': '9.5',
            'tenure_months': '36',
            'document': dummy_file
        }
        response = self.client.post('/apply', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 302)

        # Inspect database record directly
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loan_applications WHERE full_name = ?", ('Kavita Krishnan',))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row['age'], 35)
        self.assertEqual(row['monthly_income'], 70000.0)
        self.assertEqual(row['credit_score'], 780)
        self.assertEqual(row['loan_amount'], 350000.0)
        self.assertEqual(row['is_eligible'], 1)
        self.assertTrue(row['application_id'].startswith("APP-"))
        self.assertTrue(row['document_filename'].endswith("_statement.pdf"))

    # 15. Correct calculation of total repayment and total interest
    def test_correct_calculation_of_total_repayment_and_interest(self):
        res = calculate_emi(principal=500000.0, annual_interest_rate=8.5, tenure_months=60)
        # Verify mathematical identity: total_repayment = emi * tenure, total_interest = total_repayment - principal
        self.assertAlmostEqual(res['total_repayment'], round(res['monthly_emi'] * 60, 2), places=2)
        self.assertAlmostEqual(res['total_interest'], round(res['total_repayment'] - 500000.0, 2), places=2)
        self.assertGreater(res['monthly_emi'], 0)
        self.assertGreater(res['total_interest'], 0)


if __name__ == '__main__':
    unittest.main()
