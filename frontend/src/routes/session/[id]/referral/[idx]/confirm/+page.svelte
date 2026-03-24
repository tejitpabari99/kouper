<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  const idx = parseInt($page.params.idx);

  $: providerName = $page.url.searchParams.get('provider') || '';
  $: location = $page.url.searchParams.get('location') || '';
  $: specialty = $page.url.searchParams.get('specialty') || '';
  $: scheduledDatetime = $page.url.searchParams.get('scheduled_datetime') || '';

  let state = null;
  let confirming = false;
  let error = '';
  let apptInfo = null;
  let scriptOpen = true;
  let nurseNotes = '';
  let insuranceInfo = null;
  let insuranceAcknowledged = false;

  // Post-booking feedback
  let bookingConfirmed = false;
  let feedbackRating = 0;
  let feedbackComment = '';
  let feedbackSubmitting = false;
  let feedbackSubmitted = false;
  let feedbackNote = '';

  async function loadInsuranceForConfirm() {
    if (!providerName || !specialty) return;
    try {
      insuranceInfo = await api.checkInsurance(sid, providerName, specialty);
    } catch (_) {}
  }

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    api.logNurseEvent(sid, 'step_visited', { step: 'booking_confirmation', referral_index: idx });

    // Load cached appointment info
    const cacheKey = `appointment_info_${sid}_${idx}`;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      try { apptInfo = JSON.parse(cached); } catch(_) {}
    } else {
      const prov = $page.url.searchParams.get('provider') || '';
      const spec = $page.url.searchParams.get('specialty') || '';
      if (prov && spec) {
        try { apptInfo = await api.getAppointmentInfo(sid, prov, spec); } catch(_) {}
      }
    }
    await loadInsuranceForConfirm();
  });

  $: prefs = state?.patient_preferences;

  async function confirmBooking() {
    confirming = true;
    error = '';
    if (insuranceInfo?.accepted === false && !insuranceAcknowledged) {
      error = 'Please confirm the patient has been informed of the self-pay rate before proceeding.';
      confirming = false;
      return;
    }
    try {
      await api.confirmBooking(sid, {
        referral_index: idx,
        provider_name: providerName,
        specialty: specialty,
        location_name: location,
        nurse_notes: nurseNotes,
        scheduled_datetime: scheduledDatetime || undefined,
      });
      bookingConfirmed = true;
    } catch (e) {
      error = e.message;
      confirming = false;
    }
  }

  async function submitFeedback() {
    if (!feedbackRating) return;
    feedbackSubmitting = true;
    try {
      const res = await api.submitBookingFeedback({
        session_id: sid,
        referral_index: idx,
        provider_name: providerName,
        specialty: specialty,
        rating: feedbackRating,
        comment: feedbackComment,
      });
      feedbackNote = res.note;
      feedbackSubmitted = true;
    } catch (_) {
      feedbackSubmitted = true;
      feedbackNote = 'Feedback stored locally. In production, this would be emailed to the care quality team.';
    } finally {
      feedbackSubmitting = false;
    }
  }

  function continueToOverview() {
    goto(`${base}/session/${sid}`);
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

    {#if scheduledDatetime}
      <div class="detail-row">
        <span class="label">Appointment</span>
        <span class="value">{new Date(scheduledDatetime).toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span>
      </div>
    {/if}

    {#if apptInfo}
      <div class="detail-row">
        <span class="label">Type</span>
        <span class="value">
          <span class="badge {apptInfo.appointment_type === 'NEW' ? 'badge-green' : 'badge-blue'}">{apptInfo.appointment_type}</span>
          <span style="font-size:12px; color:#6b7280; margin-left:6px">{apptInfo.appointment_type === 'NEW' ? 'First visit with this provider' : 'Follow-up visit'}</span>
        </span>
      </div>
      <div class="detail-row"><span class="label">Duration</span><span class="value">{apptInfo.duration_minutes} minutes</span></div>
      <div class="detail-row"><span class="label">Arrive Early</span><span class="value">{apptInfo.arrive_early_minutes} min before appointment</span></div>
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

  <div class="card">
    <div style="font-size:15px; font-weight:600; margin-bottom:12px; color:#374151">Internal Notes</div>
    <div class="form-row" style="margin-bottom:0">
      <label style="font-size:13px; color:#6b7280">For care record only — not sent to patient</label>
      <textarea
        bind:value={nurseNotes}
        rows="2"
        placeholder="e.g., Patient concerned about copay, discussed self-pay options. Prefers morning calls."
        style="padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:13px; resize:vertical; width:100%; box-sizing:border-box; font-family:inherit"
      ></textarea>
    </div>
  </div>

  {#if insuranceInfo?.accepted === false}
    <div class="card" style="border-left:4px solid #ef4444">
      <div style="color:#dc2626; font-size:14px; font-weight:600; margin-bottom:8px">⚠ Insurance Not Covered</div>
      <div style="font-size:13px; color:#374151; margin-bottom:10px">
        {insuranceInfo.patient_insurance} is not accepted. Self-pay rate: <strong>{insuranceInfo.self_pay_rate ? '$' + insuranceInfo.self_pay_rate : 'unknown'}</strong>
      </div>
      <label style="display:flex; align-items:flex-start; gap:8px; cursor:pointer">
        <input type="checkbox" bind:checked={insuranceAcknowledged} style="width:16px; height:16px; margin-top:2px; accent-color:#2563eb" />
        <span style="font-size:13px; color:#374151">I have informed the patient of the self-pay rate and they wish to proceed with this provider.</span>
      </label>
    </div>
  {/if}

  {#if bookingConfirmed}
    <!-- Post-booking feedback form -->
    <div class="card" style="border-left:4px solid #16a34a">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px">
        <span style="color:#16a34a; font-size:20px">✓</span>
        <div style="font-weight:700; font-size:15px; color:#15803d">Booking Confirmed</div>
      </div>

      {#if !feedbackSubmitted}
        <div style="font-size:14px; font-weight:600; color:#374151; margin-bottom:8px">How was your experience with this booking?</div>
        <div style="display:flex; gap:6px; margin-bottom:10px">
          {#each [1,2,3,4,5] as star}
            <button
              on:click={() => feedbackRating = star}
              style="background:none; border:none; font-size:26px; cursor:pointer; line-height:1; padding:0; color:{feedbackRating >= star ? '#f59e0b' : '#d1d5db'}"
            >★</button>
          {/each}
          {#if feedbackRating}
            <span style="font-size:13px; color:#6b7280; align-self:center; margin-left:4px">
              {['','Poor','Fair','Good','Very good','Excellent'][feedbackRating]}
            </span>
          {/if}
        </div>
        <div style="margin-bottom:10px">
          <textarea
            bind:value={feedbackComment}
            rows="2"
            placeholder="Optional comment — e.g. 'Provider selection could be easier to filter'"
            style="width:100%; font-size:13px; padding:8px 10px; border:1px solid #d1d5db; border-radius:6px; resize:vertical; box-sizing:border-box; font-family:inherit"
          ></textarea>
        </div>
        <div style="display:flex; gap:10px; align-items:center">
          <button
            class="btn btn-primary"
            style="font-size:13px"
            on:click={submitFeedback}
            disabled={!feedbackRating || feedbackSubmitting}
          >
            {feedbackSubmitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
          <button
            style="background:none; border:none; color:#9ca3af; font-size:13px; cursor:pointer; text-decoration:underline"
            on:click={continueToOverview}
          >Skip</button>
        </div>
      {:else}
        <div style="font-size:13px; color:#16a34a; font-weight:600; margin-bottom:6px">✓ Thank you for your feedback!</div>
        <div style="font-size:12px; color:#6b7280; margin-bottom:14px">{feedbackNote}</div>
        <button class="btn btn-primary" on:click={continueToOverview}>Continue →</button>
      {/if}
    </div>
  {:else}
    <div class="nav-row">
      <div style="display:flex; flex-direction:column; gap:6px">
        <button class="btn btn-secondary" style="font-size:13px" on:click={() => goto(`${base}/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(providerName)}&specialty=${encodeURIComponent(specialty)}`)}>← Edit Location</button>
        <button class="btn btn-secondary" style="font-size:13px" on:click={() => goto(`${base}/session/${sid}/referral/${idx}/preferences?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(location)}&specialty=${encodeURIComponent(specialty)}`)}>← Edit Preferences</button>
      </div>
      <button class="btn btn-success" on:click={confirmBooking} disabled={confirming || (insuranceInfo?.accepted === false && !insuranceAcknowledged)}>
        {confirming ? 'Confirming...' : '✓ Confirm Booking'}
      </button>
    </div>
  {/if}

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
