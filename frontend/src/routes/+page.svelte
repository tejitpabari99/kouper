<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client.js';
  import { sessionId, patient } from '$lib/stores/session.js';

  let searchInput = '';
  let searchResults = [];
  let showDropdown = false;
  let selectedPatient = null;
  let loading = false;
  let loadedPatient = null;
  let createdSessionId = null;
  let error = '';
  let debounceTimer = null;

  function onSearchInput() {
    clearTimeout(debounceTimer);
    selectedPatient = null;
    showDropdown = false;

    if (!searchInput.trim()) {
      searchResults = [];
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const results = await api.searchPatients(searchInput.trim());
        searchResults = results || [];
        showDropdown = searchResults.length > 0;
      } catch (e) {
        searchResults = [];
        showDropdown = false;
      }
    }, 300);
  }

  function pickPatient(p) {
    selectedPatient = p;
    searchInput = p.name;
    showDropdown = false;
    searchResults = [];
  }

  function clearSelection() {
    selectedPatient = null;
    searchInput = '';
    searchResults = [];
    showDropdown = false;
    loadedPatient = null;
    createdSessionId = null;
    error = '';
  }

  async function loadPatient() {
    if (!selectedPatient) return;
    loading = true;
    error = '';
    loadedPatient = null;
    try {
      const session = await api.createSession();
      createdSessionId = session.session_id;
      sessionId.set(createdSessionId);
      const p = await api.startSession(createdSessionId, selectedPatient.id);
      loadedPatient = p;
      patient.set(p);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function proceed() {
    goto(`/session/${createdSessionId}`);
  }

  function handleBlur() {
    // Delay hiding dropdown so click events on results fire first
    setTimeout(() => { showDropdown = false; }, 150);
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Care Coordinator</div>
    <div class="screen-subtitle">Patient Lookup</div>
  </div>

  <div class="card">
    {#if selectedPatient && !loadedPatient}
      <div style="margin-bottom:12px; padding:12px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; display:flex; align-items:center; gap:12px">
        <span style="color:#16a34a; font-size:18px">&#10003;</span>
        <div style="flex:1">
          <div style="font-weight:600; font-size:15px">{selectedPatient.name}</div>
          <div style="font-size:13px; color:#6b7280">DOB: {selectedPatient.dob} &nbsp;·&nbsp; {selectedPatient.phone}</div>
        </div>
        <button class="btn btn-secondary" style="font-size:12px; padding:4px 10px" on:click={clearSelection}>Change</button>
      </div>
    {/if}

    {#if !selectedPatient || loadedPatient}
      <div class="form-row" style="position:relative">
        <label for="patientSearch">Search by name, phone, email, or ID</label>
        <input
          id="patientSearch"
          bind:value={searchInput}
          on:input={onSearchInput}
          on:blur={handleBlur}
          on:focus={() => { if (searchResults.length > 0) showDropdown = true; }}
          placeholder="e.g. John Smith, 555-1234, john@example.com"
          autocomplete="off"
        />

        {#if showDropdown && searchResults.length > 0}
          <div class="search-dropdown">
            {#each searchResults as result}
              <div
                class="search-dropdown-item"
                on:mousedown|preventDefault={() => pickPatient(result)}
              >
                <div style="font-weight:600; font-size:14px">{result.name}</div>
                <div style="font-size:12px; color:#6b7280">DOB: {result.dob} &nbsp;·&nbsp; {result.phone}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <div style="margin-top:12px">
      <button
        class="btn btn-primary"
        on:click={loadPatient}
        disabled={loading || !selectedPatient || !!loadedPatient}
      >
        {loading ? 'Loading...' : 'Load Patient'}
      </button>
    </div>

    {#if error}
      <div class="error-msg">{error}</div>
    {/if}

    {#if loadedPatient}
      <div style="margin-top:16px; padding:16px; background:#f9fafb; border-radius:8px; border:1px solid #e5e7eb">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px">
          <span style="color:#16a34a; font-size:18px">&#10003;</span>
          <span style="font-size:18px; font-weight:700">{loadedPatient.name}</span>
        </div>
        <div class="detail-row"><span class="label">Date of Birth</span><span class="value">{loadedPatient.dob}</span></div>
        <div class="detail-row"><span class="label">Primary Care Provider</span><span class="value">{loadedPatient.pcp}</span></div>
        <div class="detail-row"><span class="label">EHR ID</span><span class="value">{loadedPatient.ehrId}</span></div>
      </div>

      <div class="info-row" style="margin-top:12px">
        &#8505;&#65039; Please confirm patient identity verbally before proceeding.
      </div>
    {/if}
  </div>

  {#if loadedPatient}
    <div class="nav-row">
      <div></div>
      <button class="btn btn-primary" on:click={proceed}>Continue to Referrals &#8594;</button>
    </div>
  {/if}
</div>

<style>
  .search-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 100;
    max-height: 240px;
    overflow-y: auto;
  }

  .search-dropdown-item {
    padding: 10px 14px;
    cursor: pointer;
    border-bottom: 1px solid #f3f4f6;
  }

  .search-dropdown-item:last-child {
    border-bottom: none;
  }

  .search-dropdown-item:hover {
    background: #eff6ff;
  }
</style>
