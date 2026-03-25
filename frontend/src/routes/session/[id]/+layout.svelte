<!--
  Session-scoped layout — wraps every route under /session/[id]/.

  Responsibilities:
    - Renders the active child page via <slot />
    - Appends a "Delete this session" control at the bottom of every session page

  The delete flow uses a two-step confirmation to prevent accidental deletion:
    1. Low-visibility text link shown by default
    2. Inline confirmation card with Cancel / Confirm buttons

  After deletion the user is sent back to the dashboard (/). The API call
  failure is silently swallowed — the goal is always to navigate home.

  Note: `sid` is derived reactively from `$page.params.id` so it updates
  correctly if SvelteKit ever reuses this layout across different session IDs.
-->
<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { api } from '$lib/api/client.js';

  // Reactive: re-derives from the URL param if the layout is reused
  $: sid = $page.params.id;

  let showConfirm = false;
  let deleting = false;

  async function confirmDelete() {
    deleting = true;
    try { await api.deleteSession(sid); } catch(_) {}
    goto('/');
  }
</script>

<slot />

<div style="text-align:center; padding:32px 0 20px 0">
  {#if showConfirm}
    <div style="display:inline-block; padding:14px 20px; background:#fef2f2; border:1px solid #fca5a5; border-radius:8px; font-size:13px; max-width:320px">
      Delete this session permanently? This cannot be undone.
      <div style="margin-top:10px; display:flex; gap:8px; justify-content:center">
        <button
          style="font-size:12px; padding:5px 14px; border:1px solid #d1d5db; background:white; border-radius:6px; cursor:pointer"
          on:click={() => showConfirm = false}
        >Cancel</button>
        <button
          style="font-size:12px; padding:5px 14px; background:#dc2626; color:white; border:none; border-radius:6px; cursor:pointer"
          on:click={confirmDelete}
          disabled={deleting}
        >{deleting ? 'Deleting...' : 'Yes, Delete Session'}</button>
      </div>
    </div>
  {:else}
    <!-- Intentionally low-contrast to avoid accidental clicks -->
    <button
      style="background:none; border:none; color:#d1d5db; font-size:12px; cursor:pointer; text-decoration:underline"
      on:click={() => showConfirm = true}
    >Delete this session</button>
  {/if}
</div>
