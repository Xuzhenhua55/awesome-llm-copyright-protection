document.addEventListener('DOMContentLoaded', function() {
    const navPlaceholder = document.getElementById('nav-placeholder');
    
    // Try to get nav from localStorage first
    const cachedNav = localStorage.getItem('navContent');
    if (cachedNav) {
        navPlaceholder.innerHTML = cachedNav;
    }

    // Always fetch fresh content in the background
    fetch('/docs/assets/nav.html')
        .then(response => response.text())
        .then(data => {
            // Only update if content is different
            if (data !== cachedNav) {
                localStorage.setItem('navContent', data);
                navPlaceholder.innerHTML = data;
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