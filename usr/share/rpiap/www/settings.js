(() => {
    'use strict';
    
    // State management
    let countriesData = [];
    let allChannels = [];
    let wlanDataLoaded = false;

    // DOM elements (will be set when initializing)
    let form = null;
    let countrySelect = null;
    let channelSelect = null;

    // ------------------------------
    // Initialization
    // ------------------------------
    document.addEventListener('DOMContentLoaded', async () => {
        console.log('Settings.js DOMContentLoaded');
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
        if (!channelSelect) {
            console.error('Channel select element not found');
            return;
        }
        
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
        // Ensure DOM elements are available
        if (!form) {
            form = document.getElementById('wlan-form');
            countrySelect = document.getElementById('wlancountry');
            channelSelect = document.getElementById('wlanchannel');
        }
        
        try {
            console.log('Loading current settings...');
            const response = await fetch('/cgi-bin/settings.py');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            const result = await response.json();
            console.log('Settings response:', result);
            
            if (!result.success || !result.settings) {
                throw new Error(result.error || 'Invalid response format');
            }

            const { wlanssid, wlanpassword, wlanchannel, wlancountry } = result.settings;

            // Set form values
            const ssidField = document.getElementById('wlanssid');
            const passwordField = document.getElementById('wlanpassword');
            
            if (ssidField) {
                ssidField.value = wlanssid || '';
            } else {
                console.warn('SSID field not found');
            }
            
            if (passwordField) {
                passwordField.value = wlanpassword || '';
            } else {
                console.warn('Password field not found');
            }
            
            // Set country and update channels
            if (countrySelect) {
                countrySelect.value = wlancountry || '';
                updateChannelsForCountry(wlancountry);
            } else {
                console.warn('Country select not found');
            }
            
            // Set channel
            if (channelSelect) {
                channelSelect.value = String(wlanchannel || '');
            } else {
                console.warn('Channel select not found');
            }
            
            console.log('Settings loaded successfully:', { wlanssid, wlanchannel, wlancountry });
            
            if (window.showStatusMessage) {
                window.showStatusMessage('Settings loaded successfully', 'success', 3000);
            }
        } catch (err) {
            console.error('Failed to load current settings:', err);
            if (window.showStatusMessage) {
                window.showStatusMessage('Error loading settings: ' + err.message, 'error', 5000);
            }
        }
    }

    // ------------------------------
    // Form Handling
    // ------------------------------
    async function onFormSubmit(e) {
        e.preventDefault();

        if (!form) {
            console.error('Form not found');
            return;
        }

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
        // Get DOM elements when actually needed
        form = document.getElementById('wlan-form');
        countrySelect = document.getElementById('wlancountry');
        channelSelect = document.getElementById('wlanchannel');

        if (!form || !countrySelect || !channelSelect) {
            console.error('WLAN form elements not found');
            return;
        }

        console.log('Initializing WLAN data, form found:', !!form);

        try {
            // Attach form submit event listener
            form.removeEventListener('submit', onFormSubmit); // Remove any existing listener
            form.addEventListener('submit', onFormSubmit);
            console.log('Form submit event listener attached');

            // Load JSON data first
            await loadCountriesAndChannels();
            
            // Wait a bit for DOM to be ready
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Load current settings
            await loadCurrentSettings();

            // Handle country change
            countrySelect.removeEventListener('change', onCountryChange); // Remove any existing listener
            countrySelect.addEventListener('change', onCountryChange);

            wlanDataLoaded = true;
            console.log('WLAN data initialization completed');
        } catch (err) {
            console.error('Failed to initialize WLAN data:', err);
            if (window.showStatusMessage) {
                window.showStatusMessage('Error initializing WLAN settings', 'error', 5000);
            }
        }
    }

    function onCountryChange(e) {
        updateChannelsForCountry(e.target.value);
    }

    // ------------------------------
    // Global Functions
    // ------------------------------
    window.initializeWLANData = initializeWLANData;
    window.loadCurrentSettings = loadCurrentSettings;
    
    console.log('Settings.js loaded successfully');
})();
