<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  let state = null;
  let error = '';

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }
  });

  function bookReferral(idx) {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }

  function finishSession() {
    goto(`/session/${sid}/complete`);
  }

  // B8: startOver navigates back to home
  function startOver() {
    goto('/');
  }

  $: referrals = state?.patient?.referred_providers || [];
  $: bookings = state?.bookings || [];
  $: bookedIndexes = new Set(bookings.map(b => b.referral_index));
  $: allBooked = referrals.length > 0 && referrals.every((_, i) => bookedIndexes.has(i));

  $: chatContext = state ? [
    `Screen: Referrals Overview (Step 2)`,
    `Patient: ${state.patient?.name} | DOB: ${state.patient?.dob} | PCP: ${state.patient?.pcp}`,
    ...referrals.map((r, i) => {
      const b = bookings.find(b => b.referral_index === i);
      return b
        ? `Referral ${i+1} (${r.specialty}): BOOKED — ${b.provider_name} at ${b.location} (${b.appointment_type})`
        : `Referral ${i+1} (${r.specialty}): Not yet booked${r.provider ? ` — referred to ${r.provider}` : ' — provider TBD'}`;
    }),
    state.patient?.appointments?.some(a => a.status === 'noshow') ? 'Note: Patient has a previous no-show on record.' : '',
  ].filter(Boolean).join('\n') : '';
</script>

<div class="screen">
  <div style="display:flex; justify-content:space-between; align-items:flex-start">
    <div>
      <!-- B10: replace "Step 2 of 7" with Referrals Overview + progress -->
      <div class="screen-title">Referrals Overview</div>
      <div class="screen-subtitle">Step 2</div>
      {#if state?.patient}
        <div style="color:#6b7280; font-size:14px; margin-top:2px">{state.patient.name}</div>
        <div style="font-size:13px; color:#6b7280; margin-top:2px">
          {bookedIndexes.size} of {referrals.length} referral{referrals.length !== 1 ? 's' : ''} booked
        </div>
      {/if}
    </div>
    <!-- B8: wrong patient back link -->
    <button
      style="background:none; border:none; color:#6b7280; font-size:13px; cursor:pointer; text-decoration:underline; margin-top:4px; white-space:nowrap"
      on:click={startOver}
    >
      ← Wrong patient? Start over
    </button>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if state}
    <div>
      <p style="font-size:14px; color:#6b7280; margin-bottom:16px">
        Following hospital discharge, the following appointments need booking:
      </p>

      <!-- B6: no-show warning ABOVE the referrals list -->
      {#if state.patient?.appointments?.some(a => a.status === 'noshow')}
        <div class="warning-row" style="margin-bottom:16px">
          ⚠️ Note: This patient has a previous no-show on record. Consider confirming transportation needs.
        </div>
      {/if}

      {#each referrals as referral, idx}
        <div class="provider-card" class:highlighted={bookedIndexes.has(idx)}>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px">
            <div>
              <div class="provider-name">
                Referral {idx + 1} &mdash; {referral.specialty}
              </div>
              <div class="provider-specialty">
                {referral.provider || 'Provider TBD'}
              </div>
            </div>
            <span class="badge" class:badge-grey={!bookedIndexes.has(idx)} class:badge-green={bookedIndexes.has(idx)}>
              {bookedIndexes.has(idx) ? '✓ Booked' : 'Not Booked'}
            </span>
          </div>
          {#if bookedIndexes.has(idx)}
            {@const booking = bookings.find(b => b.referral_index === idx)}
            {#if booking}
              <div style="font-size:13px; color:#374151">
                <strong>{booking.provider_name}</strong> &mdash; {booking.location} &mdash; {booking.appointment_type}
              </div>
              <!-- B9: appointment time note on booked cards -->
              <div style="font-size:12px; color:#9ca3af; margin-top:4px; font-style:italic">
                The provider's office will contact the patient to confirm the appointment date and time.
              </div>
            {/if}
          {:else}
            <button class="btn btn-primary" on:click={() => bookReferral(idx)}>
              Book This →
            </button>
          {/if}
        </div>
      {/each}
    </div>

    <!-- B7: Complete Session button always visible, disabled when not all booked -->
    <div class="nav-row">
      <div></div>
      {@const remaining = referrals.filter((_, i) => !bookedIndexes.has(i)).length}
      <button class="btn btn-success" on:click={finishSession} disabled={!allBooked}>
        {allBooked ? 'Complete Session →' : `Complete Session (${remaining} referral${remaining !== 1 ? 's' : ''} remaining)`}
      </button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {/if}

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
