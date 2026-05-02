/**
 * Cloudinary Image Upload Handler
 * Handles file selection, preview, and upload to Cloudinary
 */

class CloudinaryUploader {
  constructor(config = {}) {
    this.cloudName = config.cloudName || 'dy5vntutj';
    this.uploadPreset = config.uploadPreset || '';
    this.folder = config.folder || 'momcare/posts';
    this.maxFileSize = config.maxFileSize || 10 * 1024 * 1024; // 10MB
    this.allowedTypes = config.allowedTypes || ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  }

  /**
   * Setup file input handler
   * @param {string} inputSelector - CSS selector for file input
   * @param {string} previewSelector - CSS selector for preview container
   * @param {Function} onSuccess - Callback when upload succeeds
   * @param {Function} onError - Callback when upload fails
   */
  setupFileInput(inputSelector, previewSelector, onSuccess, onError) {
    const fileInput = document.querySelector(inputSelector);
    const previewContainer = document.querySelector(previewSelector);

    if (!fileInput) {
      console.error(`File input not found: ${inputSelector}`);
      return;
    }

    fileInput.addEventListener('change', (e) => {
      this.handleFileSelect(e, previewContainer, onSuccess, onError);
    });
  }

  /**
   * Handle file selection
   */
  handleFileSelect(event, previewContainer, onSuccess, onError) {
    const file = event.target.files[0];

    if (!file) return;

    // Validate file
    const validation = this.validateFile(file);
    if (!validation.valid) {
      if (onError) onError(validation.error);
      this.showAlert(validation.error, 'error');
      event.target.value = ''; // Reset input
      return;
    }

    // Show preview
    this.showPreview(file, previewContainer);

    // Auto-upload to Cloudinary
    this.uploadFile(file, previewContainer, onSuccess, onError);
  }

  /**
   * Validate file
   */
  validateFile(file) {
    if (!this.allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `❌ Định dạng không hỗ trợ. Vui lòng chọn: ${this.allowedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')}`
      };
    }

    if (file.size > this.maxFileSize) {
      return {
        valid: false,
        error: `❌ Tệp quá lớn. Kích thước tối đa: ${(this.maxFileSize / 1024 / 1024).toFixed(0)}MB`
      };
    }

    return { valid: true };
  }

  /**
   * Show image preview
   */
  showPreview(file, previewContainer) {
    if (!previewContainer) return;

    const reader = new FileReader();

    reader.onload = (e) => {
      previewContainer.innerHTML = `
        <div class="image-preview-wrapper" style="position: relative; display: inline-block;">
          <img src="${e.target.result}" alt="Preview" style="max-width: 100%; max-height: 300px; border-radius: 8px; display: block;">
          <div class="upload-progress" style="display: none; position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 8px 12px; border-radius: 6px; font-size: 12px;">
            Đang tải lên...
          </div>
          <div class="upload-status" style="margin-top: 10px; font-size: 12px; color: #666;"></div>
        </div>
      `;
    };

    reader.readAsDataURL(file);
  }

  /**
   * Upload file to Cloudinary via backend
   */
  uploadFile(file, previewContainer, onSuccess, onError) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('folder', this.folder);

    const progressDiv = previewContainer?.querySelector('.upload-progress');
    const statusDiv = previewContainer?.querySelector('.upload-status');

    if (progressDiv) progressDiv.style.display = 'block';
    if (statusDiv) statusDiv.textContent = '⏳ Đang tải lên...';

    console.log('📤 Uploading file to server:', file.name);

    // Set a reasonable timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 second timeout

    fetch('/api/upload-image/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': this.getCookie('csrftoken')
      },
      signal: controller.signal
    })
    .then(response => {
      clearTimeout(timeoutId);
      
      // Log response details for debugging
      console.log(`Upload response status: ${response.status}`);
      
      if (response.status === 503) {
        throw new Error('Dịch vụ Cloudinary tạm thời không khả dụng. Vui lòng thử lại sau.');
      }
      
      if (!response.ok) {
        throw new Error(`Lỗi máy chủ: ${response.status}`);
      }
      
      return response.json();
    })
    .then(data => {
      if (data.success) {
        console.log('✅ Upload successful:', data);
        
        if (progressDiv) progressDiv.style.display = 'none';
        if (statusDiv) {
          statusDiv.innerHTML = `
            <span style="color: #4caf50;">✓ Tải lên thành công</span><br>
            <small style="color: #999;">Kích thước: ${data.width}×${data.height}px</small>
          `;
        }

        if (onSuccess) {
          onSuccess({
            url: data.secure_url,
            publicId: data.public_id,
            width: data.width,
            height: data.height
          });
        }
      } else {
        console.error('Upload failed with error:', data.error);
        throw new Error(data.error || 'Không thể tải lên hình ảnh');
      }
    })
    .catch(error => {
      clearTimeout(timeoutId);
      console.error('❌ Upload error:', error);
      
      let errorMessage = error.message;
      
      // Handle specific error types
      if (error.name === 'AbortError') {
        errorMessage = 'Tải lên quá lâu. Vui lòng thử lại với tệp nhỏ hơn.';
      } else if (!navigator.onLine) {
        errorMessage = 'Không có kết nối internet. Vui lòng kiểm tra mạng.';
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = 'Lỗi kết nối. Vui lòng thử lại.';
      }
      
      if (progressDiv) progressDiv.style.display = 'none';
      if (statusDiv) {
        statusDiv.innerHTML = `<span style="color: #f44336;">✗ ${errorMessage}</span>`;
      }

      if (onError) onError(errorMessage);
      this.showAlert(errorMessage, 'error');
    });
  }

  /**
   * Get CSRF token from cookies
   */
  getCookie(name) {
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

  /**
   * Show alert message
   */
  showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.style.cssText = `
      position: fixed; top: 20px; right: 20px; z-index: 10000;
      padding: 12px 20px; border-radius: 8px; font-size: 14px;
      animation: slideIn 0.3s ease-out;
      ${type === 'error' ? 'background: #ffebee; color: #c62828; border: 1px solid #ef5350;' : 
        type === 'success' ? 'background: #e8f5e9; color: #2e7d32; border: 1px solid #66bb6a;' :
        'background: #e3f2fd; color: #1565c0; border: 1px solid #42a5f5;'}
    `;
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
      alertDiv.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
  }
}

// Add slide animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(400px); opacity: 0; }
  }
`;
document.head.appendChild(style);

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CloudinaryUploader;
}
