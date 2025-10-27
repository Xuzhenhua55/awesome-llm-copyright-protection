document.addEventListener('DOMContentLoaded', function() {
    const navPlaceholder = document.getElementById('nav-placeholder');
    
    // Try to get nav from localStorage first
    const cachedNav = localStorage.getItem('navContent');
    if (cachedNav) {
        navPlaceholder.innerHTML = cachedNav;
        setActiveLink();
        setupMobileMenu();
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
                setupMobileMenu();
            }
        })
        .catch(error => {
            console.error('Error loading navigation:', error);
        });
});

function setupMobileMenu() {
    // Create mobile menu toggle button
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && !document.querySelector('.sidebar-toggle')) {
        const toggleButton = document.createElement('button');
        toggleButton.className = 'sidebar-toggle';
        toggleButton.innerHTML = '☰';
        toggleButton.setAttribute('aria-label', 'Toggle navigation menu');
        document.body.appendChild(toggleButton);
        
        toggleButton.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(event) {
            if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

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