(() => {
    'use strict';
    
    // State management
    let isMenuOpen = false;
    let openSubmenu = null;
    let wanInterfaces = [];
    let lanInterfaces = [];
    let services = [];
    let dataLoaded = false;

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
            if (mainContent) {
                mainContent.classList.add('status-bar-visible');
            }
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
        if (mainContent) {
            mainContent.classList.remove('status-bar-visible');
        }
        
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
        
        // Load services data when services submenu is visited
        if (menuItem === 'system-services') {
            await loadServicesData();
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
        const wlanContainer = document.getElementById('lan-interfaces-container');
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
        const container = document.getElementById('lan-interfaces-container');
        if (!container) return;
        
        // Clear existing cards
        container.innerHTML = '';
        
        lanInterfaces.forEach(interfaceData => {
            const isOnline = interfaceData.link === 'up';
            const isActive = interfaceData.active;
            
            // Create card element
            const card = document.createElement('div');
            card.className = 'lan-interface-card';
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
    // Services Management
    // ------------------------------
    async function loadServicesData() {
        try {
            const response = await fetch('/cgi-bin/services.py');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.success) {
                services = data.services || [];
                console.log('Services data loaded:', services);
                updateServicesDisplay();
            } else {
                throw new Error(data.error || 'Invalid services response format');
            }
        } catch (error) {
            console.error('Failed to load services data:', error);
            showStatusMessage('Failed to load services data: ' + error.message, 'error', 5000);
        }
    }

    async function refreshServices() {
        const refreshBtn = document.querySelector('.refresh-btn');
        const refreshIcon = document.querySelector('.refresh-icon');
        
        if (!refreshBtn || !refreshIcon) return;
        
        // Disable button and show loading animation
        refreshBtn.disabled = true;
        refreshBtn.classList.add('loading');
        refreshIcon.textContent = '🔄';
        
        try {
            // Show loading state
            showServicesLoadingState();
            
            // Load fresh services data
            await loadServicesData();
            
            // Show success message
            showStatusMessage('Services refreshed successfully', 'success', 3000);
            
        } catch (error) {
            console.error('Failed to refresh services:', error);
            showStatusMessage('Failed to refresh services: ' + error.message, 'error', 5000);
        } finally {
            // Re-enable button and stop loading animation
            refreshBtn.disabled = false;
            refreshBtn.classList.remove('loading');
            refreshIcon.textContent = '🔄';
        }
    }

    function showServicesLoadingState() {
        const servicesList = document.getElementById('services-list');
        if (servicesList) {
            servicesList.innerHTML = '<div class="loading-message">Loading services...</div>';
        }
    }

    function updateServicesDisplay() {
        const servicesList = document.getElementById('services-list');
        if (!servicesList) return;
        
        // Clear existing services
        servicesList.innerHTML = '';
        
        services.forEach(service => {
            const isUp = service.status === 'up';
            
            // Create service row element
            const serviceRow = document.createElement('div');
            serviceRow.className = 'service-row';
            serviceRow.setAttribute('data-service', service.name);
            
            // Add classes based on status
            if (isUp) {
                serviceRow.classList.add('service-up');
            } else {
                serviceRow.classList.add('service-down');
            }
            
            // Create service row HTML
            serviceRow.innerHTML = `
                <div class="service-name">${service.name}</div>
                <div class="service-actions">
                    <button class="btn btn-success start-btn" data-service="${service.name}">
                        Start
                    </button>
                    <button class="btn btn-danger stop-btn" data-service="${service.name}">
                        Stop
                    </button>
                    <button class="btn btn-primary restart-btn" data-service="${service.name}">
                        Restart
                    </button>
                </div>
            `;
            
            servicesList.appendChild(serviceRow);
        });
        
        // Attach event listeners after generating service rows
        attachServiceButtonListeners();
    }

    function attachServiceButtonListeners() {
        const servicesList = document.getElementById('services-list');
        if (!servicesList) return;
        
        servicesList.addEventListener('click', function(e) {
            const serviceName = e.target.getAttribute('data-service');
            if (!serviceName) return;
            
            if (e.target.classList.contains('restart-btn')) {
                restartService(serviceName);
            } else if (e.target.classList.contains('start-btn')) {
                startService(serviceName);
            } else if (e.target.classList.contains('stop-btn')) {
                stopService(serviceName);
            }
        });
    }

    async function restartService(serviceName) {
        console.log('Restarting service:', serviceName);
        
        try {
            // Send POST request to restart service
            const formData = new FormData();
            formData.append('service', serviceName);
            
            const response = await fetch('/cgi-bin/services.py', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                showStatusMessage(result.message || `Service ${serviceName} restarted successfully`, 'success', 3000);
                
                // Refresh services data to get updated status
                await loadServicesData();
                
                console.log('Successfully restarted service:', serviceName);
            } else {
                showStatusMessage(result.message || `Failed to restart service ${serviceName}`, 'error', 5000);
            }
        } catch (error) {
            console.error('Error restarting service:', error);
            showStatusMessage('Error restarting service: ' + error.message, 'error', 5000);
        }
    }

    async function startService(serviceName) {
        console.log('Starting service:', serviceName);
        
        try {
            // Send POST request to start service
            const formData = new FormData();
            formData.append('service', serviceName);
            formData.append('action', 'start');
            
            const response = await fetch('/cgi-bin/services.py', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                showStatusMessage(result.message || `Service ${serviceName} started successfully`, 'success', 3000);
                
                // Refresh services data to get updated status
                await loadServicesData();
                
                console.log('Successfully started service:', serviceName);
            } else {
                showStatusMessage(result.message || `Failed to start service ${serviceName}`, 'error', 5000);
            }
        } catch (error) {
            console.error('Error starting service:', error);
            showStatusMessage('Error starting service: ' + error.message, 'error', 5000);
        }
    }

    async function stopService(serviceName) {
        console.log('Stopping service:', serviceName);
        
        try {
            // Send POST request to stop service
            const formData = new FormData();
            formData.append('service', serviceName);
            formData.append('action', 'stop');
            
            const response = await fetch('/cgi-bin/services.py', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                showStatusMessage(result.message || `Service ${serviceName} stopped successfully`, 'success', 3000);
                
                // Refresh services data to get updated status
                await loadServicesData();
                
                console.log('Successfully stopped service:', serviceName);
            } else {
                showStatusMessage(result.message || `Failed to stop service ${serviceName}`, 'error', 5000);
            }
        } catch (error) {
            console.error('Error stopping service:', error);
            showStatusMessage('Error stopping service: ' + error.message, 'error', 5000);
        }
    }

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
    window.refreshServices = refreshServices;
    window.loadServicesData = loadServicesData;
    
    console.log('Index.js loaded successfully');
})();
