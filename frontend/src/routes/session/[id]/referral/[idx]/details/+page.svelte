<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  const idx = parseInt($page.params.idx);

  let state = null;
  let error = '';
  let apptTypeInfo = null;
  let selectedLocation = '';

  $: providerName = $page.url.searchParams.get('provider') || '';

  onMount(async () => {
    try {
      state = await api.getState(sid);
      if (providerName && state?.patient) {
        const specialty = state.patient.referred_providers[idx]?.specialty || '';
        const res = await api.sendMessage(sid,
          `Determine the appointment type for ${providerName} (${specialty}) and show their available locations. Be brief.`
        );
        apptTypeInfo = res.response;
      }
    } catch (e) {
      error = e.message;
    }
  });

  $: referral = state?.patient?.referred_providers?.[idx];
  $: specialty = referral?.specialty || '';

  function proceed() {
    if (!selectedLocation) return;
    goto(`/session/${sid}/referral/${idx}/preferences?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(selectedLocation)}&specialty=${encodeURIComponent(specialty)}`);
  }

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/provider`);
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 4 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Appointment Details</div>
    {#if providerName}<div style="color:#6b7280; font-size:14px; margin-top:4px">{providerName}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if apptTypeInfo}
    <div class="card">
      <div style="font-size:13px; font-weight:600; color:#6b7280; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em">Assistant Summary</div>
      <div style="font-size:14px; line-height:1.6; white-space:pre-wrap">{apptTypeInfo}</div>
    </div>
  {:else if !error && state}
    <div style="color:#6b7280; font-size:14px">Determining appointment type...</div>
  {/if}

  <div class="card">
    <div class="form-row">
      <label>Location Name</label>
      <input bind:value={selectedLocation} placeholder="e.g. PPTH Orthopedics or Jefferson Hospital" />
    </div>
    <div style="font-size:12px; color:#6b7280">
      The assistant above lists available locations. Enter the one you'd like to use.
    </div>
  </div>

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>&#8592; Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={!selectedLocation}>
      Next &#8594; Patient Preferences
    </button>
  </div>

  <ChatPanel sessionId={sid} />
</div>
