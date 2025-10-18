(() => {
    'use strict';
    
    // State management
    let isMenuOpen = false;
    let openSubmenu = null;
    let wanInterfaces = [];
    let lanInterfaces = [];
    let dataLoaded = false;

    // DOM elements
    const statusBar = document.getElementById('statusBar');
    const statusMessage = document.getElementById('statusMessage');

    // ------------------------------
    // Initialization
    // ------------------------------
    document.addEventListener('DOMContentLoaded', async () => {
        // Hide menu on mobile devices at startup
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.add('hidden');
        }

        // Status banner close handler
        if (statusBar) {
            statusBar.addEventListener('click', (e) => {
                if (e.target === statusBar || e.target === statusMessage) {
                    hideStatusMessage();
                }
            });
        }
        
        // Load all data from server
        await loadAllData();
    });

    // ------------------------------
    // Status Message Functions
    // ------------------------------
    function showStatusMessage(message, type = 'success', duration = 5000) {
        if (!statusBar || !statusMessage) return;

        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'status-close';
        closeButton.innerHTML = '×';
        closeButton.onclick = function(e) {
            e.stopPropagation();
            hideStatusMessage();
        };
        
        // Set message, type and close button
        statusMessage.textContent = message;
        statusBar.className = `status-bar ${type}`;
        statusBar.innerHTML = '';
        statusBar.appendChild(statusMessage);
        statusBar.appendChild(closeButton);
        
        // Show status bar
        setTimeout(() => {
            statusBar.classList.add('visible');
        }, 50);
        
        // Hide status bar after specified duration
        statusBar.timeoutId = setTimeout(() => {
            hideStatusMessage();
        }, duration);
    }

    function hideStatusMessage() {
        if (!statusBar || !statusMessage) return;
        
        // Cancel timeout if exists
        if (statusBar.timeoutId) {
            clearTimeout(statusBar.timeoutId);
            statusBar.timeoutId = null;
        }
        
        // Hide status bar
        statusBar.classList.remove('visible');
        
        // Clean up after animation completes
        setTimeout(() => {
            statusMessage.textContent = '';
            statusBar.className = 'status-bar';
            statusBar.innerHTML = '<span id="statusMessage"></span>';
        }, 300);
    }

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
    }

    function showUserMenu() {
        showStatusMessage('User menu - feature will be implemented later', 'error', 3000);
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
    // Data Management
    // ------------------------------
    async function loadAllData() {
        try {
            const response = await fetch('/cgi-bin/interfaces.py');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.success) {
                // Process WAN interfaces from 'wan' data
                wanInterfaces = (data.wan || []).map(iface => ({
                    interface: iface.interface,
                    ip4: iface.ipv4.length > 0 ? iface.ipv4[0] : '',
                    ip6: iface.ipv6.length > 0 ? iface.ipv6[0] : '',
                    link: iface.state,
                    device: iface.state,
                    active: iface.active,
                    mac: iface.mac
                }));
                
                // Process LAN interfaces from 'lan' data (including WLAN)
                lanInterfaces = (data.lan || []).map(iface => ({
                    interface: iface.interface,
                    ip4: iface.ipv4.length > 0 ? iface.ipv4[0] : '',
                    ip6: iface.ipv6.length > 0 ? iface.ipv6[0] : '',
                    link: iface.state,
                    device: iface.state,
                    active: iface.active,
                    mac: iface.mac
                }));
                
                dataLoaded = true;
                
                console.log('All data loaded:', { wanInterfaces, lanInterfaces });
                
                updateWANCards();
                updateWLANCards();
            } else {
                throw new Error(data.error || 'Invalid response format');
            }
        } catch (error) {
            console.error('Failed to load data:', error);
            showStatusMessage('Failed to load data: ' + error.message, 'error', 5000);
        }
    }

    async function refreshDashboard() {
        const refreshBtn = document.querySelector('.refresh-btn');
        const refreshIcon = document.querySelector('.refresh-icon');
        
        if (!refreshBtn || !refreshIcon) return;
        
        // Disable button and show loading animation
        refreshBtn.disabled = true;
        refreshBtn.classList.add('loading');
        refreshIcon.textContent = '🔄';
        
        try {
            // Reset data loaded flag
            dataLoaded = false;
            
            // Show loading states
            showLoadingStates();
            
            // Load fresh data
            await loadAllData();
            
            // Show success message
            showStatusMessage('Dashboard refreshed successfully', 'success', 3000);
            
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
            showStatusMessage('Failed to refresh dashboard: ' + error.message, 'error', 5000);
        } finally {
            // Re-enable button and stop loading animation
            refreshBtn.disabled = false;
            refreshBtn.classList.remove('loading');
            refreshIcon.textContent = '🔄';
        }
    }

    function showLoadingStates() {
        // Clear WAN interface container and show loading message
        const wanContainer = document.getElementById('wan-interfaces-container');
        if (wanContainer) {
            wanContainer.innerHTML = '<div class="loading-message">Loading WAN interfaces...</div>';
        }
        
        // Clear WLAN interface container and show loading message
        const wlanContainer = document.getElementById('wlan-interfaces-container');
        if (wlanContainer) {
            wlanContainer.innerHTML = '<div class="loading-message">Loading LAN/WLAN interfaces...</div>';
        }
    }

    // ------------------------------
    // Interface Management
    // ------------------------------
    function generateWANCards() {
        const container = document.getElementById('wan-interfaces-container');
        if (!container) return;
        
        // Clear existing cards
        container.innerHTML = '';
        
        wanInterfaces.forEach(interfaceData => {
            const isOnline = interfaceData.link === 'up';
            const isActive = interfaceData.active;
            
            // Create card element
            const card = document.createElement('div');
            card.className = 'wan-interface-card';
            card.setAttribute('data-interface', interfaceData.interface);
            
            // Add classes based on status
            if (isActive) {
                card.classList.add('active');
            } else if (!isOnline) {
                card.classList.add('offline');
            }
            
            // Create card HTML
            card.innerHTML = `
                <div class="interface-header">
                    <h4>${interfaceData.interface}</h4>
                    <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>IPv4: ${interfaceData.ip4 || 'N/A'}</p>
                    <p>IPv6: ${interfaceData.ip6 || 'N/A'}</p>
                    <p>MAC: ${interfaceData.mac || 'N/A'}</p>
                    <p>Status: ${isOnline ? 'Online' : 'Offline'}</p>
                </div>
                <button class="btn btn-primary use-btn" data-interface="${interfaceData.interface}">
                    Use
                </button>
            `;
            
            container.appendChild(card);
        });
        
        // Attach event listeners after generating cards
        attachWANButtonListeners();
    }

    function generateWLANCards() {
        const container = document.getElementById('wlan-interfaces-container');
        if (!container) return;
        
        // Clear existing cards
        container.innerHTML = '';
        
        lanInterfaces.forEach(interfaceData => {
            const isOnline = interfaceData.link === 'up';
            const isActive = interfaceData.active;
            
            // Create card element
            const card = document.createElement('div');
            card.className = 'wlan-interface-card';
            card.setAttribute('data-interface', interfaceData.interface);
            
            // Add classes based on status
            if (isActive) {
                card.classList.add('active');
            } else if (!isOnline) {
                card.classList.add('offline');
            }
            
            // Create card HTML WITHOUT button
            card.innerHTML = `
                <div class="interface-header">
                    <h4>${interfaceData.interface}</h4>
                    <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>IPv4: ${interfaceData.ip4 || 'N/A'}</p>
                    <p>IPv6: ${interfaceData.ip6 || 'N/A'}</p>
                    <p>MAC: ${interfaceData.mac || 'N/A'}</p>
                    <p>Status: ${isOnline ? 'Online' : 'Offline'}</p>
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    function attachWANButtonListeners() {
        const container = document.getElementById('wan-interfaces-container');
        if (!container) return;
        
        container.addEventListener('click', function(e) {
            if (e.target.classList.contains('use-btn')) {
                const interfaceName = e.target.getAttribute('data-interface');
                if (interfaceName) {
                    switchInterface(interfaceName);
                }
            }
        });
    }

    // WLAN button listeners removed - WLAN interfaces don't have buttons

    function updateWANCards() {
        generateWANCards();
    }

    function updateWLANCards() {
        generateWLANCards();
    }

    async function switchInterface(interfaceName) {
        console.log('Switching to WAN interface:', interfaceName);
        
        if (!dataLoaded) {
            showStatusMessage('Data not loaded yet', 'error', 3000);
            return;
        }
        
        // Only check WAN interfaces for switching
        const interfaceData = wanInterfaces.find(iface => iface.interface === interfaceName);
        
        if (!interfaceData) {
            console.log('WAN Interface data not found for:', interfaceName);
            showStatusMessage(`WAN Interface ${interfaceName} not found`, 'error', 3000);
            return;
        }
        
        // Check if interface is up
        if (interfaceData.link !== 'up') {
            showStatusMessage(`Cannot switch to ${interfaceName} - interface is down`, 'error', 3000);
            return;
        }
        
        try {
            // Send POST request to switch interface
            const formData = new FormData();
            formData.append('interface', interfaceName);
            
            const response = await fetch('/cgi-bin/interfaces.py', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update local data with server response
                if (result.wan) {
                    wanInterfaces = result.wan.map(iface => ({
                        interface: iface.interface,
                        ip4: iface.ipv4.length > 0 ? iface.ipv4[0] : '',
                        ip6: iface.ipv6.length > 0 ? iface.ipv6[0] : '',
                        link: iface.state,
                        device: iface.state,
                        active: iface.active,
                        mac: iface.mac
                    }));
                }
                
                if (result.lan) {
                    lanInterfaces = result.lan.map(iface => ({
                        interface: iface.interface,
                        ip4: iface.ipv4.length > 0 ? iface.ipv4[0] : '',
                        ip6: iface.ipv6.length > 0 ? iface.ipv6[0] : '',
                        link: iface.state,
                        device: iface.state,
                        active: iface.active,
                        mac: iface.mac
                    }));
                }
                
                // Update UI
                updateWANCards();
                updateWLANCards();
                
                // Show success message
                showStatusMessage(result.message || `Switched to ${interfaceName}`, 'success', 3000);
                console.log('Successfully switched to:', interfaceName);
            } else {
                showStatusMessage(result.error || 'Failed to switch interface', 'error', 5000);
            }
        } catch (error) {
            console.error('Error switching interface:', error);
            showStatusMessage('Error switching interface: ' + error.message, 'error', 5000);
        }
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
    window.showStatusMessage = showStatusMessage;
    window.hideStatusMessage = hideStatusMessage;
    window.togglePasswordVisibility = togglePasswordVisibility;
    window.switchInterface = switchInterface;
    window.refreshDashboard = refreshDashboard;
    
    console.log('Index.js loaded successfully');
})();
