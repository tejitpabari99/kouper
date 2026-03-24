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
  let providers = [];
  let providersLoading = true;
  let selectedProvider = '';
  let filterText = '';
  let navError = '';
  let navigating = false;

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
      providersLoading = false;
      return;
    }

    const ref = state?.patient?.referred_providers?.[idx];
    const spec = ref?.specialty || '';

    try {
      if (spec) {
        const results = await api.getProviders(spec);
        providers = results || [];
      }
    } catch (e) {
      // non-fatal
    } finally {
      providersLoading = false;
    }

    // Pre-select the referred provider if there is one
    const raw = ref?.provider;
    if (raw && providers.length > 0) {
      const match = findMatchingProvider(raw, providers);
      if (match) selectedProvider = match.name;
    }

    api.logNurseEvent(sid, 'step_visited', { step: 'provider_selection', referral_index: idx });
  });

  function findMatchingProvider(raw, list) {
    const normalize = s => s.toLowerCase().replace(/[^a-z\s]/g, ' ').replace(/\s+/g, ' ').trim();
    const rawWords = normalize(raw).split(' ').filter(w => w.length > 2);
    return list.find(p => {
      const pWords = normalize(p.name).split(' ');
      return rawWords.every(w => pWords.some(pw => pw.includes(w) || w.includes(pw)));
    }) || null;
  }

  $: referral = state?.patient?.referred_providers?.[idx];
  $: specialty = referral?.specialty || '';
  $: namedProvider = referral?.provider || null;

  $: filteredProviders = filterText.trim()
    ? providers.filter(p => p.name.toLowerCase().includes(filterText.toLowerCase()))
    : providers;

  function selectCard(providerName) {
    selectedProvider = providerName;
    navError = '';
    api.logNurseEvent(sid, 'provider_selected', { provider: providerName, referral_index: idx });
  }

  const ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  function providerDays(p) {
    if (!p.locations?.length) return '';
    // Per-location schedule
    return p.locations.map(l => {
      const days = (l.days || []).slice().sort((a,b) => ORDER.indexOf(a) - ORDER.indexOf(b));
      const abbr = days.map(d => d.slice(0,3)).join(', ');
      return `${l.name}: ${abbr} ${l.hours || ''}`.trim();
    }).join(' | ');
  }

  function providerLocationNames(p) {
    if (!p.locations?.length) return '';
    return p.locations.map(l => l.name).join(', ');
  }

  function providerSummary(p) {
    if (!p.locations?.length) return '';
    return p.locations.map(l => {
      const city = l.address ? l.address.split(',').slice(1,2).join('').trim() : '';
      return city ? `${l.name} (${city})` : l.name;
    }).join(' · ');
  }

  async function continueToDetails() {
    if (!selectedProvider || navigating) return;
    navigating = true;
    navError = '';
    try {
      const info = await api.getAppointmentInfo(sid, selectedProvider, specialty);
      sessionStorage.setItem(`appointment_info_${sid}_${idx}`, JSON.stringify(info));
      goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(selectedProvider)}&specialty=${encodeURIComponent(specialty)}`);
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
        navError = 'Provider not found in our system. Please select a different provider.';
      } else {
        navError = `Error: ${msg}`;
      }
    } finally {
      navigating = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      continueToDetails();
    }
  }

  $: chatContext = [
    `Screen: Provider Selection (Step 3) — Referral ${idx + 1}`,
    specialty ? `Specialty needed: ${specialty}` : '',
    namedProvider ? `Referred provider from chart: ${namedProvider}` : '',
    selectedProvider ? `Currently selected: ${selectedProvider}` : 'No provider selected yet',
    providers.length
      ? `Available providers: ${providers.map(p => `${p.name} (${p.locations?.map(l => l.name).join(', ')})`).join('; ')}`
      : 'Providers loading...',
  ].filter(Boolean).join('\n');
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 3 of 7 — Referral {idx + 1}</div>
    <div class="screen-subtitle">Provider Selection</div>
    {#if specialty}<div style="color:#6b7280; font-size:14px; margin-top:4px">Specialty: {specialty}</div>{/if}
  </div>

  {#if error}
    <div class="error-msg">{error}</div>
  {:else if !state}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {:else}
    {#if namedProvider}
      <div class="info-row">
        Referred provider: <strong>{namedProvider}</strong>
      </div>
    {/if}

    <div class="card">
      <label style="font-size:13px; font-weight:600; color:#374151; display:block; margin-bottom:6px">
        Filter providers
      </label>
      <input
        bind:value={filterText}
        placeholder="Type to filter by name..."
        autocomplete="off"
        style="width:100%; padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; box-sizing:border-box"
      />
    </div>

    {#if providersLoading}
      <div style="color:#6b7280; font-size:14px">Loading {specialty} providers...</div>
    {:else if filteredProviders.length > 0}
      <div>
        {#if !providersLoading && providers.length > 0}
          <div style="font-size:12px; color:#6b7280; margin-bottom:6px">
            {filterText ? `${filteredProviders.length} of ${providers.length}` : providers.length} {specialty} provider{providers.length !== 1 ? 's' : ''} available
          </div>
        {/if}
        <div style="font-size:13px; font-weight:600; color:#6b7280; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em">
          {filterText ? 'Matching' : 'Available'} {specialty} Providers
        </div>
        <div style="display:flex; flex-direction:column; gap:8px">
          {#each filteredProviders as p}
            {@const isSelected = selectedProvider === p.name}
            {@const isReferred = namedProvider && findMatchingProvider(namedProvider, [p]) !== null}
            <div
              class="provider-card"
              class:provider-selected={isSelected}
              class:provider-referred={isReferred && !isSelected}
              on:click={() => selectCard(p.name)}
              style="cursor:pointer"
            >
              <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:8px">
                <div>
                  <div class="provider-name">
                    {p.name}
                    {#if isSelected}<span style="color:#16a34a; margin-left:4px">✓</span>{/if}
                  </div>
                  {#if providerSummary(p)}
                    <div class="provider-specialty" style="margin-top:2px">{providerSummary(p)}</div>
                  {/if}
                  {#if providerDays(p)}
                    <div style="font-size:12px; color:#6b7280; margin-top:2px">Available: {providerDays(p)}</div>
                  {/if}
                </div>
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px; flex-shrink:0">
                  {#if isReferred && isSelected}
                    <span class="badge-selected">✓ Selected (Referred)</span>
                  {:else if isReferred}
                    <span class="badge-referred">Referred by chart</span>
                  {:else if isSelected}
                    <span class="badge-selected">✓ Selected</span>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="info-row">No {specialty} providers match your filter.</div>
    {/if}

    {#if navError}
      <div class="error-msg">{navError}</div>
    {/if}

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={() => goto(`/session/${sid}`)}>← Back</button>
      <button
        class="btn btn-primary"
        on:click={continueToDetails}
        disabled={!selectedProvider || navigating}
      >
        {navigating ? 'Checking...' : 'Continue →'}
      </button>
    </div>
  {/if}

  <ChatPanel sessionId={sid} context={chatContext} />
</div>

<style>
  .provider-card {
    padding: 14px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #ffffff;
    transition: border-color 0.15s, background 0.15s;
  }
  .provider-card:hover {
    border-color: #93c5fd;
    background: #f8faff;
  }
  .provider-selected {
    border-color: #16a34a !important;
    background: #f0fdf4 !important;
  }
  .provider-referred {
    border-color: #3b82f6;
  }
  .provider-name {
    font-size: 15px;
    font-weight: 600;
    color: #111827;
  }
  .provider-specialty {
    font-size: 13px;
    color: #6b7280;
  }
  .badge-referred {
    display: inline-block;
    padding: 2px 8px;
    background: #dbeafe;
    color: #1d4ed8;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
  }
  .badge-selected {
    display: inline-block;
    padding: 2px 8px;
    background: #dcfce7;
    color: #16a34a;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
  }
</style>
