// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('AquaGuru - Smart Shrimp Farm Management System');
    
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Confirm delete
    window.confirmDelete = function(message, callback) {
        if (confirm(message || 'Are you sure you want to delete this?')) {
            if (typeof callback === 'function') {
                callback();
            }
            return true;
        }
        return false;
    };
    
    // Format currency
    window.formatCurrency = function(amount) {
        return '$' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    };
    
    // Show toast notification
    window.showToast = function(message, type) {
        const toastHTML = `
            <div class="toast align-items-center text-white bg-${type || 'success'} border-0 show" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        const container = document.createElement('div');
        container.innerHTML = toastHTML;
        document.body.appendChild(container.firstElementChild);
        
        setTimeout(function() {
            const toast = document.querySelector('.toast');
            if (toast) {
                toast.remove();
            }
        }, 3000);
    };
});