<!--
  Insurance Interstitial — Step 2.5, inserted before provider selection when
  the session doesn't yet have an insurance plan on record.

  The referral index being booked is passed via the `?next=<idx>` query param
  so the nurse is redirected back to the correct provider selection step after
  saving insurance.

  Key behaviours:
    - On mount, pre-fills from session state (session-level insurance overrides
      the patient's EHR insurance) with fuzzy matching against the known plan
      list to handle slight name variations
    - "Other" option shows a free-text input for plans not in the known list
    - Self-Pay selection triggers a rate reference card so the nurse can
      inform the patient of estimated costs before proceeding
    - Saved value is stored at the session level (not just the patient record)
      so it can differ from the EHR-sourced patient insurance for this visit
-->
<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  const sid = $page.params.id;
  // `next` is the referral index to proceed to after saving insurance
  $: next = parseInt($page.url.searchParams.get('next') || '0');

  const KNOWN_PLANS = [
    'Medicaid',
    'United Health Care',
    'Blue Cross Blue Shield',
    'Aetna',
    'Cigna',
  ];

  let selected = '';
  let customInput = '';
  let saving = false;
  let error = '';

  onMount(async () => {
    try {
      const state = await api.getState(sid);
      // Pre-fill if already set — session-level insurance takes precedence
      if (state.insurance) {
        const match = KNOWN_PLANS.find(p => p.toLowerCase() === state.insurance.toLowerCase());
        if (match) selected = match;
        else if (state.insurance.toLowerCase() === 'self-pay') selected = 'Self-Pay';
        else { selected = 'other'; customInput = state.insurance; }
      } else if (state.patient?.insurance) {
        // Fall back to patient's EHR insurance, fuzzy-matched to known plans
        const ehr = state.patient.insurance;
        const match = KNOWN_PLANS.find(p => ehr.toLowerCase().includes(p.toLowerCase()) || p.toLowerCase().includes(ehr.toLowerCase()));
        if (match) selected = match;
        else if (ehr.toLowerCase() === 'self-pay') selected = 'Self-Pay';
        else { selected = 'other'; customInput = ehr; }
      }
    } catch (_) {}
  });

  async function save() {
    const value = selected === 'other' ? customInput.trim() : selected;
    if (!value) { error = 'Please select or enter insurance.'; return; }
    saving = true;
    error = '';
    try {
      await api.setInsurance(sid, value);
      // Return to the provider selection step for the referral that triggered this screen
      goto(`/session/${sid}/referral/${next}/provider`);
    } catch (e) {
      error = e.message;
      saving = false;
    }
  }
</script>

<div class="screen">
  <div style="display:flex; justify-content:space-between; align-items:flex-start">
    <div>
      <div class="screen-title">Step 2.5 — Insurance</div>
      <div class="screen-subtitle">Patient's insurance plan</div>
    </div>
    <button class="btn btn-secondary" style="font-size:13px; margin-top:4px" on:click={() => goto(`/session/${sid}`)}>← Back</button>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <div class="card">
    <div style="font-size:14px; font-weight:600; color:#374151; margin-bottom:14px">Select the patient's insurance</div>

    <div style="display:flex; flex-direction:column; gap:8px">
      {#each KNOWN_PLANS as plan}
        <button
          on:click={() => { selected = plan; customInput = ''; }}
          style="text-align:left; padding:12px 16px; border-radius:8px; border:2px solid {selected === plan ? '#2563eb' : '#e5e7eb'}; background:{selected === plan ? '#eff6ff' : 'white'}; font-size:14px; font-weight:{selected === plan ? '600' : '400'}; color:{selected === plan ? '#1d4ed8' : '#374151'}; cursor:pointer; display:flex; align-items:center; gap:10px"
        >
          <span style="width:16px; height:16px; border-radius:50%; border:2px solid {selected === plan ? '#2563eb' : '#9ca3af'}; background:{selected === plan ? '#2563eb' : 'white'}; flex-shrink:0; display:inline-block"></span>
          {plan}
        </button>
      {/each}

      <!-- Self-Pay rendered in purple to visually distinguish it from insured plans -->
      <button
        on:click={() => selected = 'Self-Pay'}
        style="text-align:left; padding:12px 16px; border-radius:8px; border:2px solid {selected === 'Self-Pay' ? '#7c3aed' : '#e5e7eb'}; background:{selected === 'Self-Pay' ? '#f5f3ff' : 'white'}; font-size:14px; font-weight:{selected === 'Self-Pay' ? '600' : '400'}; color:{selected === 'Self-Pay' ? '#6d28d9' : '#374151'}; cursor:pointer; display:flex; align-items:center; gap:10px"
      >
        <span style="width:16px; height:16px; border-radius:50%; border:2px solid {selected === 'Self-Pay' ? '#7c3aed' : '#9ca3af'}; background:{selected === 'Self-Pay' ? '#7c3aed' : 'white'}; flex-shrink:0; display:inline-block"></span>
        Self-Pay / Uninsured
      </button>

      <button
        on:click={() => selected = 'other'}
        style="text-align:left; padding:12px 16px; border-radius:8px; border:2px solid {selected === 'other' ? '#6b7280' : '#e5e7eb'}; background:{selected === 'other' ? '#f9fafb' : 'white'}; font-size:14px; color:{selected === 'other' ? '#374151' : '#6b7280'}; cursor:pointer; display:flex; align-items:center; gap:10px"
      >
        <span style="width:16px; height:16px; border-radius:50%; border:2px solid {selected === 'other' ? '#6b7280' : '#9ca3af'}; background:{selected === 'other' ? '#6b7280' : 'white'}; flex-shrink:0; display:inline-block"></span>
        Other / Unknown
      </button>
    </div>

    {#if selected === 'other'}
      <div style="margin-top:12px">
        <input
          bind:value={customInput}
          placeholder="Enter insurance plan name..."
          style="width:100%; padding:10px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; box-sizing:border-box"
          autofocus
        />
      </div>
    {/if}
  </div>

  <!-- Self-pay rate reference card: shown so nurse can inform patient before proceeding -->
  {#if selected === 'Self-Pay'}
    <div class="card" style="border-left:4px solid #7c3aed">
      <div style="font-size:13px; color:#6d28d9; font-weight:600; margin-bottom:6px">Self-Pay Rates</div>
      <div style="font-size:13px; color:#374151; display:flex; flex-direction:column; gap:4px">
        <div>Primary Care &mdash; <strong>$150/visit</strong></div>
        <div>Orthopedics &mdash; <strong>$300/visit</strong></div>
        <div>Surgery &mdash; <strong>$1,000/visit</strong></div>
      </div>
      <div style="font-size:12px; color:#9ca3af; margin-top:8px">Estimated rates — actual costs may vary. Share with patient before proceeding.</div>
    </div>
  {/if}

  <div class="nav-row">
    <div></div>
    <button
      class="btn btn-primary"
      on:click={save}
      disabled={saving || !selected || (selected === 'other' && !customInput.trim())}
    >
      {saving ? 'Saving...' : 'Continue →'}
    </button>
  </div>
</div>
