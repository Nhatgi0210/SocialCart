// SocialCart Prototype — App Logic
// Dependency-free, backend-free. State resets on reload.
// Direction: Concept B — Soft Daylight (docs/product-design.md)

'use strict';

/* ================================================================
   STATE
   ================================================================ */
const state = {
  isLoggedIn: false,
  seller: null,
  conversations: [],
  activeConvId: null,
  platformFilter: 'all',   // 'all' | 'facebook' | 'zalo'
  statusFilter: 'all',     // 'all' | 'moi' | 'dang-xu-ly' | 'da-xu-ly'
  orderProducts: [],       // [{productId, variantId, qty}]
  pendingFailedMsg: null,  // {convId, text} for retry
};

/* ================================================================
   BOOT
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {
  // Deep clone mock data into state
  state.conversations = JSON.parse(JSON.stringify(MOCK_DATA.conversations));
  // Convert timestamp strings back to Date objects
  state.conversations.forEach(c => {
    c.timestamp = new Date(c.timestamp);
    c.messages.forEach(m => m.time = new Date(m.time));
  });

  bindLoginForm();
  bindSidebarFilters();
  bindAvatarMenu();
  bindModalTriggers();
  bindOrderForm();
  bindChatInput();
  bindMobileBack();
  showScreen('login');
});

/* ================================================================
   SCREEN ROUTER
   ================================================================ */
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(`screen-${name}`);
  if (target) target.classList.add('active');
}

/* ================================================================
   LOGIN
   ================================================================ */
function bindLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearLoginErrors();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    let valid = true;

    if (!email) {
      showFieldError('login-email-error', 'Vui lòng nhập email');
      document.getElementById('login-email').classList.add('error');
      valid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      showFieldError('login-email-error', 'Email không hợp lệ');
      document.getElementById('login-email').classList.add('error');
      valid = false;
    }

    if (!password) {
      showFieldError('login-password-error', 'Vui lòng nhập mật khẩu');
      document.getElementById('login-password').classList.add('error');
      valid = false;
    }

    if (!valid) return;

    // Simulated auth
    const btn = document.getElementById('btn-login');
    setLoginLoading(true, btn);

    await delay(900);

    const seller = MOCK_DATA.seller;
    if (email === seller.email && password === seller.password) {
      state.seller = seller;
      state.isLoggedIn = true;
      setLoginLoading(false, btn);
      enterApp();
    } else {
      setLoginLoading(false, btn);
      document.getElementById('login-error-banner').classList.add('visible');
      document.getElementById('login-error-banner').setAttribute('role', 'alert');
    }
  });

  // Clear errors on input
  ['login-email', 'login-password'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => {
      document.getElementById(id).classList.remove('error');
      document.getElementById(`${id}-error`).classList.remove('visible');
      document.getElementById('login-error-banner').classList.remove('visible');
    });
  });

  // Enter submits form
  form.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') form.requestSubmit();
  });
}

function setLoginLoading(loading, btn) {
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<span class="spinner" aria-hidden="true"></span> Đang đăng nhập…'
    : '<span>🔑</span> Đăng nhập';
}

function clearLoginErrors() {
  document.getElementById('login-error-banner').classList.remove('visible');
  ['login-email', 'login-password'].forEach(id => {
    document.getElementById(id)?.classList.remove('error');
  });
  ['login-email-error', 'login-password-error'].forEach(id => {
    document.getElementById(id)?.classList.remove('visible');
  });
}

function showFieldError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.add('visible'); }
}

/* ================================================================
   APP ENTRY
   ================================================================ */
function enterApp() {
  // Populate seller info
  document.getElementById('seller-avatar-initials').textContent = state.seller.avatar;
  document.getElementById('dropdown-seller-name').textContent = state.seller.name;
  document.getElementById('dropdown-seller-email').textContent = state.seller.email;

  renderConversationList();
  showInboxEmptyState();
  showScreen('app');
}

function logout() {
  state.isLoggedIn = false;
  state.seller = null;
  state.activeConvId = null;
  state.orderProducts = [];
  closeSellerDropdown();
  // Reset login form
  document.getElementById('login-form').reset();
  clearLoginErrors();
  showScreen('login');
}

/* ================================================================
   SIDEBAR — AVATAR MENU
   ================================================================ */
function bindAvatarMenu() {
  const btn = document.getElementById('seller-avatar-btn');
  const dropdown = document.getElementById('seller-dropdown');
  if (!btn || !dropdown) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
    btn.setAttribute('aria-expanded', dropdown.classList.contains('open'));
  });

  document.addEventListener('click', () => closeSellerDropdown());
  dropdown.addEventListener('click', e => e.stopPropagation());

  document.getElementById('btn-logout')?.addEventListener('click', logout);
}

function closeSellerDropdown() {
  document.getElementById('seller-dropdown')?.classList.remove('open');
  document.getElementById('seller-avatar-btn')?.setAttribute('aria-expanded', 'false');
}

/* ================================================================
   SIDEBAR — FILTERS & CONVERSATION LIST
   ================================================================ */
function bindSidebarFilters() {
  // Platform filter
  document.querySelectorAll('[data-platform-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.platformFilter = btn.dataset.platformFilter;
      document.querySelectorAll('[data-platform-filter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderConversationList();
    });
  });

  // Status filter
  document.querySelectorAll('[data-status-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.statusFilter = btn.dataset.statusFilter;
      document.querySelectorAll('[data-status-filter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderConversationList();
    });
  });
}

function getFilteredConversations() {
  return state.conversations.filter(c => {
    const platformOk = state.platformFilter === 'all' || c.platform === state.platformFilter;
    const statusOk = state.statusFilter === 'all'
      || (state.statusFilter === 'moi' && c.processingStatus === 'Mới')
      || (state.statusFilter === 'dang-xu-ly' && c.processingStatus === 'Đang xử lý')
      || (state.statusFilter === 'da-xu-ly' && c.processingStatus === 'Đã xử lý');
    return platformOk && statusOk;
  }).sort((a, b) => b.timestamp - a.timestamp);
}

function renderConversationList() {
  const list = document.getElementById('conversation-list');
  if (!list) return;

  const filtered = getFilteredConversations();
  list.innerHTML = '';

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="empty-inbox" role="status" aria-live="polite">
        <div class="empty-inbox-icon" aria-hidden="true">📭</div>
        <h3>Không có hội thoại nào</h3>
        <p>Không có hội thoại nào khớp bộ lọc hiện tại.</p>
      </div>`;
    return;
  }

  filtered.forEach(conv => {
    const item = buildConvItem(conv);
    list.appendChild(item);
  });
}

function buildConvItem(conv) {
  const el = document.createElement('div');
  el.className = `conv-item${conv.unread ? ' unread' : ''}${conv.id === state.activeConvId ? ' selected' : ''}`;
  el.setAttribute('role', 'button');
  el.setAttribute('tabindex', '0');
  el.setAttribute('aria-label', `${conv.customerName}, ${conv.platform}, ${conv.processingStatus}, ${aiStatusLabel(conv.aiStatus)}`);
  el.dataset.convId = conv.id;

  const platformLabel = conv.platform === 'facebook' ? 'F' : 'Z';
  const platformText = conv.platform === 'facebook' ? 'Facebook' : 'Zalo';
  const aiStatusHtml = buildAiStatusBadge(conv.aiStatus);
  const previewHtml = conv.lastMessageIsAI
    ? `<span class="ai-preview-tag" aria-hidden="true">AI</span>${escHtml(conv.lastMessage.replace(/^AI:\s*/, ''))}`
    : escHtml(conv.lastMessage);

  el.innerHTML = `
    <div class="conv-avatar" aria-hidden="true">
      <div class="conv-avatar-img">${escHtml(conv.customerAvatar)}</div>
      <div class="platform-badge ${conv.platform}" aria-hidden="true">${platformLabel}</div>
    </div>
    <div class="conv-content">
      <div class="conv-top-row">
        <span class="conv-name">${escHtml(conv.customerName)}</span>
        <span class="conv-time">${relativeTime(conv.timestamp)}</span>
      </div>
      <div class="conv-preview">${previewHtml}</div>
      <div class="conv-bottom-row">
        ${aiStatusHtml}
        <span class="processing-badge">${escHtml(conv.processingStatus)}</span>
        ${conv.unread ? '<span class="unread-dot" aria-hidden="true"></span>' : ''}
      </div>
    </div>
    <span class="sr-only">Nền tảng: ${platformText}</span>`;

  el.addEventListener('click', () => openConversation(conv.id));
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openConversation(conv.id);
    }
  });

  return el;
}

function buildAiStatusBadge(status) {
  const configs = {
    'ai-active': { icon: '🤖', label: 'AI đang xử lý', cls: 'ai-active' },
    'need-seller': { icon: '🔔', label: 'Cần người bán', cls: 'need-seller' },
    'seller-handling': { icon: '👤', label: 'Người bán đang xử lý', cls: 'seller-handling' }
  };
  const c = configs[status] || configs['ai-active'];
  return `<span class="ai-status-badge ${c.cls}" aria-label="${c.label}"><span aria-hidden="true">${c.icon}</span>${c.label}</span>`;
}

function aiStatusLabel(status) {
  const labels = {
    'ai-active': 'AI đang xử lý',
    'need-seller': 'Cần người bán',
    'seller-handling': 'Người bán đang xử lý'
  };
  return labels[status] || '';
}

/* ================================================================
   OPEN CONVERSATION
   ================================================================ */
function openConversation(convId) {
  const conv = state.conversations.find(c => c.id === convId);
  if (!conv) return;

  // Mark read
  conv.unread = false;
  state.activeConvId = convId;

  renderConversationList();
  renderChatArea(conv);
  renderInfoPanel(conv);

  // Mobile: show chat
  if (window.innerWidth <= 768) {
    document.querySelector('.sidebar')?.classList.add('hidden');
    document.querySelector('.chat-area')?.classList.add('visible');
  }
}

function showInboxEmptyState() {
  const main = document.getElementById('main-area');
  if (!main) return;
  main.innerHTML = `
    <div class="inbox-empty-state">
      <div class="icon" aria-hidden="true">💬</div>
      <h2>Chọn một hội thoại</h2>
      <p>Chọn hội thoại từ danh sách bên trái để bắt đầu trả lời khách hàng.</p>
    </div>`;
}

/* ================================================================
   CHAT AREA RENDER
   ================================================================ */
function renderChatArea(conv) {
  const main = document.getElementById('main-area');
  if (!main) return;

  main.innerHTML = `
    <section class="chat-area" id="chat-panel" aria-label="Hội thoại với ${escHtml(conv.customerName)}">
      <!-- Chat Header -->
      <header class="chat-header">
        <div class="chat-header-left">
          <button class="btn btn-icon back-btn" id="btn-back" aria-label="Quay lại danh sách">←</button>
          <div class="chat-header-avatar" aria-hidden="true">${escHtml(conv.customerAvatar)}</div>
          <div class="chat-header-info">
            <div class="chat-header-name">${escHtml(conv.customerName)}</div>
            <div class="chat-header-meta">
              <span class="chat-header-platform ${conv.platform}" aria-label="${conv.platform === 'facebook' ? 'Facebook' : 'Zalo'}">
                <span aria-hidden="true">${conv.platform === 'facebook' ? 'f' : 'Z'}</span>
                ${conv.platform === 'facebook' ? 'Facebook' : 'Zalo'}
              </span>
              <span id="header-ai-status-wrap">${buildHeaderAiStatus(conv.aiStatus)}</span>
            </div>
          </div>
        </div>
        <div class="chat-header-actions">
          <span id="ai-toggle-wrap">${buildAiToggleBtn(conv.aiStatus)}</span>
          <button class="btn btn-primary" id="btn-create-order" aria-haspopup="dialog">
            <span aria-hidden="true">📋</span> Tạo đơn hàng
          </button>
        </div>
      </header>

      <!-- Handoff Banner -->
      <div id="handoff-banner" class="handoff-banner${conv.aiStatus === 'need-seller' ? ' visible' : ''}" role="alert" aria-live="assertive">
        <span class="handoff-banner-icon" aria-hidden="true">🔔</span>
        <div class="handoff-banner-text">
          AI đã chuyển hội thoại cho bạn
          <span class="handoff-banner-sub">Khách hàng đang chờ bạn phản hồi</span>
        </div>
        <button class="btn btn-success" id="btn-take-over" aria-label="Nhận xử lý hội thoại này">Nhận xử lý</button>
      </div>

      <!-- AI Alert (failure) -->
      <div id="chat-ai-alert" class="chat-ai-alert" role="alert" aria-live="polite">
        <span aria-hidden="true">⚠️</span>
        <span class="chat-ai-alert-text">AI gặp lỗi. Hội thoại cần bạn xử lý.</span>
        <button class="btn btn-secondary" id="btn-retry-ai" style="margin-left:auto">Thử kết nối lại AI</button>
      </div>

      <!-- Messages -->
      <main class="chat-messages" id="chat-messages" role="log" aria-label="Tin nhắn" aria-live="polite">
        <!-- Rendered by JS -->
      </main>

      <!-- Typing indicator -->
      <div class="typing-indicator" id="typing-indicator" role="status" aria-label="AI đang soạn tin nhắn" aria-live="polite">
        <div class="msg-avatar" style="background:var(--teal-light);color:var(--teal-dark)" aria-hidden="true">🤖</div>
        <div>
          <div class="typing-dots" aria-hidden="true">
            <span></span><span></span><span></span>
          </div>
          <span class="typing-label">AI đang trả lời…</span>
        </div>
      </div>

      <!-- Chat Input -->
      <footer class="chat-input-area">
        <div class="platform-disconnected-msg" id="platform-disconnected" role="alert">
          <span aria-hidden="true">⚠️</span>
          <span>Không thể gửi tin nhắn. Kết nối ${conv.platform === 'facebook' ? 'Facebook' : 'Zalo'} đang bị gián đoạn.</span>
          <button class="btn-retry" style="margin-left:auto">Kết nối lại</button>
        </div>
        <div class="input-row">
          <textarea
            class="chat-input"
            id="chat-input"
            placeholder="Nhập tin nhắn…"
            rows="1"
            aria-label="Nhập tin nhắn"
          ></textarea>
          <button class="btn-send" id="btn-send" disabled aria-label="Gửi tin nhắn">
            <span aria-hidden="true">➤</span>
          </button>
        </div>
      </footer>
    </section>`;

  renderMessages(conv);
  bindChatAreaEvents(conv);

  // Show AI alert if needed
  if (conv.aiStatus === 'need-seller') {
    document.getElementById('chat-ai-alert').classList.add('visible');
  }
}

function buildHeaderAiStatus(status) {
  const configs = {
    'ai-active': { icon: '🤖', label: 'AI đang xử lý', cls: 'ai-active' },
    'need-seller': { icon: '🔔', label: 'Cần người bán', cls: 'need-seller' },
    'seller-handling': { icon: '👤', label: 'Người bán đang xử lý', cls: 'seller-handling' }
  };
  const c = configs[status] || configs['ai-active'];
  return `<span class="header-ai-status ${c.cls}" aria-label="${c.label}"><span aria-hidden="true">${c.icon}</span>${c.label}</span>`;
}

function buildAiToggleBtn(status) {
  if (status === 'ai-active') {
    return `<button class="btn btn-secondary" id="btn-toggle-ai" data-action="disable" aria-label="Tắt AI — AI hiện đang xử lý hội thoại này">
      <span aria-hidden="true">🤖</span> Tắt AI
    </button>`;
  } else if (status === 'seller-handling') {
    return `<button class="btn btn-success" id="btn-toggle-ai" data-action="enable" aria-label="Bật lại AI">
      <span aria-hidden="true">🤖</span> Bật lại AI
    </button>`;
  }
  return ''; // need-seller: no toggle until seller takes over
}

function renderMessages(conv) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  container.innerHTML = '';

  conv.messages.forEach(msg => {
    const el = buildMessageEl(msg, conv);
    if (el) container.appendChild(el);
  });

  scrollToBottom(container);
}

function buildMessageEl(msg, conv) {
  const wrap = document.createElement('div');

  if (msg.type === 'system') {
    wrap.className = `msg-wrap system`;
    wrap.innerHTML = `<div class="msg-system${msg.isHandoff ? ' handoff-event' : ''}" role="status">${escHtml(msg.text)}</div>`;
    return wrap;
  }

  if (msg.type === 'customer') {
    wrap.className = 'msg-wrap customer';
    wrap.innerHTML = `
      <div class="msg-avatar" aria-hidden="true">${escHtml(conv.customerAvatar)}</div>
      <div>
        <div class="msg-bubble">${escHtml(msg.text)}</div>
        <time class="msg-time" datetime="${msg.time.toISOString()}">${formatTime(msg.time)}</time>
      </div>`;
  } else if (msg.type === 'ai') {
    wrap.className = 'msg-wrap ai';
    wrap.innerHTML = `
      <div class="msg-avatar" aria-hidden="true">🤖</div>
      <div>
        <div class="msg-bubble">
          <div class="msg-ai-label" aria-hidden="true">🤖 AI</div>
          ${escHtml(msg.text)}
        </div>
        <time class="msg-time" datetime="${msg.time.toISOString()}">${formatTime(msg.time)}</time>
      </div>`;
  } else if (msg.type === 'seller') {
    wrap.className = 'msg-wrap seller';
    const failureHtml = msg.failed ? `
      <div class="msg-failed" role="alert">
        <span aria-hidden="true">❌</span> Gửi thất bại
        <button class="btn-retry" data-msg-id="${msg.id}" aria-label="Thử gửi lại tin nhắn">Thử lại</button>
      </div>` : '';
    wrap.innerHTML = `
      <div>
        <div class="msg-bubble">${escHtml(msg.text)}</div>
        <time class="msg-time" datetime="${msg.time.toISOString()}">${formatTime(msg.time)}</time>
        ${failureHtml}
      </div>`;

    // Bind retry
    wrap.querySelector('.btn-retry')?.addEventListener('click', () => retryMessage(msg, conv));
  }

  return wrap;
}

/* ================================================================
   CHAT AREA EVENTS
   ================================================================ */
function bindChatAreaEvents(conv) {
  // AI toggle
  document.getElementById('btn-toggle-ai')?.addEventListener('click', () => toggleAI(conv));
  document.getElementById('btn-take-over')?.addEventListener('click', () => sellerTakeOver(conv));
  document.getElementById('btn-retry-ai')?.addEventListener('click', () => retryAI(conv));
  document.getElementById('btn-create-order')?.addEventListener('click', () => openOrderModal(conv));
  document.getElementById('btn-back')?.addEventListener('click', mobileBack);

  bindChatInput();
}

function bindChatInput() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send');
  if (!input || !sendBtn) return;

  // Existing listeners are removed when DOM is rebuilt, no need to unbind
  input.addEventListener('input', () => {
    sendBtn.disabled = input.value.trim().length === 0;
    // Auto-grow textarea
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input?.value.trim();
  if (!text || !state.activeConvId) return;

  const conv = state.conversations.find(c => c.id === state.activeConvId);
  if (!conv) return;

  input.value = '';
  input.style.height = 'auto';
  document.getElementById('btn-send').disabled = true;

  // Simulate 10% failure
  const willFail = Math.random() < 0.1;

  const msg = {
    id: `msg-${Date.now()}`,
    type: 'seller',
    text,
    time: new Date(),
    failed: willFail
  };

  conv.messages.push(msg);
  conv.lastMessage = text;
  conv.lastMessageIsAI = false;
  conv.timestamp = new Date();

  // Switch to seller-handling if not already
  if (conv.aiStatus === 'need-seller') {
    conv.aiStatus = 'seller-handling';
    conv.processingStatus = 'Đang xử lý';
  }

  renderMessages(conv);
  renderConversationList();

  if (willFail) {
    showToast('❌ Gửi tin nhắn thất bại. Nhấn "Thử lại" để gửi lại.', 'error');
  }

  // If AI is active, simulate AI typing + response
  if (conv.aiStatus === 'ai-active') {
    await simulateAIResponse(conv);
  }
}

async function simulateAIResponse(conv) {
  await delay(800);
  showTypingIndicator(true);

  const thinkTime = 1500 + Math.random() * 1000;
  await delay(thinkTime);

  // 15% chance AI fails
  const aiFails = Math.random() < 0.15;
  showTypingIndicator(false);

  if (aiFails) {
    triggerAIFailure(conv);
    return;
  }

  const responses = [
    'Dạ bạn ơi, cảm ơn bạn đã nhắn! Mình sẽ kiểm tra và phản hồi bạn ngay nhé 😊',
    'Thông tin bạn cung cấp đã được ghi nhận. Bạn có cần thêm thông tin gì không ạ?',
    'Dạ mình hiểu rồi ạ. Để mình xử lý và phản hồi bạn trong vài phút nhé!',
    'Cảm ơn bạn đã liên hệ Shop Thời Trang Lan! Mình sẽ hỗ trợ bạn ngay ạ 🌸'
  ];

  const aiMsg = {
    id: `msg-ai-${Date.now()}`,
    type: 'ai',
    text: responses[Math.floor(Math.random() * responses.length)],
    time: new Date()
  };

  conv.messages.push(aiMsg);
  conv.lastMessage = aiMsg.text;
  conv.lastMessageIsAI = true;
  conv.timestamp = new Date();

  renderMessages(conv);
  renderConversationList();
}

function showTypingIndicator(visible) {
  const el = document.getElementById('typing-indicator');
  if (!el) return;
  el.classList.toggle('visible', visible);
  if (visible) {
    const container = document.getElementById('chat-messages');
    scrollToBottom(container);
  }
}

/* ================================================================
   AI STATE TRANSITIONS
   ================================================================ */
function toggleAI(conv) {
  const btn = document.getElementById('btn-toggle-ai');
  if (!btn) return;

  if (btn.dataset.action === 'disable') {
    // AI active → Seller handling
    conv.aiStatus = 'seller-handling';
    updateAIStatusUI(conv);
    addSystemMessage(conv, '👤 Người bán đã tắt AI và tiếp nhận hội thoại');
    showToast('✅ Đã tắt AI. Bạn đang xử lý hội thoại này.', 'info');
  } else {
    // Seller handling → AI active
    retryAIConnect(conv);
  }

  renderConversationList();
}

function sellerTakeOver(conv) {
  conv.aiStatus = 'seller-handling';
  conv.processingStatus = 'Đang xử lý';
  document.getElementById('handoff-banner')?.classList.remove('visible');
  document.getElementById('chat-ai-alert')?.classList.remove('visible');
  updateAIStatusUI(conv);
  addSystemMessage(conv, '👤 Bạn đã nhận xử lý hội thoại này');
  renderConversationList();
  showToast('✅ Đã nhận xử lý. AI đã được tắt.', 'info');
}

async function retryAI(conv) {
  const btn = document.getElementById('btn-retry-ai');
  if (btn) { btn.disabled = true; btn.textContent = 'Đang kết nối lại…'; }

  await delay(1200);

  // 60% success
  const success = Math.random() > 0.4;

  if (success) {
    conv.aiStatus = 'ai-active';
    document.getElementById('chat-ai-alert')?.classList.remove('visible');
    updateAIStatusUI(conv);
    addSystemMessage(conv, '🤖 AI đã kết nối lại và tiếp tục xử lý hội thoại');
    showToast('✅ AI đã kết nối lại thành công!', 'info');
  } else {
    // Still failing
    if (btn) { btn.disabled = false; btn.textContent = 'Thử kết nối lại AI'; }
    showToast('❌ Không thể kết nối AI. Vui lòng thử lại sau.', 'error');
    triggerAIFailure(conv);
  }

  renderConversationList();
}

async function retryAIConnect(conv) {
  const btn = document.getElementById('btn-toggle-ai');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Đang bật…'; }

  await delay(1000);

  const success = Math.random() > 0.3;

  if (success) {
    conv.aiStatus = 'ai-active';
    updateAIStatusUI(conv);
    addSystemMessage(conv, '🤖 AI đã được bật lại và tiếp tục xử lý hội thoại');
    showToast('✅ AI đã được bật lại!', 'info');
  } else {
    triggerAIFailure(conv);
    showToast('❌ Không thể kết nối AI. Hội thoại vẫn do bạn xử lý.', 'error');
  }

  renderConversationList();
}

function triggerAIFailure(conv) {
  conv.aiStatus = 'need-seller';
  conv.processingStatus = 'Đang xử lý';
  updateAIStatusUI(conv);

  const failMsg = {
    id: `fail-${Date.now()}`,
    type: 'system',
    text: '⚠️ AI gặp lỗi. Hội thoại cần bạn xử lý.',
    time: new Date(),
    isHandoff: true
  };
  conv.messages.push(failMsg);

  document.getElementById('handoff-banner')?.classList.add('visible');
  document.getElementById('chat-ai-alert')?.classList.add('visible');
  renderMessages(conv);
  renderConversationList();

  // Announce to screen readers
  const alert = document.getElementById('chat-ai-alert');
  if (alert) alert.setAttribute('aria-live', 'assertive');
}

function updateAIStatusUI(conv) {
  const statusWrap = document.getElementById('header-ai-status-wrap');
  const toggleWrap = document.getElementById('ai-toggle-wrap');

  if (statusWrap) statusWrap.innerHTML = buildHeaderAiStatus(conv.aiStatus);
  if (toggleWrap) toggleWrap.innerHTML = buildAiToggleBtn(conv.aiStatus);

  // Re-bind toggle
  document.getElementById('btn-toggle-ai')?.addEventListener('click', () => toggleAI(conv));

  // Handoff banner
  const banner = document.getElementById('handoff-banner');
  if (banner) {
    banner.classList.toggle('visible', conv.aiStatus === 'need-seller');
  }

  renderConversationList();
}

function addSystemMessage(conv, text) {
  const msg = { id: `sys-${Date.now()}`, type: 'system', text, time: new Date() };
  conv.messages.push(msg);
  renderMessages(conv);
}

async function retryMessage(msg, conv) {
  msg.failed = false;
  renderMessages(conv);

  await delay(600);

  // 70% success on retry
  const success = Math.random() > 0.3;
  if (!success) {
    msg.failed = true;
    renderMessages(conv);
    showToast('❌ Vẫn không gửi được. Vui lòng kiểm tra kết nối mạng.', 'error');
  } else {
    showToast('✅ Đã gửi tin nhắn thành công!', 'info');
  }
}

/* ================================================================
   INFO PANEL
   ================================================================ */
function renderInfoPanel(conv) {
  const panel = document.getElementById('info-panel');
  if (!panel) return;

  const c = conv.customer;
  const ordersHtml = c.orders.length > 0
    ? c.orders.map(o => `
      <div class="order-card">
        <div class="order-card-id">${escHtml(o.id)}</div>
        <div class="order-card-product">${escHtml(o.product)}</div>
        <div class="order-card-meta">
          <span>${escHtml(o.amount)}</span>
          <span class="order-status-badge ${o.status === 'Chờ xác nhận' ? 'pending' : 'shipping'}">${escHtml(o.status)}</span>
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:3px">${escHtml(o.date)}</div>
      </div>`).join('')
    : '<p class="info-field-value empty">Chưa có đơn hàng.</p>';

  panel.innerHTML = `
    <div class="info-panel-header">
      <span class="info-panel-title">Thông tin khách</span>
    </div>
    <div class="info-avatar-section">
      <div class="info-avatar" aria-hidden="true">${escHtml(conv.customerAvatar)}</div>
      <div class="info-name">${escHtml(c.name)}</div>
      <span class="info-platform ${conv.platform}" aria-label="${conv.platform === 'facebook' ? 'Facebook' : 'Zalo'}">
        <span aria-hidden="true">${conv.platform === 'facebook' ? 'f' : 'Z'}</span>
        ${conv.platform === 'facebook' ? 'Facebook' : 'Zalo'} · ${escHtml(c.platformUsername)}
      </span>
    </div>
    <div class="info-section">
      <div class="info-section-title">Liên hệ</div>
      <div class="info-field">
        <div class="info-field-label">Số điện thoại</div>
        <div class="info-field-value${!c.phone ? ' empty' : ''}">${c.phone || 'Chưa có'}</div>
      </div>
    </div>
    <div class="info-section">
      <div class="info-section-title">Đơn hàng (${c.orders.length})</div>
      ${ordersHtml}
      <button class="btn btn-primary" style="width:100%;margin-top:10px" onclick="openOrderModal(window._activeConv)">
        <span aria-hidden="true">📋</span> Tạo đơn mới
      </button>
    </div>
    <div class="info-section">
      <div class="info-section-title">Ghi chú</div>
      <textarea class="info-notes" id="info-notes" aria-label="Ghi chú về khách hàng" placeholder="Nhập ghi chú…">${escHtml(c.notes)}</textarea>
    </div>`;

  // Store ref for info panel button
  window._activeConv = conv;

  // Save notes on blur
  panel.querySelector('#info-notes')?.addEventListener('blur', (e) => {
    conv.customer.notes = e.target.value;
  });
}

/* ================================================================
   ORDER MODAL
   ================================================================ */
function bindModalTriggers() {
  // Close on overlay click or Escape
  const overlay = document.getElementById('order-modal-overlay');
  if (!overlay) return;

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeOrderModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeOrderModal();
  });

  document.getElementById('btn-close-order-modal')?.addEventListener('click', closeOrderModal);
  document.getElementById('btn-cancel-order')?.addEventListener('click', closeOrderModal);
  document.getElementById('btn-add-product')?.addEventListener('click', addProductRow);
  document.getElementById('btn-submit-order')?.addEventListener('click', submitOrder);
}

function openOrderModal(conv) {
  if (!conv) return;
  window._orderConv = conv;

  // Pre-fill customer name
  const nameInput = document.getElementById('order-customer-name');
  if (nameInput) nameInput.value = conv.customer.name;

  const phoneInput = document.getElementById('order-phone');
  if (phoneInput) phoneInput.value = conv.customer.phone || '';

  // Reset product rows
  state.orderProducts = [];
  const productRows = document.getElementById('order-product-rows');
  if (productRows) productRows.innerHTML = '';
  addProductRow();
  updateOrderTotal();

  // Show form, hide success
  document.getElementById('order-form-section').style.display = '';
  document.getElementById('order-success-section').classList.remove('visible');
  document.getElementById('btn-submit-order').style.display = '';
  document.getElementById('btn-cancel-order').style.display = '';

  // Clear errors
  clearOrderErrors();

  const overlay = document.getElementById('order-modal-overlay');
  overlay.classList.add('open');
  overlay.setAttribute('aria-hidden', 'false');

  // Focus first field
  setTimeout(() => document.getElementById('order-customer-name')?.focus(), 50);
  trapFocus(overlay);
}

function closeOrderModal() {
  const overlay = document.getElementById('order-modal-overlay');
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden', 'true');

  // Return focus to trigger
  document.getElementById('btn-create-order')?.focus();
}

function addProductRow() {
  const container = document.getElementById('order-product-rows');
  if (!container) return;

  const rowIndex = container.children.length;
  const rowId = `prod-row-${Date.now()}`;

  const row = document.createElement('div');
  row.className = 'product-row';
  row.id = rowId;

  const productOptions = MOCK_DATA.products
    .map(p => `<option value="${p.id}">${escHtml(p.name)}</option>`)
    .join('');

  row.innerHTML = `
    <div class="product-row-header">
      <span class="product-row-label">Sản phẩm ${rowIndex + 1}</span>
      ${rowIndex > 0 ? `<button class="btn-remove-product" type="button" onclick="removeProductRow('${rowId}')" aria-label="Xóa sản phẩm ${rowIndex + 1}">Xóa</button>` : ''}
    </div>
    <div class="product-row-grid">
      <div>
        <label for="prod-select-${rowId}" class="sr-only">Sản phẩm</label>
        <select id="prod-select-${rowId}" aria-label="Chọn sản phẩm" onchange="updateVariants('${rowId}')">
          <option value="">-- Chọn sản phẩm --</option>
          ${productOptions}
        </select>
      </div>
      <div>
        <label for="variant-select-${rowId}" class="sr-only">Phân loại</label>
        <select id="variant-select-${rowId}" aria-label="Chọn phân loại" disabled onchange="updateOrderTotal()">
          <option value="">-- Chọn phân loại --</option>
        </select>
      </div>
      <div>
        <label for="qty-${rowId}" class="sr-only">Số lượng</label>
        <input type="number" id="qty-${rowId}" class="qty-input" min="1" value="1" aria-label="Số lượng" onchange="updateOrderTotal()">
      </div>
    </div>
    <div id="stock-warning-${rowId}"></div>`;

  container.appendChild(row);
  document.getElementById(`prod-select-${rowId}`)?.focus();
}

function removeProductRow(rowId) {
  document.getElementById(rowId)?.remove();
  updateOrderTotal();
}

function updateVariants(rowId) {
  const productId = document.getElementById(`prod-select-${rowId}`)?.value;
  const variantSelect = document.getElementById(`variant-select-${rowId}`);
  const stockWarning = document.getElementById(`stock-warning-${rowId}`);
  if (!variantSelect) return;

  if (!productId) {
    variantSelect.innerHTML = '<option value="">-- Chọn phân loại --</option>';
    variantSelect.disabled = true;
    if (stockWarning) stockWarning.innerHTML = '';
    return;
  }

  const product = MOCK_DATA.products.find(p => p.id === productId);
  if (!product) return;

  variantSelect.disabled = false;
  variantSelect.innerHTML = '<option value="">-- Chọn phân loại --</option>' +
    product.variants.map(v => {
      const outOfStock = v.stock === 0;
      return `<option value="${v.id}" ${outOfStock ? 'disabled' : ''} data-price="${v.price}" data-stock="${v.stock}">
        ${escHtml(v.name)} — ${formatPrice(v.price)}${outOfStock ? ' (Hết hàng)' : ''}
      </option>`;
    }).join('');

  updateOrderTotal();
}

function updateOrderTotal() {
  const rows = document.querySelectorAll('.product-row');
  let total = 0;

  rows.forEach(row => {
    const rowId = row.id;
    const variantSelect = document.getElementById(`variant-select-${rowId}`);
    const qtyInput = document.getElementById(`qty-${rowId}`);
    const stockWarn = document.getElementById(`stock-warning-${rowId}`);

    if (!variantSelect || !qtyInput) return;

    const selectedOption = variantSelect.options[variantSelect.selectedIndex];
    if (!selectedOption || !selectedOption.value) return;

    const price = parseInt(selectedOption.dataset.price) || 0;
    const stock = parseInt(selectedOption.dataset.stock) || 0;
    const qty = parseInt(qtyInput.value) || 1;

    total += price * qty;

    if (stockWarn) {
      if (stock > 0 && qty > stock) {
        stockWarn.innerHTML = `<span class="out-of-stock-badge">⚠️ Chỉ còn ${stock} cái</span>`;
      } else {
        stockWarn.innerHTML = '';
      }
    }
  });

  const totalEl = document.getElementById('order-total-value');
  if (totalEl) totalEl.textContent = formatPrice(total) || '—';
}

async function submitOrder() {
  clearOrderErrors();

  let valid = true;

  const name = document.getElementById('order-customer-name')?.value.trim();
  const phone = document.getElementById('order-phone')?.value.trim();
  const address = document.getElementById('order-address')?.value.trim();

  if (!name) {
    showOrderFieldError('err-name', 'Vui lòng nhập tên khách hàng');
    document.getElementById('order-customer-name')?.classList.add('error');
    valid = false;
  }

  if (!phone || !/^\d{10,11}$/.test(phone)) {
    showOrderFieldError('err-phone', 'Số điện thoại không hợp lệ (10–11 chữ số)');
    document.getElementById('order-phone')?.classList.add('error');
    valid = false;
  }

  if (!address) {
    showOrderFieldError('err-address', 'Vui lòng nhập địa chỉ giao hàng');
    document.getElementById('order-address')?.classList.add('error');
    valid = false;
  }

  // Check at least 1 product
  const rows = document.querySelectorAll('.product-row');
  let hasProduct = false;
  rows.forEach(row => {
    const rowId = row.id;
    const variantSelect = document.getElementById(`variant-select-${rowId}`);
    if (variantSelect?.value) hasProduct = true;
  });

  if (!hasProduct) {
    showOrderFieldError('err-products', 'Vui lòng chọn ít nhất 1 sản phẩm và phân loại');
    valid = false;
  }

  if (!valid) return;

  // Submit
  const submitBtn = document.getElementById('btn-submit-order');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Đang tạo đơn…';

  await delay(1000);

  // Create order in conv customer
  const conv = window._orderConv;
  const orderId = '#' + Math.floor(Math.random() * 90000 + 10000);
  const newOrder = {
    id: orderId,
    status: 'Chờ xác nhận',
    product: name,
    amount: document.getElementById('order-total-value')?.textContent || '',
    date: new Date().toLocaleDateString('vi-VN')
  };
  if (conv) conv.customer.orders.unshift(newOrder);

  // Add message to chat
  if (conv) {
    addSystemMessage(conv, `📋 Đơn hàng ${orderId} đã được tạo — Chờ xác nhận`);
    renderInfoPanel(conv);
  }

  // Show success
  document.getElementById('order-form-section').style.display = 'none';
  submitBtn.style.display = 'none';
  document.getElementById('btn-cancel-order').style.display = 'none';
  document.getElementById('order-success-section').classList.add('visible');
  document.getElementById('order-success-id').textContent = orderId;
}

function clearOrderErrors() {
  ['err-name', 'err-phone', 'err-address', 'err-products'].forEach(id => {
    document.getElementById(id)?.classList.remove('visible');
  });
  ['order-customer-name', 'order-phone', 'order-address'].forEach(id => {
    document.getElementById(id)?.classList.remove('error');
  });
}

function showOrderFieldError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.add('visible'); }
}

/* ================================================================
   MOBILE BACK
   ================================================================ */
function bindMobileBack() {
  // Delegated — button is added dynamically
}

function mobileBack() {
  document.querySelector('.sidebar')?.classList.remove('hidden');
  document.querySelector('.chat-area')?.classList.remove('visible');
  state.activeConvId = null;
  renderConversationList();
}

/* ================================================================
   FOCUS TRAP
   ================================================================ */
function trapFocus(container) {
  const focusable = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  container.addEventListener('keydown', function handler(e) {
    if (e.key !== 'Tab') return;
    if (!container.classList.contains('open')) {
      container.removeEventListener('keydown', handler);
      return;
    }
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
}

/* ================================================================
   TOAST
   ================================================================ */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/* ================================================================
   UTILITY
   ================================================================ */
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function scrollToBottom(el) {
  if (el) el.scrollTop = el.scrollHeight;
}

function relativeTime(date) {
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60) return 'Vừa xong';
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
  if (diff < 172800) return 'Hôm qua';
  return date.toLocaleDateString('vi-VN');
}

function formatTime(date) {
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

function formatPrice(n) {
  if (!n) return '';
  return n.toLocaleString('vi-VN') + 'đ';
}

/* ================================================================
   BIND ORDER FORM (called once on boot)
   ================================================================ */
function bindOrderForm() {
  bindModalTriggers();
}
