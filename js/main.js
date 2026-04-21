const obs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => obs.observe(el));

(function initPortfolioAskChat() {
  const toggle = document.getElementById('portfolio-chat-toggle');
  const panel = document.getElementById('portfolio-chat-panel');
  const closeBtn = document.getElementById('portfolio-chat-close');
  const messagesEl = document.getElementById('portfolio-chat-messages');
  const inputEl = document.getElementById('portfolio-chat-input');
  const quickEl = document.getElementById('portfolio-chat-quick');

  if (!toggle || !panel || !messagesEl || !inputEl || !quickEl) return;

  const quickPrompts = [
    'What did you build at Apexon?',
    'Explain your agentic AI work',
    'What is your strongest project?',
  ];

  let thinkingNode = null;
  let isSending = false;

  function getAskApiBase() {
    const meta = document.querySelector('meta[name="portfolio-ask-api"]');
    const raw = meta && meta.content ? meta.content.trim() : '';
    return raw ? raw.replace(/\/$/, '') : '';
  }

  function setPanelOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    if (open) inputEl.focus();
  }

  function appendMessage(role, text) {
    const wrap = document.createElement('div');
    wrap.className = `portfolio-chat__msg portfolio-chat__msg--${role === 'user' ? 'user' : 'ai'}`;
    const label = document.createElement('strong');
    label.textContent = role === 'user' ? 'You' : "Afzal's AI";
    const p = document.createElement('p');
    p.textContent = text;
    wrap.appendChild(label);
    wrap.appendChild(p);
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showThinking() {
    hideThinking();
    thinkingNode = document.createElement('div');
    thinkingNode.className = 'portfolio-chat__msg portfolio-chat__thinking';
    thinkingNode.textContent = 'AI is thinking…';
    messagesEl.appendChild(thinkingNode);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideThinking() {
    if (thinkingNode && thinkingNode.parentNode) {
      thinkingNode.parentNode.removeChild(thinkingNode);
    }
    thinkingNode = null;
  }

  function setBusy(busy) {
    isSending = busy;
    inputEl.disabled = busy;
    quickEl.querySelectorAll('.portfolio-chat__chip').forEach(chip => {
      chip.disabled = busy;
    });
  }

  async function sendQuestion(question) {
    const trimmed = (question || '').trim();
    if (!trimmed || isSending) return;

    const base = getAskApiBase();
    if (!base) {
      appendMessage('ai', 'Chat API URL is not set. Add your deployed API origin to the portfolio-ask-api meta tag in index.html (e.g. https://your-api.onrender.com).');
      return;
    }

    appendMessage('user', trimmed);
    showThinking();
    setBusy(true);

    try {
      const res = await fetch(`${base}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed }),
      });
      const data = await res.json().catch(() => ({}));
      hideThinking();

      if (!res.ok) {
        const detail = data.detail;
        const msg = typeof detail === 'string'
          ? detail
          : Array.isArray(detail) && detail[0]?.msg
            ? detail[0].msg
            : `Request failed (${res.status}).`;
        appendMessage('ai', msg);
        return;
      }

      const answer = typeof data.answer === 'string' ? data.answer : 'No answer returned.';
      appendMessage('ai', answer);
    } catch {
      hideThinking();
      appendMessage('ai', 'Could not reach the API (network, CORS, or cold start). Wait ~1 min and retry, or open the API URL in a new tab once to wake Render, then try again.');
    } finally {
      setBusy(false);
    }
  }

  quickPrompts.forEach(text => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'portfolio-chat__chip';
    chip.textContent = text;
    chip.addEventListener('click', () => sendQuestion(text));
    quickEl.appendChild(chip);
  });

  toggle.addEventListener('click', () => setPanelOpen(panel.hidden));
  if (closeBtn) closeBtn.addEventListener('click', () => setPanelOpen(false));

  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const q = inputEl.value;
      inputEl.value = '';
      sendQuestion(q);
    }
  });
})();
