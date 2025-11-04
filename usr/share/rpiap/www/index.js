(() => {
    'use strict';
    
    // State management
    let isMenuOpen = false;
    let openSubmenu = null;

    // DOM elements
    const statusBar = document.getElementById('statusBar');
    const statusMessage = document.getElementById('statusMessage');
    const mainContent = document.querySelector('.main-content');

    // ------------------------------
    // Initialization
    // ------------------------------
    document.addEventListener('DOMContentLoaded', async () => {
        // Hide menu on mobile devices at startup
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.add('hidden');
        }

        // Status banner close handler - handled by HTMX
        
        // Attach drag and drop listeners on initial load
        attachDragAndDropListeners();
    });

    // Status messages are now handled by HTMX via hx-swap-oob

    // ------------------------------
    // Content Navigation
    // ------------------------------
    async function showContent(menuItem) {
        // Close menu on mobile after clicking menu item
        if (window.innerWidth <= 768) {
            closeMenu();
        }
        
        // Hide all sections
        const allSections = document.querySelectorAll('.content-section');
        allSections.forEach(section => {
            section.style.display = 'none';
        });
        
        // Show requested section
        const targetSection = document.getElementById(menuItem + '-content');
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // Load WLAN data when WLAN submenu is visited
        if (menuItem === 'settings-wlan' && window.initializeWLANData) {
            await window.initializeWLANData();
        }
        
        // Initialize speed test content when speed test submenu is visited
        if (menuItem === 'system-speedtest' && window.initializeSpeedTestContent) {
            await window.initializeSpeedTestContent();
        }
    }

    function showUserMenu() {
        // Use HTMX to show status message
        const statusHtml = `<div class="status-bar error visible" id="statusBar" hx-swap-oob="true">
            <span id="statusMessage">User menu - feature will be implemented later</span>
            <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
        </div>`;
        htmx.ajax('GET', 'about:blank', {
            swap: 'none',
            headers: {'X-HTML': statusHtml}
        });
        // Simple approach - just update the status bar directly
        if (statusBar && statusMessage) {
            statusBar.className = 'status-bar error visible';
            statusBar.innerHTML = '<span id="statusMessage">User menu - feature will be implemented later</span><button class="status-close" onclick="document.getElementById(\'statusBar\').classList.remove(\'visible\')">×</button>';
        }
    }

    function togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;
        
        const toggleButton = input.parentElement.querySelector('.password-toggle');
        if (!toggleButton) return;
        
        const icon = toggleButton.querySelector('.password-icon');
        if (!icon) return;
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.textContent = '🙈';
            toggleButton.classList.add('visible');
        } else {
            input.type = 'password';
            icon.textContent = '👁️';
            toggleButton.classList.remove('visible');
        }
    }

    // ------------------------------
    // HTMX Event Handlers
    // ------------------------------
    // Listen for HTMX events to reattach drag and drop listeners after content swap
    document.body.addEventListener('htmx:afterSwap', function(event) {
        // Reattach drag and drop listeners after dashboard content is swapped
        if (event.detail.target.id === 'dashboard-content') {
            attachDragAndDropListeners();
        }
    });

    // ------------------------------
    // Interface Management
    // ------------------------------
    function attachDragAndDropListeners() {
        const otherContainer = document.getElementById('other-interfaces-container');
        const wanContainer = document.getElementById('wan-interfaces-container');
        
        if (!otherContainer || !wanContainer) return;
        
        // Add drag event listeners to OTHER interface cards
        otherContainer.addEventListener('dragstart', function(e) {
            const card = e.target.closest('.other-interface-card');
            if (card) {
                card.classList.add('dragging');
                e.dataTransfer.setData('text/plain', card.getAttribute('data-interface'));
                e.dataTransfer.effectAllowed = 'move';
            }
        });
        
        otherContainer.addEventListener('dragend', function(e) {
            const card = e.target.closest('.other-interface-card');
            if (card) {
                card.classList.remove('dragging');
            }
        });
        
        // Add drop event listeners to WAN container
        wanContainer.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            wanContainer.classList.add('drag-over');
        });
        
        wanContainer.addEventListener('dragleave', function(e) {
            // Only remove drag-over class if we're actually leaving the container
            if (!wanContainer.contains(e.relatedTarget)) {
                wanContainer.classList.remove('drag-over');
            }
        });
        
        wanContainer.addEventListener('drop', function(e) {
            e.preventDefault();
            wanContainer.classList.remove('drag-over');
            
            const interfaceName = e.dataTransfer.getData('text/plain');
            if (interfaceName) {
                console.log('Dropped interface:', interfaceName);
                switchInterface(interfaceName);
            }
        });
    }


    function switchInterface(interfaceName) {
        console.log('Switching to interface:', interfaceName);
        
        // Check if interface card exists and is online
        const interfaceCard = document.querySelector(`[data-interface="${interfaceName}"]`);
        if (!interfaceCard) {
            console.log('Interface card not found for:', interfaceName);
            return;
        }
        
        // Check if interface is online (draggable attribute indicates online status)
        if (!interfaceCard.draggable) {
            console.log('Interface is not online:', interfaceName);
            return;
        }
        
        // Use HTMX to switch interface
        htmx.ajax('POST', '/cgi-bin/interfaces.py?format=html', {
            values: {interface: interfaceName},
            target: '#dashboard-content',
            swap: 'innerHTML'
        });
    }

    // ------------------------------
    // Menu Functions
    // ------------------------------
    function toggleMenu() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        
        isMenuOpen = !isMenuOpen;
        
        if (window.innerWidth <= 768) {
            // Mobile version
            if (isMenuOpen) {
                sidebar.classList.remove('hidden');
                sidebar.classList.add('visible');
                createOverlay();
            } else {
                sidebar.classList.add('hidden');
                sidebar.classList.remove('visible');
                removeOverlay();
            }
        } else {
            // Desktop version
            if (isMenuOpen) {
                sidebar.classList.add('hidden');
                mainContent.classList.add('expanded');
            } else {
                sidebar.classList.remove('hidden');
                mainContent.classList.remove('expanded');
            }
        }
    }

    function createOverlay() {
        if (!document.querySelector('.overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'overlay visible';
            overlay.onclick = closeMenu;
            document.body.appendChild(overlay);
        }
    }

    function removeOverlay() {
        const overlay = document.querySelector('.overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    function closeMenu() {
        if (isMenuOpen) {
            toggleMenu();
        }
    }

    function toggleSubmenu(submenuId) {
        const submenu = document.getElementById(submenuId + '-submenu');
        const menuItem = submenu ? submenu.closest('.menu-item') : null;
        
        // Close other submenus
        if (openSubmenu && openSubmenu !== submenu) {
            openSubmenu.classList.remove('visible');
            const otherMenuItem = openSubmenu.closest('.menu-item');
            if (otherMenuItem) {
                otherMenuItem.classList.remove('expanded');
            }
        }
        
        // Toggle current submenu
        if (submenu && menuItem) {
            submenu.classList.toggle('visible');
            menuItem.classList.toggle('expanded');
            openSubmenu = submenu.classList.contains('visible') ? submenu : null;
        }
    }

    // Resize handler for responsive behavior
    window.addEventListener('resize', function() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (window.innerWidth > 768) {
            // Desktop - reset state
            sidebar.classList.remove('visible', 'hidden');
            mainContent.classList.remove('expanded');
            removeOverlay();
            isMenuOpen = false;
        } else {
            // Mobile - hide menu
            sidebar.classList.add('hidden');
            sidebar.classList.remove('visible');
            mainContent.classList.remove('expanded');
            removeOverlay();
            isMenuOpen = false;
        }
    });

    // ------------------------------
    // Global Functions
    // ------------------------------
    window.toggleMenu = toggleMenu;
    window.toggleSubmenu = toggleSubmenu;
    window.showContent = showContent;
    window.showUserMenu = showUserMenu;
    window.togglePasswordVisibility = togglePasswordVisibility;
    window.switchInterface = switchInterface;
    
    console.log('Index.js loaded successfully');
})();
