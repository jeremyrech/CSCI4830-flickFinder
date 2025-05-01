document.addEventListener('DOMContentLoaded', function() {
    const searchingForm = document.getElementById('navbarSearchForm');
    if (searchingForm) {
        searchingForm.addEventListener('submit', function(e) {
            const searchingInput = this.querySelector('input[name="query"]');
            if (!searchingInput.value.trim()) {
                e.preventDefault();
                searchingInput.classList.add('is-invalid');
                setTimeout(() => searchingInput.classList.remove('is-invalid'), 2000);
            }
        });
    }

    const navbarTog = document.querySelector('.navbar-toggler');
    if (navbarTog) {
        navbarTog.addEventListener('click', function() {
            // delay collapse
            setTimeout(() => {
                const navbarCollapse = document.getElementById('navbarNav');
                // Check if the navbar expanded
                if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                    const searchingInput = document.querySelector('#navbarSearchForm input');
                    if (searchingInput) {
                        searchingInput.focus();
                    }
                }
            }, 300);
        });
    }

    let searchTimeout; // extra cauction 
    const searchingInput = document.querySelector('#navbarSearchForm input[name="query"]');
    if (searchingInput) {
        searchingInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            if (this.value.length > 2) {
                searchTimeout = setTimeout(() => {
                    fetchSuggestions(this.value);
                }, 300); // Debounce delay
            }
        });
    }
});