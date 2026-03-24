<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { api } from '$lib/api/client.js';

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
    <button
      style="background:none; border:none; color:#d1d5db; font-size:12px; cursor:pointer; text-decoration:underline"
      on:click={() => showConfirm = true}
    >Delete this session</button>
  {/if}
</div>
