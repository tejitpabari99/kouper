<!--
  Referrals Overview — Step 2 of the booking flow.

  This is the central hub of a session. After the patient is loaded (Step 1),
  the nurse lands here to see all outstanding referrals and their booking status.

  Key behaviours:
    - Loads full session state on mount (patient info, existing bookings)
    - Checks for colocated provider suggestions (appointments that could be
      combined into one trip) and shows a dismissable banner
    - Warns if the patient has a prior no-show on record
    - "Book This" button for unbooked referrals gates on insurance being set:
        if not yet set → redirect to /insurance?next=<idx>
        if set         → go directly to /referral/<idx>/provider
    - "Complete Session" is disabled until every referral has a booking
    - Booking status and referral count are derived reactively from state

  The `chatContext` string is assembled from live state and passed to
  ChatPanel so the LLM knows which referrals are booked vs. pending.
-->
<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  let state = null;
  let error = '';
  let colocatedSuggestions = [];
  let colocatedDismissed = false;

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    api.logNurseEvent(sid, 'step_visited', { step: 'referrals_overview' });

    // Persist dismiss state to sessionStorage so a page refresh doesn't
    // re-show the banner the nurse already dismissed this visit
    colocatedDismissed = sessionStorage.getItem(`coloc_dismissed_${sid}`) === 'true';

    try {
      colocatedSuggestions = await api.getColocatedSuggestions(sid);
    } catch (_) {
      colocatedSuggestions = [];
    }
  });

  // Guard: if insurance hasn't been captured yet, capture it before
  // proceeding to provider selection
  function bookReferral(idx) {
    if (!state?.insurance) {
      goto(`/session/${sid}/insurance?next=${idx}`);
    } else {
      goto(`/session/${sid}/referral/${idx}/provider`);
    }
  }

  function finishSession() {
    goto(`/session/${sid}/complete`);
  }

  // B8: startOver navigates back to home
  function startOver() {
    goto('/');
  }

  function dismissColocated() {
    colocatedDismissed = true;
    sessionStorage.setItem(`coloc_dismissed_${sid}`, 'true');
  }

  // Reactive derivations from state — recompute whenever state changes
  $: referrals = state?.patient?.referred_providers || [];
  $: bookings = state?.bookings || [];
  // Build a Set of booked indexes for O(1) lookup in the template
  $: bookedIndexes = new Set(bookings.map(b => b.referral_index));
  $: allBooked = referrals.length > 0 && referrals.every((_, i) => bookedIndexes.has(i));

  // chatContext is rebuilt whenever state or bookings change so the LLM always
  // has a current picture of what's booked and what's pending
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
          {#if state.insurance}
            &nbsp;·&nbsp;
            <span style="color:{state.insurance === 'Self-Pay' ? '#7c3aed' : '#374151'}">
              {state.insurance}
            </span>
            <button
              style="background:none; border:none; color:#9ca3af; font-size:11px; cursor:pointer; text-decoration:underline; padding:0; margin-left:4px"
              on:click={() => goto(`/session/${sid}/insurance?next=0`)}
            >edit</button>
          {:else}
            &nbsp;·&nbsp; <span style="color:#dc2626; font-size:12px; font-weight:600">Insurance not set</span>
          {/if}
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

      <!-- Colocated suggestion banner: shown once per session unless dismissed -->
      {#if colocatedSuggestions.length > 0 && !colocatedDismissed}
        {#each colocatedSuggestions as suggestion}
          <div style="margin-bottom:16px; padding:14px 16px; background:#eef2ff; border:1px solid #c7d2fe; border-radius:8px; display:flex; align-items:flex-start; gap:12px">
            <span style="font-size:18px; flex-shrink:0">💡</span>
            <div style="flex:1">
              <div style="font-weight:600; font-size:14px; color:#3730a3; margin-bottom:4px">Scheduling Tip — {suggestion.location_name}</div>
              <div style="font-size:13px; color:#4338ca">{suggestion.message}</div>
              <div style="font-size:12px; color:#6366f1; margin-top:4px">{suggestion.address}</div>
            </div>
            <button on:click={dismissColocated} style="background:none; border:none; color:#6366f1; cursor:pointer; font-size:16px; line-height:1; flex-shrink:0">&times;</button>
          </div>
        {/each}
      {/if}

      <!-- B6: no-show warning ABOVE the referrals list -->
      {#if state.patient?.appointments?.some(a => a.status === 'noshow')}
        <div class="warning-row" style="margin-bottom:16px">
          ⚠️ Note: This patient has a previous no-show on record. Consider confirming transportation needs.
        </div>
      {/if}

      {#each referrals as referral, idx}
        <!-- highlighted class applied to booked cards (green border via CSS) -->
        <div class="provider-card" class:highlighted={bookedIndexes.has(idx)}>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px">
            <div>
              <div class="provider-name">
                Referral {idx + 1} &mdash; {referral.specialty}
                {#if referral.urgency === 'urgent' || referral.urgency === 'stat'}
                  <span style="display:inline-block; padding:2px 8px; background:{referral.urgency === 'stat' ? '#fef2f2' : '#fff7ed'}; color:{referral.urgency === 'stat' ? '#dc2626' : '#c2410c'}; border-radius:9999px; font-size:11px; font-weight:700; text-transform:uppercase; margin-left:6px">
                    {referral.urgency === 'stat' ? '🚨 STAT' : '⚡ URGENT'}
                  </span>
                {/if}
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
              <div style="font-size:12px; color:#9ca3af; margin-top:4px; font-style:italic">
                The provider's office will contact the patient to confirm the appointment date and time.
              </div>
              <div style="margin-top:10px">
                <button class="btn btn-secondary" style="font-size:12px; padding:4px 12px" on:click={() => bookReferral(idx)}>
                  ✏ Edit Booking
                </button>
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
      <button class="btn btn-success" on:click={finishSession} disabled={!allBooked}>
        {#if allBooked}Complete Session →{:else}Complete Session ({referrals.filter((_, i) => !bookedIndexes.has(i)).length} referral{referrals.filter((_, i) => !bookedIndexes.has(i)).length !== 1 ? 's' : ''} remaining){/if}
      </button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {/if}

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
