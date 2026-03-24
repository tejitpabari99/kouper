<script>
  import { api } from '$lib/api/client.js';
  import { marked } from 'marked';

  marked.setOptions({ breaks: true });

  export let sessionId;

  let messages = [];
  let input = '';
  let sending = false;
  let open = false;

  async function sendMessage() {
    if (!input.trim() || sending) return;
    const msg = input.trim();
    input = '';
    messages = [...messages, { role: 'user', text: msg }];
    sending = true;
    try {
      const res = await api.sendMessage(sessionId, msg);
      messages = [...messages, { role: 'assistant', text: res.response }];
    } catch (e) {
      messages = [...messages, { role: 'assistant', text: `Error: ${e.message}` }];
    } finally {
      sending = false;
      setTimeout(() => {
        const el = document.getElementById('chat-messages');
        if (el) el.scrollTop = el.scrollHeight;
      }, 50);
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }
</script>

<div style="position:fixed; bottom:24px; right:24px; z-index:100">
  {#if open}
    <div style="width:360px; height:480px; background:white; border-radius:12px; box-shadow:0 8px 32px rgba(0,0,0,0.18); display:flex; flex-direction:column; overflow:hidden">
      <!-- Header -->
      <div style="padding:14px 16px; background:#1e40af; color:white; display:flex; justify-content:space-between; align-items:center">
        <div>
          <div style="font-weight:700; font-size:15px">&#128172; Care Coordinator Assistant</div>
          <div style="font-size:11px; opacity:0.8">Ask me anything about this booking</div>
        </div>
        <button on:click={() => open = false} style="background:none; border:none; color:white; cursor:pointer; font-size:18px; line-height:1">&times;</button>
      </div>

      <!-- Messages -->
      <div id="chat-messages" style="flex:1; overflow-y:auto; padding:12px; display:flex; flex-direction:column; gap:10px">
        {#if messages.length === 0}
          <div style="color:#9ca3af; font-size:13px; text-align:center; margin-top:24px">
            Ask about providers, insurance, availability, or appointment types.
          </div>
        {/if}
        {#each messages as msg}
          <div style="display:flex; {msg.role === 'user' ? 'justify-content:flex-end' : 'justify-content:flex-start'}">
            {#if msg.role === 'assistant'}
              <div class="msg-assistant" style="max-width:85%; padding:8px 12px; border-radius:8px; font-size:13px; line-height:1.5; background:#f3f4f6; color:#111827">
                {@html marked(msg.text)}
              </div>
            {:else}
              <div style="max-width:85%; padding:8px 12px; border-radius:8px; font-size:13px; line-height:1.5; background:#2563eb; color:white">
                {msg.text}
              </div>
            {/if}
          </div>
        {/each}
        {#if sending}
          <div style="display:flex; justify-content:flex-start">
            <div style="background:#f3f4f6; padding:8px 12px; border-radius:8px; font-size:13px; color:#6b7280">
              Thinking...
            </div>
          </div>
        {/if}
      </div>

      <!-- Input -->
      <div style="padding:10px; border-top:1px solid #e5e7eb; display:flex; gap:8px">
        <textarea
          bind:value={input}
          on:keydown={handleKey}
          placeholder="Ask about providers, insurance..."
          rows="2"
          style="flex:1; padding:8px 10px; border:1px solid #d1d5db; border-radius:6px; font-size:13px; resize:none; font-family:inherit"
        ></textarea>
        <button
          on:click={sendMessage}
          disabled={!input.trim() || sending}
          style="padding:8px 14px; background:#2563eb; color:white; border:none; border-radius:6px; font-weight:600; font-size:13px; cursor:pointer; align-self:flex-end"
        >
          Send
        </button>
      </div>
    </div>
  {:else}
    <button
      on:click={() => open = true}
      style="padding:12px 20px; background:#1e40af; color:white; border:none; border-radius:9999px; font-weight:700; font-size:14px; cursor:pointer; box-shadow:0 4px 16px rgba(30,64,175,0.4); display:flex; align-items:center; gap:8px"
    >
      &#128172; Ask Assistant
    </button>
  {/if}
</div>

<style>
  .msg-assistant :global(p) { margin: 0 0 8px 0; }
  .msg-assistant :global(p:last-child) { margin-bottom: 0; }
  .msg-assistant :global(table) { border-collapse: collapse; width: 100%; font-size: 12px; margin: 8px 0; }
  .msg-assistant :global(th), .msg-assistant :global(td) { border: 1px solid #d1d5db; padding: 4px 8px; text-align: left; }
  .msg-assistant :global(th) { background: #f3f4f6; font-weight: 600; }
  .msg-assistant :global(strong) { font-weight: 700; }
  .msg-assistant :global(ul), .msg-assistant :global(ol) { margin: 4px 0; padding-left: 16px; }
  .msg-assistant :global(li) { margin: 2px 0; }
  .msg-assistant :global(blockquote) { margin: 4px 0; padding-left: 10px; border-left: 3px solid #d1d5db; color: #6b7280; font-style: italic; }
</style>
