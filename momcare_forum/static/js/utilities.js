/**
 * Shared utility functions used across all templates
 * Reduces code duplication by centralizing common functionality
 */

/**
 * Get CSRF token from cookie (for AJAX requests)
 * @param {string} name - Cookie name
 * @returns {string} Cookie value or empty string
 */
function getCookie(name) {
  const cookieArr = document.cookie.split(';');
  for (let i = 0; i < cookieArr.length; i += 1) {
    const cookie = cookieArr[i].trim();
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

/**
 * Open a modal by adding 'show' class
 * @param {HTMLElement} modal - Modal element to open
 */
function openSimpleModal(modal) {
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

/**
 * Close a modal by removing 'show' class
 * @param {HTMLElement} modal - Modal element to close
 */
function closeSimpleModal(modal) {
  modal.classList.remove('show');
  const anyModalOpen = document.querySelector('.modal-overlay.active, .post-modal-overlay.show, .report-modal-overlay.show');
  if (!anyModalOpen) {
    document.body.style.overflow = '';
  }
}

/**
 * Close all modals with specified selector
 * @param {string} selector - CSS selector for modals
 */
function closeAllModals(selector = '.modal') {
  document.querySelectorAll(selector).forEach(modal => {
    modal.classList.remove('show');
  });
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString('vi-VN', options);
}

/**
 * Show notification toast message or alert in container
 * @param {string|HTMLElement} target - Message string or element to display in
 * @param {string} messageOrType - Message (if target is element) or type (if target is string)
 * @param {string} type - Alert type ('success', 'error', 'info')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showAlert(target, messageOrType = 'success', type = 'success', duration = 3000) {
  // Handle different function signatures
  let message, containerElement, alertType, timeout;
  
  if (typeof target === 'string') {
    // showAlert("message text") or showAlert("message text", "success", 3000)
    message = target;
    alertType = typeof messageOrType === 'string' ? messageOrType : 'success';
    timeout = typeof messageOrType === 'number' ? messageOrType : duration;
    containerElement = document.getElementById('alertContainer');
  } else if (target instanceof HTMLElement) {
    // showAlert(element, "message text", "success")
    containerElement = target;
    message = messageOrType;
    alertType = type;
    timeout = duration;
  } else {
    return;
  }
  
  if (containerElement) {
    // Display in container (for modals/pages with alertContainer)
    containerElement.innerHTML = `<div class="alert alert-${alertType}">${message}</div>`;
    if (timeout > 0) {
      setTimeout(() => {
        containerElement.innerHTML = '';
      }, timeout);
    }
  } else {
    // Display as toast notification
    const toast = document.createElement('div');
    toast.className = `notification notification-${alertType}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 16px 20px;
      background: ${alertType === 'success' ? '#4caf50' : alertType === 'error' ? '#f44336' : '#2196f3'};
      color: white;
      border-radius: 4px;
      z-index: 10000;
      font-size: 14px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(toast);
    
    if (timeout > 0) {
      setTimeout(() => toast.remove(), timeout);
    }
  }
}

/**
 * Show notification toast message (alias for showAlert with different parameters)
 * @param {string} message - Message to display
 * @param {string} type - 'success', 'error', 'info' (default: 'info')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showNotification(message, type = 'info', duration = 3000) {
  showAlert(message, type, 'info', duration);
}

let confirmModalReady = false;

function ensureConfirmModal() {
  if (confirmModalReady) return;

  const style = document.createElement('style');
  style.id = 'global-confirm-style';
  style.textContent = `
    .global-confirm-overlay {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(18, 20, 27, 0.45);
      z-index: 2500;
      padding: 16px;
    }

    .global-confirm-overlay.show {
      display: flex;
    }

    .global-confirm-card {
      width: min(420px, calc(100vw - 24px));
      border-radius: 14px;
      background: #fff;
      border: 1px solid #ead9e2;
      box-shadow: 0 18px 40px rgba(21, 20, 28, 0.24);
      padding: 16px;
    }

    .global-confirm-title {
      margin: 0 0 8px;
      font-size: 18px;
      color: #1f2430;
      font-weight: 700;
    }

    .global-confirm-message {
      margin: 0;
      color: #4b5565;
      line-height: 1.5;
      font-size: 14px;
      white-space: pre-wrap;
    }

    .global-confirm-actions {
      margin-top: 14px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }

    .global-confirm-btn {
      min-width: 100px;
      height: 38px;
      border-radius: 10px;
      border: 1px solid #d8dde8;
      background: #fff;
      color: #2f3645;
      font-weight: 700;
      cursor: pointer;
    }

    .global-confirm-btn.primary {
      border-color: #c9507f;
      background: #c9507f;
      color: #fff;
    }
  `;

  const modal = document.createElement('div');
  modal.id = 'global-confirm-overlay';
  modal.className = 'global-confirm-overlay';
  modal.innerHTML = `
    <div class="global-confirm-card" role="dialog" aria-modal="true" aria-labelledby="global-confirm-title" onclick="event.stopPropagation()">
      <h3 class="global-confirm-title" id="global-confirm-title">Xác nhận thao tác</h3>
      <p class="global-confirm-message" id="global-confirm-message"></p>
      <div class="global-confirm-actions">
        <button type="button" class="global-confirm-btn" id="global-confirm-cancel">Hủy</button>
        <button type="button" class="global-confirm-btn primary" id="global-confirm-ok">Xác nhận</button>
      </div>
    </div>
  `;

  document.head.appendChild(style);
  document.body.appendChild(modal);
  confirmModalReady = true;
}

function showConfirm(message, options = {}) {
  ensureConfirmModal();

  const overlay = document.getElementById('global-confirm-overlay');
  const messageEl = document.getElementById('global-confirm-message');
  const titleEl = document.getElementById('global-confirm-title');
  const okBtn = document.getElementById('global-confirm-ok');
  const cancelBtn = document.getElementById('global-confirm-cancel');

  if (!overlay || !messageEl || !titleEl || !okBtn || !cancelBtn) {
    return Promise.resolve(false);
  }

  messageEl.textContent = message || 'Bạn có chắc chắn muốn tiếp tục?';
  titleEl.textContent = options.title || 'Xác nhận thao tác';
  okBtn.textContent = options.confirmText || 'Xác nhận';
  cancelBtn.textContent = options.cancelText || 'Hủy';
  overlay.classList.add('show');
  document.body.style.overflow = 'hidden';

  return new Promise((resolve) => {
    const cleanup = () => {
      overlay.classList.remove('show');
      const anyModalOpen = document.querySelector('.modal-overlay.active, .post-modal-overlay.show, .report-modal-overlay.show');
      if (!anyModalOpen) {
        document.body.style.overflow = '';
      }
      okBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      overlay.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKeydown);
    };

    const onConfirm = () => {
      cleanup();
      resolve(true);
    };

    const onCancel = () => {
      cleanup();
      resolve(false);
    };

    const onKeydown = (event) => {
      if (event.key === 'Escape') {
        onCancel();
      }
    };

    okBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
    overlay.addEventListener('click', onCancel);
    document.addEventListener('keydown', onKeydown);
  });
}

window.showConfirm = showConfirm;

// Intercept forms that declare data-confirm-message to use the custom confirm modal.
document.addEventListener('submit', async (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;

  const message = form.dataset.confirmMessage;
  if (!message) return;

  if (form.dataset.confirmBypassed === '1') {
    form.dataset.confirmBypassed = '0';
    return;
  }

  event.preventDefault();
  const confirmed = await showConfirm(message);
  if (!confirmed) return;

  form.dataset.confirmBypassed = '1';
  if (typeof form.requestSubmit === 'function') {
    form.requestSubmit();
  } else {
    form.submit();
  }
}, true);

function isUserAuthenticated() {
  const flag = document.body?.dataset?.userAuthenticated;
  return flag === '1';
}

// Capture phase: block comment actions for guests before per-page handlers execute.
document.addEventListener('click', (event) => {
  const commentTrigger = event.target.closest('.open-comment-modal-btn');
  if (!commentTrigger) return;
  if (isUserAuthenticated()) return;

  event.preventDefault();
  event.stopPropagation();
  if (typeof event.stopImmediatePropagation === 'function') {
    event.stopImmediatePropagation();
  }

  showAlert('Vui lòng đăng nhập để bình luận.', 'error');
  if (typeof openModal === 'function') {
    openModal('auth-modal');
  }
}, true);

/**
 * Debounce function to limit function calls
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} True if element is visible in viewport
 */
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Open post detail modal - Unified function for both forum and profile pages
 * @param {number} postId - Post ID to display
 */
function openPostDetailModal(postId) {
  try {
    const postCard = document.querySelector(`[data-post-id="${postId}"]`);
    if (!postCard) {
      console.error(`Post card not found for ID: ${postId}`);
      return;
    }

    // Get modal elements safely
    const modal = document.getElementById('post-detail-modal');
    if (!modal) {
      console.error('Modal not found in DOM');
      return;
    }

    // Extract title
    const title = postCard.dataset.postTitle || postCard.querySelector('.post-title')?.textContent || '';
    const titleEl = document.getElementById('modal-post-title');
    const titleMainEl = document.getElementById('modal-post-title-main');
    if (titleEl) titleEl.textContent = title;
    if (titleMainEl) titleMainEl.textContent = title;
    
    // Extract author
    const author = postCard.querySelector('.post-username')?.textContent?.trim() || 'Người dùng ẩn danh';
    const authorEl = document.getElementById('modal-post-author');
    if (authorEl) authorEl.textContent = author;
    
    // Extract time
    const time = postCard.querySelector('.post-time')?.textContent || 'Vừa xong';
    const timeEl = document.getElementById('modal-post-time');
    if (timeEl) timeEl.textContent = time;

    // Extract content - get full content, not truncated
    const contentEl = postCard.querySelector('.post-content');
    const content = contentEl?.textContent?.trim() || '';
    const contentDisplay = document.getElementById('modal-post-content-text');
    if (contentDisplay) contentDisplay.textContent = content;

    // Extract images (supports multiple images with backward-compatible fallback)
    const imageElements = postCard.querySelectorAll('.post-images-grid .post-image, .post-image');
    const imageList = Array.from(imageElements)
      .map((img) => img?.src)
      .filter((src, idx, arr) => src && arr.indexOf(src) === idx);

    const imagesContainer = document.getElementById('modal-post-images');
    if (imagesContainer) {
      if (imageList.length > 0) {
        imagesContainer.innerHTML = imageList
          .map((src) => `<img src="${src}" alt="Bài viết" class="modal-post-image-item">`)
          .join('');

        imagesContainer.querySelectorAll('.modal-post-image-item').forEach((imgEl) => {
          imgEl.addEventListener('click', (event) => {
            event.stopPropagation();
            openImageZoom(imgEl.src, imgEl.alt || 'Ảnh bài viết');
          });
        });

        imagesContainer.classList.toggle('single', imageList.length === 1);
        imagesContainer.style.display = 'grid';
      } else {
        imagesContainer.innerHTML = '';
        imagesContainer.classList.remove('single');
        imagesContainer.style.display = 'none';
      }
    }

    // Extract likes and comments count
    const likesCount = postCard.querySelector('.post-likes-count')?.textContent || '0 lượt thích';
    const commentsCount = postCard.querySelector('.post-comments-count')?.textContent || '0 bình luận';
    const likesEl = document.getElementById('modal-post-likes');
    const commentsCountEl = document.getElementById('modal-post-comments-count');
    if (likesEl) likesEl.textContent = likesCount;
    if (commentsCountEl) commentsCountEl.textContent = commentsCount;

    // Set avatar - handle both forum and profile styles
    const modalAvatar = document.getElementById('modal-post-avatar');
    const feedAvatar = postCard.querySelector('.post-avatar') || postCard.querySelector('.avatar-mini');
    
    if (modalAvatar && feedAvatar) {
      // Copy avatar styling
      try {
        modalAvatar.style.background = window.getComputedStyle(feedAvatar).background;
      } catch (e) {}
      
      // Check if avatar contains SVG (anonymous) or text (regular)
      const avatarContent = feedAvatar?.innerHTML?.trim();
      if (avatarContent?.includes('svg')) {
        // Anonymous avatar - clone SVG
        modalAvatar.innerHTML = avatarContent;
      } else {
        // Regular avatar - use text initial
        const avatarText = feedAvatar?.textContent?.trim() || 'U';
        modalAvatar.textContent = avatarText;
      }
    }

    // Set verification badge if exists
    const verificationEl = postCard.querySelector('.review-approved.show');
    const modalVerification = document.getElementById('modal-post-verification');
    if (modalVerification) {
      if (verificationEl) {
        modalVerification.innerHTML = verificationEl.innerHTML;
      } else {
        modalVerification.innerHTML = '';
      }
    }

    // Check if current user is post owner and show edit/delete buttons
    const isPostOwner = postCard.dataset.postOwner === 'true';
    const editBtn = document.getElementById('modal-edit-post-btn');
    const deleteBtn = document.getElementById('modal-delete-post-btn');
    if (editBtn) {
      if (isPostOwner) {
        editBtn.style.display = 'block';
        editBtn.dataset.postId = postId;
      } else {
        editBtn.style.display = 'none';
      }
    }
    if (deleteBtn) {
      if (isPostOwner) {
        deleteBtn.style.display = 'block';
        deleteBtn.dataset.postId = postId;
      } else {
        deleteBtn.style.display = 'none';
      }
    }

    // Update like and comment buttons
    const isLiked = postCard.querySelector('.like-post-btn.liked') !== null;
    
    // Set form post ID
    const commentForm = document.getElementById('modal-comment-form');
    if (commentForm) {
      commentForm.dataset.postId = postId;
    }
    if (typeof resetModalCommentMode === 'function') {
      resetModalCommentMode();
    }

    // Update like button
    const likeButtons = document.querySelectorAll('.modal-card-post-detail .like-post-btn');
    if (likeButtons.length > 0) {
      likeButtons.forEach(btn => {
        btn.dataset.postId = postId;
        if (isLiked) {
          btn.classList.add('liked');
        } else {
          btn.classList.remove('liked');
        }
      });
    }

    // Update comment and share buttons
    const commentBtns = document.querySelectorAll('.modal-card-post-detail .open-comment-modal-btn');
    if (commentBtns.length > 0) {
      commentBtns.forEach(btn => btn.dataset.postId = postId);
    }
    
    const shareBtns = document.querySelectorAll('.modal-card-post-detail .share-post-btn');
    if (shareBtns.length > 0) {
      shareBtns.forEach(btn => btn.dataset.shareUrl = `/post/${postId}/`);
    }

    // Fetch comments if function exists
    if (typeof fetchAndDisplayComments === 'function') {
      fetchAndDisplayComments(postId);
    }

    // Show modal
    modal.style.display = 'flex';
  } catch (error) {
    console.error('Error opening post detail modal:', error);
    showAlert('Không thể mở bài viết', 'error');
  }
}

/**
 * Close post detail modal
 */
function closePostDetailModal() {
  const modal = document.getElementById('post-detail-modal');
  if (modal) {
    modal.style.display = 'none';
  }
  if (typeof resetModalCommentMode === 'function') {
    resetModalCommentMode();
  }
  closeImageZoom();
}

function openImageZoom(src, altText) {
  const zoomOverlay = document.getElementById('image-zoom-overlay');
  const zoomTarget = document.getElementById('image-zoom-target');
  if (!zoomOverlay || !zoomTarget || !src) return;

  zoomTarget.src = src;
  zoomTarget.alt = altText || 'Ảnh phóng to';
  zoomOverlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeImageZoom() {
  const zoomOverlay = document.getElementById('image-zoom-overlay');
  const zoomTarget = document.getElementById('image-zoom-target');
  if (!zoomOverlay || !zoomTarget) return;

  zoomOverlay.style.display = 'none';
  zoomTarget.removeAttribute('src');
  document.body.style.overflow = '';
}

window.openImageZoom = openImageZoom;
window.closeImageZoom = closeImageZoom;

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeImageZoom();
  }
});

/**
 * Fetch and display comments for a post
 * @param {number} postId - Post ID
 */
function fetchAndDisplayComments(postId) {
  const commentsList = document.getElementById('modal-comments-list');
  if (!commentsList) return;

  fetch(`/api/post/${postId}/comments/`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.comments && data.comments.length > 0) {
        commentsList.innerHTML = renderModalComments(data.comments);
      } else {
        commentsList.innerHTML = '<div class="modal-comments-empty">Chưa có bình luận nào</div>';
      }

      const totalComments = typeof data.total_comments === 'number'
        ? data.total_comments
        : (Array.isArray(data.comments) ? data.comments.length : 0);

      const commentsCountEl = document.getElementById('modal-post-comments-count');
      if (commentsCountEl) {
        commentsCountEl.textContent = `${totalComments} bình luận`;
      }

      const postCard = document.querySelector(`.post-card-wrapper[data-post-id="${postId}"] .post-card`) || document.querySelector(`[data-post-id="${postId}"]`);
      const feedCommentsCountEl = postCard?.querySelector?.('.post-comments-count, .comments-count');
      if (feedCommentsCountEl) {
        feedCommentsCountEl.textContent = `${totalComments} bình luận`;
      }
    })
    .catch(err => {
      console.error('Error fetching comments:', err);
      commentsList.innerHTML = '<div class="modal-comments-empty">Không thể tải bình luận</div>';
    });
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function buildCommentTree(comments) {
  const byId = new Map();
  const roots = [];

  comments.forEach((comment) => {
    byId.set(comment.id, { ...comment, children: [] });
  });

  byId.forEach((comment) => {
    if (comment.parent_id && byId.has(comment.parent_id)) {
      byId.get(comment.parent_id).children.push(comment);
    } else {
      roots.push(comment);
    }
  });

  return roots;
}

function renderSingleModalComment(comment, depth) {
  const marginLeft = Math.min(depth * 18, 54);
  const isAnonymousComment = Boolean(comment.is_anonymous);
  const safeAuthorLabel = isAnonymousComment ? 'Nguoi dung an danh' : (comment.author || 'Nguoi dung');
  const avatarText = isAnonymousComment ? 'A' : (comment.author_username ? comment.author_username.charAt(0).toUpperCase() : 'U');
  const authorBadge = comment.is_anonymous ? '<span style="font-size:11px;color:#7c3aed;background:#f3e8ff;border-radius:999px;padding:2px 8px;">Ẩn danh</span>' : '';
  const editedBadge = comment.updated_at && comment.updated_at !== comment.created_at
    ? '<span style="font-size:11px;color:#94a3b8;">(đã sửa)</span>'
    : '';
  const actions = [];
  const canReply = typeof comment.can_reply === 'boolean' ? comment.can_reply : isUserAuthenticated();
  const canEdit = typeof comment.can_edit === 'boolean' ? comment.can_edit : false;
  const canDelete = typeof comment.can_delete === 'boolean' ? comment.can_delete : false;

  if (canReply) {
    actions.push(`<button type="button" onclick="startReplyComment(${comment.id}, '${escapeHtml(safeAuthorLabel)}')" style="border:none;background:transparent;color:#4f46e5;font-size:12px;cursor:pointer;padding:0;">Trả lời</button>`);
  }
  if (canEdit) {
    actions.push(`<button type="button" onclick="startEditComment(${comment.id})" style="border:none;background:transparent;color:#0f766e;font-size:12px;cursor:pointer;padding:0;">Sửa</button>`);
  }
  if (canDelete) {
    actions.push(`<button type="button" onclick="deleteCommentInModal(${comment.id})" style="border:none;background:transparent;color:#b91c1c;font-size:12px;cursor:pointer;padding:0;">Xóa</button>`);
  }

  const childrenHtml = (comment.children || []).map((child) => renderSingleModalComment(child, depth + 1)).join('');
  return `
    <div class="modal-comment-item" style="margin-left:${marginLeft}px" data-comment-id="${comment.id}" data-comment-content="${escapeHtml(comment.content)}" data-comment-anonymous="${comment.is_anonymous ? '1' : '0'}">
      <div class="modal-comment-avatar">${avatarText}</div>
      <div class="modal-comment-body">
        <div class="modal-comment-header">
          <span class="modal-comment-author">${escapeHtml(safeAuthorLabel)}</span>
          ${authorBadge}
          <span class="modal-comment-time">${escapeHtml(comment.created_at)}</span>
          ${editedBadge}
        </div>
        <div class="modal-comment-content">${escapeHtml(comment.content)}</div>
        ${actions.length ? `<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:4px;">${actions.join('')}</div>` : ''}
      </div>
    </div>
    ${childrenHtml}
  `;
}

function renderModalComments(comments) {
  const roots = buildCommentTree(comments);
  return roots.map((comment) => renderSingleModalComment(comment, 0)).join('');
}

function setModalCommentMode(mode, targetCommentId, options = {}) {
  const modeInput = document.getElementById('modal-comment-mode-type');
  const targetInput = document.getElementById('modal-comment-target-id');
  const modeBox = document.getElementById('modal-comment-mode');
  const cancelBtn = document.getElementById('modal-comment-cancel-btn');
  const textarea = document.getElementById('modal-comment-textarea');
  const submitBtn = document.getElementById('modal-comment-submit-btn');
  const anonymousCheckbox = document.getElementById('modal-comment-anonymous');

  if (!modeInput || !targetInput || !modeBox || !cancelBtn || !textarea || !submitBtn || !anonymousCheckbox) return;

  modeInput.value = mode;
  targetInput.value = targetCommentId ? String(targetCommentId) : '';

  if (mode === 'reply') {
    modeBox.style.display = 'block';
    modeBox.textContent = `Đang trả lời: ${options.author || 'bình luận này'}`;
    cancelBtn.style.display = 'inline-flex';
    submitBtn.textContent = '↩';
    textarea.focus();
  } else if (mode === 'edit') {
    modeBox.style.display = 'block';
    modeBox.textContent = 'Đang chỉnh sửa bình luận';
    cancelBtn.style.display = 'inline-flex';
    submitBtn.textContent = '✓';
    textarea.value = options.content || '';
    anonymousCheckbox.checked = Boolean(options.isAnonymous);
    textarea.focus();
  }
}

function resetModalCommentMode() {
  const modeInput = document.getElementById('modal-comment-mode-type');
  const targetInput = document.getElementById('modal-comment-target-id');
  const modeBox = document.getElementById('modal-comment-mode');
  const cancelBtn = document.getElementById('modal-comment-cancel-btn');
  const submitBtn = document.getElementById('modal-comment-submit-btn');
  const textarea = document.getElementById('modal-comment-textarea');
  const anonymousCheckbox = document.getElementById('modal-comment-anonymous');

  if (modeInput) modeInput.value = 'create';
  if (targetInput) targetInput.value = '';
  if (modeBox) {
    modeBox.style.display = 'none';
    modeBox.textContent = '';
  }
  if (cancelBtn) cancelBtn.style.display = 'none';
  if (submitBtn) submitBtn.textContent = '➤';
  if (textarea) textarea.value = '';
  if (anonymousCheckbox) anonymousCheckbox.checked = false;
}

function startReplyComment(commentId, authorName) {
  setModalCommentMode('reply', commentId, { author: authorName });
}

function startEditComment(commentId) {
  const row = document.querySelector(`.modal-comment-item[data-comment-id="${commentId}"]`);
  if (!row) return;
  const content = row.dataset.commentContent || '';
  const isAnonymous = row.dataset.commentAnonymous === '1';
  setModalCommentMode('edit', commentId, { content, isAnonymous });
}

async function deleteCommentInModal(commentId) {
  const confirmed = await showConfirm('Bạn có chắc muốn xóa bình luận này?');
  if (!confirmed) return;

  fetch(`/comment/${commentId}/delete/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
    .then((res) => res.json().then((data) => ({ status: res.status, ok: res.ok, data })))
    .then(({ ok, status, data }) => {
      if (status === 401) {
        closeSimpleModal(document.getElementById('post-detail-modal'));
        openModal('auth-modal');
        return;
      }
      if (!ok || !data.success) {
        showAlert(data.error || 'Không thể xóa bình luận', 'error');
        return;
      }

      const postId = document.getElementById('modal-comment-form')?.dataset?.postId;
      if (postId) {
        fetchAndDisplayComments(postId);
      }
      resetModalCommentMode();
      showAlert('Đã xóa bình luận', 'success');
    })
    .catch((err) => {
      console.error('Error deleting comment:', err);
      showAlert('Không thể xóa bình luận', 'error');
    });
}

window.resetModalCommentMode = resetModalCommentMode;
window.startReplyComment = startReplyComment;
window.startEditComment = startEditComment;
window.deleteCommentInModal = deleteCommentInModal;

/**
 * Submit a comment on a post from the modal
 * @param {Event} event - Form submit event
 */
function submitModalComment(event) {
  try {
    event.preventDefault();
    
    const form = event.target;
    const postId = form?.dataset?.postId;
    
    if (!postId) {
      showAlert('Không thể xác định bài viết', 'error');
      return;
    }
    
    const textarea = form.querySelector('#modal-comment-textarea');
    if (!textarea) {
      showAlert('Form bình luận không hợp lệ', 'error');
      return;
    }

    // Remove accidental leading spaces/newlines inserted by paste or template formatting.
    textarea.value = textarea.value.replace(/^\s+/, '');
    
    const content = textarea.value.trim();
    
    if (!content) {
      showAlert('Vui lòng nhập bình luận', 'error');
      return;
    }
    
    // Disable submit button to prevent double submission
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
    }
    
    const mode = document.getElementById('modal-comment-mode-type')?.value || 'create';
    const targetId = document.getElementById('modal-comment-target-id')?.value || '';
    const anonymousChecked = document.getElementById('modal-comment-anonymous')?.checked;

    const formData = new FormData();
    formData.append('content', content);
    formData.append('is_anonymous', anonymousChecked ? '1' : '0');
    if (mode === 'reply' && targetId) {
      formData.append('parent_id', targetId);
    }

    const endpoint = mode === 'edit' && targetId
      ? `/comment/${targetId}/edit/`
      : `/post/${postId}/comment/`;

    fetch(endpoint, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData
    })
      .then(res => {
        if (res.status === 401) {
            showAlert('Vui lòng đăng nhập để bình luận.', 'error');
            closeSimpleModal(document.getElementById('post-detail-modal'));
            openModal('auth-modal');
            return null;
        }
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (!data) return; // For handled errors like 401
        
        if (data.success) {
          resetModalCommentMode();
          // Refresh comments
          if (typeof fetchAndDisplayComments === 'function') {
            fetchAndDisplayComments(postId);
          }
          showAlert(mode === 'edit' ? 'Đã cập nhật bình luận' : 'Bình luận đã được gửi', 'success');
          // Focus back on textarea
          textarea.focus();
        } else {
          showAlert(data.error || 'Có lỗi xảy ra khi gửi bình luận', 'error');
        }
      })
      .catch(err => {
        console.error('Error submitting comment:', err);
        showAlert('Không thể gửi bình luận: ' + err.message, 'error');
      })
      .finally(() => {
        // Re-enable submit button
        if (submitBtn) {
          submitBtn.disabled = false;
        }
      });
  } catch (error) {
    console.error('Error in submitModalComment:', error);
    showAlert('Có lỗi xảy ra', 'error');
  }
}
