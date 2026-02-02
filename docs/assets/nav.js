function loadNavigation() {
    const navPlaceholder = document.getElementById('nav-placeholder');
    if (!navPlaceholder) return;
    
    // Determine path based on current location
    const isRoot = !window.location.pathname.includes('/docs/html/');
    const navPath = isRoot ? 'docs/assets/nav.html' : '../assets/nav.html';

    // Clear old cache to ensure new navigation is loaded
    const navVersion = 'v6'; // Increment when nav structure changes (e.g. hidden-item)
    const cachedVersion = localStorage.getItem('navVersion');
    
    if (cachedVersion !== navVersion) {
        localStorage.removeItem('navContent');
        localStorage.setItem('navVersion', navVersion);
    }
    
    // Try to get nav from localStorage first
    const cachedNav = localStorage.getItem('navContent');
    if (cachedNav) {
        navPlaceholder.innerHTML = cachedNav;
        adjustNavPaths(navPlaceholder, isRoot);
        setActiveLink();
        setupMobileMenu();
        setupHiddenNavItem();
    }

    // Always fetch fresh content in the background
    fetch(navPath)
        .then(response => {
            if (!response.ok) throw new Error('Navigation not found');
            return response.text();
        })
        .then(data => {
            // Only update if content is different
            if (data !== cachedNav) {
                localStorage.setItem('navContent', data);
                navPlaceholder.innerHTML = data;
                adjustNavPaths(navPlaceholder, isRoot);
                setActiveLink();
                setupMobileMenu();
            }
            setupHiddenNavItem(); // Apply hidden/unlocked state
        })
        .catch(error => {
            console.error('Error loading navigation:', error);
        });
}

function adjustNavPaths(container, isRoot) {
    // Adjust logo path
    const logoImg = container.querySelector('.logo-icon');
    if (logoImg) {
        logoImg.src = isRoot ? 'docs/assets/logo.svg' : '../assets/logo.svg';
    }
    
    // Adjust all links
    const links = container.querySelectorAll('a');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('http') || href.startsWith('#')) return;
        
        if (isRoot) {
            // From root, we need to fix paths that assume they are in docs/html/
            if (href.includes('index.html')) {
                link.setAttribute('href', 'index.html');
            } else if (!href.startsWith('docs/html/')) {
                link.setAttribute('href', 'docs/html/' + href);
            }
        } else {
            // From docs/html/, ensure Home points to ../../index.html
            if (href.includes('index.html') && !href.startsWith('..')) {
                link.setAttribute('href', '../../index.html');
            }
        }
    });
}

var HIDDEN_UNLOCK_KEY = 'scholarMonitorUnlocked';
var HIDDEN_KEYS = { Q: false, W: false, E: false };

function setupHiddenNavItem() {
    var item = document.querySelector('.nav-hidden-item[data-unlock-key="scholar-monitor"]');
    if (!item) return;
    // 仅在本会话内有效：用 sessionStorage，关闭标签/窗口后再次打开需重新按 QWE 才显示
    if (sessionStorage.getItem(HIDDEN_UNLOCK_KEY)) {
        item.classList.add('unlocked');
        return;
    }
    item.classList.remove('unlocked');
    if (window._hiddenNavShortcutBound) return;
    window._hiddenNavShortcutBound = true;
    function checkQWE() {
        if (HIDDEN_KEYS.Q && HIDDEN_KEYS.W && HIDDEN_KEYS.E) {
            sessionStorage.setItem(HIDDEN_UNLOCK_KEY, '1');
            item.classList.add('unlocked');
            showUnlockToast('Scholar Monitor 已解锁');
            HIDDEN_KEYS.Q = HIDDEN_KEYS.W = HIDDEN_KEYS.E = false;
        }
    }
    document.addEventListener('keydown', function (e) {
        var k = e.key && e.key.toUpperCase();
        if (k === 'Q') { HIDDEN_KEYS.Q = true; checkQWE(); }
        if (k === 'W') { HIDDEN_KEYS.W = true; checkQWE(); }
        if (k === 'E') { HIDDEN_KEYS.E = true; checkQWE(); }
    });
    document.addEventListener('keyup', function (e) {
        var k = e.key && e.key.toUpperCase();
        if (k === 'Q') HIDDEN_KEYS.Q = false;
        if (k === 'W') HIDDEN_KEYS.W = false;
        if (k === 'E') HIDDEN_KEYS.E = false;
    });
}

function showUnlockToast(text) {
    var toast = document.createElement('div');
    toast.textContent = text;
    toast.style.cssText = 'position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);background:#7048e8;color:#fff;padding:0.6rem 1.2rem;border-radius:8px;font-size:0.9rem;z-index:9999;box-shadow:0 4px 12px rgba(112,72,232,0.4);opacity:0;transition:opacity 0.3s';
    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.style.opacity = '1'; });
    setTimeout(function () {
        toast.style.opacity = '0';
        setTimeout(function () { toast.remove(); }, 300);
    }, 2500);
}

function setupMobileMenu() {
    // Create mobile menu toggle button
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && !document.querySelector('.sidebar-toggle')) {
        const toggleButton = document.createElement('button');
        toggleButton.className = 'sidebar-toggle';
        toggleButton.innerHTML = '☰';
        toggleButton.setAttribute('aria-label', 'Toggle navigation menu');
        document.body.appendChild(toggleButton);
        
        // Update button icon and position based on sidebar state
        function updateButtonState() {
            const logoSection = sidebar.querySelector('.sidebar-logo');
            if (sidebar.classList.contains('open')) {
                toggleButton.innerHTML = '✕';
                toggleButton.setAttribute('aria-label', 'Close navigation menu');
                // Move button inside logo row for alignment
                if (logoSection) logoSection.appendChild(toggleButton);
                else sidebar.appendChild(toggleButton);
                toggleButton.classList.add('moved');
            } else {
                toggleButton.innerHTML = '☰';
                toggleButton.setAttribute('aria-label', 'Open navigation menu');
                document.body.appendChild(toggleButton);
                toggleButton.classList.remove('moved');
            }
        }
        
        toggleButton.addEventListener('click', function(event) {
            event.stopPropagation();
            sidebar.classList.toggle('open');
            updateButtonState();
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(event) {
            if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
                sidebar.classList.remove('open');
                updateButtonState();
            }
        });
    }
}

function setActiveLink() {
    const currentPath = window.location.pathname;
    // Select links from nav-list (main nav items) and submenu
    const links = document.querySelectorAll('.sidebar .nav-list a, .sidebar .submenu a');
    
    // First, remove all active and parent-active classes
    links.forEach(link => {
        link.classList.remove('active');
        link.classList.remove('parent-active');
    });
    
    // Then, find and set the active link
    links.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (!linkPath) return;
        
        // Get the filename from the current path
        let currentFileName = currentPath.split('/').pop();
        if (currentFileName === '' || currentFileName === 'awesome-llm-copyright-protection') {
            currentFileName = 'index.html';
        }
        
        const linkFileName = linkPath.split('/').pop();
        
        if (currentFileName === linkFileName) {
            link.classList.add('active');
            
            // Only highlight parent if this is a submenu item (use parent-active class)
            const submenu = link.closest('.submenu');
            if (submenu) {
                const parentLi = submenu.closest('.has-submenu');
                if (parentLi) {
                    const parentLink = parentLi.querySelector(':scope > a');
                    if (parentLink) {
                        parentLink.classList.add('parent-active');
                    }
                }
            }
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadNavigation);
} else {
    loadNavigation();
}
