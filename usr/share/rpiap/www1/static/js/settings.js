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
            const response = await fetch('/static/settings.json');
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
        
        // Populate from JSON data (including "Not set" entry)
        countriesData.forEach(({ code, name }) => {
            const opt = document.createElement('option');
            opt.value = code;
            // If code is empty, show just the name, otherwise show "code (name)"
            opt.textContent = code ? `${code} (${name})` : name;
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
        
        // Add "Auto" (0) option as first
        const autoOpt = document.createElement('option');
        autoOpt.value = '0';
        autoOpt.textContent = '0 (Auto)';
        channelSelect.appendChild(autoOpt);
        
        const seen = new Map();

        countriesData.forEach((country) => {
            country.allowed_channels.forEach((ch) => {
                // Skip channel 0, as it's already added manually
                if (ch.id !== 0 && !seen.has(ch.id)) {
                    seen.set(ch.id, ch.description);
                }
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
        
        console.log('Channels populated:', allChannels.length + 1);
    }

    // ------------------------------
    // Channel Management
    // ------------------------------
    function updateChannelsForCountry(countryCode) {
        if (!channelSelect) {
            console.error('Channel select element not found');
            return;
        }
        
        // Convert undefined/null to empty string for "Not set" country
        const code = countryCode || '';
        
        // Find country in JSON data (including empty code for "Not set")
        const country = countriesData.find((c) => c.code === code);
        if (!country) {
            console.warn('Country not found for code:', code);
            return;
        }

        // Get allowed channels from country data
        const allowed = country.allowed_channels.map((ch) => String(ch.id));
        
        console.log('Updating channels for country:', code, 'allowed channels:', allowed);
        
        [...channelSelect.options].forEach((opt) => {
            const available = allowed.includes(opt.value);
            opt.disabled = !available;
            
            // Clean up text content - remove "(unavailable)" if present
            const baseText = opt.textContent.replace(' (unavailable)', '');
            
            if (!available && !baseText.includes('(unavailable)')) {
                opt.textContent = baseText + ' (unavailable)';
            } else if (available) {
                opt.textContent = baseText;
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
            countrySelect = document.getElementById('hostapd_country');
            channelSelect = document.getElementById('hostapd_channel');
        }
        
        try {
            console.log('Loading current settings...');
            const response = await fetch('/api/settings');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            const result = await response.json();
            console.log('Settings response:', result);
            
            if (!result.success || !result.settings) {
                throw new Error(result.error || 'Invalid response format');
            }

            const { hostapd_ssid, hostapd_password, hostapd_channel, hostapd_country } = result.settings;

            // Set form values
            const ssidField = document.getElementById('hostapd_ssid');
            const passwordField = document.getElementById('hostapd_password');
            
            if (ssidField) {
                ssidField.value = hostapd_ssid || '';
            } else {
                console.warn('SSID field not found');
            }
            
            if (passwordField) {
                passwordField.value = hostapd_password || '';
            } else {
                console.warn('Password field not found');
            }
            
            // Set country and update channels
            if (countrySelect) {
                const countryValue = hostapd_country || '';
                countrySelect.value = countryValue;
                updateChannelsForCountry(countryValue);
            } else {
                console.warn('Country select not found');
            }
            
            // Set channel - if not set, use 0
            if (channelSelect) {
                channelSelect.value = String(hostapd_channel || '0');
            } else {
                console.warn('Channel select not found');
            }
            
            console.log('Settings loaded successfully:', { hostapd_ssid, hostapd_channel, hostapd_country });
            
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
            const response = await fetch('/api/settings', {
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
        countrySelect = document.getElementById('hostapd_country');
        channelSelect = document.getElementById('hostapd_channel');

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
            
            // Initialize with default "Not set" country if no country is selected
            if (countrySelect && !countrySelect.value) {
                countrySelect.value = '';
                updateChannelsForCountry('');
            }
            
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
    window.togglePasswordVisibility = function(inputId) {
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
    };
    
    // Auto-initialize when page loads
    document.addEventListener('DOMContentLoaded', async () => {
        await initializeWLANData();
    });
    
    console.log('Settings.js loaded successfully');
})();

