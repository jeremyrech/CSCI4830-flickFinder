document.addEventListener('DOMContentLoaded', () => {
    // Get movie container
    const movieContainer = document.getElementById('movieContainer');
    if (!movieContainer) return;

    // Configuration
    const MAX_SWIPE_DISTANCE = 150; // Max in pixels card can be dragged
    const DECISION_THRESHOLD = 80; // Dist threshold to trigger a decision
    
    // State variables
    let isDragging = false;
    let startX = 0;
    let currentX = 0;
    let movieId = null;
    let isInTransition = false;
    let hasSwiped = false; // Track if a swipe happened to prevent nav (the click thing was annoying)
    
    // Get movie ID from the action buttons
    const actionBtn = document.querySelector('.action-btn');
    if (actionBtn) {
        movieId = actionBtn.dataset.movieId;
    }
    
    // Add visual cue elements for swipe direction
    const leftCue = document.createElement('div');
    leftCue.className = 'swipe-cue swipe-left';
    leftCue.innerHTML = '<i class="fas fa-times"></i>'; // I just used the same icons as the buttons
    leftCue.style.opacity = 0; // Initially hidden
    
    const rightCue = document.createElement('div');
    rightCue.className = 'swipe-cue swipe-right';
    rightCue.innerHTML = '<i class="fas fa-plus"></i>';
    rightCue.style.opacity = 0; // Initially hidden
    
    movieContainer.appendChild(leftCue);
    movieContainer.appendChild(rightCue);
    
    // Prevent navigation after swiping
    function preventNavigation(e) {
        if (isDragging || hasSwiped || isInTransition) {
            e.preventDefault();
        }
    }
    
    // Apply event listeners to prevent navigation
    function setupNavigationPrevention() {
        const posterLink = movieContainer.querySelector('.poster-link');
        if (posterLink) {
            posterLink.addEventListener('click', preventNavigation);
            
            // Disable default drag behavior on the image
            const posterImage = posterLink.querySelector('img');
            if (posterImage) {
                posterImage.draggable = false;
            }
        }
    }
    
    // Init
    setupNavigationPrevention();
    
    // Event Listeners for dragging
    movieContainer.addEventListener('mousedown', startDrag); // not direction, mouse1 down
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag); // mouse1 up
    
    // I don't know if we want this but it was in the library so we get it now
    movieContainer.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);
    
    // Drag Start
    function startDrag(e) {
        if (isInTransition) return; // Don't start new drag during transition (weird things)
        
        isDragging = true;
        startX = e.clientX;
        currentX = 0;
        
        // Add visual feedback, expandable
        movieContainer.classList.add('dragging');
        
        // Prevent default behavior
        e.preventDefault();
    }
    
    // Touch Start
    function handleTouchStart(e) {
        if (isInTransition) return; // Don't start new drag during transition
        
        if (e.touches.length === 1) {
            isDragging = true;
            startX = e.touches[0].clientX;
            currentX = 0;
            
            // Add visual feedback, expandable too
            movieContainer.classList.add('dragging');
        }
    }
    
    // Drag
    function drag(e) {
        if (!isDragging) return;
        
        const pageX = e.clientX;
        updateDragPosition(pageX);
    }
    
    // Touch Move
    function handleTouchMove(e) {
        if (!isDragging || e.touches.length !== 1) return;
        
        const pageX = e.touches[0].clientX;
        updateDragPosition(pageX);
        
        // Prevent scrolling when dragging
        e.preventDefault();
    }
    
    // Common function to update position during drag
    function updateDragPosition(pageX) {
        // Calculate how far we've moved
        currentX = pageX - startX;
        
        // Limit the drag distance
        if (currentX > MAX_SWIPE_DISTANCE) currentX = MAX_SWIPE_DISTANCE;
        if (currentX < -MAX_SWIPE_DISTANCE) currentX = -MAX_SWIPE_DISTANCE;
        
        // Apply transformation
        movieContainer.style.transform = `translateX(${currentX}px) rotate(${currentX * 0.1}deg)`;
        
        // Update opacity of direction cues based on drag distance
        const leftOpacity = currentX < 0 ? Math.min(Math.abs(currentX) / DECISION_THRESHOLD, 1) : 0;
        const rightOpacity = currentX > 0 ? Math.min(currentX / DECISION_THRESHOLD, 1) : 0;
        
        leftCue.style.opacity = leftOpacity;
        rightCue.style.opacity = rightOpacity;
    }
    
    // Drag End
    function endDrag() {
        if (!isDragging) return;
        
        isDragging = false;
        movieContainer.classList.remove('dragging');
        
        // Check if we've dragged past the pixel threshold, does not interact if not
        if (currentX > DECISION_THRESHOLD) {
            // Right - add to watchlist
            hasSwiped = true;
            triggerAction('watchlist');
        } else if (currentX < -DECISION_THRESHOLD) {
            // Left - skip
            hasSwiped = true;
            triggerAction('skip');
        } else {
            // Not enough to trigger action, animate back to center
            resetPosition(); // function of death
        }
        
        // Ensure cues are hidden when not dragging, idk if this is needed but many things were added to fix bugs
        leftCue.style.opacity = 0;
        rightCue.style.opacity = 0;
    }
    
    // Touch End, why did I even make this
    function handleTouchEnd() {
        endDrag();
    }
    
    // Rese position of card
    function resetPosition() {
        movieContainer.style.transition = 'transform 0.3s ease';
        movieContainer.style.transform = 'translateX(0) rotate(0deg)';
        
        // Reset cues
        leftCue.style.opacity = 0;
        rightCue.style.opacity = 0;
        
        // Remove transition after animation completes
        setTimeout(() => {
            movieContainer.style.transition = '';
        }, 200); // 200ms may be too long
    }
    
    // Trigger the appropriate action based on swipe direction
    function triggerAction(action) {
        if (!movieId) return;
        
        isInTransition = true; // Mark as in transition | I love state machines I love state machines
        
        // Add exit class to prevent interactions
        movieContainer.classList.add('card-exit');
        
        // Fly card off screen, very goofy
        const direction = action === 'skip' ? -1 : 1;
        movieContainer.style.transition = 'transform 0.3s ease';
        movieContainer.style.transform = `translateX(${direction * window.innerWidth}px) rotate(${direction * 30}deg)`;
        
        // Trigger the corresponding button action
        setTimeout(() => {
            const button = document.querySelector(`.action-btn[data-action="${action}"]`);
            if (button) button.click();
        }, 300);
    }
    
    // This entire thing was just made so that we can better hone in buttons if they use the swipe animation :D
    window.movieSwipe = {
        // Trigger swipe animation for button clicks
        animateSwipe: function(action) {
            const direction = (action === 'skip' || action === 'block') ? -1 : 1;
            
            isInTransition = true; // Mark as in transition
            hasSwiped = true;      // Mark as swiped to prevent navigation
            
            // Set transition for smooth animation
            movieContainer.style.transition = 'transform 0.3s ease';
            movieContainer.style.transform = `translateX(${direction * window.innerWidth}px) rotate(${direction * 30}deg)`;
            
            // Hide cues
            leftCue.style.opacity = 0;
            rightCue.style.opacity = 0;
        },
        
        // Reset the movie card to center position
        resetCardPosition: function() {
            movieContainer.style.transition = '';
            movieContainer.style.transform = '';
            movieContainer.classList.remove('card-exit');
            isInTransition = false; // Reset transition state
            hasSwiped = false;     // Reset swiped state
        },
        
        // Update the movie ID (called after new movie  loaded)
        updateMovieId: function(newMovieId) {
            movieId = newMovieId;
            isInTransition = false;
            hasSwiped = false;
            
            // Make sure the movie container is fully visible
            movieContainer.style.display = 'block';
            movieContainer.style.opacity = '1';
            movieContainer.style.transform = 'none';
            movieContainer.style.transition = 'none';
            movieContainer.classList.remove('card-exit');
            
            // Update the cu if they were removed
            if (!movieContainer.contains(leftCue)) {
                movieContainer.appendChild(leftCue);
            }
            if (!movieContainer.contains(rightCue)) {
                movieContainer.appendChild(rightCue);
            }
            
            // Ensure cues are hidden when not dragging
            leftCue.style.opacity = 0;
            rightCue.style.opacity = 0;
            
            // Setup navigation prevention for the new link
            setupNavigationPrevention();
        }
    };
});