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

  const LANGUAGES = ['English','Spanish','Portuguese','French','Haitian Creole','Vietnamese','Tagalog','Korean','Mandarin','Cantonese','Arabic','Russian','Polish','Other'];

  const CONTACT_TIMES = [
    { value: 'morning', label: 'Morning', sub: '8am–12pm' },
    { value: 'afternoon', label: 'Afternoon', sub: '12pm–5pm' },
    { value: 'evening', label: 'Evening', sub: '5pm–8pm' },
  ];

  let contactMethod = 'phone';
  let bestContactTime = 'morning';
  let language = 'English';
  let languageOther = '';
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
        language: language === 'Other' ? languageOther || 'Other' : language,
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

  $: chatContext = [
    `Screen: Patient Preferences (Step 5) — Referral ${idx + 1}`,
    `Provider: ${providerName}`,
    `Location: ${location}`,
    `Specialty: ${specialty}`,
    `Preferred contact method: ${contactMethod}`,
    `Best contact time: ${bestContactTime}`,
    `Language: ${language === 'Other' ? languageOther || 'Other' : language}`,
    `Transportation needed: ${transportationNeeds ? 'Yes — needs ride assistance' : 'No'}`,
    notes ? `Additional notes: ${notes}` : '',
  ].filter(Boolean).join('\n');
</script>

<div class="screen">
  <div>
    <div class="screen-title">Step 5 &mdash; Referral {idx + 1}</div>
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
        {#each CONTACT_TIMES as opt}
          <label class="radio-option" class:selected={bestContactTime === opt.value} style="cursor:pointer">
            <input type="radio" bind:group={bestContactTime} value={opt.value} style="display:none" />
            <span>{opt.label}</span>
            <span style="display:block; font-size:11px; color:#9ca3af; margin-top:1px">{opt.sub}</span>
          </label>
        {/each}
      </div>
    </div>

    <div class="form-row">
      <label>Language Preference</label>
      <select bind:value={language} style="padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px">
        {#each LANGUAGES as lang}
          <option>{lang}</option>
        {/each}
      </select>
      {#if language === 'Other'}
        <input bind:value={languageOther} placeholder="Please specify language" style="margin-top:8px; width:100%; padding:8px 10px; border:1px solid #d1d5db; border-radius:6px; font-size:14px" />
      {/if}
    </div>
  </div>

  <div class="card">
    <div style="font-size:15px; font-weight:600; margin-bottom:16px; color:#374151">Logistics</div>

    <div class="form-row">
      <label>Future Location Preference (for follow-up appointments)</label>
      <div style="font-size:12px; color:#9ca3af; margin-bottom:8px">This booking was made at the location selected in the previous step.</div>
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
      <div style="margin-top:12px; padding:12px 14px; background:#fefce8; border:1px solid #fde047; border-radius:8px">
        <div style="font-size:13px; color:#713f12; margin-bottom:8px">
          ✓ Transportation need will be recorded in the session summary for care coordinator follow-up.
        </div>
        <div style="padding:10px 12px; background:#4f46e5; border-radius:6px; color:white; font-size:13px; line-height:1.5">
          <div style="font-weight:700; margin-bottom:4px; font-size:11px; text-transform:uppercase; opacity:0.8">Tell the patient:</div>
          "We'll have someone call you within 24 hours to arrange your transportation to this appointment."
        </div>
      </div>
    {/if}

    <div class="form-row" style="margin-bottom:0">
      <label>Additional Notes</label>
      <textarea bind:value={notes} rows="2" placeholder="e.g., needs interpreter on site, hard of hearing, lives in assisted living" style="padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; resize:vertical"></textarea>
    </div>
  </div>

  <div class="nav-row">
    <button class="btn btn-secondary" on:click={goBack}>← Back</button>
    <button class="btn btn-primary" on:click={proceed} disabled={saving}>
      {saving ? 'Saving...' : 'Next → Review Booking'}
    </button>
  </div>

  <ChatPanel sessionId={sid} context={chatContext} />
</div>
