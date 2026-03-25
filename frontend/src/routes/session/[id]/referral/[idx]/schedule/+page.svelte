<!--
  Schedule Appointment — Step 5 of the referral booking flow.

  Displays available appointment slots grouped by week in collapsible panels.
  The nurse picks a time slot; it is persisted to sessionStorage so that
  navigating back and forward preserves the selection.

  Key behaviours:
    - Slots are fetched from the backend (which may call an external scheduling
      API or return mock data depending on the environment)
    - Slots are grouped by week, then further bucketed by day for display
    - The first week is auto-expanded on load
    - Selected slot is stored in sessionStorage keyed by session + referral index
      so the confirm page can read it if the nurse revisits this step
    - Provider/location/specialty are passed through query params to maintain
      a clean navigation chain back to the overview
-->
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
  let slotGroups = [];
  let loading = true;
  let error = '';
  let selectedSlot = null;
  let openWeeks = {};

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    // Restore a previously selected slot if the nurse navigated away and back
    const cached = sessionStorage.getItem(`slot_${sid}_${idx}`);
    if (cached) {
      try { selectedSlot = JSON.parse(cached); } catch(_) {}
    }

    try {
      const data = await api.getAppointmentSlots(sid, providerName, location);
      slotGroups = data.slots_by_week || [];
      // Auto-open the first week so the nurse sees slots immediately
      if (slotGroups.length > 0) {
        openWeeks = { 0: true };
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  // Group a week's flat slot array into { dayKey: slots[] } for day-level headers
  function slotsByDay(group) {
    return Object.entries(group.slots.reduce((acc, s) => {
      const key = s.date + '|' + s.day_name;
      if (!acc[key]) acc[key] = [];
      acc[key].push(s);
      return acc;
    }, {}));
  }

  function selectSlot(slot) {
    selectedSlot = slot;
    // Persist so the confirm page can read the datetime without re-fetching
    sessionStorage.setItem(`slot_${sid}_${idx}`, JSON.stringify(slot));
  }

  function toggleWeek(i) {
    openWeeks = { ...openWeeks, [i]: !openWeeks[i] };
  }

  function proceed() {
    if (!selectedSlot) return;
    const params = new URLSearchParams({
      provider: providerName,
      location,
      specialty,
      // ISO-ish datetime string passed through to the confirm page
      scheduled_datetime: selectedSlot.date + 'T' + selectedSlot.start_time + ':00',
    });
    goto(`/session/${sid}/referral/${idx}/preferences?${params}`);
  }

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(providerName)}&specialty=${encodeURIComponent(specialty)}`);
  }

  $: chatContext = [
    `Screen: Schedule Appointment (Step 5) — Referral ${idx + 1}`,
    `Provider: ${providerName}`,
    `Location: ${location}`,
    `Specialty: ${specialty}`,
    selectedSlot ? `Selected slot: ${selectedSlot.display}` : 'No time slot selected yet',
  ].filter(Boolean).join('\n');
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 5 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Schedule Appointment</div>
    {#if providerName}<div style="color:#6b7280; font-size:14px; margin-top:4px">{providerName} · {location}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <!-- Sticky selection summary shown once a slot is picked -->
  {#if selectedSlot}
    <div style="padding:12px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center">
      <div>
        <div style="font-size:12px; color:#6b7280; margin-bottom:2px">Selected appointment time</div>
        <div style="font-weight:600; font-size:14px; color:#15803d">✓ {selectedSlot.display}</div>
      </div>
      <button
        on:click={() => { selectedSlot = null; sessionStorage.removeItem(`slot_${sid}_${idx}`); }}
        style="background:none; border:none; color:#6b7280; font-size:12px; cursor:pointer; text-decoration:underline"
      >Clear</button>
    </div>
  {/if}

  {#if loading}
    <div class="card" style="color:#6b7280; font-size:14px">Loading available slots...</div>
  {:else if slotGroups.length === 0}
    <div class="card" style="color:#9ca3af; font-size:14px; text-align:center; padding:24px">
      No available slots found in the next 3 weeks. The office will contact the patient to schedule.
    </div>
  {:else}
    <!-- Collapsible week panels with time-slot buttons -->
    {#each slotGroups as group, wi}
      <div class="card" style="margin-bottom:10px; padding:12px 14px">
        <button
          on:click={() => toggleWeek(wi)}
          style="background:none; border:none; padding:0; font-size:14px; font-weight:600; color:#374151; cursor:pointer; display:flex; align-items:center; gap:6px; width:100%; text-align:left"
        >
          <span>{openWeeks[wi] ? '▾' : '▸'}</span>
          {group.week_label}
          <span style="font-size:12px; color:#9ca3af; font-weight:400; margin-left:4px">{group.slots.length} slot{group.slots.length !== 1 ? 's' : ''}</span>
        </button>

        {#if openWeeks[wi]}
          <div style="margin-top:10px">
            {#each slotsByDay(group) as [dayKey, daySlots]}
              <div style="margin-bottom:10px">
                <div style="font-size:12px; font-weight:600; color:#6b7280; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.05em">
                  {daySlots[0].day_name} · {new Date(daySlots[0].date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:6px">
                  {#each daySlots as slot}
                    {@const isSelected = selectedSlot?.date === slot.date && selectedSlot?.start_time === slot.start_time}
                    <button
                      on:click={() => selectSlot(slot)}
                      style="padding:6px 12px; border-radius:6px; font-size:13px; cursor:pointer; border:1px solid {isSelected ? '#16a34a' : '#d1d5db'}; background:{isSelected ? '#f0fdf4' : 'white'}; color:{isSelected ? '#15803d' : '#374151'}; font-weight:{isSelected ? '600' : '400'}"
                    >
                      {slot.start_time.replace(/^0/, '')} {parseInt(slot.start_time) < 12 ? 'AM' : 'PM'}{isSelected ? ' ✓' : ''}
                    </button>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  {/if}

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={!selectedSlot}>
      Next → Patient Preferences
    </button>
  </div>

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
