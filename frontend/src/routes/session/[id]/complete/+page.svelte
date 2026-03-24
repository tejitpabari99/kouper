<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  const sid = $page.params.id;
  let summary = null;
  let error = '';
  let showDeleteConfirm = false;
  let deleting = false;
  let sendMethod = 'text';
  let sendContact = '';
  let sending = false;
  let sendResult = null;
  let sendError = '';

  onMount(async () => {
    try {
      summary = await api.getSummary(sid);
    } catch (e) {
      error = e.message;
    }
  });

  function startNew() {
    goto('/');
  }

  function printSummary() {
    window.print();
  }

  async function deleteSession() {
    deleting = true;
    try {
      await api.deleteSession(sid);
    } catch(_) {}
    goto('/');
  }

  async function sendToPatient() {
    sending = true;
    sendError = '';
    sendResult = null;
    try {
      const res = await api.sendSummary(sid, sendMethod, sendContact);
      sendResult = res.message;
    } catch(e) {
      sendError = e.message;
    } finally {
      sending = false;
    }
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Session Complete</div>
    <div class="screen-subtitle">
      {#if summary?.patient}{summary.patient.name} &mdash; {/if}{summary?.bookings?.length || 0} referral{summary?.bookings?.length !== 1 ? 's' : ''} processed
    </div>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if summary}
    <div class="card">
      <div style="font-size:15px; font-weight:600; margin-bottom:4px; color:#374151">Referral Requests Submitted</div>
      <div style="font-size:13px; color:#9ca3af; margin-bottom:16px">The provider's office will contact the patient to confirm the appointment date and time.</div>

      {#each summary.bookings as booking}
        <div style="padding:12px; background:#f0fdf4; border-radius:8px; margin-bottom:10px; border:1px solid #bbf7d0">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px">
            <span style="color:#16a34a; font-weight:700">&#10003;</span>
            <span style="font-weight:700">{booking.specialty} &mdash; {booking.provider_name}</span>
            <span class="badge badge-blue">{booking.appointment_type}</span>
          </div>
          <div style="font-size:13px; color:#374151">
            📍 {booking.location}
            {#if booking.provider_hours} &nbsp;&middot;&nbsp; 🕐 {booking.provider_hours}{/if}
          </div>
          <div style="font-size:13px; color:#374151; margin-top:4px">
            ⏰ Arrive <strong>{booking.arrival_minutes_early} minutes early</strong>
            &nbsp;&middot;&nbsp; Appointment: <strong>{booking.duration_minutes} min</strong>
          </div>
          {#if booking.provider_phone}
            <div style="font-size:13px; color:#6b7280; margin-top:4px">📞 {booking.provider_phone}</div>
          {/if}
        </div>
      {/each}
    </div>

    {#if summary.preferences}
      <div class="card">
        <div style="font-size:15px; font-weight:600; margin-bottom:12px; color:#374151">Follow-Up Reminders</div>
        <div style="font-size:14px; color:#374151">
          Scheduled via: <strong>{summary.preferences.contact_method}</strong>
          &nbsp;&middot;&nbsp; Best time: <strong>{summary.preferences.best_contact_time}</strong>
        </div>
        {#if summary.preferences.transportation_needs}
          <div class="warning-row" style="margin-top:10px">⚠️ Transportation assistance required &mdash; care coordinator follow-up needed.</div>
        {/if}
        {#if summary?.preferences?.notes}
          <div class="detail-row"><span class="label">Notes</span><span class="value">{summary.preferences.notes}</span></div>
        {/if}
      </div>
    {/if}

    <div class="card">
      <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Send Summary to Patient</div>
      <div class="form-row">
        <label>Method</label>
        <div class="radio-group">
          {#each [['text','Text Message'],['email','Email']] as [val,label]}
            <label class="radio-option" class:selected={sendMethod === val} style="cursor:pointer">
              <input type="radio" bind:group={sendMethod} value={val} style="display:none"/>
              {label}
            </label>
          {/each}
        </div>
      </div>
      <div class="form-row" style="margin-bottom:0">
        <label>{sendMethod === 'text' ? 'Phone Number' : 'Email Address'}</label>
        <input bind:value={sendContact} placeholder={sendMethod === 'text' ? '555-123-4567' : 'patient@example.com'} />
      </div>
      {#if sendResult}
        <div style="margin-top:10px; color:#16a34a; font-size:13px; font-weight:600">&#10003; {sendResult}</div>
      {/if}
      {#if sendError}
        <div class="error-msg">{sendError}</div>
      {/if}
      <div style="margin-top:12px">
        <button class="btn btn-primary" on:click={sendToPatient} disabled={sending || !sendContact.trim()}>
          {sending ? 'Sending...' : 'Send Summary \u2192'}
        </button>
      </div>
    </div>

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={printSummary}>&#128424; Print Summary</button>
      <button class="btn btn-primary" on:click={startNew}>Start New Session</button>
    </div>
    <div style="text-align:center; margin-top:12px">
      {#if showDeleteConfirm}
        <div style="padding:12px; background:#fef2f2; border:1px solid #fca5a5; border-radius:8px; font-size:13px; margin-bottom:8px">
          Delete this session permanently? This cannot be undone.
          <div style="margin-top:8px; display:flex; gap:8px; justify-content:center">
            <button class="btn btn-secondary" style="font-size:12px; padding:4px 12px" on:click={() => showDeleteConfirm = false}>Cancel</button>
            <button style="font-size:12px; padding:4px 12px; background:#dc2626; color:white; border:none; border-radius:6px; cursor:pointer" on:click={deleteSession} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Yes, Delete'}
            </button>
          </div>
        </div>
      {:else}
        <button style="background:none; border:none; color:#9ca3af; font-size:12px; cursor:pointer; text-decoration:underline" on:click={() => showDeleteConfirm = true}>
          Delete this session
        </button>
      {/if}
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading summary...</div>
  {/if}
</div>

<style>
  @media print {
    :global(.screen > div:first-child) { display: block !important; }
    :global(button), :global(.nav-row) { display: none !important; }
    :global(.card) { break-inside: avoid; box-shadow: none !important; border: 1px solid #e5e7eb !important; background: white !important; }
    :global(.screen) { max-width: 100% !important; padding: 0 !important; }
    :global(body) { background: white !important; }
  }
</style>
