<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client.js';
  import { sessionId, patient } from '$lib/stores/session.js';

  let patientIdInput = '1';
  let loading = false;
  let error = '';
  let loadedPatient = null;
  let createdSessionId = null;

  async function loadPatient() {
    loading = true;
    error = '';
    loadedPatient = null;
    try {
      const session = await api.createSession();
      createdSessionId = session.session_id;
      sessionId.set(createdSessionId);
      const p = await api.startSession(createdSessionId, patientIdInput);
      loadedPatient = p;
      patient.set(p);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function proceed() {
    goto(`/session/${createdSessionId}`);
  }
</script>

<div class="screen">
  <div>
    <div class="screen-title">Care Coordinator</div>
    <div class="screen-subtitle">Patient Lookup</div>
  </div>

  <div class="card">
    <div class="form-row">
      <label for="patientId">Patient ID</label>
      <div style="display:flex; gap:10px">
        <input id="patientId" bind:value={patientIdInput} placeholder="Enter patient ID" style="flex:1" />
        <button class="btn btn-primary" on:click={loadPatient} disabled={loading || !patientIdInput}>
          {loading ? 'Loading...' : 'Load Patient'}
        </button>
      </div>
    </div>

    {#if error}
      <div class="error-msg">{error}</div>
    {/if}

    {#if loadedPatient}
      <div style="margin-top:16px; padding:16px; background:#f9fafb; border-radius:8px; border:1px solid #e5e7eb">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px">
          <span style="color:#16a34a; font-size:18px">&#10003;</span>
          <span style="font-size:18px; font-weight:700">{loadedPatient.name}</span>
        </div>
        <div class="detail-row"><span class="label">Date of Birth</span><span class="value">{loadedPatient.dob}</span></div>
        <div class="detail-row"><span class="label">Primary Care Provider</span><span class="value">{loadedPatient.pcp}</span></div>
        <div class="detail-row"><span class="label">EHR ID</span><span class="value">{loadedPatient.ehrId}</span></div>
      </div>

      <div class="info-row" style="margin-top:12px">
        &#8505;&#65039; Please confirm patient identity verbally before proceeding.
      </div>
    {/if}
  </div>

  {#if loadedPatient}
    <div class="nav-row">
      <div></div>
      <button class="btn btn-primary" on:click={proceed}>Continue to Referrals &#8594;</button>
    </div>
  {/if}
</div>
