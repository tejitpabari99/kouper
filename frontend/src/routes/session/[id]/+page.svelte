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

  $: referrals = state?.patient?.referred_providers || [];
  $: bookings = state?.bookings || [];
  $: bookedIndexes = new Set(bookings.map(b => b.referral_index));
  $: allBooked = referrals.length > 0 && referrals.every((_, i) => bookedIndexes.has(i));
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 2 of 7</div>
    <div class="screen-subtitle">Referrals Overview</div>
    {#if state?.patient}<div style="color:#6b7280; font-size:14px; margin-top:4px">{state.patient.name}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if state}
    <div>
      <p style="font-size:14px; color:#6b7280; margin-bottom:16px">
        Following hospital discharge, the following appointments need booking:
      </p>

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
            {/if}
          {:else}
            <button class="btn btn-primary" on:click={() => bookReferral(idx)}>
              Book This →
            </button>
          {/if}
        </div>
      {/each}
    </div>

    {#if state.patient?.appointments?.some(a => a.status === 'noshow')}
      <div class="warning-row">
        ⚠️ Note: This patient has a previous no-show on record. Consider confirming transportation needs.
      </div>
    {/if}

    {#if allBooked}
      <div class="nav-row">
        <div></div>
        <button class="btn btn-success" on:click={finishSession}>Complete Session →</button>
      </div>
    {/if}
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {/if}

  <ChatPanel sessionId={sid} />
</div>
