/* ============================================
   MomCare Authentication JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all functionality
  initModals();
  initPasswordToggles();
  initTabSwitching();
  initMultiStepForms();
  initOTPTimer();
  initTopicSelection();
  initFormValidation();
  initNotificationPopup();
  initUserMenu();
  checkLoginStatus();
});

/* ============================================
   Modal Management
   ============================================ */

function initModals() {
  const modalTriggers = document.querySelectorAll('[data-modal]');
  const modalCloseButtons = document.querySelectorAll('.modal-close, .modal-overlay');

  // Open modal
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', function(e) {
      e.preventDefault();
      const modalId = this.getAttribute('data-modal');
      openModal(modalId);
    });
  });

  // Close modal
  modalCloseButtons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      if (this.classList.contains('modal-overlay')) {
        closeModal(this);
      }
    });
  });

  // Close modal on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const activeModal = document.querySelector('.modal-overlay.active');
      if (activeModal) {
        closeModal(activeModal);
      }
    }
  });

  // Prevent closing when clicking inside modal
  document.querySelectorAll('.modal-card').forEach(card => {
    card.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  });
}

function openModal(modalId) {
  // Close all other modals first
  document.querySelectorAll('.modal-overlay.active').forEach(m => {
    m.classList.remove('active');
  });

  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Focus first input
    const firstInput = modal.querySelector('.form-input');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100);
    }
  }
}

function closeModal(modal) {
  modal.classList.remove('active');
  document.body.style.overflow = '';

  // Reset form when closing
  const form = modal.querySelector('form');
  if (form) {
    form.reset();
  }
}

/* ============================================
   Password Toggle (Show/Hide)
   ============================================ */

function initPasswordToggles() {
  const toggles = document.querySelectorAll('.password-toggle');

  toggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      const input = this.parentElement.querySelector('.form-input');
      const isPassword = input.type === 'password';

      input.type = isPassword ? 'text' : 'password';

      // Toggle icon
      const svgShow = this.querySelector('.icon-show');
      const svgHide = this.querySelector('.icon-hide');

      if (svgShow && svgHide) {
        svgShow.style.display = isPassword ? 'none' : 'block';
        svgHide.style.display = isPassword ? 'block' : 'none';
      }
    });
  });
}

/* ============================================
   Tab Switching (Login/Register)
   ============================================ */

function initTabSwitching() {
  const tabs = document.querySelectorAll('.auth-tab');
  const tabContents = document.querySelectorAll('.auth-tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      const target = this.getAttribute('data-tab');
      switchTab(target);
    });
  });
}

function switchTab(target) {
  const tabs = document.querySelectorAll('.auth-tab');
  const tabContents = document.querySelectorAll('.auth-tab-content');

  // Update tabs
  tabs.forEach(t => t.classList.remove('active'));
  tabs.forEach(t => {
    if (t.getAttribute('data-tab') === target) {
      t.classList.add('active');
    }
  });

  // Update content
  tabContents.forEach(content => {
    content.classList.remove('active');
    if (content.id === target) {
      content.classList.add('active');
    }
  });
}

/* ============================================
   Multi-Step Forms
   ============================================ */

function initMultiStepForms() {
  // Register Steps
  initRegisterSteps();

  // Forgot Password Steps
  initForgotPasswordSteps();
}

function initRegisterSteps() {
  const steps = {
    step1: { next: 'register-step2' },
    step2: { prev: 'register-step1', next: 'register-step3' },
    step3: { prev: 'register-step2', next: 'register-step4' },
    step4: { prev: 'register-step3' }
  };

  // Next buttons
  document.querySelectorAll('[data-next-step]').forEach(btn => {
    btn.addEventListener('click', function() {
      const currentStep = this.closest('.auth-step');
      const nextStepId = this.getAttribute('data-next-step');
      const nextStep = document.getElementById(nextStepId);

      if (validateStep(currentStep)) {
        currentStep.classList.remove('active');
        nextStep.classList.add('active');
        updateStepIndicator(nextStepId);
      }
    });
  });

  // Previous buttons
  document.querySelectorAll('[data-prev-step]').forEach(btn => {
    btn.addEventListener('click', function() {
      const currentStep = this.closest('.auth-step');
      const prevStepId = this.getAttribute('data-prev-step');
      const prevStep = document.getElementById(prevStepId);

      currentStep.classList.remove('active');
      prevStep.classList.add('active');
      updateStepIndicator(prevStepId);
    });
  });

  // Submit register
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
      e.preventDefault();

      // Validate final step (topics)
      const selectedTopics = document.querySelectorAll('.topic-checkbox:checked');
      if (selectedTopics.length === 0) {
        alert('Vui lòng chọn ít nhất một chủ đề quan tâm!');
        return;
      }

      // Show success message
      alert('Đăng ký thành công! Chào mừng bạn đến với MomCare!');

      // Close modal
      const modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  }
}

function initForgotPasswordSteps() {
  // Next buttons
  document.querySelectorAll('[data-next-forgot]').forEach(btn => {
    btn.addEventListener('click', function() {
      const currentStep = this.closest('.auth-step');
      const nextStepId = this.getAttribute('data-next-forgot');
      const nextStep = document.getElementById(nextStepId);

      if (validateStep(currentStep)) {
        currentStep.classList.remove('active');
        nextStep.classList.add('active');

        // Start OTP timer for step 2
        if (nextStepId === 'forgot-password-step2' || nextStepId === 'register-step2') {
          startOTPTimer();
        }
      }
    });
  });

  // Previous buttons
  document.querySelectorAll('[data-prev-forgot]').forEach(btn => {
    btn.addEventListener('click', function() {
      const currentStep = this.closest('.auth-step');
      const prevStepId = this.getAttribute('data-prev-forgot');
      const prevStep = document.getElementById(prevStepId);

      currentStep.classList.remove('active');
      prevStep.classList.add('active');
    });
  });

  // Submit forgot password
  const forgotPasswordForm = document.getElementById('forgot-password-form');
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', function(e) {
      e.preventDefault();
      alert('Mật khẩu đã được cập nhật thành công!');

      // Close modal
      const modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  }
}

function updateStepIndicator(stepId) {
  const indicator = document.querySelector('.step-indicator');
  if (!indicator) return;

  const stepMap = {
    'register-step1': 0,
    'register-step2': 1,
    'register-step3': 2,
    'register-step4': 3,
    'forgot-password-step1': 0,
    'forgot-password-step2': 1,
    'forgot-password-step3': 2
  };

  const currentStep = stepMap[stepId];
  const dots = indicator.querySelectorAll('.step-dot');

  dots.forEach((dot, index) => {
    dot.classList.remove('active', 'completed');
    if (index < currentStep) {
      dot.classList.add('completed');
    } else if (index === currentStep) {
      dot.classList.add('active');
    }
  });
}

/* ============================================
   OTP Timer
   ============================================ */

let otpTimerInterval = null;
let otpTimeLeft = 60;

function initOTPTimer() {
  // Resend OTP link
  const resendLinks = document.querySelectorAll('.resend-link');
  resendLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      if (!this.classList.contains('disabled')) {
        resetOTPTimer();
        // Here you would typically call API to resend OTP
        alert('Mã OTP đã được gửi lại!');
      }
    });
  });
}

function startOTPTimer() {
  // Reset timer
  otpTimeLeft = 60;

  // Clear existing timer
  if (otpTimerInterval) {
    clearInterval(otpTimerInterval);
  }

  const timerElement = document.querySelector('.otp-timer');
  const timeDisplay = timerElement?.querySelector('.timer-value');
  const resendLink = document.querySelector('.resend-link');

  if (timerElement && timeDisplay) {
    updateTimerDisplay(timeDisplay);

    otpTimerInterval = setInterval(function() {
      otpTimeLeft--;
      updateTimerDisplay(timeDisplay);

      if (otpTimeLeft <= 0) {
        clearInterval(otpTimerInterval);
        timerElement.classList.add('expired');
        if (resendLink) {
          resendLink.classList.remove('disabled');
        }
      }
    }, 1000);
  }
}

function updateTimerDisplay(display) {
  const minutes = Math.floor(otpTimeLeft / 60);
  const seconds = otpTimeLeft % 60;
  display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function resetOTPTimer() {
  otpTimeLeft = 60;
  const timerElement = document.querySelector('.otp-timer');
  const timeDisplay = timerElement?.querySelector('.timer-value');
  const resendLink = document.querySelector('.resend-link');

  if (resendLink) {
    resendLink.classList.add('disabled');
  }
  if (timerElement) {
    timerElement.classList.remove('expired');
  }
  if (timeDisplay) {
    updateTimerDisplay(timeDisplay);
  }

  startOTPTimer();
}

/* ============================================
   Topic Selection
   ============================================ */

function initTopicSelection() {
  const topicCheckboxes = document.querySelectorAll('.topic-checkbox');

  topicCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      updateTopicSelection();
    });
  });
}

function updateTopicSelection() {
  const selectedTopics = document.querySelectorAll('.topic-checkbox:checked');
  const submitBtn = document.querySelector('#register-form .btn-primary');

  // Enable/disable submit button based on selection
  if (submitBtn) {
    submitBtn.disabled = selectedTopics.length === 0;
  }
}

/* ============================================
   Form Validation
   ============================================ */

function initFormValidation() {
  // Email validation
  const emailInputs = document.querySelectorAll('input[type="email"]');
  emailInputs.forEach(input => {
    input.addEventListener('blur', function() {
      validateEmail(this);
    });
  });

  // Password validation
  const passwordInputs = document.querySelectorAll('input[type="password"]');
  passwordInputs.forEach(input => {
    input.addEventListener('blur', function() {
      if (this.id === 'password' || this.id === 'new-password') {
        validatePassword(this);
      }
    });
  });

  // Confirm password validation
  const confirmPasswordInputs = document.querySelectorAll('#confirm-password, #confirm-new-password');
  confirmPasswordInputs.forEach(input => {
    input.addEventListener('blur', function() {
      const passwordInput = document.querySelector('#password, #new-password');
      if (passwordInput) {
        validateConfirmPassword(this, passwordInput);
      }
    });
  });

  // Login form
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
      e.preventDefault();

      const username = this.querySelector('#username');
      const password = this.querySelector('#password');

      if (!username.value.trim()) {
        showError(username, 'Vui lòng nhập tên đăng nhập');
        return;
      }

      if (!password.value) {
        showError(password, 'Vui lòng nhập mật khẩu');
        return;
      }

      // Here you would typically call API
      const usernameVal = username.value.trim();
      alert('Đăng nhập thành công!');
      login(usernameVal || 'M'); // Show user menu

      // Close modal
      const modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  }

  // Send OTP (Register Step 1)
  const sendOTPForm = document.getElementById('send-otp-form');
  if (sendOTPForm) {
    sendOTPForm.addEventListener('submit', function(e) {
      e.preventDefault();

      const email = this.querySelector('#register-email');

      if (!validateEmail(email)) return;

      // Here you would typically call API to send OTP
      // For demo, move to next step
      const nextBtn = this.querySelector('[data-next-step]');
      if (nextBtn) nextBtn.click();
    });
  }

  // Verify OTP (Register Step 2 & Forgot Password Step 2)
  const verifyOTPForms = document.querySelectorAll('.verify-otp-form');
  verifyOTPForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();

      const otpInput = this.querySelector('.otp-input');

      if (!otpInput.value.trim()) {
        showError(otpInput, 'Vui lòng nhập mã OTP');
        return;
      }

      if (otpInput.value.length !== 6) {
        showError(otpInput, 'Mã OTP phải có 6 chữ số');
        return;
      }

      // Here you would typically verify OTP via API
      // For demo, move to next step
      const nextBtn = this.querySelector('[data-next-step], [data-next-forgot]');
      if (nextBtn) nextBtn.click();
    });
  });

  // Password setup (Register Step 3 & Forgot Password Step 3)
  const passwordSetupForms = document.querySelectorAll('.password-setup-form');
  passwordSetupForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();

      const password = this.querySelector('#password, #new-password');
      const confirmPassword = this.querySelector('#confirm-password, #confirm-new-password');

      if (!validatePassword(password)) return;
      if (!validateConfirmPassword(confirmPassword, password)) return;

      // Here you would typically call API to set password
      // For demo, move to next step
      const nextBtn = this.querySelector('[data-next-step], [data-next-forgot]');
      if (nextBtn) nextBtn.click();
    });
  });
}

function validateEmail(input) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!input.value.trim()) {
    showError(input, 'Vui lòng nhập email');
    return false;
  }

  if (!emailRegex.test(input.value)) {
    showError(input, 'Email không hợp lệ');
    return false;
  }

  clearError(input);
  return true;
}

function validatePassword(input) {
  if (!input.value) {
    showError(input, 'Vui lòng nhập mật khẩu');
    return false;
  }

  if (input.value.length < 6) {
    showError(input, 'Mật khẩu phải có ít nhất 6 ký tự');
    return false;
  }

  clearError(input);
  return true;
}

function validateConfirmPassword(input, passwordInput) {
  if (!input.value) {
    showError(input, 'Vui lòng xác nhận mật khẩu');
    return false;
  }

  if (input.value !== passwordInput.value) {
    showError(input, 'Mật khẩu xác nhận không khớp');
    return false;
  }

  clearError(input);
  return true;
}

function validateStep(stepElement) {
  const inputs = stepElement.querySelectorAll('.form-input[required]');
  let isValid = true;

  inputs.forEach(input => {
    if (!input.value.trim()) {
      showError(input, 'Vui lòng nhập trường này');
      isValid = false;
    } else {
      clearError(input);
    }
  });

  return isValid;
}

function showError(input, message) {
  const formGroup = input.closest('.form-group');
  if (formGroup) {
    formGroup.classList.add('error');
    let errorElement = formGroup.querySelector('.form-error');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'form-error';
      formGroup.appendChild(errorElement);
    }
    errorElement.textContent = message;
  }
}

function clearError(input) {
  const formGroup = input.closest('.form-group');
  if (formGroup) {
    formGroup.classList.remove('error');
    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
      errorElement.remove();
    }
  }
}

/* ============================================
   Utility Functions
   ============================================ */

// Close all modals
function closeAllModals() {
  document.querySelectorAll('.modal-overlay.active').forEach(modal => {
    closeModal(modal);
  });
}

// Open specific auth modal
function openLoginModal() {
  openModal('auth-modal');
}

function openRegisterModal() {
  openModal('auth-modal');
  // Switch to register tab
  const registerTab = document.querySelector('[data-tab="register"]');
  if (registerTab) {
    registerTab.click();
  }
}

function openForgotPasswordModal() {
  openModal('forgot-password-modal');
}

// Export for global use
window.MomCareAuth = {
  openModal,
  closeModal,
  openLoginModal,
  openRegisterModal,
  openForgotPasswordModal,
  closeAllModals,
  switchTab
};

/* ============================================
   User Menu & Login/Logout
   ============================================ */

function initUserMenu() {
  const userAvatarBtn = document.getElementById('user-avatar-btn');
  const dropdownMenu = document.getElementById('dropdown-menu');
  const logoutBtn = document.getElementById('logout-btn');
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');

  if (!userAvatarBtn || !dropdownMenu) return;

  // Toggle dropdown
  userAvatarBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdownMenu.classList.toggle('show');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(e) {
    if (!dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.remove('show');
    }
  });

  // Logout
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
      e.preventDefault();
      logout();
    });
  }
}

function login(userName) {
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');
  const name = userName || 'M';

  if (authButtons) authButtons.style.display = 'none';
  if (userMenu) userMenu.style.display = 'flex';

  localStorage.setItem('isLoggedIn', 'true');
  localStorage.setItem('momcare_user', JSON.stringify({ name: name }));

  // Update avatar display
  const initial = name.charAt(0).toUpperCase();
  const avatarEl = document.getElementById('user-avatar-display');
  const dropdownAvatar = document.getElementById('dropdown-avatar-display');
  const userNameEl = document.getElementById('user-name-display');

  if (avatarEl) avatarEl.textContent = initial;
  if (dropdownAvatar) dropdownAvatar.textContent = initial;
  if (userNameEl) userNameEl.textContent = name;
}

function logout() {
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');
  const dropdownMenu = document.getElementById('dropdown-menu');

  if (authButtons) authButtons.style.display = 'flex';
  if (userMenu) userMenu.style.display = 'none';
  if (dropdownMenu) dropdownMenu.classList.remove('show');

  localStorage.removeItem('isLoggedIn');
}

// Check login status on load
function checkLoginStatus() {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (isLoggedIn) {
    login();
  }
}

/* ============================================
   Notification Popup
   ============================================ */

function initNotificationPopup() {
  const notifBtn = document.getElementById('notification-btn');
  const notifPopup = document.getElementById('notification-popup');

  if (!notifBtn || !notifPopup) return;

  // Toggle popup on click
  notifBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    notifPopup.classList.toggle('show');
  });

  // Close when clicking outside
  document.addEventListener('click', function(e) {
    if (!notifPopup.contains(e.target) && !notifBtn.contains(e.target)) {
      notifPopup.classList.remove('show');
    }
  });

  // Mark all as read
  const markAllRead = document.querySelector('.notif-mark-read');
  if (markAllRead) {
    markAllRead.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      document.querySelectorAll('.notif-item.unread').forEach(item => {
        item.classList.remove('unread');
        const dot = item.querySelector('.notif-dot');
        if (dot) dot.remove();
      });
      const badge = document.querySelector('.notification-badge');
      if (badge) badge.style.display = 'none';
    });
  }

  // Tab switching
  const tabs = document.querySelectorAll('.notif-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      tabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');

      const isUnread = this.textContent === 'Chưa đọc';
      document.querySelectorAll('.notif-item').forEach(item => {
        if (isUnread) {
          item.style.display = item.classList.contains('unread') ? 'flex' : 'none';
        } else {
          item.style.display = 'flex';
        }
      });
    });
  });
}
