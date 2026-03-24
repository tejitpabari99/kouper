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
  let showDistance = false;
  let patientAddress = '';
  let distanceResult = null;
  let distanceLoading = false;
  let insuranceInfo = null;
  let insuranceLoading = false;

  $: providerName = $page.url.searchParams.get('provider') || '';
  $: specialtyParam = $page.url.searchParams.get('specialty') || '';

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    api.logNurseEvent(sid, 'step_visited', { step: 'appointment_details', referral_index: idx });

    // Try sessionStorage first (pre-fetched by Step 3 guard C3)
    const key = `appointment_info_${sid}_${idx}`;
    const cached = sessionStorage.getItem(key);
    if (cached) {
      try {
        apptInfo = JSON.parse(cached);
        apptLoading = false;
        autoSelectLocation();
        await loadInsuranceInfo();
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
    await loadInsuranceInfo();
  });

  function autoSelectLocation() {
    if (apptInfo?.locations?.length === 1) {
      selectedLocation = apptInfo.locations[0].name;
    }
  }

  async function loadInsuranceInfo() {
    if (!providerName || !specialty) return;
    insuranceLoading = true;
    try {
      insuranceInfo = await api.checkInsurance(sid, providerName, specialty);
    } catch (_) {
      insuranceInfo = null;
    } finally {
      insuranceLoading = false;
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
    goto(`/session/${sid}/referral/${idx}/schedule?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(selectedLocation)}&specialty=${encodeURIComponent(specialty)}`);
  }

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }

  function changeProvider() {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }

  async function fetchDistance() {
    if (!patientAddress.trim() || !selectedLocation) return;
    distanceLoading = true;
    distanceResult = null;
    try {
      const loc = apptInfo?.locations?.find(l => l.name === selectedLocation);
      distanceResult = await api.getDistance(patientAddress, loc?.address || selectedLocation);
    } catch(e) {
      distanceResult = { error: e.message };
    } finally {
      distanceLoading = false;
    }
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
      <div style="font-size:12px; color:#6b7280; margin-top:4px">
        {apptInfo.appointment_type === 'ESTABLISHED'
          ? 'Established patient — has seen this provider/specialty before within 5 years'
          : 'New patient — first visit with this provider/specialty'}
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

  {#if insuranceInfo}
    <div class="card" style="border-left:4px solid {insuranceInfo.accepted === false ? '#ef4444' : insuranceInfo.prior_auth_required ? '#f59e0b' : '#16a34a'}">
      <div style="font-size:13px; font-weight:600; color:#374151; margin-bottom:8px">Insurance Status</div>
      {#if insuranceInfo.accepted === true}
        <div style="color:#16a34a; font-size:14px; font-weight:600; margin-bottom:4px">✓ {insuranceInfo.patient_insurance} accepted</div>
        {#if insuranceInfo.prior_auth_required}
          <div style="padding:8px 12px; background:#fffbeb; border:1px solid #fde68a; border-radius:6px; font-size:13px; color:#92400e; margin-top:8px">
            ⚠ Prior authorization may be required. Contact {insuranceInfo.patient_insurance} before the appointment date.
          </div>
        {/if}
      {:else if insuranceInfo.accepted === false}
        <div style="color:#dc2626; font-size:14px; font-weight:600; margin-bottom:6px">✗ {insuranceInfo.patient_insurance} not accepted at this provider</div>
        {#if insuranceInfo.self_pay_rate}
          <div style="font-size:13px; color:#374151; margin-bottom:8px">Estimated self-pay rate: <strong>${insuranceInfo.self_pay_rate}/visit</strong></div>
        {/if}
        {#if insuranceInfo.patient_script}
          <div style="padding:10px 12px; background:#fef2f2; border-radius:6px; font-size:13px; color:#991b1b; margin-bottom:8px">
            <div style="font-weight:600; margin-bottom:4px">Script for patient:</div>
            "{insuranceInfo.patient_script}"
          </div>
        {/if}
        {#if insuranceInfo.alternatives?.length}
          <div style="font-size:13px; font-weight:600; color:#374151; margin-bottom:4px">Covered alternatives:</div>
          {#each insuranceInfo.alternatives as alt}
            <div style="font-size:13px; color:#374151; padding:6px 10px; background:#f9fafb; border-radius:6px; margin-bottom:4px">
              {alt.name} · {alt.location}
              {#if !alt.accepting_new_patients}<span style="font-size:11px; color:#9ca3af"> (not accepting new patients)</span>{/if}
            </div>
          {/each}
        {/if}
      {:else if insuranceInfo.self_pay}
        <div style="font-size:13px; color:#6b7280">Patient is self-pay.
          {#if insuranceInfo.self_pay_rate}Estimated rate: <strong>${insuranceInfo.self_pay_rate}/visit</strong>{/if}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Location selection (C6/C7) -->
  {#if apptInfo?.locations}
    <div class="card">
      <div class="form-row">
        <label>Location</label>
        {#if apptInfo.locations.length === 1}
          {@const loc = apptInfo.locations[0]}
          <div style="padding:12px 14px; border:2px solid #16a34a; border-radius:8px; background:#f0fdf4">
            <div style="font-size:11px; color:#15803d; font-weight:600; margin-bottom:4px; text-transform:uppercase">Only available location — auto-selected</div>
            <div style="font-weight:600; font-size:14px">{loc.name} ✓</div>
            <div style="font-size:13px; color:#6b7280; margin-top:4px">{Array.isArray(loc.days) ? loc.days.map(d=>d.slice(0,3)).join(', ') : loc.days} · {loc.hours}</div>
            {#if loc.address}<div style="font-size:12px; color:#9ca3af; margin-top:2px">{loc.address}</div>{/if}
            {#if loc.phone}<div style="font-size:12px; color:#9ca3af">{loc.phone}</div>{/if}
          </div>
        {:else}
          <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px">
            {#each apptInfo.locations as loc}
              {@const selected = selectedLocation === loc.name}
              <div
                on:click={() => selectedLocation = loc.name}
                style="padding:12px 14px; border:2px solid {selected ? '#16a34a' : '#e5e7eb'}; border-radius:8px; cursor:pointer; background:{selected ? '#f0fdf4' : 'white'}; transition: all 0.15s"
              >
                <div style="display:flex; justify-content:space-between; align-items:center">
                  <div style="font-weight:600; font-size:14px; color:#111827">{loc.name} {selected ? '✓' : ''}</div>
                  {#if selected}<span style="font-size:11px; background:#dcfce7; color:#15803d; padding:2px 8px; border-radius:9999px; font-weight:600">Selected</span>{/if}
                </div>
                <div style="font-size:13px; color:#6b7280; margin-top:4px">
                  {Array.isArray(loc.days) ? loc.days.map(d => d.slice(0,3)).join(', ') : loc.days} · {loc.hours || ''}
                </div>
                {#if loc.address}<div style="font-size:12px; color:#9ca3af; margin-top:2px">{loc.address}</div>{/if}
                {#if loc.phone}<div style="font-size:12px; color:#9ca3af">{loc.phone}</div>{/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Distance calculator (C10) -->
      <div style="margin-top:12px">
        <button type="button" style="background:none;border:none;color:#3b82f6;font-size:13px;cursor:pointer;padding:0" on:click={() => showDistance = !showDistance}>
          {showDistance ? '▾' : '▸'} How far is this location for the patient?
        </button>
        {#if showDistance}
          <div style="margin-top:8px; padding:12px 14px; background:#f9fafb; border-radius:8px; border:1px solid #e5e7eb">
            <div style="display:flex; gap:8px; align-items:center">
              <input bind:value={patientAddress} placeholder="Patient's address or zip code" style="flex:1; padding:8px 10px; border:1px solid #d1d5db; border-radius:6px; font-size:13px" on:keydown={(e) => e.key==='Enter' && fetchDistance()} />
              <button class="btn btn-secondary" style="font-size:13px; padding:8px 14px" on:click={fetchDistance} disabled={distanceLoading || !patientAddress.trim()}>
                {distanceLoading ? '...' : 'Get Distance'}
              </button>
            </div>
            {#if distanceResult && !distanceResult.error}
              <div style="margin-top:8px; font-size:14px; color:#374151; font-weight:600">
                ~{distanceResult.miles} miles · ~{distanceResult.drive_minutes} min drive
              </div>
              <div style="font-size:11px; color:#9ca3af; margin-top:2px">{distanceResult.note}</div>
            {:else if distanceResult?.error}
              <div style="margin-top:8px; font-size:13px; color:#dc2626">{distanceResult.error}</div>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Change Provider button (C9) -->
      <div style="margin-top:12px">
        <button class="btn btn-secondary" on:click={changeProvider}>← Choose a Different Provider</button>
      </div>
    </div>
  {:else if !apptLoading}
    <!-- Fallback: plain text input if no locations available -->
    <div class="card">
      <div class="form-row">
        <label>Location Name</label>
        <input bind:value={selectedLocation} placeholder="e.g. PPTH Orthopedics or Jefferson Hospital" />
      </div>
      <div style="margin-top:12px">
        <button class="btn btn-secondary" on:click={changeProvider}>← Choose a Different Provider</button>
      </div>
    </div>
  {/if}

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={!selectedLocation || apptLoading}>
      Next → Schedule Appointment
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
