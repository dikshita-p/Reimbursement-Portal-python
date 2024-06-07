window.onload = function() {
    var flashMessage = document.getElementById('flash-message');
    
    if (flashMessage) {
        setTimeout(function() {
            flashMessage.style.display = 'none';
        }, 3000); 
    }
};
