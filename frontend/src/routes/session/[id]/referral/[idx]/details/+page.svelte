<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  const idx = parseInt($page.params.idx);

  let state = null;
  let error = '';
  let apptInfo = null;
  let apptLoading = true;
  let selectedLocation = '';

  $: providerName = $page.url.searchParams.get('provider') || '';
  $: specialtyParam = $page.url.searchParams.get('specialty') || '';

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    // Try sessionStorage first (pre-fetched by Step 3 guard C3)
    const key = `appointment_info_${sid}_${idx}`;
    const cached = sessionStorage.getItem(key);
    if (cached) {
      try {
        apptInfo = JSON.parse(cached);
        apptLoading = false;
        autoSelectLocation();
        return;
      } catch (_) {
        // Malformed cache — fall through to API call
      }
    }

    // Fallback: fetch directly
    if (providerName) {
      const sp = specialtyParam || state?.patient?.referred_providers?.[idx]?.specialty || '';
      try {
        apptInfo = await api.getAppointmentInfo(sid, providerName, sp);
        sessionStorage.setItem(key, JSON.stringify(apptInfo));
      } catch (e) {
        error = e.message;
      }
    }
    apptLoading = false;
    autoSelectLocation();
  });

  function autoSelectLocation() {
    if (apptInfo?.locations?.length === 1) {
      selectedLocation = apptInfo.locations[0].name;
    }
  }

  $: referral = state?.patient?.referred_providers?.[idx];
  $: specialty = specialtyParam || referral?.specialty || '';

  $: badgeClass = apptInfo?.appointment_type === 'ESTABLISHED' ? 'badge-established' : 'badge-new';
  $: badgeLabel = apptInfo?.appointment_type || '';

  function locationLabel(loc) {
    const days = Array.isArray(loc.days) ? loc.days.join(', ') : (loc.days || '');
    return `${loc.name} — ${days} ${loc.hours || ''}`.trim();
  }

  function proceed() {
    if (!selectedLocation) return;
    goto(`/session/${sid}/referral/${idx}/preferences?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(selectedLocation)}&specialty=${encodeURIComponent(specialty)}`);
  }

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }

  function changeProvider() {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }

  $: chatContext = [
    `Screen: Appointment Details (Step 4) — Referral ${idx + 1}`,
    `Provider: ${providerName}`,
    `Specialty: ${specialty}`,
    apptInfo ? [
      `Appointment type: ${apptInfo.appointment_type} (${apptInfo.duration_minutes} min, arrive ${apptInfo.arrive_early_minutes} min early)`,
      `Reason: ${apptInfo.reason}`,
      apptInfo.locations?.length
        ? `Available locations: ${apptInfo.locations.map(l => `${l.name} — ${Array.isArray(l.days) ? l.days.join(', ') : l.days} ${l.hours} — ${l.address} — ${l.phone}`).join('; ')}`
        : '',
      selectedLocation ? `Selected location: ${selectedLocation}` : 'Location not yet selected',
    ].filter(Boolean).join('\n') : 'Loading appointment info...',
  ].filter(Boolean).join('\n');
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 4 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Appointment Details</div>
    {#if providerName}<div style="color:#6b7280; font-size:14px; margin-top:4px">{providerName}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <!-- Structured appointment info (replaces LLM summary) -->
  {#if apptLoading}
    <div class="card" style="display:flex; align-items:center; gap:10px; color:#6b7280; font-size:14px">
      <div class="spinner"></div>
      Loading appointment information...
    </div>
  {:else if apptInfo}
    <div class="card appt-card">
      <div style="font-size:13px; font-weight:600; color:#6b7280; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.05em">Appointment Type</div>
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px">
        <span class="appt-badge {badgeClass}">{badgeLabel}</span>
        {#if apptInfo.duration_minutes}
          <span style="font-size:14px; color:#374151">· {apptInfo.duration_minutes} minutes</span>
        {/if}
      </div>
      {#if apptInfo.arrive_early_minutes}
        <div style="font-size:13px; color:#6b7280; margin-bottom:8px">
          Arrive {apptInfo.arrive_early_minutes} minutes early
        </div>
      {/if}
      {#if apptInfo.reason}
        <div style="font-size:13px; color:#374151; padding-top:8px; border-top:1px solid #e5e7eb">
          <span style="font-weight:600">Reason:</span> {apptInfo.reason}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Location dropdown (C5) -->
  {#if apptInfo?.locations}
    <div class="card">
      <div class="form-row">
        <label for="locationSelect">Location</label>
        <select id="locationSelect" bind:value={selectedLocation}>
          {#if apptInfo.locations.length > 1}
            <option value="" disabled selected>Select a location...</option>
          {/if}
          {#each apptInfo.locations as loc}
            <option value={loc.name}>{locationLabel(loc)}</option>
          {/each}
        </select>
      </div>
      {#if selectedLocation}
        {@const loc = apptInfo.locations.find(l => l.name === selectedLocation)}
        {#if loc?.address || loc?.phone}
          <div style="margin-top:8px; font-size:13px; color:#6b7280">
            {#if loc.address}<div>{loc.address}</div>{/if}
            {#if loc.phone}<div>Phone: {loc.phone}</div>{/if}
          </div>
        {/if}
      {/if}
      <div style="margin-top:10px">
        <button
          type="button"
          style="background:none; border:none; color:#3b82f6; font-size:13px; cursor:pointer; padding:0; text-decoration:underline"
          on:click={changeProvider}
        >
          ← Location not suitable? Change provider
        </button>
      </div>
    </div>
  {:else if !apptLoading}
    <!-- Fallback: plain text input if no locations available -->
    <div class="card">
      <div class="form-row">
        <label>Location Name</label>
        <input bind:value={selectedLocation} placeholder="e.g. PPTH Orthopedics or Jefferson Hospital" />
      </div>
      <div style="margin-top:10px">
        <button
          type="button"
          style="background:none; border:none; color:#3b82f6; font-size:13px; cursor:pointer; padding:0; text-decoration:underline"
          on:click={changeProvider}
        >
          ← Location not suitable? Change provider
        </button>
      </div>
    </div>
  {/if}

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={!selectedLocation || apptLoading}>
      Next → Patient Preferences
    </button>
  </div>

  <ChatPanel sessionId={sid} context={chatContext} />
</div>

<style>
  .appt-card {
    border-left: 4px solid #3b82f6;
  }

  .appt-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .badge-established {
    background: #dcfce7;
    color: #15803d;
  }

  .badge-new {
    background: #dbeafe;
    color: #1d4ed8;
  }

  select {
    width: 100%;
    padding: 9px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    background: #ffffff;
    color: #111827;
    cursor: pointer;
  }

  select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
