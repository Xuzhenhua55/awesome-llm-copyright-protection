document.addEventListener('DOMContentLoaded', function() {
    const navPlaceholder = document.getElementById('nav-placeholder');
    
    // If we already have content from preload, just set active link
    if (window.navContent) {
        setActiveLink();
    }

    // Always fetch fresh content in the background
    fetch('../assets/nav.html')
        .then(response => response.text())
        .then(data => {
            // Only update if content is different
            if (data !== window.navContent) {
                localStorage.setItem('navContent', data);
                window.navContent = data;
                navPlaceholder.innerHTML = data;
                setActiveLink();
            }
        })
        .catch(error => {
            console.error('Error loading navigation:', error);
        });
});

function setActiveLink() {
    const currentPage = window.location.pathname.split('/').pop();
    const links = document.querySelectorAll('.sidebar a');
    
    links.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
            // If it's a submenu item, also highlight the parent
            const parent = link.closest('li').parentElement.previousElementSibling;
            if (parent && parent.tagName === 'A') {
                parent.classList.add('active');
            }
        }
    });
} 