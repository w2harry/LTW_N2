(function () {
  const root = document.getElementById('ai-chatbox-root');
  if (!root) return;

  const toggleBtn = root.querySelector('#ai-chat-toggle');
  const toggleText = root.querySelector('.ai-chat-toggle-text');
  const panel = root.querySelector('#ai-chat-panel');
  const backdrop = root.querySelector('#ai-chat-backdrop');
  const closeBtn = root.querySelector('#ai-chat-close');
  const refreshBtn = root.querySelector('#ai-chat-refresh');
  const messagesEl = root.querySelector('#ai-chat-messages');
  const form = root.querySelector('#ai-chat-form');
  const input = root.querySelector('#ai-chat-input');
  const sendBtn = root.querySelector('#ai-chat-send');

  if (!toggleBtn || !toggleText || !panel || !backdrop || !closeBtn || !refreshBtn || !messagesEl || !form || !input || !sendBtn) {
    return;
  }

  const HISTORY_KEY = 'momcare_ai_chat_history_v1';
  const PANEL_STATE_KEY = 'momcare_ai_chat_open_v1';
  const MAX_HISTORY = 20;
  const PANEL_ANIMATION_MS = 220;
  const WELCOME_MESSAGE = 'Xin chao! Minh la tro ly MomCare AI, san sang ho tro me va be voi goi y de hieu, ngan gon.';

  const state = {
    open: false,
    hideTimer: null,
    pending: false,
  };

  function isAssistantRole(role) {
    return role === 'assistant' || role === 'ai';
  }

  function removeIfAttached(element) {
    if (element && element.parentNode === messagesEl) {
      messagesEl.removeChild(element);
    }
  }

  function readHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function writeHistory(history) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
    } catch (_) {
      // Ignore localStorage failures.
    }
  }

  function clearHistory() {
    try {
      localStorage.removeItem(HISTORY_KEY);
    } catch (_) {
      // Ignore localStorage failures.
    }
  }

  function setBusy(isBusy) {
    state.pending = isBusy;
    sendBtn.disabled = isBusy;
    input.disabled = isBusy;
    refreshBtn.disabled = isBusy;
  }

  function escapeHtml(value) {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatInlineMarkdown(line) {
    let text = line;
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    return text;
  }

  function markdownToSafeHtml(content) {
    const source = escapeHtml(content).replace(/\r\n/g, '\n');
    const codeBlocks = [];

    const withCodePlaceholders = source.replace(/```([\s\S]*?)```/g, (_, block) => {
      const token = `__MC_CODE_${codeBlocks.length}__`;
      codeBlocks.push(`<pre><code>${block.trim()}</code></pre>`);
      return token;
    });

    const lines = withCodePlaceholders.split('\n');
    const htmlLines = [];
    let listType = null;

    function closeListIfOpen() {
      if (listType) {
        htmlLines.push(`</${listType}>`);
        listType = null;
      }
    }

    lines.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line) {
        closeListIfOpen();
        return;
      }

      if (line.startsWith('__MC_CODE_')) {
        closeListIfOpen();
        htmlLines.push(line);
        return;
      }

      const heading = line.match(/^(#{1,4})\s+(.*)$/);
      if (heading) {
        closeListIfOpen();
        const level = heading[1].length;
        htmlLines.push(`<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`);
        return;
      }

      const bullet = line.match(/^[-*]\s+(.*)$/);
      if (bullet) {
        if (listType !== 'ul') {
          closeListIfOpen();
          listType = 'ul';
          htmlLines.push('<ul>');
        }
        htmlLines.push(`<li>${formatInlineMarkdown(bullet[1])}</li>`);
        return;
      }

      const ordered = line.match(/^\d+\.\s+(.*)$/);
      if (ordered) {
        if (listType !== 'ol') {
          closeListIfOpen();
          listType = 'ol';
          htmlLines.push('<ol>');
        }
        htmlLines.push(`<li>${formatInlineMarkdown(ordered[1])}</li>`);
        return;
      }

      if (line.startsWith('&gt;')) {
        closeListIfOpen();
        htmlLines.push(`<blockquote>${formatInlineMarkdown(line.replace(/^&gt;\s?/, ''))}</blockquote>`);
        return;
      }

      closeListIfOpen();
      htmlLines.push(`<p>${formatInlineMarkdown(line)}</p>`);
    });

    closeListIfOpen();

    let html = htmlLines.join('');
    codeBlocks.forEach((block, index) => {
      html = html.replace(`__MC_CODE_${index}__`, block);
    });

    return html;
  }

  function normalizeRole(role) {
    return isAssistantRole(role) ? 'ai' : role;
  }

  function renderMessage(role, content, asMarkdown) {
    const displayRole = normalizeRole(role);
    const item = document.createElement('div');
    item.className = `ai-chat-item ${displayRole}`;
    if (displayRole === 'ai' && asMarkdown) {
      item.innerHTML = markdownToSafeHtml(content);
    } else {
      item.textContent = content;
    }
    messagesEl.appendChild(item);
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
    return item;
  }

  function renderTypingBubble() {
    const item = document.createElement('div');
    item.className = 'ai-chat-item ai loading';
    item.innerHTML = '<span class="ai-chat-dot"></span><span class="ai-chat-dot"></span><span class="ai-chat-dot"></span>';
    messagesEl.appendChild(item);
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
    return item;
  }

  function renderAll(history) {
    messagesEl.innerHTML = '';
    if (!history.length) {
      renderMessage('ai', WELCOME_MESSAGE, true);
      return;
    }
    history.forEach((item) => renderMessage(item.role, item.content, isAssistantRole(item.role)));
  }

  function isPanelOpen() {
    return state.open;
  }

  function persistPanelState(isOpen) {
    try {
      localStorage.setItem(PANEL_STATE_KEY, isOpen ? '1' : '0');
    } catch (_) {
      // Ignore localStorage failures.
    }
  }

  function autoResizeInput() {
    input.style.height = 'auto';
    const next = Math.min(Math.max(input.scrollHeight, 40), 120);
    input.style.height = `${next}px`;
  }

  function updateToggleUi(isOpen) {
    toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', isOpen ? 'Đóng trợ lý AI' : 'Mở trợ lý AI');
    toggleText.textContent = isOpen ? 'Đóng AI' : 'Tư vấn AI';
  }

  function setPanelState(open) {
    const isOpen = Boolean(open);
    if (state.open === isOpen) return;

    state.open = isOpen;
    updateToggleUi(isOpen);

    if (state.hideTimer) {
      clearTimeout(state.hideTimer);
      state.hideTimer = null;
    }

    if (isOpen) {
      panel.hidden = false;
      backdrop.hidden = false;
      panel.setAttribute('aria-hidden', 'false');
      requestAnimationFrame(() => {
        root.classList.add('is-open');
      });
    } else {
      root.classList.remove('is-open');
      panel.setAttribute('aria-hidden', 'true');
      state.hideTimer = setTimeout(() => {
        panel.hidden = true;
        backdrop.hidden = true;
      }, PANEL_ANIMATION_MS);
    }

    if (isOpen) {
      autoResizeInput();
      setTimeout(() => input.focus(), 0);
    }

    persistPanelState(isOpen);
  }

  function getInitialPanelState() {
    try {
      return localStorage.getItem(PANEL_STATE_KEY) === '1';
    } catch (_) {
      return false;
    }
  }

  async function askAI(message, history) {
    const response = await fetch('/api/ai-chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': typeof getCookie === 'function' ? getCookie('csrftoken') : '',
      },
      body: JSON.stringify({
        message,
        history,
      }),
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Khong the ket noi tro ly AI.');
    }
    return {
      reply: data.reply,
      reasoningDetails: data.reasoning_details || null,
    };
  }

  toggleBtn.addEventListener('click', () => setPanelState(!isPanelOpen()));
  closeBtn.addEventListener('click', () => setPanelState(false));
  backdrop.addEventListener('click', () => setPanelState(false));
  refreshBtn.addEventListener('click', () => {
    if (state.pending) return;
    clearHistory();
    renderAll([]);
    setPanelState(true);
    autoResizeInput();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isPanelOpen()) {
      setPanelState(false);
      toggleBtn.focus();
    }
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  input.addEventListener('input', autoResizeInput);

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (state.pending) return;

    const message = input.value.trim();
    if (!message) return;

    const history = readHistory();
    const userItem = { role: 'user', content: message };
    history.push(userItem);
    writeHistory(history);
    renderMessage('user', message, false);
    input.value = '';
    autoResizeInput();

    setBusy(true);
    const loadingEl = renderTypingBubble();

    try {
      const result = await askAI(message, history);
      removeIfAttached(loadingEl);
      renderMessage('ai', result.reply, true);
      history.push({
        role: 'assistant',
        content: result.reply,
        reasoning_details: result.reasoningDetails,
      });
      writeHistory(history);
    } catch (error) {
      removeIfAttached(loadingEl);
      renderMessage('ai', `AI đang quá tải để trả lời, lỗi cụ thể: ${error.message}`, false);
    } finally {
      setBusy(false);
      if (isPanelOpen()) {
        input.focus();
      }
    }
  });

  renderAll(readHistory());
  setPanelState(getInitialPanelState());
  autoResizeInput();
})();
