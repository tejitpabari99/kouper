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

  // Currently selected provider name
  let selectedProvider = '';

  // Manual input autocomplete
  let manualInput = '';
  let autocompleteResults = [];
  let showAutocomplete = false;

  // Guard / navigation error
  let navError = '';
  let navigating = false;

  onMount(async () => {
    try {
      state = await api.getState(sid);
    } catch (e) {
      error = e.message;
    }

    try {
      if (specialty) {
        const results = await api.getProviders(specialty);
        providers = results || [];
      }
    } catch (e) {
      // Non-fatal; still allow manual entry
    } finally {
      providersLoading = false;
    }

    // Pre-select named provider if present
    if (namedProvider) {
      selectedProvider = namedProvider;
    }
  });

  $: referral = state?.patient?.referred_providers?.[idx];
  $: specialty = referral?.specialty || '';
  $: namedProvider = referral?.provider || null;

  function formatProvider(raw) {
    if (!raw) return '';
    return raw.replace(/ MD$/, '').replace(/ FNP$/, '').replace(/, PhD$/, '');
  }

  function isNamedProvider(p) {
    if (!namedProvider) return false;
    const norm = (s) => s.toLowerCase().replace(/[,.\s]+/g, ' ').trim();
    return norm(p.name) === norm(namedProvider) ||
           norm(p.name) === norm(formatProvider(namedProvider));
  }

  function selectCard(providerName) {
    selectedProvider = providerName;
    manualInput = '';
    showAutocomplete = false;
    autocompleteResults = [];
    navError = '';
  }

  function onManualInput() {
    selectedProvider = '';
    navError = '';
    const q = manualInput.trim().toLowerCase();
    if (!q) {
      autocompleteResults = [];
      showAutocomplete = false;
      return;
    }
    autocompleteResults = providers.filter(p =>
      p.name.toLowerCase().includes(q)
    );
    showAutocomplete = autocompleteResults.length > 0;
  }

  function pickAutocomplete(p) {
    manualInput = p.name;
    selectedProvider = p.name;
    showAutocomplete = false;
    autocompleteResults = [];
    navError = '';
  }

  function handleManualBlur() {
    setTimeout(() => { showAutocomplete = false; }, 150);
  }

  $: activeProvider = selectedProvider || (manualInput.trim() ? manualInput.trim() : '');

  async function continueToDetails() {
    if (!activeProvider) return;
    navigating = true;
    navError = '';
    try {
      const info = await api.getAppointmentInfo(sid, activeProvider, specialty);
      const key = `appointment_info_${sid}_${idx}`;
      sessionStorage.setItem(key, JSON.stringify(info));
      goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(activeProvider)}&specialty=${encodeURIComponent(specialty)}`);
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
        navError = 'Provider not found in our system. Please select a different provider or check the spelling.';
      } else {
        navError = `Error: ${msg}`;
      }
    } finally {
      navigating = false;
    }
  }

  function goBack() {
    goto(`/session/${sid}`);
  }

  function providerDays(p) {
    if (!p.locations || p.locations.length === 0) return '';
    const days = p.locations.flatMap(l => l.days || []);
    const unique = [...new Set(days)];
    return unique.join(', ');
  }

  function providerLocationNames(p) {
    if (!p.locations || p.locations.length === 0) return '';
    return p.locations.map(l => l.name).join(', ');
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 3 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Provider Selection</div>
    {#if specialty}<div style="color:#6b7280; font-size:14px; margin-top:4px">Specialty: {specialty}</div>{/if}
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if state && referral}
    <!-- Manual / autocomplete input -->
    <div class="card">
      <div style="font-size:14px; font-weight:600; margin-bottom:8px">Search Manually</div>
      <div style="position:relative">
        <input
          bind:value={manualInput}
          on:input={onManualInput}
          on:blur={handleManualBlur}
          on:focus={() => { if (autocompleteResults.length > 0) showAutocomplete = true; }}
          placeholder="Type provider name..."
          style="width:100%; padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; box-sizing:border-box"
          autocomplete="off"
        />
        {#if showAutocomplete && autocompleteResults.length > 0}
          <div class="autocomplete-dropdown">
            {#each autocompleteResults as p}
              <div class="autocomplete-item" on:mousedown|preventDefault={() => pickAutocomplete(p)}>
                {p.name}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Suggestion cards -->
    {#if providersLoading}
      <div style="color:#6b7280; font-size:14px">Loading {specialty} providers...</div>
    {:else if providers.length > 0}
      <div>
        <div style="font-size:13px; font-weight:600; color:#6b7280; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em">
          Available {specialty} Providers
        </div>
        <div style="display:flex; flex-direction:column; gap:8px">
          {#each providers as p}
            {@const isReferred = isNamedProvider(p)}
            {@const isSelected = selectedProvider === p.name || (isReferred && selectedProvider === namedProvider)}
            <div
              class="provider-card {isSelected ? 'provider-selected' : ''} {isReferred ? 'provider-referred' : ''}"
              on:click={() => selectCard(p.name)}
              style="cursor:pointer"
            >
              <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:8px">
                <div>
                  <div class="provider-name">
                    {p.name}
                    {#if isSelected}
                      <span style="color:#16a34a; font-size:14px; margin-left:4px">&#10003;</span>
                    {/if}
                  </div>
                  {#if providerLocationNames(p)}
                    <div class="provider-specialty" style="margin-top:2px">{providerLocationNames(p)}</div>
                  {/if}
                  {#if providerDays(p)}
                    <div style="font-size:12px; color:#6b7280; margin-top:2px">Available: {providerDays(p)}</div>
                  {/if}
                </div>
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px; flex-shrink:0">
                  {#if isReferred}
                    <span class="badge-referred">Referred</span>
                  {/if}
                  {#if isSelected}
                    <span class="badge-selected">Selected</span>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else if !error}
      <div class="info-row">
        &#8505;&#65039; No {specialty} providers found. Enter a provider name manually above.
      </div>
    {/if}

    {#if navError}
      <div class="error-msg">{navError}</div>
    {/if}

    <div class="nav-row">
      <button class="btn btn-secondary" on:click={goBack}>&#8592; Back</button>
      <button
        class="btn btn-primary"
        on:click={continueToDetails}
        disabled={!activeProvider || navigating}
      >
        {navigating ? 'Checking...' : 'Continue &#8594;'}
      </button>
    </div>
  {:else if !error}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {/if}

  <ChatPanel sessionId={sid} />
</div>

<style>
  .autocomplete-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 100;
    max-height: 200px;
    overflow-y: auto;
  }

  .autocomplete-item {
    padding: 9px 14px;
    cursor: pointer;
    font-size: 14px;
    border-bottom: 1px solid #f3f4f6;
  }

  .autocomplete-item:last-child {
    border-bottom: none;
  }

  .autocomplete-item:hover {
    background: #eff6ff;
  }

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
