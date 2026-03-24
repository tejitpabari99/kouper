<script>
  import { api } from '$lib/api/client.js';
  import { marked } from 'marked';
  import { chatMessages } from '$lib/stores/session.js';

  marked.setOptions({ breaks: true });

  export let sessionId;
  export let context = '';

  $: messages = $chatMessages[sessionId] || [];
  let input = '';
  let sending = false;
  let slowWarning = false;
  let open = false;

  function addMessage(msg) {
    chatMessages.update(all => ({
      ...all,
      [sessionId]: [...(all[sessionId] || []), msg]
    }));
  }

  function makeIncidentId() {
    return 'INC-' + Date.now().toString(36).toUpperCase();
  }

  let feedbackState = {}; // { incidentId: 'idle' | 'sending' | 'sent' }
  let feedbackComment = {};

  async function reportIncident(incidentId, errorCode, errorMessage) {
    feedbackState = { ...feedbackState, [incidentId]: 'sending' };
    try {
      await api.submitErrorFeedback({
        incident_id: incidentId,
        error_code: errorCode || null,
        error_message: errorMessage,
        session_id: sessionId,
        page_context: context.slice(0, 300),
        user_comment: feedbackComment[incidentId] || '',
      });
      feedbackState = { ...feedbackState, [incidentId]: 'sent' };
    } catch (_) {
      feedbackState = { ...feedbackState, [incidentId]: 'sent' };
    }
  }

  async function sendMessage() {
    if (!input.trim() || sending) return;
    const msg = input.trim();
    input = '';
    addMessage({ role: 'user', text: msg });
    sending = true;
    slowWarning = false;

    let slowTimer = setTimeout(() => {
      if (sending) slowWarning = true;
    }, 5000);
    let timeoutTimer = setTimeout(() => {
      if (sending) {
        sending = false;
        slowWarning = false;
        const incidentId = makeIncidentId();
        addMessage({
          role: 'assistant',
          text: 'The assistant is not responding. You can continue booking without it.',
          error: true,
          errorCode: 'TIMEOUT',
          errorMessage: 'Request timed out after 15s',
          incidentId,
        });
        clearTimeout(slowTimer);
      }
    }, 15000);

    try {
      const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('Request timed out after 30s')), 30000));
      const res = await Promise.race([api.sendMessage(sessionId, msg, context), timeout]);
      clearTimeout(slowTimer);
      clearTimeout(timeoutTimer);
      slowWarning = false;
      addMessage({ role: 'assistant', text: res.response });
    } catch (e) {
      clearTimeout(slowTimer);
      clearTimeout(timeoutTimer);
      slowWarning = false;
      const incidentId = makeIncidentId();
      addMessage({
        role: 'assistant',
        text: e.message,
        error: true,
        errorCode: e.code || 'UNKNOWN',
        errorMessage: e.message,
        incidentId,
      });
    } finally {
      sending = false;
      setTimeout(() => {
        const el = document.getElementById('chat-messages');
        if (el) el.scrollTop = el.scrollHeight;
      }, 50);
    }
  }

  async function submitPrompt(text) {
    input = text;
    await sendMessage();
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
          <div style="padding:8px 4px">
            <div style="color:#9ca3af; font-size:12px; margin-bottom:10px; text-align:center">Suggested questions:</div>
            {#each [
              'Is this patient covered for this specialty?',
              "What's the difference between NEW and ESTABLISHED?",
              'Who else is available for this specialty?'
            ] as prompt}
              <button type="button" on:click={() => submitPrompt(prompt)}
                style="display:block;width:100%;text-align:left;padding:7px 10px;margin-bottom:6px;background:#f0f4ff;border:1px solid #c7d2fe;border-radius:6px;font-size:12px;color:#3730a3;cursor:pointer;line-height:1.4">
                {prompt}
              </button>
            {/each}
          </div>
        {/if}
        {#each messages as msg}
          <div style="display:flex; {msg.role === 'user' ? 'justify-content:flex-end' : 'justify-content:flex-start'}">
            {#if msg.role === 'assistant'}
              {#if msg.error}
                <div style="max-width:92%; padding:10px 12px; border-radius:8px; font-size:13px; line-height:1.5; background:#fef2f2; border:1px solid #fca5a5; color:#991b1b">
                  <div style="font-weight:600; margin-bottom:4px">⚠ System Error</div>
                  <div style="margin-bottom:6px">{msg.text}</div>
                  <div style="font-size:11px; color:#b91c1c; font-family:monospace; margin-bottom:8px">
                    Code: {msg.errorCode} &nbsp;·&nbsp; Incident: {msg.incidentId}
                  </div>
                  {#if feedbackState[msg.incidentId] === 'sent'}
                    <div style="font-size:11px; color:#16a34a; font-weight:600">✓ Reported. In production, this would notify the engineering team.</div>
                  {:else}
                    <div style="margin-bottom:4px">
                      <textarea
                        placeholder="Optional: describe what you were doing (helps the team)"
                        rows="2"
                        style="width:100%; font-size:11px; padding:4px 6px; border:1px solid #fca5a5; border-radius:4px; resize:none; background:#fff8f8; color:#374151; box-sizing:border-box; font-family:inherit"
                        on:input={(e) => feedbackComment = { ...feedbackComment, [msg.incidentId]: e.target.value }}
                      ></textarea>
                    </div>
                    <button
                      on:click={() => reportIncident(msg.incidentId, msg.errorCode, msg.errorMessage)}
                      disabled={feedbackState[msg.incidentId] === 'sending'}
                      style="font-size:11px; padding:3px 10px; background:#dc2626; color:white; border:none; border-radius:4px; cursor:pointer"
                    >
                      {feedbackState[msg.incidentId] === 'sending' ? 'Sending…' : 'Report Issue'}
                    </button>
                  {/if}
                </div>
              {:else}
                <div class="msg-assistant" style="max-width:85%; padding:8px 12px; border-radius:8px; font-size:13px; line-height:1.5; background:#f3f4f6; color:#111827">
                  {@html marked(msg.text)}
                </div>
              {/if}
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
              {slowWarning ? 'Still working... (taking longer than usual)' : 'Thinking...'}
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
