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
  let existingSession = null;
  let identityVerified = false;
  let showNewSessionModal = false;

  function onSearchInput() {
    clearTimeout(debounceTimer);
    selectedPatient = null;
    existingSession = null;
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

  // B1: session check happens immediately on patient pick
  async function pickPatient(p) {
    selectedPatient = p;
    searchInput = p.name;
    showDropdown = false;
    searchResults = [];
    existingSession = null;
    identityVerified = false;
    error = '';

    try {
      existingSession = await api.getSessionByPatient(p.id);
    } catch (_) {
      existingSession = null; // 404 = no prior session
    }
  }

  function clearSelection() {
    selectedPatient = null;
    searchInput = '';
    searchResults = [];
    showDropdown = false;
    loadedPatient = null;
    createdSessionId = null;
    error = '';
    existingSession = null;
    identityVerified = false;
    showNewSessionModal = false;
  }

  // B2: single action — create session, load patient, navigate
  async function confirmAndBegin() {
    if (!selectedPatient) return;
    loading = true;
    error = '';
    try {
      const session = await api.createSession();
      createdSessionId = session.session_id;
      sessionId.set(createdSessionId);
      const p = await api.startSession(createdSessionId, selectedPatient.id);
      loadedPatient = p;
      patient.set(p);
      goto(`/session/${createdSessionId}`);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function continueExisting() {
    goto(`/session/${existingSession.session_id}`);
  }

  function openNewSessionModal() {
    showNewSessionModal = true;
  }

  function cancelNewSessionModal() {
    showNewSessionModal = false;
  }

  function handleBlur() {
    setTimeout(() => { showDropdown = false; }, 150);
  }

  // B3: derive session state for button logic
  $: sessionComplete = existingSession && existingSession.step === 'complete';
  $: sessionInProgress = existingSession && existingSession.step !== 'complete';
  // primary button disabled if no patient or identity not verified
  $: primaryDisabled = loading || !selectedPatient || !identityVerified;
</script>

<!-- B3: "Start New Session" confirmation modal -->
{#if showNewSessionModal}
  <div style="position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:200; display:flex; align-items:center; justify-content:center">
    <div style="background:#fff; border-radius:12px; padding:28px 32px; max-width:420px; width:90%; box-shadow:0 8px 32px rgba(0,0,0,0.18)">
      <div style="font-weight:700; font-size:16px; margin-bottom:10px">Start a new session?</div>
      <div style="font-size:14px; color:#374151; margin-bottom:20px">
        This will create a new session. The existing session will still be accessible.
      </div>
      <div style="display:flex; gap:10px; justify-content:flex-end">
        <button class="btn btn-secondary" on:click={cancelNewSessionModal}>Cancel</button>
        <button class="btn btn-primary" on:click={() => { showNewSessionModal = false; confirmAndBegin(); }}>Confirm</button>
      </div>
    </div>
  </div>
{/if}

<div class="screen">
  <div>
    <div class="screen-title">Care Coordinator</div>
    <div class="screen-subtitle">Patient Lookup</div>
  </div>

  <div class="card">
    <!-- Selected patient confirmation card (B5: richer card) -->
    {#if selectedPatient}
      <div style="margin-bottom:12px; padding:12px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; display:flex; align-items:center; gap:12px">
        <span style="color:#16a34a; font-size:18px">✓</span>
        <div style="flex:1">
          <div style="font-weight:600; font-size:15px">{selectedPatient.name}</div>
          <div style="font-size:13px; color:#6b7280">DOB: {selectedPatient.dob}</div>
          <div style="font-size:13px; color:#6b7280">{selectedPatient.phone}</div>
          <div style="font-size:11px; color:#9ca3af; font-family:monospace">ID: {selectedPatient.id}</div>
        </div>
        <button class="btn btn-secondary" style="font-size:12px; padding:4px 10px" on:click={clearSelection}>Change</button>
      </div>
    {/if}

    <!-- Search input — always visible when no patient selected -->
    {#if !selectedPatient}
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

        <!-- B5: richer dropdown results -->
        {#if showDropdown && searchResults.length > 0}
          <div class="search-dropdown">
            {#each searchResults as result}
              <div
                class="search-dropdown-item"
                on:mousedown|preventDefault={() => pickPatient(result)}
              >
                <div style="font-weight:600; font-size:14px">{result.name}</div>
                <div style="font-size:12px; color:#6b7280">DOB: {result.dob}</div>
                <div style="font-size:12px; color:#6b7280">{result.phone}</div>
                <div style="font-size:11px; color:#9ca3af; font-family:monospace">ID: {result.id}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- B4: mandatory identity verification checkbox -->
    {#if selectedPatient}
      <div style="margin-top:12px; display:flex; align-items:center; gap:8px">
        <input
          id="identityCheck"
          type="checkbox"
          bind:checked={identityVerified}
          style="width:16px; height:16px; cursor:pointer; accent-color:#2563eb"
        />
        <label for="identityCheck" style="font-size:14px; color:#374151; cursor:pointer; user-select:none">
          I have verbally confirmed the patient's name and date of birth
        </label>
      </div>
    {/if}

    {#if error}
      <div class="error-msg">{error}</div>
    {/if}

    <!-- B3: session-state-aware primary button + secondary "Start New Session" -->
    {#if selectedPatient}
      <div style="margin-top:16px; display:flex; flex-direction:column; gap:8px; align-items:flex-start">
        {#if sessionComplete}
          <!-- Existing session, all done -->
          <button
            class="btn btn-primary"
            disabled={primaryDisabled}
            on:click={continueExisting}
          >
            Review Completed Session →
          </button>
          <button
            style="background:none; border:none; color:#6b7280; font-size:13px; cursor:pointer; text-decoration:underline; padding:0"
            disabled={loading}
            on:click={openNewSessionModal}
          >
            Start New Session
          </button>
        {:else if sessionInProgress}
          <!-- Existing session, in progress -->
          <button
            class="btn btn-primary"
            disabled={primaryDisabled}
            on:click={continueExisting}
          >
            Continue Session →
          </button>
          <button
            style="background:none; border:none; color:#6b7280; font-size:13px; cursor:pointer; text-decoration:underline; padding:0"
            disabled={loading}
            on:click={openNewSessionModal}
          >
            Start New Session
          </button>
        {:else}
          <!-- No existing session -->
          <button
            class="btn btn-primary"
            disabled={primaryDisabled}
            on:click={confirmAndBegin}
          >
            {#if loading}
              <span style="display:inline-flex; align-items:center; gap:6px">
                <svg style="animation:spin 1s linear infinite; width:14px; height:14px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
                Loading...
              </span>
            {:else}
              Confirm &amp; Begin Booking →
            {/if}
          </button>
        {/if}
      </div>
    {/if}
  </div>
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
    max-height: 280px;
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

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
