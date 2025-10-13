(() => {
  let countriesData = [];
  let allChannels = [];

  const form = document.getElementById('wlan-form');
  const countrySelect = document.getElementById('wlancountry');
  const channelSelect = document.getElementById('wlanchannel');
  const statusBanner = document.getElementById('status-banner');
  const statusMessage = document.getElementById('status-message');
  const statusClose = document.getElementById('status-close');

  // ------------------------------
  // Inicialization
  // ------------------------------
  document.addEventListener('DOMContentLoaded', async () => {
    if (!form || !countrySelect || !channelSelect) return;

    // Status banner close
    if (statusClose) statusClose.addEventListener('click', hideStatusBanner);

    // Load JSON + config
    await loadCountriesAndChannels();
    await loadCurrentSettings();

    // Handle country change
    countrySelect.addEventListener('change', (e) => {
      updateChannelsForCountry(e.target.value);
    });

    // Handle form submit
    form.addEventListener('submit', onFormSubmit);
  });

  // ------------------------------
  // Load data from settings.json
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
    countrySelect.innerHTML = '';
    countriesData.forEach(({ code, name }) => {
      const opt = document.createElement('option');
      opt.value = code;
      opt.textContent = `${code} (${name})`;
      countrySelect.appendChild(opt);
    });
  }

  function populateAllChannels() {
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
  }

  // ------------------------------
  // Update channels
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
  // Load configuration
  // ------------------------------
  async function loadCurrentSettings() {
    try {
      const response = await fetch('/cgi-bin/settings.py');
      if (!response.ok) throw new Error('Load failed');

      const { success, settings, error } = await response.json();
      if (!success || !settings) throw new Error(error || 'Invalid config');

      const { wlanssid, wlanpassword, wlanchannel, wlancountry } = settings;

      document.getElementById('wlanssid').value = wlanssid || '';
      document.getElementById('wlanpassword').value = wlanpassword || '';
      countrySelect.value = wlancountry || '';
      updateChannelsForCountry(wlancountry);
      channelSelect.value = String(wlanchannel || '');
    } catch (err) {
      console.warn('Could not load current config:', err);
    }
  }

  // ------------------------------
  // Send form
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
        showStatusBanner(res.message || 'Settings saved successfully.', 'success');
      } else {
        const msg = res.error || 'Error saving settings.';
        if (res.traceback) console.error('Server traceback:', res.traceback);
        showStatusBanner(msg, 'error');
      }
    } catch (err) {
      console.error('Network or parsing error:', err);
      showStatusBanner('Network error or invalid response.', 'error');
    } finally {
      disable(form, false);
    }
  }

  // ------------------------------
  // Other functions
  // ------------------------------
  function disable(form, on) {
    Array.from(form.elements).forEach((el) => (el.disabled = !!on));
  }

  function showStatusBanner(message, type = 'success') {
    if (!statusBanner || !statusMessage) return;

    statusMessage.textContent = message;
    statusBanner.className = `status-banner ${type}`;
    statusBanner.style.display = 'block';
    document.body.classList.add('has-banner');

    const timeout = type === 'error' ? 60000 : 5000;
    clearTimeout(statusBanner._timeout);
    statusBanner._timeout = setTimeout(hideStatusBanner, timeout);
  }

  function hideStatusBanner() {
    if (!statusBanner) return;
    statusBanner.style.display = 'none';
    document.body.classList.remove('has-banner');
    clearTimeout(statusBanner._timeout);
  }
})();
