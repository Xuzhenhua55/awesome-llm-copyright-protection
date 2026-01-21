function loadFooter() {
    const footerPlaceholder = document.getElementById('footer-placeholder');
    if (!footerPlaceholder) return;
    
    // Determine path based on current location
    const isRoot = !window.location.pathname.includes('/docs/html/');
    const footerPath = isRoot ? 'docs/assets/footer.html' : '../assets/footer.html';

    fetch(footerPath)
        .then(response => {
            if (!response.ok) throw new Error('Footer not found');
            return response.text();
        })
        .then(data => {
            footerPlaceholder.innerHTML = data;
        })
        .catch(error => {
            console.error('Error loading footer:', error);
            // Attempt fallback if first one fails
            const fallbackPath = isRoot ? 'docs/assets/footer.html' : '../assets/footer.html';
            if (footerPath !== fallbackPath) {
                fetch(fallbackPath)
                    .then(response => response.text())
                    .then(data => {
                        footerPlaceholder.innerHTML = data;
                    })
                    .catch(err => console.error('Error loading footer fallback:', err));
            }
        });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadFooter);
} else {
    loadFooter();
}
