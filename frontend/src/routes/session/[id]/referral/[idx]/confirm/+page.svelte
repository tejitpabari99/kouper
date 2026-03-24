<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  const idx = parseInt($page.params.idx);

  $: providerName = $page.url.searchParams.get('provider') || '';
  $: location = $page.url.searchParams.get('location') || '';
  $: specialty = $page.url.searchParams.get('specialty') || '';

  let state = null;
  let confirming = false;
  let error = '';
  let apptInfo = null;
  let scriptOpen = true;

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }
    // Load cached appointment info
    const key = `appointment_info_${sid}_${idx}`;
    const cached = sessionStorage.getItem(key);
    if (cached) {
      try { apptInfo = JSON.parse(cached); } catch(_) {}
    }
  });

  $: prefs = state?.patient_preferences;

  async function confirmBooking() {
    confirming = true;
    error = '';
    try {
      await api.confirmBooking(sid, {
        referral_index: idx,
        provider_name: providerName,
        specialty: specialty,
        location_name: location,
      });
      goto(`/session/${sid}`);
    } catch (e) {
      error = e.message;
      confirming = false;
    }
  }

  $: chatContext = [
    `Screen: Booking Confirmation (Step 6) — Referral ${idx + 1}`,
    state?.patient ? `Patient: ${state.patient.name} (DOB: ${state.patient.dob})` : '',
    `Provider: ${providerName}`,
    `Specialty: ${specialty}`,
    `Location: ${location}`,
    prefs ? [
      `Contact: ${prefs.contact_method} at ${prefs.best_contact_time}`,
      `Language: ${prefs.language}`,
      prefs.transportation_needs ? 'Transportation assistance needed: YES' : '',
      prefs.notes ? `Notes: ${prefs.notes}` : '',
    ].filter(Boolean).join('\n') : '',
    'Awaiting nurse confirmation to finalize booking.',
  ].filter(Boolean).join('\n');
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 6 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Booking Summary</div>
    <div style="color:#6b7280; font-size:14px; margin-top:4px">Please review before confirming</div>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <div class="card">
    <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Appointment Details</div>

    {#if state?.patient}
      <div class="detail-row"><span class="label">Patient</span><span class="value">{state.patient.name} (DOB: {state.patient.dob})</span></div>
    {/if}
    <div class="detail-row"><span class="label">Provider</span><span class="value">{providerName}</span></div>
    <div class="detail-row"><span class="label">Specialty</span><span class="value">{specialty}</span></div>
    <div class="detail-row"><span class="label">Location</span><span class="value">{location}</span></div>

    {#if apptInfo}
      <div class="detail-row"><span class="label">Appointment Type</span><span class="value">{apptInfo.appointment_type === 'ESTABLISHED' ? 'Established Patient' : 'New Patient'}</span></div>
      <div class="detail-row"><span class="label">Duration</span><span class="value">{apptInfo.duration_minutes} minutes</span></div>
      <div class="detail-row"><span class="label">Arrive Early</span><span class="value">{apptInfo.arrive_early_minutes} minutes before appointment</span></div>
    {/if}
  </div>

  {#if prefs}
    <div class="card">
      <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Follow-Up Plan</div>
      <div class="detail-row"><span class="label">Contact Method</span><span class="value">{prefs.contact_method}</span></div>
      <div class="detail-row"><span class="label">Best Time</span><span class="value">{prefs.best_contact_time}</span></div>
      <div class="detail-row"><span class="label">Language</span><span class="value">{prefs.language}</span></div>
      {#if prefs.transportation_needs}
        <div class="warning-row" style="margin-top:8px">⚠️ Transportation assistance needed &mdash; flag for care coordinator.</div>
      {/if}
    </div>
  {/if}

  <div class="card" style="border-left:4px solid #4f46e5">
    <button type="button" style="background:none;border:none;font-size:14px;font-weight:600;color:#4f46e5;cursor:pointer;padding:0;display:flex;align-items:center;gap:6px;width:100%;text-align:left" on:click={() => scriptOpen = !scriptOpen}>
      💬 What to Tell the Patient {scriptOpen ? '▾' : '▸'}
    </button>
    {#if scriptOpen}
      <div style="margin-top:12px; padding:12px 14px; background:#eef2ff; border-radius:6px; font-size:13px; line-height:1.7; color:#312e81">
        "I've submitted your referral request with <strong>{providerName}</strong> at <strong>{location}</strong>.
        {#if apptInfo}Please plan to arrive <strong>{apptInfo.arrive_early_minutes} minutes early</strong> for your <strong>{apptInfo.duration_minutes}-minute</strong> appointment.{/if}
        {#if prefs}The office will reach you by <strong>{prefs.contact_method}</strong> during the <strong>{prefs.best_contact_time}</strong>{/if} to confirm your appointment date and time.
        {#if prefs?.transportation_needs}Someone will also call you within 24 hours to arrange your transportation.{/if}"
      </div>
    {/if}
  </div>

  <div class="nav-row">
    <div style="display:flex; flex-direction:column; gap:6px">
      <button class="btn btn-secondary" style="font-size:13px" on:click={() => goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(providerName)}&specialty=${encodeURIComponent(specialty)}`)}>← Edit Location</button>
      <button class="btn btn-secondary" style="font-size:13px" on:click={() => goto(`/session/${sid}/referral/${idx}/preferences?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(location)}&specialty=${encodeURIComponent(specialty)}`)}>← Edit Preferences</button>
    </div>
    <button class="btn btn-success" on:click={confirmBooking} disabled={confirming}>
      {confirming ? 'Confirming...' : '✓ Confirm Booking'}
    </button>
  </div>

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
