/**
 * File Preview Module
 * Handles image/GIF/video preview functionality with memory management
 * and comprehensive error handling
 */

class FilePreviewManager {
  constructor(options = {}) {
    // Configuration
    this.config = {
      fileInputId: options.fileInputId || 'file-upload',
      previewContainerId: options.previewContainerId || 'preview',
      uploadDefaultId: options.uploadDefaultId || 'upload-default',
      maxFileSize: options.maxFileSize || 50 * 1024 * 1024, // 50MB default
      acceptedTypes: options.acceptedTypes || ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'video/mp4', 'video/webm'],
      ...options
    };

    // State
    this.state = {
      currentFile: null,
      currentObjectUrl: null,
      formState: null
    };

    // Bind methods
    this.handleFileSelect = this.handleFileSelect.bind(this);
    this.removePreview = this.removePreview.bind(this);
    this.validateFile = this.validateFile.bind(this);
    this.displayImagePreview = this.displayImagePreview.bind(this);
    this.displayMediaPreview = this.displayMediaPreview.bind(this);

    // Initialize event listeners
    this.init();
  }

  /**
   * Initialize event listeners
   */
  init() {
    const fileInput = document.getElementById(this.config.fileInputId);
    if (fileInput) {
      fileInput.addEventListener('change', this.handleFileSelect);
    }
  }

  /**
   * Main file selection handler
   */
  handleFileSelect(event) {
    const file = event.target.files?.[0];
    
    if (!file) return;

    // Validate file
    const validation = this.validateFile(file);
    if (!validation.valid) {
      this.showError(validation.error);
      this.resetFileInput();
      return;
    }

    // Store file and display preview
    this.state.currentFile = file;
    this.displayPreview(file);

    // Callback for form state (if needed)
    if (window.formState) {
      window.formState.imageFile = file;
    }
  }

  /**
   * Validate file type, size, and format
   */
  validateFile(file) {
    // Check file type
    if (!this.config.acceptedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `Invalid file type. Accepted: images (JPEG, PNG, WebP), GIFs, and videos (MP4, WebM)`
      };
    }

    // Check file size
    if (file.size > this.config.maxFileSize) {
      const maxMB = (this.config.maxFileSize / (1024 * 1024)).toFixed(1);
      return {
        valid: false,
        error: `File size exceeds ${maxMB}MB limit. Please choose a smaller file.`
      };
    }

    return { valid: true };
  }

  /**
   * Display preview based on file type
   */
  displayPreview(file) {
    const previewContainer = document.getElementById(this.config.previewContainerId);
    const uploadDefault = document.getElementById(this.config.uploadDefaultId);

    if (!previewContainer) return;

    // Hide default upload icon
    if (uploadDefault) {
      uploadDefault.style.display = 'none';
    }

    // Display preview based on file type
    if (file.type === 'image/gif' || file.type.startsWith('video/')) {
      this.displayMediaPreview(file, previewContainer);
    } else {
      this.displayImagePreview(file, previewContainer);
    }
  }

  /**
   * Display actual image preview using Object URL for better performance
   */
  displayImagePreview(file, previewContainer) {
    // Revoke old object URL if exists (memory management)
    if (this.state.currentObjectUrl) {
      URL.revokeObjectURL(this.state.currentObjectUrl);
    }

    // Create new object URL (more efficient than FileReader for images)
    const objectUrl = URL.createObjectURL(file);
    this.state.currentObjectUrl = objectUrl;

    const img = document.createElement('img');
    img.src = objectUrl;
    img.alt = 'Preview';
    img.style.cssText = 'width: 100%; height: 100%; object-fit: cover; border-radius: var(--radius-lg);';
    
    img.onload = () => {
      previewContainer.innerHTML = '';
      previewContainer.appendChild(img);
      this.addRemoveButton(previewContainer);
    };

    img.onerror = () => {
      this.showError('Failed to load image preview');
      this.removePreview();
    };
  }

  /**
   * Display GIF/Video preview with media icon and filename
   */
  displayMediaPreview(file, previewContainer) {
    const mediaType = file.type === 'image/gif' ? 'GIF' : 'Video';
    const fileName = file.name;

    previewContainer.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; width: 100%; height: 100%;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px; color: var(--color-primary);">
          <polygon points="23 7 16 12 23 17 23 7"></polygon>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
        </svg>
        <div style="text-align: center;">
          <div style="font-size: var(--font-size-sm); font-weight: 500; color: var(--text-primary);">${mediaType}</div>
          <div style="font-size: var(--font-size-xs); color: var(--text-tertiary); word-break: break-all; max-width: 200px; margin-top: 4px;">${fileName}</div>
        </div>
      </div>
    `;

    this.addRemoveButton(previewContainer);
  }

  /**
   * Add remove/replace button to preview
   */
  addRemoveButton(previewContainer) {
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
      position: absolute;
      top: 8px;
      right: 8px;
      display: flex;
      gap: 8px;
    `;

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.innerHTML = '✕';
    removeBtn.style.cssText = `
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: none;
      background: rgba(0, 0, 0, 0.6);
      color: white;
      cursor: pointer;
      font-size: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    `;

    removeBtn.onmouseover = () => removeBtn.style.background = 'rgba(0, 0, 0, 0.8)';
    removeBtn.onmouseout = () => removeBtn.style.background = 'rgba(0, 0, 0, 0.6)';
    removeBtn.onclick = (e) => {
      e.preventDefault();
      this.removePreview();
    };

    buttonContainer.appendChild(removeBtn);
    previewContainer.style.position = 'relative';
    previewContainer.appendChild(buttonContainer);
  }

  /**
   * Remove preview and reset state
   */
  removePreview() {
    const previewContainer = document.getElementById(this.config.previewContainerId);
    const uploadDefault = document.getElementById(this.config.uploadDefaultId);
    const fileInput = document.getElementById(this.config.fileInputId);

    // Clear preview
    if (previewContainer) {
      previewContainer.innerHTML = '';
      previewContainer.style.position = 'relative';
    }

    // Show upload default
    if (uploadDefault) {
      uploadDefault.style.display = '';
    }

    // Reset file input
    if (fileInput) {
      fileInput.value = '';
    }

    // Clean up object URL (memory management)
    if (this.state.currentObjectUrl) {
      URL.revokeObjectURL(this.state.currentObjectUrl);
      this.state.currentObjectUrl = null;
    }

    // Clear state
    this.state.currentFile = null;
    if (window.formState) {
      window.formState.imageFile = null;
    }
  }

  /**
   * Reset file input
   */
  resetFileInput() {
    const fileInput = document.getElementById(this.config.fileInputId);
    if (fileInput) {
      fileInput.value = '';
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    console.error('[FilePreview]', message);
    
    // Use existing toast system if available
    if (window.Toast) {
      window.Toast.error(message);
    } else {
      alert(message);
    }
  }

  /**
   * Get current file
   */
  getFile() {
    return this.state.currentFile;
  }

  /**
   * Cleanup and destroy
   */
  destroy() {
    const fileInput = document.getElementById(this.config.fileInputId);
    if (fileInput) {
      fileInput.removeEventListener('change', this.handleFileSelect);
    }

    // Clean up object URL
    if (this.state.currentObjectUrl) {
      URL.revokeObjectURL(this.state.currentObjectUrl);
    }
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FilePreviewManager;
}
