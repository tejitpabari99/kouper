<!--
  Audit Log — read-only diagnostic view of all system activity.

  Accessible from the dashboard header. Shows every event recorded by the
  backend: nurse actions, API calls, LLM interactions, tool calls, and system
  events. Intended for supervisors, engineers, or demo walkthroughs.

  Key behaviours:
    - Entries are fetched directly via fetch (not the api client) to allow
      fine-grained URL construction for the type filter query param
    - Entries are reversed on load so newest appear first
    - TYPE_COLORS maps each event type to a colour scheme for visual scanning
    - Each entry can be expanded to reveal raw JSON payloads (tool input/output,
      detail, HTTP path) for debugging
    - `reasoning_hint` is a special field populated by LLM tool calls — shows
      the model's chain-of-thought inline, which is useful for interviews to
      demonstrate that LLM reasoning is being logged
    - n (entry limit) and typeFilter are both reactive: changing either
      triggers a fresh loadLog() call
-->
<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client.js';

  let entries = [];
  let loading = true;
  let error = '';
  let expanded = {};  // { entryIndex: bool } for expand/collapse state
  let n = 100;        // Number of entries to load; bound to select
  let typeFilter = '';

  // Visual styling per event type — used for both filter chips and entry rows
  const TYPE_COLORS = {
    api:    { bg: '#f3f4f6', border: '#9ca3af',  text: '#374151',  label: 'API'    },
    system: { bg: '#eff6ff', border: '#93c5fd',  text: '#1d4ed8',  label: 'System' },
    llm:    { bg: '#eef2ff', border: '#a5b4fc',  text: '#4338ca',  label: 'LLM'    },
    tool:   { bg: '#faf5ff', border: '#c4b5fd',  text: '#7c3aed',  label: 'Tool'   },
    nurse:  { bg: '#f0fdf4', border: '#86efac',  text: '#15803d',  label: 'Nurse'  },
  };

  onMount(() => loadLog());

  async function loadLog() {
    loading = true;
    error = '';
    try {
      // Build URL manually to support an optional type filter param
      const url = `/api/audit/log?n=${n}${typeFilter ? '&type=' + typeFilter : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      // Reverse so newest entries appear at the top
      entries = [...data].reverse();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  // Re-fetch when the filter chip changes
  function setFilter(t) {
    typeFilter = t;
    loadLog();
  }

  function toggle(i) {
    expanded = { ...expanded, [i]: !expanded[i] };
  }

  function formatTime(ts) {
    try { return new Date(ts).toLocaleString(); } catch (_) { return ts; }
  }

  // Truncate session UUIDs for display to keep rows compact
  function shortSession(id) {
    return id ? id.slice(0, 8) + '…' : '—';
  }

  function entryColor(type) {
    return TYPE_COLORS[type] || TYPE_COLORS.api;
  }

  // Derive a human-readable title from whichever field is most informative
  function entryTitle(entry) {
    if (entry.action) return entry.action.replace(/_/g, ' ');
    if (entry.tool_name) return entry.tool_name;
    if (entry.http_path) return `${entry.http_method || 'GET'} ${entry.http_path}`;
    return entry.type;
  }
</script>

<div class="screen">
  <div style="display:flex; justify-content:space-between; align-items:flex-start">
    <div>
      <div class="screen-title">Audit Log</div>
      <div class="screen-subtitle">All interactions — nurse, API, LLM, system</div>
    </div>
    <button class="btn btn-secondary" style="font-size:13px; margin-top:4px" on:click={() => goto('/')}>← Back</button>
  </div>

  <!-- Type filter tabs — each maps to a backend event type -->
  <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:16px">
    {#each [['', 'All'], ['api', 'API'], ['system', 'System'], ['llm', 'LLM'], ['tool', 'Tool'], ['nurse', 'Nurse']] as [val, label]}
      {@const color = val ? entryColor(val) : null}
      <button
        on:click={() => setFilter(val)}
        style="font-size:12px; padding:4px 12px; border-radius:9999px; border:1px solid {typeFilter === val ? (color?.border || '#9ca3af') : '#e5e7eb'}; background:{typeFilter === val ? (color?.bg || '#f3f4f6') : 'white'}; color:{typeFilter === val ? (color?.text || '#374151') : '#6b7280'}; cursor:pointer; font-weight:{typeFilter === val ? '700' : '400'}"
      >{label}</button>
    {/each}
    <div style="margin-left:auto; display:flex; gap:8px; align-items:center">
      <!-- n changes trigger loadLog via on:change -->
      <select bind:value={n} on:change={loadLog} style="font-size:12px; padding:4px 8px; border:1px solid #d1d5db; border-radius:4px">
        {#each [50, 100, 250, 500] as v}<option value={v}>{v} entries</option>{/each}
      </select>
      <button class="btn btn-secondary" style="font-size:12px; padding:4px 10px" on:click={loadLog}>Refresh</button>
      {#if !loading}<span style="font-size:12px; color:#9ca3af">{entries.length} shown</span>{/if}
    </div>
  </div>

  {#if error}<div class="error-msg">{error}</div>{/if}

  {#if loading}
    <div style="color:#6b7280; font-size:14px">Loading...</div>
  {:else if entries.length === 0}
    <div class="card" style="text-align:center; color:#9ca3af; padding:32px">
      No audit entries yet{typeFilter ? ` for type "${typeFilter}"` : ''}. Start a session to generate entries.
    </div>
  {:else}
    {#each entries as entry, i}
      {@const c = entryColor(entry.type)}
      <!-- Error entries get a red left border regardless of their type colour -->
      <div style="margin-bottom:8px; padding:10px 14px; border-radius:8px; border:1px solid {c.border}; background:{c.bg}; border-left:4px solid {entry.error ? '#ef4444' : c.border}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px">
          <div style="flex:1; min-width:0">
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:2px">
              <span style="font-size:10px; font-weight:700; padding:1px 7px; border-radius:9999px; background:{c.border}20; color:{c.text}; text-transform:uppercase; letter-spacing:0.05em">{entry.type}</span>
              <span style="font-weight:600; font-size:13px; color:#111827">{entryTitle(entry)}</span>
              {#if entry.error}
                <span style="font-size:11px; background:#fee2e2; color:#dc2626; padding:1px 7px; border-radius:9999px; font-weight:600">ERROR{entry.error_code ? ' · ' + entry.error_code : ''}</span>
              {/if}
              {#if entry.duration_ms != null}
                <span style="font-size:11px; color:#9ca3af">{entry.duration_ms}ms</span>
              {/if}
              {#if entry.http_status}
                <span style="font-size:11px; color:{entry.http_status >= 400 ? '#dc2626' : '#6b7280'}">{entry.http_status}</span>
              {/if}
            </div>
            <div style="font-size:11px; color:#9ca3af">
              {formatTime(entry.timestamp)}
              {#if entry.session_id} · session: {shortSession(entry.session_id)}{/if}
            </div>
            {#if entry.reasoning_hint}
              <!-- LLM chain-of-thought excerpt — key demo talking point -->
              <div style="margin-top:5px; font-size:12px; color:#4338ca; background:#eef2ff; border-radius:4px; padding:5px 8px; border-left:3px solid #a5b4fc; font-style:italic">"{entry.reasoning_hint.length > 180 ? entry.reasoning_hint.slice(0, 180) + '…' : entry.reasoning_hint}"</div>
            {/if}
          </div>
          {#if entry.tool_input || entry.tool_output || entry.detail || entry.http_path}
            <button on:click={() => toggle(i)} style="background:none; border:none; color:{c.text}; font-size:12px; cursor:pointer; white-space:nowrap; flex-shrink:0">
              {expanded[i] ? '▾ Hide' : '▸ Details'}
            </button>
          {/if}
        </div>

        <!-- Expanded payload: shows raw JSON for tool input/output and detail fields -->
        {#if expanded[i]}
          <div style="margin-top:8px; padding-top:8px; border-top:1px solid {c.border}40">
            {#if entry.detail}
              <div style="font-size:11px; font-weight:600; color:#6b7280; margin-bottom:3px">Detail</div>
              <pre style="font-size:11px; background:rgba(0,0,0,0.04); border-radius:4px; padding:7px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; color:#374151; margin:0 0 8px 0">{JSON.stringify(entry.detail, null, 2)}</pre>
            {/if}
            {#if entry.tool_input}
              <div style="font-size:11px; font-weight:600; color:#6b7280; margin-bottom:3px">Input</div>
              <pre style="font-size:11px; background:rgba(0,0,0,0.04); border-radius:4px; padding:7px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; color:#374151; margin:0 0 8px 0">{JSON.stringify(entry.tool_input, null, 2)}</pre>
            {/if}
            {#if entry.tool_output}
              <div style="font-size:11px; font-weight:600; color:#6b7280; margin-bottom:3px">Output</div>
              <pre style="font-size:11px; background:rgba(0,0,0,0.04); border-radius:4px; padding:7px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; color:{entry.error ? '#dc2626' : '#374151'}; margin:0">{(() => { try { return JSON.stringify(JSON.parse(entry.tool_output), null, 2); } catch(_) { return entry.tool_output; } })()}</pre>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>
