// MedTrack - Client-side Interactive Functionality
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 5s
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Password Match Validation in Register Form
    const regForm = document.querySelector('#register-form');
    if (regForm) {
        const password = regForm.querySelector('input[name="password"]');
        const confirmPassword = regForm.querySelector('input[name="confirm_password"]');
        regForm.addEventListener('submit', function (e) {
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match. Please verify.');
                confirmPassword.focus();
            }
        });
    }

    // Appointment Date validation (Prevent past dates)
    const apptDateInput = document.querySelector('#appointment_date');
    if (apptDateInput) {
        const today = new Date().toISOString().split('T')[0];
        apptDateInput.setAttribute('min', today);
    }

    // Mark notification as read via AJAX
    document.querySelectorAll('.btn-mark-read').forEach(function (btn) {
        btn.addEventListener('click', async function (e) {
            e.preventDefault();
            const notifId = this.getAttribute('data-id');
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                              document.querySelector('input[name="csrf_token"]')?.value;

            try {
                const res = await fetch(`/api/notifications/${notifId}/read`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });
                if (res.ok) {
                    const row = document.getElementById(`notif-row-${notifId}`);
                    if (row) {
                        row.classList.remove('table-light', 'fw-bold');
                        row.classList.add('text-muted');
                        this.remove();
                    }
                    const badge = document.getElementById('notif-badge');
                    if (badge) {
                        let count = parseInt(badge.innerText, 10);
                        if (count > 1) {
                            badge.innerText = count - 1;
                        } else {
                            badge.remove();
                        }
                    }
                }
            } catch (err) {
                console.error('Failed to mark notification as read', err);
            }
        });
    });

    // Submit button loading spinner
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]:not(.no-spin)');
            if (submitBtn && form.checkValidity()) {
                const origText = submitBtn.innerHTML;
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...`;
                }, 10);
                // Restore after timeout in case form is invalid or handled via AJAX
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origText;
                }, 8000);
            }
        });
    });
});
