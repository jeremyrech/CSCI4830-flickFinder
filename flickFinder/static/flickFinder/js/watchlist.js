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
        /* remove-from-watchlist */
        $(document).on('click', '.remove-btn', function () {
            const $btn   = $(this);
            const $item  = $btn.closest('.watchlist-item');
            const id     = $btn.data('movie-id');
    
            $item.css({ transition: 'all .3s ease', opacity: 0, transform: 'scale(0.8)' });
    
            $.post(API.unwatchlist, { movie_id: id })
            .done(res => {
                if (res.status === 'success' || res.status === 'not_found') {
                setTimeout(() => {
                    $item.remove();
                    if (!$('.watchlist-item:visible').length) {
                    $('#watchlistGrid').html(
                        '<div class="col-12"><div class="empty-watchlist"><h3>Watchlist is now empty</h3></div></div>'
                    );
                    $('.filter-section').hide();
                    }
                }, 300);
                } else {
                $item.css({ opacity: 1, transform: 'none' });
                alert(res.message || 'Failed to remove item. Please try again.');
                }
            })
            .fail(() => {
                $item.css({ opacity: 1, transform: 'none' });
                alert('An error occurred. Please try again.');
            });
      });
  
      /* search */
      $('#searchWatchlist').on('keyup', function () {
            const term = $(this).val().toLowerCase();
            let found  = false;
    
            $('.watchlist-item').each(function () {
                const match = $(this).data('title').includes(term);
                $(this).toggle(match);
                if (match) found = true;
            });
            $('#noResults').toggle(!found);
      });
  
      /* sort case machine */
      $('#sortWatchlist').on('change', function () {
            const mode  = $(this).val();
            const $grid = $('#watchlistGrid');
            const $it   = $('.watchlist-item');
    
            $it.sort((a, b) => {
            switch (mode) {
                case 'date-desc':   return $(b).data('date')   - $(a).data('date');
                case 'date-asc':    return $(a).data('date')   - $(b).data('date');
                case 'title-asc':   return $(a).data('title').localeCompare($(b).data('title'));
                case 'title-desc':  return $(b).data('title').localeCompare($(a).data('title'));
                case 'rating-desc': return $(b).data('rating') - $(a).data('rating');
                case 'rating-asc':  return $(a).data('rating') - $(b).data('rating');
                default:            return 0;
            }
        });
  
            $it.detach().appendTo($grid).css('opacity', 0);
            $it.each((i, el) =>
            setTimeout(() => $(el).css({ transition: 'opacity .3s ease', opacity: 1 }), i * 50)
            );
        });
    });
})();