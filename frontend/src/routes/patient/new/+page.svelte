<script>
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';
  import { api } from '$lib/api/client.js';

  const SPECIALTIES = ['Primary Care', 'Orthopedics', 'Surgery', 'Cardiology', 'Neurology', 'Dermatology', 'Other'];
  const KNOWN_PLANS = ['Medicaid', 'United Health Care', 'Blue Cross Blue Shield', 'Aetna', 'Cigna'];

  let name = '';
  let dob = '';
  let pcp = '';
  let phone = '';
  let email = '';
  let insurance = '';
  let referrals = [''];  // start with one empty specialty slot

  let saving = false;
  let error = '';

  function addReferral() {
    referrals = [...referrals, ''];
  }

  function removeReferral(i) {
    referrals = referrals.filter((_, idx) => idx !== i);
  }

  $: validReferrals = referrals.filter(r => r.trim());
  $: canSubmit = name.trim() && dob && validReferrals.length > 0;

  async function submit() {
    if (!canSubmit) return;
    saving = true;
    error = '';
    try {
      // Create the patient
      const patient = await api.createLocalPatient({
        name: name.trim(),
        dob,
        pcp: pcp.trim() || 'Self-referred',
        phone: phone.trim(),
        email: email.trim(),
        insurance: insurance || null,
        referred_specialties: validReferrals,
      });

      // Create a session and load the patient into it
      const session = await api.createSession();
      await api.startSessionWithLocalPatient(session.session_id, patient.id);

      // If insurance was set, save it to the session too
      if (insurance) {
        await api.setInsurance(session.session_id, insurance);
      }

      goto(`${base}/session/${session.session_id}`);
    } catch (e) {
      error = e.message;
      saving = false;
    }
  }
</script>

<div class="screen">
  <div style="display:flex; justify-content:space-between; align-items:flex-start">
    <div>
      <div class="screen-title">New Patient</div>
      <div class="screen-subtitle">Register and begin referral session</div>
    </div>
    <button class="btn btn-secondary" style="font-size:13px; margin-top:4px" on:click={() => goto(base + '/')}>← Back</button>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  <!-- Patient Info -->
  <div class="card">
    <div style="font-size:15px; font-weight:600; color:#374151; margin-bottom:16px">Patient Information</div>

    <div class="form-row">
      <label>Full Name <span style="color:#dc2626">*</span></label>
      <input bind:value={name} placeholder="e.g. Jane Smith" autofocus />
    </div>

    <div class="form-row">
      <label>Date of Birth <span style="color:#dc2626">*</span></label>
      <input type="date" bind:value={dob} max={new Date().toISOString().split('T')[0]} />
    </div>

    <div class="form-row">
      <label>Primary Care Provider</label>
      <input bind:value={pcp} placeholder="e.g. Dr. Smith — leave blank if self-referred" />
    </div>

    <div class="form-row">
      <label>Phone</label>
      <input bind:value={phone} type="tel" placeholder="555-123-4567" />
    </div>

    <div class="form-row" style="margin-bottom:0">
      <label>Email</label>
      <input bind:value={email} type="email" placeholder="patient@example.com" />
    </div>
  </div>

  <!-- Insurance -->
  <div class="card">
    <div style="font-size:15px; font-weight:600; color:#374151; margin-bottom:12px">Insurance</div>
    <div style="display:flex; flex-wrap:wrap; gap:8px">
      {#each [...KNOWN_PLANS, 'Self-Pay'] as plan}
        <button
          on:click={() => insurance = insurance === plan ? '' : plan}
          style="padding:6px 14px; border-radius:9999px; border:1px solid {insurance === plan ? '#2563eb' : '#e5e7eb'}; background:{insurance === plan ? '#eff6ff' : 'white'}; color:{insurance === plan ? '#1d4ed8' : '#6b7280'}; font-size:13px; font-weight:{insurance === plan ? '600' : '400'}; cursor:pointer"
        >{plan}</button>
      {/each}
    </div>
    {#if !insurance}
      <div style="font-size:12px; color:#9ca3af; margin-top:8px">Optional — can be set later in the session</div>
    {/if}
  </div>

  <!-- Referrals -->
  <div class="card">
    <div style="font-size:15px; font-weight:600; color:#374151; margin-bottom:4px">Referrals <span style="color:#dc2626">*</span></div>
    <div style="font-size:13px; color:#9ca3af; margin-bottom:14px">At least one specialty required</div>

    {#each referrals as specialty, i}
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:8px">
        <select
          bind:value={referrals[i]}
          style="flex:1; padding:9px 12px; border:1px solid #d1d5db; border-radius:6px; font-size:14px; background:white"
        >
          <option value="">— Select specialty —</option>
          {#each SPECIALTIES as s}
            <option value={s}>{s}</option>
          {/each}
        </select>
        {#if referrals.length > 1}
          <button
            on:click={() => removeReferral(i)}
            style="background:none; border:none; color:#9ca3af; font-size:18px; cursor:pointer; padding:0 4px; line-height:1"
          >×</button>
        {/if}
      </div>
    {/each}

    <button
      on:click={addReferral}
      style="font-size:13px; color:#2563eb; background:none; border:1px dashed #93c5fd; border-radius:6px; padding:6px 14px; cursor:pointer; margin-top:4px"
    >+ Add another referral</button>
  </div>

  <div class="nav-row">
    <div></div>
    <button
      class="btn btn-primary"
      on:click={submit}
      disabled={saving || !canSubmit}
    >
      {saving ? 'Creating...' : 'Create Patient & Begin →'}
    </button>
  </div>
</div>
