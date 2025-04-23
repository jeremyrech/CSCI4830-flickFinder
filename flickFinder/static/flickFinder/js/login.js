(() => {
    'use strict';
    $(function () {
        const $tabs      = $('.tab-btn');
        const $sections  = $('.form-section');
    
        $('#loginTab').on('click', () => {
            $tabs.removeClass('active');
            $('#loginTab').addClass('active');
            $sections.removeClass('active');
            $('#loginForm').addClass('active');
        });
    
        $('#signupTab').on('click', () => {
            $tabs.removeClass('active');
            $('#signupTab').addClass('active');
            $sections.removeClass('active');
            $('#signupForm').addClass('active');
        });
    });
})();