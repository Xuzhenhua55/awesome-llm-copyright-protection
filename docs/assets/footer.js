function adjustFooterPaths(container, isRoot) {
    // Adjust avatar image path
    const avatarImg = container.querySelector('.maintainer-avatar');
    if (avatarImg) {
        const avatarSrc = avatarImg.getAttribute('data-avatar-src');
        if (avatarSrc) {
            avatarImg.src = isRoot ? `docs/assets/${avatarSrc}` : `../assets/${avatarSrc}`;
        }
    }
}

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
            adjustFooterPaths(footerPlaceholder, isRoot);
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
                        adjustFooterPaths(footerPlaceholder, isRoot);
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
