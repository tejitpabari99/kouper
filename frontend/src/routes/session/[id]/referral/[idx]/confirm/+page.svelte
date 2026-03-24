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

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
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

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/preferences?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(location)}&specialty=${encodeURIComponent(specialty)}`);
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 6 of 7 &mdash; Referral {idx + 1}</div>
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

    <div class="info-row" style="margin-top:12px">
      ℹ️ The assistant has determined the appointment type (NEW/ESTABLISHED) and arrival time based on the patient's history. Review the details screen if needed.
    </div>
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

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Edit</button>
    <button class="btn btn-success" on:click={confirmBooking} disabled={confirming}>
      {confirming ? 'Confirming...' : '\u2713 Confirm Booking'}
    </button>
  </div>

  <ChatPanel sessionId={sid} />
</div>
