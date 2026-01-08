/**
 * Party Time Texas - Contact Form JavaScript
 * Form validation and UX enhancements
 */
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    
    if (!form) return;
    
    // Form submission handling
    form.addEventListener('submit', function(e) {
        const submitBtn = form.querySelector('.ptt-submit-btn');
        
        // Show loading state
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Submitting...';
            submitBtn.disabled = true;
        }
    });
    
    // Phone number formatting
    const phoneInput = form.querySelector('input[name="phone"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 10) {
                value = value.substring(0, 10);
                e.target.value = '(' + value.substring(0,3) + ') ' + value.substring(3,6) + '-' + value.substring(6,10);
            }
        });
    }
    
    // Set minimum date to today for event date
    const eventDateInput = form.querySelector('input[name="event_date"]');
    if (eventDateInput) {
        const today = new Date().toISOString().split('T')[0];
        eventDateInput.setAttribute('min', today);
    }
    
    // Check for embed mode (iframe)
    if (window.self !== window.top) {
        document.querySelector('.ptt-contact-page')?.classList.add('embed-mode');
    }
});
