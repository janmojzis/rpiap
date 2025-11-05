(() => {
    'use strict';
    
    // State management
    let isMenuOpen = false;
    let openSubmenu = null;
    let wanInterfaces = [];
    let lanInterfaces = [];
    let otherInterfaces = [];
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
        
        // Initialize speed test content when speed test submenu is visited
        if (menuItem === 'system-speedtest' && window.initializeSpeedTestContent) {
            await window.initializeSpeedTestContent();
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
                // Process WAN data - IP addresses are now at interface level, same as OTHERS
                const wanData = data.wan || {};
                
                // Process WAN interfaces from 'wan.interfaces' data (with IP addresses)
                wanInterfaces = (wanData.interfaces || []).map(iface => ({
                    interface: iface.interface,
                    link: iface.state,
                    device: iface.state,
                    active: iface.active,
                    mac: iface.mac,
                    ipv4: iface.ipv4 || [],
                    ipv6: iface.ipv6 || [],
                    ipv4active: iface.ipv4active,
                    ipv6active: iface.ipv6active
                }));
                
                // Determine WAN active status based on interfaces (if at least one interface is active)
                const wanActive = wanInterfaces.some(iface => iface.ipv4active || iface.ipv6active);
                window.wanActive = wanActive;
                
                // Process LAN data - IP addresses are now at LAN level, not individual interfaces
                const lanData = data.lan || {};
                const lanIP4 = lanData.ipv4 && lanData.ipv4.length > 0 ? lanData.ipv4[0] : '';
                const lanIP6 = lanData.ipv6 && lanData.ipv6.length > 0 ? lanData.ipv6[0] : '';
                const lanActive = lanData.ipv4active || lanData.ipv6active || false;
                
                // Process LAN interfaces from 'lan.interfaces' data (without IP addresses)
                lanInterfaces = (lanData.interfaces || []).map(iface => ({
                    interface: iface.interface,
                    ip4: '', // No IP addresses on individual LAN interfaces anymore
                    ip6: '', // No IP addresses on individual LAN interfaces anymore
                    link: iface.state,
                    device: iface.state,
                    active: iface.active,
                    mac: iface.mac
                }));
                
                // Store LAN IP addresses and active status separately for display
                window.lanIP4 = lanIP4;
                window.lanIP6 = lanIP6;
                window.lanActive = lanActive;
                window.lanIPv4active = lanData.ipv4active;
                window.lanIPv6active = lanData.ipv6active;
                
                // Process OTHER interfaces
                const otherData = data.other || {};
                
                // Process OTHER interfaces from 'other.interfaces' data
                otherInterfaces = (otherData.interfaces || []).map(iface => ({
                    interface: iface.interface,
                    link: iface.state,
                    device: iface.state,
                    active: iface.active,
                    mac: iface.mac,
                    ipv4: iface.ipv4 || [],
                    ipv6: iface.ipv6 || [],
                    ipv4active: iface.ipv4active,
                    ipv6active: iface.ipv6active
                }));
                
                dataLoaded = true;
                
                console.log('All data loaded:', { wanInterfaces, lanInterfaces, otherInterfaces });
                
                updateWANCards();
                updateWLANCards();
                updateOtherCards();
                updateWANIPInfo();
                updateLANIPInfo();
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
            
            // Build IP addresses display with status indicators
            const ipv4List = interfaceData.ipv4 || [];
            const ipv6List = interfaceData.ipv6 || [];
            const ipv4Display = ipv4List.length > 0 ? ipv4List.join(', ') : 'None';
            const ipv6Display = ipv6List.length > 0 ? ipv6List.join(', ') : 'None';
            
            // Build IPv4 status indicator if available
            let ipv4StatusHtml = '';
            if (interfaceData.ipv4active !== undefined) {
                const ipv4Status = interfaceData.ipv4active ? '✓ Active' : '✗ Inactive';
                const ipv4Class = interfaceData.ipv4active ? 'ipv4-active' : 'ipv4-inactive';
                ipv4StatusHtml = ` <span class="${ipv4Class}">(${ipv4Status})</span>`;
            }
            
            // Build IPv6 status indicator if available
            let ipv6StatusHtml = '';
            if (interfaceData.ipv6active !== undefined) {
                const ipv6Status = interfaceData.ipv6active ? '✓ Active' : '✗ Inactive';
                const ipv6Class = interfaceData.ipv6active ? 'ipv6-active' : 'ipv6-inactive';
                ipv6StatusHtml = ` <span class="${ipv6Class}">(${ipv6Status})</span>`;
            }
            
            // Create card HTML WITH IP addresses (same as OTHERS)
            card.innerHTML = `
                <div class="interface-header">
                    <h4>${interfaceData.interface}</h4>
                    <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>MAC: ${interfaceData.mac || 'N/A'}</p>
                    <p>Status: ${isOnline ? 'Online' : 'Offline'}</p>
                    <p>IPv4: ${ipv4Display}${ipv4StatusHtml}</p>
                    <p>IPv6: ${ipv6Display}${ipv6StatusHtml}</p>
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    function generateWLANCards() {
        const container = document.getElementById('lan-interfaces-container');
        if (!container) return;
        
        // Clear existing cards
        container.innerHTML = '';
        
        // Add individual interface cards (without IP addresses)
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
            
            // Create card HTML WITHOUT IP addresses and WITHOUT button
            card.innerHTML = `
                <div class="interface-header">
                    <h4>${interfaceData.interface}</h4>
                    <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>MAC: ${interfaceData.mac || 'N/A'}</p>
                    <p>Status: ${isOnline ? 'Online' : 'Offline'}</p>
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    // Button listeners removed - now using drag and drop

    function attachDragAndDropListeners() {
        const otherContainer = document.getElementById('other-interfaces-container');
        const wanContainer = document.getElementById('wan-interfaces-container');
        
        if (!otherContainer || !wanContainer) return;
        
        // Add drag event listeners to OTHER interface cards
        otherContainer.addEventListener('dragstart', function(e) {
            if (e.target.classList.contains('other-interface-card')) {
                e.target.classList.add('dragging');
                e.dataTransfer.setData('text/plain', e.target.getAttribute('data-interface'));
                e.dataTransfer.effectAllowed = 'move';
            }
        });
        
        otherContainer.addEventListener('dragend', function(e) {
            if (e.target.classList.contains('other-interface-card')) {
                e.target.classList.remove('dragging');
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

    // WLAN button listeners removed - WLAN interfaces don't have buttons

    function updateWANCards() {
        generateWANCards();
    }

    function updateWLANCards() {
        generateWLANCards();
    }

    function generateOtherCards() {
        const container = document.getElementById('other-interfaces-container');
        if (!container) return;
        
        // Clear existing cards
        container.innerHTML = '';
        
        // Add individual interface cards
        otherInterfaces.forEach(interfaceData => {
            const isOnline = interfaceData.link === 'up';
            const isActive = interfaceData.active;
            
            // Create card element
            const card = document.createElement('div');
            card.className = 'other-interface-card';
            card.setAttribute('data-interface', interfaceData.interface);
            card.draggable = isOnline; // Only allow dragging if online
            
            // Add classes based on status
            if (isActive) {
                card.classList.add('active');
            } else if (!isOnline) {
                card.classList.add('offline');
            }
            
            // Build IP addresses display with status indicators
            const ipv4List = interfaceData.ipv4 || [];
            const ipv6List = interfaceData.ipv6 || [];
            const ipv4Display = ipv4List.length > 0 ? ipv4List.join(', ') : 'None';
            const ipv6Display = ipv6List.length > 0 ? ipv6List.join(', ') : 'None';
            
            // Build IPv4 status indicator if available
            let ipv4StatusHtml = '';
            if (interfaceData.ipv4active !== undefined) {
                const ipv4Status = interfaceData.ipv4active ? '✓ Active' : '✗ Inactive';
                const ipv4Class = interfaceData.ipv4active ? 'ipv4-active' : 'ipv4-inactive';
                ipv4StatusHtml = ` <span class="${ipv4Class}">(${ipv4Status})</span>`;
            }
            
            // Build IPv6 status indicator if available
            let ipv6StatusHtml = '';
            if (interfaceData.ipv6active !== undefined) {
                const ipv6Status = interfaceData.ipv6active ? '✓ Active' : '✗ Inactive';
                const ipv6Class = interfaceData.ipv6active ? 'ipv6-active' : 'ipv6-inactive';
                ipv6StatusHtml = ` <span class="${ipv6Class}">(${ipv6Status})</span>`;
            }
            
            // Create card HTML WITH IP addresses (drag and drop instead of button)
            card.innerHTML = `
                <div class="interface-header">
                    <h4>${interfaceData.interface}</h4>
                    <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>MAC: ${interfaceData.mac || 'N/A'}</p>
                    <p>Status: ${isOnline ? 'Online' : 'Offline'}</p>
                    <p>IPv4: ${ipv4Display}${ipv4StatusHtml}</p>
                    <p>IPv6: ${ipv6Display}${ipv6StatusHtml}</p>
                    ${isOnline ? '<p style="color: #4CAF50; font-size: 12px; margin-top: 8px;">Drag to WAN to use</p>' : ''}
                </div>
            `;
            
            container.appendChild(card);
        });
        
        // Attach drag and drop event listeners
        attachDragAndDropListeners();
    }

    function updateOtherCards() {
        generateOtherCards();
    }

    function updateWANIPInfo() {
        const wanCard = document.getElementById('wan-card');
        
        // Apply CSS class based on WAN active status
        if (wanCard) {
            // Remove existing status classes
            wanCard.classList.remove('wan-active', 'wan-inactive');
            
            // Add appropriate class based on active status
            if (window.wanActive) {
                wanCard.classList.add('wan-active');
            } else {
                wanCard.classList.add('wan-inactive');
            }
        }
    }

    function updateLANIPInfo() {
        const lanIPv4Element = document.getElementById('lan-ipv4');
        const lanIPv6Element = document.getElementById('lan-ipv6');
        const lanCard = document.getElementById('lan-card');
        
        // Build IPv4 status indicator if available
        let ipv4StatusHtml = '';
        if (window.lanIPv4active !== undefined) {
            const ipv4Status = window.lanIPv4active ? '✓ Active' : '✗ Inactive';
            const ipv4Class = window.lanIPv4active ? 'ipv4-active' : 'ipv4-inactive';
            ipv4StatusHtml = ` <span class="${ipv4Class}">(${ipv4Status})</span>`;
        }
        
        // Build IPv6 status indicator if available
        let ipv6StatusHtml = '';
        if (window.lanIPv6active !== undefined) {
            const ipv6Status = window.lanIPv6active ? '✓ Active' : '✗ Inactive';
            const ipv6Class = window.lanIPv6active ? 'ipv6-active' : 'ipv6-inactive';
            ipv6StatusHtml = ` <span class="${ipv6Class}">(${ipv6Status})</span>`;
        }
        
        if (lanIPv4Element) {
            lanIPv4Element.innerHTML = (window.lanIP4 || 'N/A') + ipv4StatusHtml;
        }
        if (lanIPv6Element) {
            lanIPv6Element.innerHTML = (window.lanIP6 || 'N/A') + ipv6StatusHtml;
        }
        
        // Apply CSS class based on LAN active status
        if (lanCard) {
            // Remove existing status classes
            lanCard.classList.remove('lan-active', 'lan-inactive');
            
            // Add appropriate class based on active status
            if (window.lanActive) {
                lanCard.classList.add('lan-active');
            } else {
                lanCard.classList.add('lan-inactive');
            }
        }
    }


    async function switchInterface(interfaceName) {
        console.log('Switching to interface:', interfaceName);
        
        if (!dataLoaded) {
            showStatusMessage('Data not loaded yet', 'error', 3000);
            return;
        }
        
        // Check OTHER interfaces for switching (since only OTHER interfaces have buttons now)
        const interfaceData = otherInterfaces.find(iface => iface.interface === interfaceName);
        
        if (!interfaceData) {
            console.log('Interface data not found for:', interfaceName);
            showStatusMessage(`Interface ${interfaceName} not found`, 'error', 3000);
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
                    // Process WAN data - IP addresses are now at interface level, same as OTHERS
                    const wanData = result.wan;
                    
                    // Process WAN interfaces from 'wan.interfaces' data (with IP addresses)
                    wanInterfaces = (wanData.interfaces || []).map(iface => ({
                        interface: iface.interface,
                        link: iface.state,
                        device: iface.state,
                        active: iface.active,
                        mac: iface.mac,
                        ipv4: iface.ipv4 || [],
                        ipv6: iface.ipv6 || [],
                        ipv4active: iface.ipv4active,
                        ipv6active: iface.ipv6active
                    }));
                    
                    // Determine WAN active status based on interfaces
                    const wanActive = wanInterfaces.some(iface => iface.ipv4active || iface.ipv6active);
                    window.wanActive = wanActive;
                }
                
                if (result.lan) {
                    // Process LAN data - IP addresses are now at LAN level
                    const lanData = result.lan;
                    const lanIP4 = lanData.ipv4 && lanData.ipv4.length > 0 ? lanData.ipv4[0] : '';
                    const lanIP6 = lanData.ipv6 && lanData.ipv6.length > 0 ? lanData.ipv6[0] : '';
                    const lanActive = lanData.ipv4active || lanData.ipv6active || false;
                    
                    // Process LAN interfaces from 'lan.interfaces' data (without IP addresses)
                    lanInterfaces = (lanData.interfaces || []).map(iface => ({
                        interface: iface.interface,
                        ip4: '', // No IP addresses on individual LAN interfaces anymore
                        ip6: '', // No IP addresses on individual LAN interfaces anymore
                        link: iface.state,
                        device: iface.state,
                        active: iface.active,
                        mac: iface.mac
                    }));
                    
                    // Update LAN IP addresses and active status
                    window.lanIP4 = lanIP4;
                    window.lanIP6 = lanIP6;
                    window.lanActive = lanActive;
                    window.lanIPv4active = lanData.ipv4active;
                    window.lanIPv6active = lanData.ipv6active;
                }
                
                if (result.other) {
                    // Process OTHER data
                    const otherData = result.other;
                    
                    // Process OTHER interfaces from 'other.interfaces' data
                    otherInterfaces = (otherData.interfaces || []).map(iface => ({
                        interface: iface.interface,
                        link: iface.state,
                        device: iface.state,
                        active: iface.active,
                        mac: iface.mac,
                        ipv4: iface.ipv4 || [],
                        ipv6: iface.ipv6 || [],
                        ipv4active: iface.ipv4active,
                        ipv6active: iface.ipv6active
                    }));
                }
                
                // Update UI
                updateWANCards();
                updateWLANCards();
                updateOtherCards();
                updateWANIPInfo();
                updateLANIPInfo();
                
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
