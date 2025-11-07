(() => {
    'use strict';
    
    // State management
    let isMenuOpen = false;
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
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.add('hidden');
            }
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
    // Data Management
    // ------------------------------
    async function loadAllData() {
        try {
            const response = await fetch('/api/interfaces');
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
        
        // Clear OTHER interface container and show loading message
        const otherContainer = document.getElementById('other-interfaces-container');
        if (otherContainer) {
            otherContainer.innerHTML = '<div class="loading-message">Loading other interfaces...</div>';
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
            
            // Create card HTML WITH IP addresses
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
            
            // Create card HTML WITHOUT IP addresses
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
            
            // Create card HTML WITH IP addresses
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
    window.showUserMenu = function() {
        showStatusMessage('User menu - feature will be implemented later', 'error', 3000);
    };
    window.showStatusMessage = showStatusMessage;
    window.hideStatusMessage = hideStatusMessage;
    window.refreshDashboard = refreshDashboard;
    
    console.log('Index.js loaded successfully');
})();

