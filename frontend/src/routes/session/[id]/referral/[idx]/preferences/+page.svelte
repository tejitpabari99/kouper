<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client.js';
  import ChatPanel from '$lib/components/ChatPanel.svelte';

  const sid = $page.params.id;
  const idx = parseInt($page.params.idx);

  $: providerName = $page.url.searchParams.get('provider') || '';
  $: location = $page.url.searchParams.get('location') || '';
  $: specialty = $page.url.searchParams.get('specialty') || '';

  let contactMethod = 'phone';
  let bestContactTime = 'morning';
  let language = 'English';
  let locationPreference = 'none';
  let transportationNeeds = false;
  let notes = '';
  let saving = false;
  let error = '';

  async function proceed() {
    saving = true;
    error = '';
    try {
      await api.savePreferences(sid, {
        contact_method: contactMethod,
        best_contact_time: bestContactTime,
        language,
        location_preference: locationPreference,
        transportation_needs: transportationNeeds,
        notes,
      });
      goto(`/session/${sid}/referral/${idx}/confirm?provider=${encodeURIComponent(providerName)}&location=${encodeURIComponent(location)}&specialty=${encodeURIComponent(specialty)}`);
    } catch (e) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  function goBack() {
    goto(`/session/${sid}/referral/${idx}/details?provider=${encodeURIComponent(providerName)}`);
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 5 of 7 &mdash; Referral {idx + 1}</div>
    <div class="screen-subtitle">Patient Preferences</div>
    <div style="color:#6b7280; font-size:14px; margin-top:4px">These help with booking and follow-ups</div>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <div class="card">
    <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Communication Preference</div>

    <div class="form-row">
      <label>Preferred Contact Method</label>
      <div class="radio-group">
        {#each ['phone', 'text', 'email'] as opt}
          <label class="radio-option" class:selected={contactMethod === opt} style="cursor:pointer">
            <input type="radio" bind:group={contactMethod} value={opt} style="display:none" />
            {opt.charAt(0).toUpperCase() + opt.slice(1)}
          </label>
        {/each}
      </div>
    </div>

    <div class="form-row">
      <label>Best Contact Time</label>
      <div class="radio-group">
        {#each ['morning', 'afternoon', 'evening'] as opt}
          <label class="radio-option" class:selected={bestContactTime === opt} style="cursor:pointer">
            <input type="radio" bind:group={bestContactTime} value={opt} style="display:none" />
            {opt.charAt(0).toUpperCase() + opt.slice(1)}
          </label>
        {/each}
      </div>
    </div>

    <div class="form-row">
      <label>Language Preference</label>
      <select bind:value={language} style="padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px">
        {#each ['English', 'Spanish', 'French', 'Mandarin', 'Arabic', 'Other'] as lang}
          <option>{lang}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="card">
    <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Logistics</div>

    <div class="form-row">
      <label>Location Preference</label>
      <div class="radio-group">
        {#each [['home', 'Closest to Home'], ['work', 'Closest to Work'], ['none', 'No Preference']] as [val, label]}
          <label class="radio-option" class:selected={locationPreference === val} style="cursor:pointer">
            <input type="radio" bind:group={locationPreference} value={val} style="display:none" />
            {label}
          </label>
        {/each}
      </div>
    </div>

    <div class="form-row">
      <label>Transportation Needs</label>
      <div class="radio-group">
        <label class="radio-option" class:selected={!transportationNeeds} style="cursor:pointer">
          <input type="radio" bind:group={transportationNeeds} value={false} style="display:none" />
          Has Own Transport
        </label>
        <label class="radio-option" class:selected={transportationNeeds} style="cursor:pointer">
          <input type="radio" bind:group={transportationNeeds} value={true} style="display:none" />
          Needs Ride Assistance
        </label>
      </div>
    </div>

    {#if transportationNeeds}
      <div class="warning-row">
        ⚠️ Patient needs transportation. Flag for care coordinator to arrange assistance.
      </div>
    {/if}

    <div class="form-row" style="margin-bottom:0">
      <label>Additional Notes</label>
      <textarea bind:value={notes} rows="2" placeholder="Any relevant notes..." style="padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; resize:vertical"></textarea>
    </div>
  </div>

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={saving}>
      {saving ? 'Saving...' : 'Next \u2192 Review Booking'}
    </button>
  </div>

  <ChatPanel sessionId={sid} />
</div>
