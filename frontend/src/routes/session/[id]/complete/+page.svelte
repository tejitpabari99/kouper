<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  const sid = $page.params.id;
  let summary = null;
  let error = '';
  let showDeleteConfirm = false;
  let sendSuccess = '';
  let sending = '';

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
    try {
      await api.deleteSession(sid);
      goto('/');
    } catch(e) {
      // show error
    }
  }

  async function sendSummary(method) {
    sending = method;
    try {
      const res = await api.sendSummary(sid, method);
      sendSuccess = res.message;
    } catch(e) {
      sendSuccess = `Queued (${method}) — integration pending.`;
    } finally {
      sending = '';
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
      <div style="font-size:15px; font-weight:600; margin-bottom:12px; color:#374151">Session Actions</div>
      <div style="display:flex; flex-direction:column; gap:8px">
        {#each (summary?.bookings || []) as booking, i}
          <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:#f9fafb; border-radius:6px">
            <span style="font-size:13px; color:#374151">{booking.specialty} — {booking.provider_name}</span>
            <button class="btn btn-secondary" style="font-size:12px; padding:4px 10px" on:click={() => goto(`/session/${sid}/referral/${booking.referral_index}/provider`)}>Edit</button>
          </div>
        {/each}
        <button class="btn btn-secondary" on:click={() => goto(`/session/${sid}`)}>Edit Entire Session</button>
        <button class="btn" style="background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;border-radius:8px;padding:10px 16px;font-weight:600;font-size:14px;cursor:pointer" on:click={() => showDeleteConfirm = true}>🗑 Delete Session</button>
      </div>
    </div>

    <div class="card">
      <div style="font-size:15px; font-weight:600; margin-bottom:12px; color:#374151">Send Summary to Patient</div>
      {#if sendSuccess}
        <div style="padding:12px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:14px; color:#15803d">
          ✓ {sendSuccess}
          <div style="font-size:12px; color:#6b7280; margin-top:4px">Note: SMS/email integration (Twilio/SendGrid) not yet connected — this is a mock confirmation.</div>
        </div>
      {:else}
        <div style="display:flex; gap:8px">
          <button class="btn btn-secondary" on:click={() => sendSummary('text')} disabled={sending}>
            {sending === 'text' ? 'Sending...' : '📱 Send via Text'}
          </button>
          <button class="btn btn-secondary" on:click={() => sendSummary('email')} disabled={sending}>
            {sending === 'email' ? 'Sending...' : '✉️ Send via Email'}
          </button>
        </div>
      {/if}
    </div>

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={printSummary}>🖨️ Print Summary</button>
      <button class="btn btn-primary" on:click={startNew}>Start New Session</button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading summary...</div>
  {/if}
</div>

{#if showDeleteConfirm}
  <div style="position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:200;display:flex;align-items:center;justify-content:center">
    <div style="background:white;border-radius:12px;padding:24px;width:320px;box-shadow:0 20px 60px rgba(0,0,0,0.2)">
      <div style="font-size:18px;font-weight:700;margin-bottom:8px">Delete Session?</div>
      <p style="color:#6b7280;font-size:14px;margin-bottom:20px">This will permanently delete all booking data for this patient. This cannot be undone.</p>
      <div style="display:flex;gap:10px;justify-content:flex-end">
        <button class="btn btn-secondary" on:click={() => showDeleteConfirm = false}>Cancel</button>
        <button style="background:#dc2626;color:white;border:none;border-radius:8px;padding:8px 16px;font-size:14px;font-weight:600;cursor:pointer" on:click={deleteSession}>Delete</button>
      </div>
    </div>
  </div>
{/if}

<style>
  @media print {
    :global(.btn), :global(.nav-row), :global(button) { display: none !important; }
    :global(.card) { box-shadow: none !important; border: 1px solid #e5e7eb !important; background: white !important; }
    :global(.screen) { max-width: 100% !important; padding: 0 !important; }
    :global(body) { background: white !important; }
  }
</style>
