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

    /* config and state machine */
    const cfg = {
      MAX_SWIPE: 150,       // px - limit card drag distance
      DECISION: 80,         // px - threshold to trigger action
      FADE_OUT: 200,        // ms - fade-out current card
      FADE_IN : 300,        // ms - fade-in new card
      DELAY   : 300         // ms - wait after swipe / before swap
    };
  
    // URLs injected index.html
    const URLS = window.flickFinderUrls || {};
    const $doc = $(document);
    const $win = $(window);
  
    /* ELEMENT CACHE */
    const els = {
        container   : $('#movieContainer'),
        next        : $('#nextMovieContainer'),
        actions     : $('.action-btn'),
        overlay     : $('#feedback-overlay'),
        filterModal : $('#filtersModal'),
        filterForm  : $('#filterForm'),
        saveBtn     : $('#saveFilters'),
        clearBtn    : $('#clearFilters')
    };
    if (!els.container.length) return; // no movie on page
  
    /* STATE */
    const st = {
        id            : els.actions.first().data('movie-id') ?? null,
        dragging      : false,
        startX        : 0,
        dx            : 0,
        transitioning : false,
        swiped        : false,
        nextMovie     : null
    };
    function shouldBlockLink() {
        return st.dragging || st.swiped || st.transitioning;
    }

    // event delegation to minimize listener
    document.addEventListener('click', function (ev) {
        const link = ev.target.closest('.poster-link');
        if (link && shouldBlockLink()) {
            ev.preventDefault();   // Cancel navigation
            ev.stopPropagation();  // No other handlers
        }
    });
    
    /* helpers */
    const csrf = () => $('input[name="csrfmiddlewaretoken"]').val();
  
    const posterURL = p => p ? `https://image.tmdb.org/t/p/w500${p}` : URLS.noPoster;
  
    const preload = url => { const img = new Image(); img.src = url; };
  
    const feedback = msg => els.overlay
        .text(msg)
        .stop(true, true)
        .fadeIn(200)
        .delay(600)
        .fadeOut(200);
  
    const disableUI = () => {
        st.transitioning = true;
        els.actions.prop('disabled', true);
        els.container.addClass('card-exit');
    };
    const enableUI = () => {
        st.transitioning = false;
        els.actions.prop('disabled', false);
        els.container.removeClass('card-exit dragging');
    };
  
    /* SWIPE */
    const cueL = $('<div class="swipe-cue swipe-left"><i class="fas fa-times"></i></div>').css('opacity',0).appendTo(els.container);
    const cueR = $('<div class="swipe-cue swipe-right"><i class="fas fa-plus"></i></div>').css('opacity',0).appendTo(els.container);
  
    const setTransform = x => els.container.css('transform', `translateX(${x}px) rotate(${x*0.1}deg)`);
  
    const onPointerDown = e => {
        if (st.transitioning) return;
        st.dragging = true;
        st.startX = e.clientX ?? e.touches?.[0]?.clientX;
        st.dx = 0;
        els.container.addClass('dragging');
        e.preventDefault();
    };
    const onPointerMove = e => {
        if (!st.dragging) return;
        const pageX = e.clientX ?? e.touches?.[0]?.clientX;
        st.dx = Math.max(-cfg.MAX_SWIPE, Math.min(cfg.MAX_SWIPE, pageX - st.startX));
        setTransform(st.dx);
        cueL.css('opacity', st.dx < 0 ? Math.min(Math.abs(st.dx)/cfg.DECISION,1) : 0);
        cueR.css('opacity', st.dx > 0 ? Math.min(st.dx/cfg.DECISION,1) : 0);
    };
    const resetCard = () => {
        els.container.css({transition:'transform .25s ease', transform:'translateX(0) rotate(0deg)'});
        cueL.add(cueR).css('opacity',0);
        setTimeout(()=>els.container.css('transition',''),250);
        st.swiped = false;
    };
    const fireAction = a => {
        st.swiped = true; 
        const dir = (a==='skip'||a==='block')?-1:1;
        els.container.css({transition:'transform .3s ease',transform:`translateX(${dir*$win.width()}px) rotate(${dir*30}deg)`});
        setTimeout(()=>$(`.action-btn[data-action="${a}"]`).trigger('click'),300);
    };
    const onPointerUp = () => {
        if (!st.dragging) return;
        st.dragging = false;
        els.container.removeClass('dragging');
        cueL.add(cueR).css('opacity',0);
        if (st.dx > cfg.DECISION) fireAction('watchlist');
        else if (st.dx < -cfg.DECISION) fireAction('skip');
        else resetCard();
    };
    els.container.on('pointerdown', onPointerDown);
    $doc.on('pointermove', onPointerMove).on('pointerup pointercancel', onPointerUp);
  
    /* build / swap cards */
    const buildCard = m => {
        const year = m.release_date?.slice(0,4) || 'N/A';
        const rating = m.vote_average!=null ? m.vote_average.toFixed(1) : 'N/A';
        const overview = m.overview ? (m.overview.length>150?`${m.overview.slice(0,150)}…`:m.overview) : 'No overview available.';
        return `
            <a href="/movie/${m.id}/" class="poster-link">
            <img src="${posterURL(m.poster_path)}" alt="${m.title}" class="movie-poster" draggable="false">
            </a>
            <div class="movie-info">
            <h3>${m.title}</h3>
            <p>${year} | ${rating}/10</p>
            <p class="movie-overview">${overview}</p>
            </div>
            <div class="swipe-cue swipe-left" style="opacity:0;"><i class="fas fa-times"></i></div>
            <div class="swipe-cue swipe-right" style="opacity:0;"><i class="fas fa-plus"></i></div>`;
    };
  
    const prepareNext = m => {
        st.nextMovie = m;
        els.next.html(buildCard(m)).css({opacity:0});
        if (m.poster_path) preload(posterURL(m.poster_path));
    };
    const swapCard = () => {
        els.container.animate({opacity:0}, cfg.FADE_OUT, () => {
            els.container.html(els.next.html()).css({transition:'none',transform:'none',opacity:0})
            .animate({opacity:1}, cfg.FADE_IN, () => {
                els.actions
                    .attr('data-movie-id', st.nextMovie.id)   // update DOM attribute
                    .data('movie-id', st.nextMovie.id);       // update jQuery’s cache
                window.movieSwipe?.updateMovieId?.(st.nextMovie.id);
                st.id = st.nextMovie.id;
                st.nextMovie = null;
                st.swiped = false;
                enableUI();
            });
            els.next.empty();
        });
    };
    const endOfLine = msg => {
        els.container.html(`<div class="no-movies"><h3>End of the Line!</h3><p>${msg||'No more movies found.'}</p></div>`);
        els.actions.hide();
        enableUI();
    };
  
    /* ajax calls */
    const interact = (id, act) => {
        if (!URLS.movieInteraction) return console.error('movieInteraction URL missing');
        $.post(URLS.movieInteraction, {
            movie_id: id,
            interaction_type: act,
            csrfmiddlewaretoken: csrf()
        }).done(res=>{
            const map={watchlist:'Added to Watchlist',heart:'Favorited',skip:'Skipped',block:'Blocked'};
            feedback(map[act]||'Recorded');
            if(res.status==='success' && res.next_movie){prepareNext(res.next_movie);setTimeout(swapCard,cfg.DELAY);} else {endOfLine(res.message);}  
        }).fail(()=>{alert('Error, please try again.');window.movieSwipe?.resetCardPosition?.();enableUI();});
    };
  
    /* button clicks */
    $doc.on('click','.action-btn',function(){
        if(st.transitioning) return;
        const $b=$(this); const act=$b.data('action'); st.id=$b.data('movie-id');
        window.movieSwipe?.animateSwipe?.(act);
        disableUI();
        interact(st.id,act);
    });
  
    /* filters */
    els.saveBtn.on('click',function(){
        if(!URLS.saveFilters){console.error('saveFilters URL missing');return;}
        const $btn=$(this);
        disableUI();
        $btn.html('<i class="fas fa-spinner fa-spin"></i>');
    
        // ensure csrf token present
        const payload=els.filterForm.serializeArray();
        if(!payload.find(f=>f.name==='csrfmiddlewaretoken')){
            payload.push({name:'csrfmiddlewaretoken',value:csrf()});
        }
    
        $.post(URLS.saveFilters,$.param(payload)).done(res=>{
            els.filterModal.modal('hide');
            enableUI();
            $btn.text('Apply Filters');
            if(res.status==='success' && res.next_movie){prepareNext(res.next_movie);swapCard();els.actions.show();} else {endOfLine();}
        }).fail(xhr=>{
            console.error('saveFilters error',xhr.status,xhr.responseText);
            alert('Error saving filters.');
            enableUI();
            $btn.text('Apply Filters');
        });
    });
    els.clearBtn.on('click',()=>{els.filterForm.find('input,select').val('').prop('checked',false);els.saveBtn.click();});
  
    /* swipe */
    window.movieSwipe={
        animateSwipe:a=>{const d=(a==='skip'||a==='block')?-1:1;els.container.css({transition:'transform .3s ease',transform:`translateX(${d*$win.width()}px) rotate(${d*30}deg)`});st.transitioning=true;},
        resetCardPosition:resetCard,
        updateMovieId:id=>{st.id=id;st.transitioning=false;els.container.removeClass('card-exit').css({transform:'none',transition:'none'});}
    };
  
    /* INIT */
    els.container.css('opacity',0).animate({opacity:1},cfg.FADE_IN);
  
})();