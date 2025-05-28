document.addEventListener('DOMContentLoaded', function() {
    const navPlaceholder = document.getElementById('nav-placeholder');
    
    // Try to get nav from localStorage first
    const cachedNav = localStorage.getItem('navContent');
    if (cachedNav) {
        navPlaceholder.innerHTML = cachedNav;
        setActiveLink();
    }

    // Always fetch fresh content in the background
    fetch('../assets/nav.html')
        .then(response => response.text())
        .then(data => {
            // Only update if content is different
            if (data !== cachedNav) {
                localStorage.setItem('navContent', data);
                navPlaceholder.innerHTML = data;
                setActiveLink();
            }
        })
        .catch(error => {
            console.error('Error loading navigation:', error);
        });
});

function setActiveLink() {
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll('.sidebar a');
    
    // First, remove all active classes
    links.forEach(link => link.classList.remove('active'));
    
    // Then, find and set the active link
    links.forEach(link => {
        const linkPath = link.getAttribute('href');
        // Get the filename from the current path
        const currentFileName = currentPath.split('/').pop();
        const linkFileName = linkPath.split('/').pop();
        
        if (currentFileName === linkFileName) {
            link.classList.add('active');
            
            // Only highlight parent if this is a submenu item
            const parent = link.closest('li').parentElement.previousElementSibling;
            if (parent && parent.tagName === 'A' && link.closest('.submenu')) {
                parent.classList.add('active');
            }
        }
    });
} 