(() => {
    'use strict';
  
    /* CSRF header */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(c => {
                c = c.trim();
                if (c.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(c.slice(name.length + 1));
                }
            });
        }
        return cookieValue;
    }
    const CSRF_TOKEN = getCookie('csrftoken');
  
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
            }
        }
    });
  
    const API = window.flickFinderUrls || {};
  
    $(function () {
        $(document).on('click', '.movie-actions button', function () {
            const $btn           = $(this);
            const movieId        = $btn.data('movie-id');
            const actionRaw      = $btn.data('action');          // heart / unheart / watchlist …
            const interaction    = actionRaw.replace(/^un/, ''); // heart | watchlist | block …
    
            $btn.prop('disabled', true)
                .addClass('button-loading')
                .html(
                '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Working…'
                );
    
            $.post(API.movieInteraction, { movie_id: movieId, interaction_type: interaction })
            .done(() => location.reload())
            .fail(() => {
                alert('An error occurred. Please try again.');
                $btn.prop('disabled', false).removeClass('button-loading')
                    .html('<i class="fas fa-redo-alt"></i> Retry');
            });
        });
    });
})();