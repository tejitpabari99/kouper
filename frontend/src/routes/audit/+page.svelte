<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  let entries = [];
  let loading = true;
  let error = '';
  let expanded = {};
  let n = 100;

  onMount(() => loadLog());

  async function loadLog() {
    loading = true;
    error = '';
    try {
      entries = await api.getAuditLog(n);
      entries = [...entries].reverse(); // newest first
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function toggle(i) {
    expanded = { ...expanded, [i]: !expanded[i] };
  }

  function formatTime(ts) {
    try {
      return new Date(ts).toLocaleString();
    } catch (_) {
      return ts;
    }
  }

  function shortSession(id) {
    return id ? id.slice(0, 8) + '…' : '—';
  }
</script>

<div class="screen">
  <div style="display:flex; justify-content:space-between; align-items:flex-start">
    <div>
      <div class="screen-title">Audit Log</div>
      <div class="screen-subtitle">LLM tool calls &amp; reasoning traces</div>
    </div>
    <button
      class="btn btn-secondary"
      style="font-size:13px; margin-top:4px"
      on:click={() => goto('/')}
    >← Back</button>
  </div>

  <div style="display:flex; gap:10px; align-items:center; margin-bottom:16px">
    <div style="font-size:13px; color:#6b7280">Show last</div>
    <select
      bind:value={n}
      on:change={loadLog}
      style="font-size:13px; padding:4px 8px; border:1px solid #d1d5db; border-radius:4px"
    >
      {#each [25, 50, 100, 250] as val}
        <option value={val}>{val} entries</option>
      {/each}
    </select>
    <button class="btn btn-secondary" style="font-size:12px; padding:4px 12px" on:click={loadLog}>
      Refresh
    </button>
    {#if !loading}
      <div style="font-size:12px; color:#9ca3af">{entries.length} entries loaded</div>
    {/if}
  </div>

  {#if error}
    <div class="error-msg">{error}</div>
  {/if}

  {#if loading}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {:else if entries.length === 0}
    <div class="card" style="text-align:center; color:#9ca3af; padding:32px">
      No audit log entries yet. Start a session and ask the assistant a question to generate entries.
    </div>
  {:else}
    {#each entries as entry, i}
      <div
        class="card"
        style="margin-bottom:10px; padding:12px 14px; border-left:4px solid {entry.error ? '#ef4444' : '#2563eb'}"
      >
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px">
          <div style="flex:1; min-width:0">
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:4px">
              <span style="font-weight:700; font-size:14px; color:#1e3a8a">{entry.tool_name}</span>
              {#if entry.error}
                <span class="badge" style="background:#fee2e2; color:#dc2626; font-size:11px">
                  ERROR {entry.error_code ? `· ${entry.error_code}` : ''}
                </span>
              {:else}
                <span class="badge badge-green" style="font-size:11px">OK</span>
              {/if}
              <span style="font-size:11px; color:#9ca3af; font-family:monospace">session: {shortSession(entry.session_id)}</span>
            </div>
            <div style="font-size:12px; color:#6b7280">{formatTime(entry.timestamp)}</div>
            {#if entry.reasoning_hint}
              <div style="margin-top:6px; font-size:12px; color:#374151; background:#f9fafb; border-radius:4px; padding:6px 8px; border-left:3px solid #c7d2fe; font-style:italic">
                "{entry.reasoning_hint.length > 200 ? entry.reasoning_hint.slice(0, 200) + '…' : entry.reasoning_hint}"
              </div>
            {/if}
          </div>
          <button
            on:click={() => toggle(i)}
            style="background:none; border:none; color:#6366f1; font-size:12px; cursor:pointer; white-space:nowrap; flex-shrink:0"
          >
            {expanded[i] ? '▾ Hide' : '▸ Details'}
          </button>
        </div>

        {#if expanded[i]}
          <div style="margin-top:10px; padding-top:10px; border-top:1px solid #e5e7eb">
            <div style="font-size:12px; font-weight:600; color:#374151; margin-bottom:4px">Input</div>
            <pre style="font-size:11px; background:#f3f4f6; border-radius:4px; padding:8px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; color:#1f2937; margin:0 0 10px 0">{JSON.stringify(entry.tool_input, null, 2)}</pre>
            <div style="font-size:12px; font-weight:600; color:#374151; margin-bottom:4px">Output</div>
            <pre style="font-size:11px; background:#f3f4f6; border-radius:4px; padding:8px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; color:{entry.error ? '#dc2626' : '#1f2937'}; margin:0">{(() => { try { return JSON.stringify(JSON.parse(entry.tool_output), null, 2); } catch(_) { return entry.tool_output; } })()}</pre>
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>
