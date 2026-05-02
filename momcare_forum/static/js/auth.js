/* ============================================
   MomCare Authentication JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all functionality
  initModals();
  initPasswordToggles();
  initTabSwitching();
  initMultiStepForms();
  initRegisterBackButtons();
  initOTPTimer();
  initFormValidation();
  initNotificationPopup();
  initUserMenu();
  checkLoginStatus();
});

function notifyUser(message, type = 'error') {
  if (typeof showAlert === 'function') {
    showAlert(message, type);
    return;
  }

  const toast = document.createElement('div');
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 99999;
    padding: 12px 16px;
    border-radius: 8px;
    color: #fff;
    font-size: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    background: ${type === 'success' ? '#2e7d32' : type === 'info' ? '#1565c0' : '#c62828'};
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
}

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
  // ===== STEP 1: Send OTP =====
  const sendOtpForm = document.getElementById('send-otp-form');
  if (sendOtpForm) {
    sendOtpForm.addEventListener('submit', function(e) {
      e.preventDefault();

      const email = document.getElementById('register-email');
      const username = document.getElementById('register-username');
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.textContent : 'Gửi OTP';

      // Validate
      if (!email.value.trim() || !username.value.trim()) {
        notifyUser('Vui lòng nhập email và tên đăng nhập', 'error');
        return;
      }

      // Show loading
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang gửi...';
      }

      // Send OTP
      fetch('/api/register/send-otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.value.trim(),
          username: username.value.trim()
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Move to step 2
          const step1 = document.getElementById('register-step1');
          const step2 = document.getElementById('register-step2');
          step1.classList.remove('active');
          step2.classList.add('active');

          // Store email for next steps
          window.registerData = {
            email: email.value.trim(),
            username: username.value.trim()
          };

          // Start OTP timer
          startOTPTimer();
        } else {
          notifyUser(data.error || 'Lỗi khi gửi OTP', 'error');
        }
      })
      .catch(error => notifyUser('Lỗi: ' + error.message, 'error'))
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalBtnText;
        }
      });
    });
  }

  // ===== STEP 2: Verify OTP =====
  const verifyOtpForm = document.querySelector('#register-step2 .verify-otp-form');
  if (verifyOtpForm) {
    verifyOtpForm.addEventListener('submit', function(e) {
      e.preventDefault();

      const otpInput = document.getElementById('register-otp');
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.textContent : 'Xác minh';

      if (!otpInput.value.trim()) {
        notifyUser('Vui lòng nhập mã OTP', 'error');
        return;
      }

      if (otpInput.value.length !== 6) {
        notifyUser('Mã OTP phải có 6 ký tự', 'error');
        return;
      }

      // Show loading
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang xác minh...';
      }

      // Verify OTP
      fetch('/api/register/verify-otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: window.registerData.email,
          username: window.registerData.username,
          otp_code: otpInput.value.trim()
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Move to step 3
          const step2 = document.getElementById('register-step2');
          const step3 = document.getElementById('register-step3');
          step2.classList.remove('active');
          step3.classList.add('active');
        } else {
          notifyUser(data.error || 'Mã OTP không hợp lệ', 'error');
        }
      })
      .catch(error => notifyUser('Lỗi: ' + error.message, 'error'))
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalBtnText;
        }
      });
    });
  }

  // ===== Resend OTP =====
  const resendLinks = document.querySelectorAll('#register-step2 .resend-link');
  resendLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();

      if (this.classList.contains('disabled')) {
        return;
      }

      // Send resend request
      fetch('/api/register/resend-otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: window.registerData.email
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          notifyUser(data.message || 'Mã OTP mới đã được gửi', 'success');

          // Reset OTP input and timer
          document.getElementById('register-otp').value = '';
          this.classList.add('disabled');
          startOTPTimer();
        } else {
          notifyUser(data.error || 'Lỗi khi gửi lại mã', 'error');
        }
      })
      .catch(error => notifyUser('Lỗi: ' + error.message, 'error'));
    });
  });

  // ===== STEP 3: Set Password =====
  const passwordSetupForm = document.querySelector('#register-step3 .password-setup-form');
  if (passwordSetupForm) {
    passwordSetupForm.addEventListener('submit', function(e) {
      e.preventDefault();

      const password = document.getElementById('register-password');
      const confirmPassword = document.getElementById('register-confirm-password');
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.textContent : 'Hoàn tất đăng ký';

      if (!password.value || !confirmPassword.value) {
        notifyUser('Vui lòng nhập mật khẩu', 'error');
        return;
      }

      if (password.value !== confirmPassword.value) {
        notifyUser('Mật khẩu xác nhận không khớp', 'error');
        return;
      }

      if (password.value.length < 8) {
        notifyUser('Mật khẩu phải có ít nhất 8 ký tự', 'error');
        return;
      }

      // Store password in memory for next step
      window.registerData = window.registerData || {};
      window.registerData.password = password.value;
      window.registerData.passwordConfirm = confirmPassword.value;

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang xử lý...';
      }

      // Show loading
      // Complete registration (interests now optional, send empty array)
      fetch('/api/register/complete/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          password: window.registerData.password,
          password_confirm: window.registerData.passwordConfirm,
          interests: []
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          notifyUser('Đăng ký thành công, vui lòng đăng nhập để tiếp tục.', 'success');
          
          // Switch to login tab instead of reloading
          const loginTab = document.querySelector('[data-tab="login"]');
          const registerTab = document.querySelector('[data-tab="register"]');
          const loginStep1 = document.getElementById('login-step1');
          const registerStep1 = document.getElementById('register-step1');
          
          if (loginTab && registerTab) {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
          }
          
          if (loginStep1 && registerStep1) {
            loginStep1.classList.add('active');
            registerStep1.classList.remove('active');
          }

          const step2 = document.getElementById('register-step2');
          const step3 = document.getElementById('register-step3');
          if (step2) step2.classList.remove('active');
          if (step3) step3.classList.remove('active');
          
          // Clear form
          passwordSetupForm.reset();
          const otpInput = document.getElementById('register-otp');
          if (otpInput) otpInput.value = '';
        } else {
          notifyUser(data.error || 'Lỗi khi hoàn tất đăng ký', 'error');
        }
      })
      .catch(error => notifyUser('Lỗi: ' + error.message, 'error'))
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalBtnText;
        }
      });
    });
  }
}

// Back button handlers for registration steps
function initRegisterBackButtons() {
  // Back buttons with data-prev-step attribute
  const backButtons = document.querySelectorAll('#auth-modal [data-prev-step]');
  backButtons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const prevStepId = this.getAttribute('data-prev-step');
      const prevStep = document.getElementById(prevStepId);
      
      if (prevStep) {
        const currentStep = this.closest('.auth-step');
        if (currentStep) {
          currentStep.classList.remove('active');
        }
        prevStep.classList.add('active');
      }
    });
  });
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
      notifyUser('Mật khẩu đã được cập nhật thành công!', 'success');

      // Close modal
      const modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  }
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
        notifyUser('Mã OTP đã được gửi lại!', 'success');
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
  // Load categories from API and render topics
  loadCategoriesAndRenderTopics();
  
  // Add event listeners to dynamically loaded checkboxes
  const topicsGrid = document.querySelector('.topics-grid');
  if (topicsGrid) {
    topicsGrid.addEventListener('change', (e) => {
      if (e.target.classList.contains('topic-checkbox')) {
        updateTopicSelection();
      }
    });
  }
}

function loadCategoriesAndRenderTopics() {
  // Load categories from API and render topic checkboxes
  fetch('/api/categories/')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.categories) {
        renderTopicCheckboxes(data.categories);
      } else {
        console.error('Failed to load categories:', data.error);
      }
    })
    .catch(error => console.error('Error loading categories:', error));
}

function renderTopicCheckboxes(categories) {
  // Render topic checkboxes with category IDs from database
  const topicsGrid = document.querySelector('.topics-grid');
  if (!topicsGrid) return;
  
  // Clear existing topics
  topicsGrid.innerHTML = '';
  
  // Topic icons mapping
  const iconColors = ['green', 'yellow', 'red', 'pink', 'orange', 'yellow', 'orange'];
  const icons = ['circle', 'circle', 'circle', 'circle', 'circle', 'circle', 'circle'];
  
  // Render checkbox for each category
  categories.forEach((category, index) => {
    const iconColor = iconColors[index % iconColors.length];
    const topicItem = document.createElement('div');
    topicItem.className = 'topic-item';
    topicItem.innerHTML = `
      <input type="checkbox" id="topic-${category.id}" class="topic-checkbox" value="${category.id}">
      <label for="topic-${category.id}" class="topic-label">
        <span class="topic-icon ${iconColor}">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          </svg>
        </span>
        <span class="topic-text">${category.name}</span>
        <span class="topic-checkmark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </span>
      </label>
    `;
    topicsGrid.appendChild(topicItem);
  });
  
  // Update submit button state
  updateTopicSelection();
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
      const errorDiv = this.querySelector('#login-error-message');

      // Clear previous errors
      if (errorDiv) {
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
      }
      if (username) username.classList.remove('error');
      if (password) password.classList.remove('error');

      // Client-side validation
      if (!username || !username.value.trim()) {
        if (errorDiv) {
          errorDiv.textContent = 'Vui lòng nhập tên đăng nhập';
          errorDiv.style.display = 'block';
        }
        showError(username, '');
        return;
      }

      if (!password || !password.value) {
        if (errorDiv) {
          errorDiv.textContent = 'Vui lòng nhập mật khẩu';
          errorDiv.style.display = 'block';
        }
        showError(password, '');
        return;
      }

      // Show loading state
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.textContent : 'Đăng nhập';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang xử lý...';
      }

      // POST to API with both username and password
      fetch('/api/login-validate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
          username: username.value.trim(),
          password: password.value
        })
      })
        .then(response => response.json())
        .then(data => {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
          }

          // STRICT CHECK: must be exactly true
          if (data.success === true) {
            // Successful login - Django session is set on server
            
            // Clear error message and styling
            if (errorDiv) {
              errorDiv.style.display = 'none';
              errorDiv.textContent = '';
            }
            if (password) password.classList.remove('error');
            if (username) username.classList.remove('error');
            
            // Close modal and refresh to sync UI with server state
            const modal = loginForm.closest('.modal-overlay');
            if (modal) closeModal(modal);
            
            // Reload page to verify session and update UI
            setTimeout(() => {
              window.location.reload();
            }, 300);
          } else {
            // Login FAILED
            
            // Clear password field on error
            if (password) {
              password.value = '';
              password.classList.add('error');
            }
            
            // Show error message
            const errorMsg = data.error || 'Đăng nhập không thành công!';
            if (errorDiv) {
              errorDiv.textContent = errorMsg;
              errorDiv.style.display = 'block';
            } else {
              notifyUser(errorMsg, 'error');
            }
            
            // Keep modal open so user can retry
            if (username) username.focus();
          }
        })
        .catch(error => {
          console.error('Login error:', error);
          
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
          }
          
          // Clear password on connection error
          if (password) {
            password.value = '';
            password.classList.add('error');
          }
          
          // Show error message
          const errorMsg = 'Lỗi kết nối. Vui lòng thử lại!';
          if (errorDiv) {
            errorDiv.textContent = errorMsg;
            errorDiv.style.display = 'block';
          } else {
            notifyUser(errorMsg, 'error');
          }
          
          if (username) username.focus();
        });
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

      const password = this.querySelector('#register-password, #password, #new-password');
      const confirmPassword = this.querySelector('#register-confirm-password, #confirm-password, #confirm-new-password');

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
  if (!input) {
    return false;
  }

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
  if (!input) {
    notifyUser('Không tìm thấy trường mật khẩu', 'error');
    return false;
  }

  if (!input.value) {
    showError(input, 'Vui lòng nhập mật khẩu');
    return false;
  }

  if (input.value.length < 8) {
    showError(input, 'Mật khẩu phải có ít nhất 8 ký tự');
    return false;
  }

  clearError(input);
  return true;
}

function validateConfirmPassword(input, passwordInput) {
  if (!input || !passwordInput) {
    notifyUser('Không tìm thấy trường xác nhận mật khẩu', 'error');
    return false;
  }

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
  window.location.href = '/forgot-password/step1/';
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

function login(userFullName, access = false) {
  // Update UI to show user is logged in
  // No localStorage - rely on Django session cookie
  
  const authButtons = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');
  const name = userFullName || 'User';

  if (authButtons) authButtons.style.display = 'none';
  if (userMenu) userMenu.style.display = 'flex';

  // Update avatar display with first letter
  const initial = name.charAt(0).toUpperCase();
  const avatarEl = document.getElementById('user-avatar-display');
  const dropdownAvatar = document.getElementById('dropdown-avatar-display');
  const userNameEl = document.getElementById('user-name-display');
  const profileMenuLink = document.getElementById('profile-menu-link');
  const profileMenuLabel = document.getElementById('profile-menu-label');
  const isAccessObject = access && typeof access === 'object';
  const isSuperuser = isAccessObject ? !!(access.isSuperuser ?? access.is_superuser) : false;
  const isStaff = isAccessObject ? !!(access.isStaff ?? access.is_staff) : false;

  if (avatarEl) avatarEl.textContent = initial;
  if (dropdownAvatar) dropdownAvatar.textContent = initial;
  if (userNameEl) userNameEl.textContent = name;

  if (profileMenuLink && profileMenuLabel) {
    if (isSuperuser) {
      profileMenuLink.setAttribute('href', '/admin/');
      profileMenuLabel.textContent = 'Trang quản trị';
    } else if (isStaff) {
      profileMenuLink.setAttribute('href', '/admin-panel/');
      profileMenuLabel.textContent = 'Trang quản trị';
    } else {
      profileMenuLink.setAttribute('href', '/profile/');
      profileMenuLabel.textContent = 'Trang cá nhân';
    }
  }
}

function logout() {
  // Call server logout API to clear Django session
  fetch('/api/logout/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    }
  })
    .then(response => response.json())
    .then(data => {
      // Redirect to forum - page load will verify no session and show login UI
      window.location.href = '/forum/';
    })
    .catch(error => {
      console.error('Logout error:', error);
      // Even if API fails, redirect - session might be cleared
      window.location.href = '/forum/';
    });
}

// Check login status on load
function checkLoginStatus() {
  // Verify current user session with server
  // This is the ONLY way to know if user is logged in
  fetch('/api/check-admin-status/', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    credentials: 'include'  // Include cookies for session verification
  })
    .then(response => response.json())
    .then(data => {
      if (data.is_authenticated) {
        // User HAS valid server session - show logged-in UI
        const userName = data.full_name || data.username || 'User';
        login(userName, {
          isSuperuser: data.is_superuser || false,
          isStaff: data.is_staff || false
        });
      } else {
        // User does NOT have valid server session - show login UI
        const authButtons = document.getElementById('auth-buttons');
        const userMenu = document.getElementById('user-menu');
        const profileMenuLink = document.getElementById('profile-menu-link');
        const profileMenuLabel = document.getElementById('profile-menu-label');
        if (authButtons) authButtons.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'none';
        if (profileMenuLink && profileMenuLabel) {
          profileMenuLink.setAttribute('href', '/profile/');
          profileMenuLabel.textContent = 'Trang cá nhân';
        }
      }
    })
    .catch(error => {
      console.error('[SESSION] Verification failed:', error);
      // On error, assume NOT logged in (safer)
      const authButtons = document.getElementById('auth-buttons');
      const userMenu = document.getElementById('user-menu');
      const profileMenuLink = document.getElementById('profile-menu-link');
      const profileMenuLabel = document.getElementById('profile-menu-label');
      if (authButtons) authButtons.style.display = 'flex';
      if (userMenu) userMenu.style.display = 'none';
      if (profileMenuLink && profileMenuLabel) {
        profileMenuLink.setAttribute('href', '/profile/');
        profileMenuLabel.textContent = 'Trang cá nhân';
      }
    });
  
}

/* ============================================
   Notification Popup
   ============================================ */

function initNotificationPopup() {
  const notifBtn = document.getElementById('notification-btn');
  const notifPopup = document.getElementById('notification-popup');

  if (!notifBtn || !notifPopup) return;

  const applyNotificationFilter = (showUnreadOnly) => {
    const groups = notifPopup.querySelectorAll('.notif-group');
    let hasVisibleItems = false;

    groups.forEach(group => {
      const items = group.querySelectorAll('.notif-item');

      if (items.length === 0) {
        if (group.dataset.emptyState !== 'true') {
          group.style.display = 'none';
        }
        return;
      }

      let visibleInGroup = 0;
      items.forEach(item => {
        const shouldShow = !showUnreadOnly || item.classList.contains('unread');
        item.style.display = shouldShow ? 'flex' : 'none';
        if (shouldShow) {
          visibleInGroup += 1;
          hasVisibleItems = true;
        }
      });

      group.style.display = visibleInGroup > 0 ? 'block' : 'none';
    });

    const existingEmpty = notifPopup.querySelector('.notif-empty-state');
    if (existingEmpty) {
      existingEmpty.remove();
    }

    if (!hasVisibleItems) {
      const body = notifPopup.querySelector('.notif-body');
      if (body) {
        const empty = document.createElement('div');
        empty.className = 'notif-group notif-empty-state';
        empty.dataset.emptyState = 'true';
        empty.style.textAlign = 'center';
        empty.style.padding = '20px';
        empty.style.color = '#999';
        empty.innerHTML = `<p>${showUnreadOnly ? 'Không có thông báo chưa đọc' : 'Bạn không có thông báo nào'}</p>`;
        body.appendChild(empty);
      }
    }
  };

  // Toggle popup on click
  notifBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    const isShowing = notifPopup.classList.toggle('show');
    
    // Theo yêu cầu: hiện ra thông tin dòng thông báo chưa đọc
    if (isShowing) {
      const unreadTab = Array.from(document.querySelectorAll('.notif-tab')).find(t => t.textContent.trim() === 'Chưa đọc');
      if (unreadTab) {
        unreadTab.click();
      } else {
        applyNotificationFilter(false);
      }
    }
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
      fetch('/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        }
      })
        .then(response => response.json())
        .then(data => {
          if (!data.success) return;

          document.querySelectorAll('.notif-item.unread').forEach(item => {
            item.classList.remove('unread');
            const dot = item.querySelector('.notif-dot');
            if (dot) dot.remove();
          });

          const badge = document.querySelector('.notification-badge');
          if (badge) badge.remove();

          const activeTab = notifPopup.querySelector('.notif-tab.active');
          const showUnreadOnly = activeTab && activeTab.textContent.trim() === 'Chưa đọc';
          applyNotificationFilter(showUnreadOnly);
        })
        .catch(error => {
          console.error('Mark all as read failed:', error);
        });
    });
  }

  // Tab switching
  const tabs = document.querySelectorAll('.notif-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      tabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');

      const isUnread = this.textContent.trim() === 'Chưa đọc';
      applyNotificationFilter(isUnread);
    });
  });
}

/* ============================================
   Utility Functions
   ============================================ */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function handleAdminLogout(event) {
  event.preventDefault();
  
  // Clear all client-side authentication data
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('momcare_user');
  
  // Redirect to admin logout URL
  window.location.href = '/admin-logout/';
}
