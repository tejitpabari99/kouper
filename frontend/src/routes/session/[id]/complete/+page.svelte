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
  let reminders = [];
  let remindersOpen = false;
  let remindersLoaded = false;

  // A3: outcome logging per booking
  let outcomeOpen = {};       // { referral_index: bool }
  let outcomeForm = {};       // { referral_index: { date, status, notes } }
  let outcomeSaving = {};     // { referral_index: bool }
  let outcomeSaved = {};      // { referral_index: bool }
  let outcomeError = {};      // { referral_index: string }

  function toggleOutcome(idx) {
    outcomeOpen = { ...outcomeOpen, [idx]: !outcomeOpen[idx] };
    if (!outcomeForm[idx]) {
      outcomeForm = { ...outcomeForm, [idx]: { date: '', status: 'completed', notes: '' } };
    }
  }

  async function saveOutcome(booking) {
    const idx = booking.referral_index;
    const form = outcomeForm[idx];
    if (!form?.date || !form?.status) {
      outcomeError = { ...outcomeError, [idx]: 'Appointment date and status are required.' };
      return;
    }
    outcomeSaving = { ...outcomeSaving, [idx]: true };
    outcomeError = { ...outcomeError, [idx]: '' };
    try {
      await api.logOutcome({
        patient_id: summary.patient.id,
        session_id: sid,
        referral_index: idx,
        provider_name: booking.provider_name,
        specialty: booking.specialty,
        location: booking.location,
        appointment_date: form.date,
        status: form.status,
        nurse_notes: form.notes || '',
      });
      outcomeSaved = { ...outcomeSaved, [idx]: true };
      outcomeOpen = { ...outcomeOpen, [idx]: false };
    } catch (e) {
      outcomeError = { ...outcomeError, [idx]: e.message };
    } finally {
      outcomeSaving = { ...outcomeSaving, [idx]: false };
    }
  }

  async function loadReminders() {
    if (remindersLoaded) return;
    remindersLoaded = true;
    try {
      const res = await api.getReminders(sid);
      reminders = res.reminders || [];
    } catch (_) {
      reminders = [];
    }
  }

  onMount(async () => {
    try {
      summary = await api.getSummary(sid);
    } catch (e) {
      error = e.message;
    }
    api.logNurseEvent(sid, 'step_visited', { step: 'session_complete' });
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
          {#if booking.nurse_notes}
            <div style="font-size:12px; color:#6b7280; margin-top:8px; padding-top:8px; border-top:1px solid #e5e7eb; font-style:italic">
              📝 {booking.nurse_notes}
            </div>
          {/if}

          <!-- A3: outcome logging -->
          <div style="margin-top:12px; padding-top:12px; border-top:1px solid #e5e7eb">
            <div style="font-size:12px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px">Post-Appointment Outcome</div>
            {#if outcomeSaved[booking.referral_index]}
              <div style="font-size:13px; color:#16a34a; font-weight:600; padding:8px 10px; background:#f0fdf4; border-radius:6px; border:1px solid #bbf7d0">✓ Outcome logged — feeds back into future NEW/ESTABLISHED calculations</div>
            {:else}
              <div style="font-size:12px; color:#6b7280; margin-bottom:8px">Log what happened after the appointment. Completed visits update the patient's appointment type eligibility.</div>
              <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:8px">
                <div>
                  <label style="font-size:11px; color:#6b7280; display:block; margin-bottom:2px">Appointment Date</label>
                  <input
                    type="date"
                    value={outcomeForm[booking.referral_index]?.date || ''}
                    on:input={(e) => {
                      const f = outcomeForm[booking.referral_index] || { date: '', status: 'completed', notes: '' };
                      outcomeForm = { ...outcomeForm, [booking.referral_index]: { ...f, date: e.target.value } };
                    }}
                    style="font-size:12px; padding:4px 8px; border:1px solid #d1d5db; border-radius:4px"
                  />
                </div>
                <div>
                  <label style="font-size:11px; color:#6b7280; display:block; margin-bottom:2px">Status</label>
                  <select
                    value={outcomeForm[booking.referral_index]?.status || 'completed'}
                    on:change={(e) => {
                      const f = outcomeForm[booking.referral_index] || { date: '', status: 'completed', notes: '' };
                      outcomeForm = { ...outcomeForm, [booking.referral_index]: { ...f, status: e.target.value } };
                    }}
                    style="font-size:12px; padding:4px 8px; border:1px solid #d1d5db; border-radius:4px"
                  >
                    <option value="completed">✓ Completed</option>
                    <option value="no-show">✗ No-Show</option>
                    <option value="cancelled">— Cancelled</option>
                  </select>
                </div>
              </div>
              <div style="margin-bottom:8px">
                <label style="font-size:11px; color:#6b7280; display:block; margin-bottom:2px">Notes (optional)</label>
                <textarea
                  value={outcomeForm[booking.referral_index]?.notes || ''}
                  on:input={(e) => {
                    const f = outcomeForm[booking.referral_index] || { date: '', status: 'completed', notes: '' };
                    outcomeForm = { ...outcomeForm, [booking.referral_index]: { ...f, notes: e.target.value } };
                  }}
                  rows="2"
                  placeholder="e.g., Patient arrived on time, follow-up scheduled in 6 weeks"
                  style="width:100%; font-size:12px; padding:6px 8px; border:1px solid #d1d5db; border-radius:4px; resize:vertical; box-sizing:border-box; font-family:inherit"
                ></textarea>
              </div>
              {#if outcomeError[booking.referral_index]}
                <div style="font-size:12px; color:#dc2626; margin-bottom:6px">{outcomeError[booking.referral_index]}</div>
              {/if}
              <button
                class="btn btn-primary"
                style="font-size:12px; padding:5px 16px"
                on:click={() => saveOutcome(booking)}
                disabled={outcomeSaving[booking.referral_index]}
              >
                {outcomeSaving[booking.referral_index] ? 'Saving...' : 'Log Outcome'}
              </button>
            {/if}
          </div>
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
      <button
        on:click={() => { remindersOpen = !remindersOpen; if (remindersOpen) loadReminders(); }}
        style="background:none; border:none; padding:0; font-size:15px; font-weight:600; color:#374151; cursor:pointer; display:flex; align-items:center; gap:8px; width:100%"
      >
        <span>{remindersOpen ? '▾' : '▸'}</span>
        Scheduled Reminder Touchpoints
      </button>

      {#if remindersOpen}
        <div style="margin-top:12px">
          {#if reminders.length === 0}
            <div style="font-size:13px; color:#9ca3af">No reminders scheduled.</div>
          {:else}
            {#each summary?.bookings || [] as booking, i}
              {@const bookingReminders = reminders.filter(r => r.booking_referral_index === booking.referral_index)}
              {#if bookingReminders.length > 0}
                <div style="margin-bottom:14px">
                  <div style="font-size:13px; font-weight:600; color:#374151; margin-bottom:6px">
                    Referral {booking.referral_index + 1} — {booking.specialty}
                  </div>
                  {#each bookingReminders as r}
                    <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:8px; padding:8px 10px; background:#f9fafb; border-radius:6px; border:1px solid #e5e7eb">
                      <span style="color:{r.scheduled_for === 'pending_date' ? '#9ca3af' : '#16a34a'}; font-size:14px; flex-shrink:0; margin-top:1px">
                        {r.scheduled_for === 'pending_date' ? '○' : '✓'}
                      </span>
                      <div style="flex:1; min-width:0">
                        <div style="font-size:12px; font-weight:600; color:#374151; text-transform:capitalize">
                          {r.touchpoint.replace(/_/g, ' ')}
                        </div>
                        <div style="font-size:12px; color:#6b7280; margin-top:2px">
                          {r.channel} · {r.scheduled_for === 'pending_date' ? 'Pending appointment date' : 'Queued'}
                        </div>
                        <div style="font-size:12px; color:#9ca3af; margin-top:4px; font-style:italic; overflow:hidden; text-overflow:ellipsis; white-space:nowrap">
                          "{r.message_template}"
                        </div>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            {/each}
          {/if}
        </div>
      {/if}
    </div>

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
