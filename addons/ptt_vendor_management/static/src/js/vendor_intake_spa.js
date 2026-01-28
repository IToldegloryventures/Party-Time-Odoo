// vendor_intake_spa.js - Multi-step wizard logic for vendor intake form

document.addEventListener('DOMContentLoaded', function() {
    var steps = document.querySelectorAll('.form-step');
    var navLinks = document.querySelectorAll('#formSteps .nav-link');
    var currentStep = 1;
    function showStep(step) {
        steps.forEach(function(s) {
            s.classList.add('d-none');
            if (parseInt(s.getAttribute('data-step')) === step) {
                s.classList.remove('d-none');
            }
        });
        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (parseInt(link.getAttribute('data-step')) === step) {
                link.classList.add('active');
            }
        });
        currentStep = step;
    }
    document.querySelectorAll('.next-step').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (currentStep < steps.length) {
                showStep(currentStep + 1);
            }
        });
    });
    document.querySelectorAll('.prev-step').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (currentStep > 1) {
                showStep(currentStep - 1);
            }
        });
    });
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            var step = parseInt(link.getAttribute('data-step'));
            showStep(step);
        });
    });
    showStep(1);
    // TODO: Add dynamic contact/service/document logic and review summary
});
