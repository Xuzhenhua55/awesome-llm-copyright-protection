document.addEventListener('DOMContentLoaded', function() {
    const footerPlaceholder = document.getElementById('footer-placeholder');
    
    // Try to get footer from localStorage first
    const cachedFooter = localStorage.getItem('footerContent');
    if (cachedFooter) {
        footerPlaceholder.innerHTML = cachedFooter;
    }

    // Always fetch fresh content in the background
    fetch('../assets/footer.html')
        .then(response => response.text())
        .then(data => {
            // Only update if content is different
            if (data !== cachedFooter) {
                localStorage.setItem('footerContent', data);
                footerPlaceholder.innerHTML = data;
            }
        })
        .catch(error => {
            console.error('Error loading footer:', error);
        });
}); 