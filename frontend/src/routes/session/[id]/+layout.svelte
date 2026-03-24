<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  let showConfirm = false;

  function startOver() {
    showConfirm = true;
  }

  function confirmStartOver() {
    showConfirm = false;
    goto('/');
  }

  function cancelStartOver() {
    showConfirm = false;
  }
</script>

<div class="session-layout">
  <div class="top-bar">
    <button class="btn-start-over" on:click={startOver}>↩ Start Over</button>
  </div>

  <slot />
</div>

{#if showConfirm}
  <div class="modal-backdrop" on:click={cancelStartOver}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-title">Start Over?</div>
      <p>Current session progress will be lost.</p>
      <div class="modal-actions">
        <button class="btn btn-secondary" on:click={cancelStartOver}>Cancel</button>
        <button class="btn btn-danger" on:click={confirmStartOver}>Yes, Start Over</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .session-layout {
    min-height: 100vh;
  }

  .top-bar {
    position: fixed;
    top: 12px;
    left: 16px;
    z-index: 50;
  }

  .btn-start-over {
    background: none;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-start-over:hover {
    background: #f9fafb;
    color: #374151;
    border-color: #9ca3af;
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal {
    background: white;
    border-radius: 12px;
    padding: 24px;
    width: 320px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  }

  .modal-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #111827;
  }

  .modal p {
    color: #6b7280;
    font-size: 14px;
    margin-bottom: 20px;
  }

  .modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }

  .btn-danger {
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-danger:hover {
    background: #b91c1c;
  }

  .btn-secondary {
    background: white;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-secondary:hover {
    background: #f9fafb;
  }
</style>
