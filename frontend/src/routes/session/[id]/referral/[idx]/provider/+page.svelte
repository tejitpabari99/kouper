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

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }
  });

  $: referral = state?.patient?.referred_providers?.[idx];
  $: specialty = referral?.specialty || '';
  $: namedProvider = referral?.provider || null;

  function selectProvider(providerName) {
    goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(providerName)}`);
  }

  function goBack() {
    goto(`/session/${sid}`);
  }

  function formatProvider(raw) {
    if (!raw) return '';
    return raw.replace(/ MD$/, '').replace(/ FNP$/, '').replace(/, PhD$/, '');
  }

  let manualProvider = '';
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 3 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Provider Selection</div>
    {#if specialty}<div style="color:#6b7280; font-size:14px; margin-top:4px">Specialty: {specialty}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if state && referral}
    {#if namedProvider}
      <div>
        <div style="font-size:13px; font-weight:600; color:#6b7280; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em">Referred Provider</div>
        <div class="provider-card highlighted">
          <div class="provider-name">{formatProvider(namedProvider)}</div>
          <div class="provider-specialty">{specialty}</div>
          <div style="margin-top:10px">
            <button class="btn btn-primary" on:click={() => selectProvider(namedProvider)}>
              Select This Provider &#8594;
            </button>
          </div>
        </div>
      </div>
    {:else}
      <div class="info-row">
        &#8505;&#65039; No specific provider listed for this referral. Ask the assistant to find available {specialty} providers, or select one below.
      </div>
    {/if}

    <div class="card">
      <div style="font-size:14px; font-weight:600; margin-bottom:8px">Enter Provider Name Manually</div>
      <div style="display:flex; gap:10px">
        <input bind:value={manualProvider} placeholder="e.g. Dr. Gregory House" style="flex:1; padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px" />
        <button class="btn btn-secondary" on:click={() => { if (manualProvider.trim()) selectProvider(manualProvider.trim()); }}>Select</button>
      </div>
      <div style="margin-top:12px; font-size:13px; color:#6b7280">
        Or ask the assistant below: "Who else is available for {specialty}?"
      </div>
    </div>

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={goBack}>&#8592; Back</button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {/if}

  <ChatPanel sessionId={sid} />
</div>
