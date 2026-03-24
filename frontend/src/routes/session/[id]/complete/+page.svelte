<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  const sid = $page.params.id;
  let summary = null;
  let error = '';

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
      <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Bookings Confirmed</div>

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
      </div>
    {/if}

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={printSummary}>🖨️ Print Summary</button>
      <button class="btn btn-primary" on:click={startNew}>Start New Session</button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading summary...</div>
  {/if}
</div>
