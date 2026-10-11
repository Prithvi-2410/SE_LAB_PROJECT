/**
 * Loan Approval System - Client-Side Enhancements
 * Live EMI preview, client-side validation hints, and file upload size/type checking.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements for Live EMI Preview
    const loanAmountInput = document.getElementById('loan_amount');
    const interestRateInput = document.getElementById('interest_rate');
    const tenureMonthsInput = document.getElementById('tenure_months');

    const previewEmi = document.getElementById('previewEmi');
    const previewPrincipal = document.getElementById('previewPrincipal');
    const previewInterest = document.getElementById('previewInterest');
    const previewTotal = document.getElementById('previewTotal');

    // Document File Input
    const documentInput = document.getElementById('document');
    const loanForm = document.getElementById('loanForm');

    const formatCurrency = (val) => {
        return '₹' + Number(val).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    };

    /**
     * Compute EMI preview
     * Formula: EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
     */
    const updateEmiPreview = () => {
        if (!previewEmi || !loanAmountInput || !interestRateInput || !tenureMonthsInput) {
            return;
        }

        const P = parseFloat(loanAmountInput.value) || 0;
        const annualRate = parseFloat(interestRateInput.value) || 0;
        const n = parseInt(tenureMonthsInput.value, 10) || 0;

        if (P <= 0 || n <= 0 || annualRate < 0) {
            previewEmi.textContent = '₹0.00';
            previewPrincipal.textContent = formatCurrency(P > 0 ? P : 0);
            previewInterest.textContent = '₹0.00';
            previewTotal.textContent = formatCurrency(P > 0 ? P : 0);
            return;
        }

        let emi = 0;
        let totalRepayment = 0;
        let totalInterest = 0;

        if (annualRate === 0) {
            emi = P / n;
            totalRepayment = P;
            totalInterest = 0;
        } else {
            const r = (annualRate / 100) / 12;
            const factor = Math.pow(1 + r, n);
            emi = (P * r * factor) / (factor - 1);
            totalRepayment = emi * n;
            totalInterest = totalRepayment - P;
        }

        previewEmi.textContent = formatCurrency(emi);
        previewPrincipal.textContent = formatCurrency(P);
        previewInterest.textContent = formatCurrency(Math.max(0, totalInterest));
        previewTotal.textContent = formatCurrency(totalRepayment);
    };

    if (loanAmountInput) {
        loanAmountInput.addEventListener('input', updateEmiPreview);
    }
    if (interestRateInput) {
        interestRateInput.addEventListener('input', updateEmiPreview);
    }
    if (tenureMonthsInput) {
        tenureMonthsInput.addEventListener('input', updateEmiPreview);
    }

    // Trigger initial calculation if form has repopulated values
    updateEmiPreview();

    // Client-side file size and extension pre-validation
    const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
    const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png'];

    if (documentInput) {
        documentInput.addEventListener('change', () => {
            const file = documentInput.files[0];
            if (!file) return;

            const ext = file.name.split('.').pop().toLowerCase();
            
            // Check extension
            if (!ALLOWED_EXTENSIONS.includes(ext)) {
                alert(`Unsupported file type (.${ext}). Please select a PDF, JPG, JPEG, or PNG document.`);
                documentInput.value = '';
                return;
            }

            // Check size
            if (file.size > MAX_FILE_SIZE_BYTES) {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                alert(`File is too large (${sizeMB} MB). Maximum allowed size is 5 MB.`);
                documentInput.value = '';
                return;
            }

            if (file.size === 0) {
                alert('The selected file is empty (0 bytes). Please select a valid document.');
                documentInput.value = '';
                return;
            }
        });
    }
});
