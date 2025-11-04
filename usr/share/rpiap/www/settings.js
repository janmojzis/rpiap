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

    // Settings management is now handled by HTMX
    // Form submission and loading are done via HTMX attributes

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
            // Load JSON data for country options
            await loadCountriesAndChannels();
            
            // Load current settings via HTMX
            // The form will be loaded via HTMX when the section is shown
            // Just trigger the HTMX load if form is empty
            const ssidInput = form.querySelector('input[name="wlanssid"]');
            if (ssidInput && !ssidInput.value && typeof htmx !== 'undefined') {
                htmx.ajax('GET', '/cgi-bin/settings.py?format=html', {
                    target: '#wlan-form',
                    swap: 'outerHTML'
                });
            }

            wlanDataLoaded = true;
            console.log('WLAN data initialization completed');
        } catch (err) {
            console.error('Failed to initialize WLAN data:', err);
        }
    }

    function onCountryChange(e) {
        updateChannelsForCountry(e.target.value);
    }

    // ------------------------------
    // Global Functions
    // ------------------------------
    window.initializeWLANData = initializeWLANData;
    
    console.log('Settings.js loaded successfully');
})();
