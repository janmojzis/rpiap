(() => {
    'use strict';
    
    // State management
    let countriesData = [];
    let allChannels = [];
    let wlanDataLoaded = false;

    // DOM elements
    const form = document.getElementById('wlan-form');
    const countrySelect = document.getElementById('wlancountry');
    const channelSelect = document.getElementById('wlanchannel');

    // ------------------------------
    // Initialization
    // ------------------------------
    document.addEventListener('DOMContentLoaded', async () => {
        if (form) {
            form.addEventListener('submit', onFormSubmit);
        }
    });

    // ------------------------------
    // Data Loading
    // ------------------------------
    async function loadCountriesAndChannels() {
        try {
            const response = await fetch('settings.json');
            if (!response.ok) throw new Error('Failed to load settings.json');

            const data = await response.json();
            countriesData = data.countries || [];

            populateCountries();
            populateAllChannels();
        } catch (err) {
            console.error('Failed to load channel data:', err);
        }
    }

    function populateCountries() {
        if (!countrySelect) {
            console.error('Country select element not found');
            return;
        }
        
        countrySelect.innerHTML = '';
        countriesData.forEach(({ code, name }) => {
            const opt = document.createElement('option');
            opt.value = code;
            opt.textContent = `${code} (${name})`;
            countrySelect.appendChild(opt);
        });
        
        console.log('Countries populated:', countriesData.length);
    }

    function populateAllChannels() {
        if (!channelSelect) {
            console.error('Channel select element not found');
            return;
        }
        
        channelSelect.innerHTML = '';
        const seen = new Map();

        countriesData.forEach((country) => {
            country.allowed_channels.forEach((ch) => {
                if (!seen.has(ch.id)) seen.set(ch.id, ch.description);
            });
        });

        allChannels = Array.from(seen, ([id, description]) => ({ id, description }))
            .sort((a, b) => Number(a.id) - Number(b.id));

        allChannels.forEach(({ id, description }) => {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = description;
            opt.disabled = true;
            channelSelect.appendChild(opt);
        });
        
        console.log('Channels populated:', allChannels.length);
    }

    // ------------------------------
    // Channel Management
    // ------------------------------
    function updateChannelsForCountry(countryCode) {
        const country = countriesData.find((c) => c.code === countryCode);
        if (!country) return;

        const allowed = country.allowed_channels.map((ch) => String(ch.id));
        [...channelSelect.options].forEach((opt) => {
            const available = allowed.includes(opt.value);
            opt.disabled = !available;
            if (!available && !opt.textContent.includes('(unavailable)')) {
                opt.textContent += ' (unavailable)';
            } else if (available) {
                opt.textContent = opt.textContent.replace(' (unavailable)', '');
            }
        });
    }

    // ------------------------------
    // Settings Management
    // ------------------------------
    async function loadCurrentSettings() {
        try {
            const response = await fetch('/cgi-bin/settings.py');
            if (!response.ok) throw new Error('Load failed');

            const { success, settings, error } = await response.json();
            if (!success || !settings) throw new Error(error || 'Invalid config');

            const { wlanssid, wlanpassword, wlanchannel, wlancountry } = settings;

            // Set form values
            const ssidField = document.getElementById('wlanssid');
            const passwordField = document.getElementById('wlanpassword');
            
            if (ssidField) ssidField.value = wlanssid || '';
            if (passwordField) passwordField.value = wlanpassword || '';
            
            // Set country and update channels
            if (countrySelect) {
                countrySelect.value = wlancountry || '';
                updateChannelsForCountry(wlancountry);
            }
            
            // Set channel
            if (channelSelect) {
                channelSelect.value = String(wlanchannel || '');
            }
            
            console.log('Settings loaded:', { wlanssid, wlanpassword, wlanchannel, wlancountry });
            
            if (window.showStatusMessage) {
                window.showStatusMessage('Settings loaded successfully', 'success', 3000);
            }
        } catch (err) {
            console.warn('Could not load current config:', err);
            if (window.showStatusMessage) {
                window.showStatusMessage('Error loading settings: ' + err.message, 'error', 1000000);
            }
        }
    }

    // ------------------------------
    // Form Handling
    // ------------------------------
    async function onFormSubmit(e) {
        e.preventDefault();

        const formData = new FormData(form);
        disable(form, true);

        try {
            const response = await fetch('/cgi-bin/settings.py', {
                method: 'POST',
                body: formData,
            });

            const res = await response.json();

            if (response.ok && res.success) {
                if (window.showStatusMessage) {
                    window.showStatusMessage(res.message || 'Settings saved successfully.', 'success');
                }
            } else {
                const msg = res.error || 'Error saving settings.';
                if (res.traceback) console.error('Server traceback:', res.traceback);
                if (window.showStatusMessage) {
                    window.showStatusMessage(msg, 'error');
                }
            }
        } catch (err) {
            console.error('Network or parsing error:', err);
            if (window.showStatusMessage) {
                window.showStatusMessage('Network error or invalid response.', 'error');
            }
        } finally {
            disable(form, false);
        }
    }

    function disable(form, on) {
        Array.from(form.elements).forEach((el) => (el.disabled = !!on));
    }

    // ------------------------------
    // WLAN Data Initialization
    // ------------------------------
    async function initializeWLANData() {
        if (!form || !countrySelect || !channelSelect) {
            console.error('WLAN form elements not found');
            return;
        }

        try {
            // Load JSON data first
            await loadCountriesAndChannels();
            
            // Wait a bit for DOM to be ready
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Load current settings
            await loadCurrentSettings();

            // Handle country change
            countrySelect.addEventListener('change', (e) => {
                updateChannelsForCountry(e.target.value);
            });

            wlanDataLoaded = true;
        } catch (err) {
            console.error('Failed to initialize WLAN data:', err);
            if (window.showStatusMessage) {
                window.showStatusMessage('Error initializing WLAN settings', 'error', 5000);
            }
        }
    }

    // ------------------------------
    // Global Functions
    // ------------------------------
    window.initializeWLANData = initializeWLANData;
    window.loadCurrentSettings = loadCurrentSettings;
    
    console.log('Settings.js loaded successfully');
})();
