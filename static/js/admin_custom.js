/**
 * ShopKart Pro - Executive Admin Suite Enhancements
 * Provides instant image previews, tab memory, Ctrl+S save shortcuts,
 * visual delete indicators, and real-time color syncing.
 */

document.addEventListener('DOMContentLoaded', function () {
  initTabPersistence();
  initInstantImagePreviews();
  initSaveShortcut();
  initDeleteCheckboxes();
  initColorPickers();
  initUnsavedChangesTracker();
  initStructuredImageUploader();
  initOrderFulfillmentStudio();
  initProductMediaMerchandisingUI();
});


/**
 * 1. Tab Memory (Remembers which tab was active across saves)
 */
function initTabPersistence() {
  const tabs = document.querySelectorAll('#jazzy-tabs .nav-link, .nav-tabs .nav-link');
  if (!tabs.length) return;

  const storageKey = 'shopkart_admin_tab_' + window.location.pathname;
  const savedTab = sessionStorage.getItem(storageKey);

  if (savedTab) {
    const targetTab = Array.from(tabs).find(t => t.getAttribute('href') === savedTab);
    if (targetTab && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
      const tabTrigger = new bootstrap.Tab(targetTab);
      tabTrigger.show();
    } else if (targetTab) {
      targetTab.click();
    }
  }

  tabs.forEach(tab => {
    tab.addEventListener('shown.bs.tab', function (e) {
      const href = e.target.getAttribute('href');
      if (href) sessionStorage.setItem(storageKey, href);
    });
    tab.addEventListener('click', function (e) {
      const href = e.target.getAttribute('href');
      if (href) sessionStorage.setItem(storageKey, href);
    });
  });
}

/**
 * 2. Instant Image Previews for File Uploads
 */
function initInstantImagePreviews() {
  document.addEventListener('change', function (e) {
    if (e.target.matches('input[type="file"]')) {
      const input = e.target;
      if (!input.files || !input.files[0]) return;

      const file = input.files[0];
      if (!file.type.startsWith('image/')) return;

      let previewContainer = input.parentElement.querySelector('.admin-instant-preview');
      if (!previewContainer) {
        previewContainer = document.createElement('div');
        previewContainer.className = 'admin-instant-preview';
        previewContainer.style.cssText = 'display: inline-flex; align-items: center; gap: 10px; margin-top: 8px; padding: 6px 12px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;';
        input.parentElement.appendChild(previewContainer);
      }

      const reader = new FileReader();
      reader.onload = function (event) {
        previewContainer.innerHTML = `
          <img src="${event.target.result}" style="width: 48px; height: 48px; object-fit: contain; border-radius: 8px; border: 1px solid #86efac; background: #ffffff; padding: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);" />
          <div>
            <div style="font-size: 11px; font-weight: 700; color: #166534; display: flex; align-items: center; gap: 4px;">
              <i class="fas fa-check-circle" style="color: #22c55e;"></i> New Photo Ready
            </div>
            <div style="font-size: 11px; color: #4b5563; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              ${file.name} (${Math.round(file.size / 1024)} KB)
            </div>
          </div>
        `;
      };
      reader.readAsDataURL(file);
    }
  });
}

/**
 * 3. Ctrl+S / Cmd+S Quick Save Shortcut
 */
function initSaveShortcut() {
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      const form = document.querySelector('form#change-form, form#product_form, form.changeform, form');
      if (!form) return;

      e.preventDefault();

      // Show toast
      showAdminToast('💾 Saving changes...', 'brand');

      // Click "Save and continue editing" if available, else standard save
      const saveAndContinueBtn = form.querySelector('input[name="_continue"], button[name="_continue"]');
      const saveBtn = form.querySelector('input[type="submit"], button[type="submit"]');

      if (saveAndContinueBtn) {
        saveAndContinueBtn.click();
      } else if (saveBtn) {
        saveBtn.click();
      } else {
        form.submit();
      }
    }
  });
}

/**
 * 4. Visual Feedback for Delete Checkboxes in Inlines
 */
function initDeleteCheckboxes() {
  function updateDeleteState(checkbox) {
    const parentRow = checkbox.closest('.inline-related, tr, .card');
    if (!parentRow) return;

    if (checkbox.checked) {
      parentRow.style.transition = 'all 0.2s ease';
      parentRow.style.opacity = '0.45';
      parentRow.style.filter = 'grayscale(1)';
      parentRow.style.background = '#fef2f2';
      parentRow.style.border = '1px dashed #f87171';
    } else {
      parentRow.style.opacity = '1';
      parentRow.style.filter = 'none';
      parentRow.style.background = '';
      parentRow.style.border = '';
    }
  }

  document.addEventListener('change', function (e) {
    if (e.target.matches('input[type="checkbox"][name$="-DELETE"]')) {
      updateDeleteState(e.target);
    }
  });

  // Run once on load for pre-checked
  document.querySelectorAll('input[type="checkbox"][name$="-DELETE"]').forEach(updateDeleteState);
}

/**
 * 5. Color Picker Real-time Visual Swatch Synchronization
 */
function initColorPickers() {
  document.addEventListener('input', function (e) {
    if (e.target.matches('input[type="color"]')) {
      const picker = e.target;
      const parent = picker.closest('.inline-related, fieldset, tr, .form-row, .card-body');
      if (!parent) return;

      const hexInput = parent.querySelector('input[name$="color_code"]');
      if (hexInput) {
        hexInput.value = picker.value;
      }

      // Update swatch circle if present
      const swatchCircle = parent.querySelector('.color-swatch-circle');
      if (swatchCircle) {
        swatchCircle.style.backgroundColor = picker.value;
      }
    }

    if (e.target.matches('input[name$="color_code"]')) {
      const hexInput = e.target;
      let val = hexInput.value.trim();
      if (!val.startsWith('#') && val.length > 0) val = '#' + val;
      if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
        const parent = hexInput.closest('.inline-related, fieldset, tr, .form-row, .card-body');
        if (parent) {
          const picker = parent.querySelector('input[type="color"]');
          if (picker) picker.value = val;
        }
      }
    }
  });
}

/**
 * 6. Form Unsaved Changes Indicator
 */
function initUnsavedChangesTracker() {
  const form = document.querySelector('form#change-form, form#product_form, form.changeform');
  if (!form) return;

  let hasChanges = false;
  const saveButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');

  form.addEventListener('change', function () {
    if (!hasChanges) {
      hasChanges = true;
      saveButtons.forEach(btn => {
        if (btn.name === '_continue' || btn.classList.contains('btn-primary')) {
          btn.style.boxShadow = '0 0 0 3px rgba(255, 96, 0, 0.4), 0 4px 14px rgba(255, 96, 0, 0.4)';
        }
      });
    }
  });
}

/**
 * Toast Notification Helper
 */
function showAdminToast(message, type = 'brand') {
  let toast = document.getElementById('admin-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'admin-toast';
    toast.style.cssText = 'position: fixed; bottom: 85px; right: 28px; z-index: 99999; padding: 12px 20px; border-radius: 12px; font-weight: 700; font-size: 13.5px; display: flex; align-items: center; gap: 10px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.25); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); transform: translateY(20px); opacity: 0; pointer-events: none;';
    document.body.appendChild(toast);
  }

  toast.style.background = '#0f172a';
  toast.style.color = '#ffffff';
  toast.style.border = '1px solid #ff6000';
  toast.innerHTML = `<span style="color: #ff8c42;">${message}</span>`;
  toast.style.transform = 'translateY(0)';
  toast.style.opacity = '1';

  setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
  }, 2200);
}

/**
 * 7. Structured Image Uploader (Thumbnail Dropzone & Gallery Cards Grid)
 * Matches user-uploaded reference design with drag-and-drop, multi-file support,
 * instant live preview cards, and one-click deletion with undo.
 */
function initStructuredImageUploader() {
  initThumbnailDropzone();
  initGalleryDropzoneGrid();
}

/**
 * 7A. Main Product Thumbnail Dropzone & Preview Card
 */
function initThumbnailDropzone() {
  const dropzones = document.querySelectorAll('.shopkart-dropzone-card.thumbnail-dropzone');
  if (!dropzones.length) return;

  dropzones.forEach(dropzone => {
    const fileInput = dropzone.querySelector('input[type="file"].thumbnail-file-input');
    if (!fileInput) return;

    const inputId = fileInput.id;

    // Drag-and-drop visual states
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'dragend'].forEach(eventName => {
      dropzone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      });
    });

    // Handle dropped file
    dropzone.addEventListener('drop', function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');

      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        const file = e.dataTransfer.files[0];
        if (file.type.startsWith('image/')) {
          try {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
          } catch (err) {
            console.error('DataTransfer error:', err);
          }
        } else {
          showAdminToast('⚠️ Please drop a valid image file (PNG, JPG, WEBP, GIF).', 'brand');
        }
      }
    });

    // File input change -> Instant live preview
    fileInput.addEventListener('change', function () {
      if (!fileInput.files || !fileInput.files[0]) return;
      const file = fileInput.files[0];
      if (!file.type.startsWith('image/')) return;

      const previewImg = document.getElementById(`img_preview_${inputId}`);
      const emptyPlaceholder = document.getElementById(`empty_placeholder_${inputId}`);
      const newBadge = document.getElementById(`badge_new_${inputId}`);
      const filenameLabel = document.getElementById(`label_filename_${inputId}`);
      const clearOverlay = document.getElementById(`clear_overlay_${inputId}`);
      const clearCheckbox = document.querySelector(`.thumbnail-clear-checkbox`);

      const reader = new FileReader();
      reader.onload = function (evt) {
        if (previewImg) {
          previewImg.src = evt.target.result;
          previewImg.style.display = 'block';
        }
        if (emptyPlaceholder) emptyPlaceholder.style.display = 'none';
        if (newBadge) newBadge.style.display = 'inline-flex';
        if (filenameLabel) {
          filenameLabel.textContent = file.name;
          filenameLabel.title = file.name;
        }
        if (clearOverlay) clearOverlay.style.display = 'none';
        if (clearCheckbox) clearCheckbox.checked = false;

        showAdminToast('📸 Thumbnail updated live! Save to apply.', 'brand');
      };
      reader.readAsDataURL(file);
    });
  });

  // Clear Checkbox / Trash toggle
  document.addEventListener('change', function (e) {
    if (e.target.matches('.thumbnail-clear-checkbox')) {
      const checkbox = e.target;
      const parentCard = checkbox.closest('.thumbnail-preview-card');
      if (!parentCard) return;
      const overlay = parentCard.querySelector('.card-deleted-overlay');
      if (overlay) {
        if (checkbox.checked) {
          overlay.classList.add('is-active', 'active', 'show');
          overlay.style.setProperty('display', 'flex', 'important');
        } else {
          overlay.classList.remove('is-active', 'active', 'show');
          overlay.style.setProperty('display', 'none', 'important');
        }
      }
    }
  });

  // Undo Thumbnail Clear button
  document.addEventListener('click', function (e) {
    const undoBtn = e.target.closest('.btn-undo-thumbnail-clear');
    if (!undoBtn) return;
    const parentCard = undoBtn.closest('.thumbnail-preview-card');
    if (!parentCard) return;
    const checkbox = parentCard.querySelector('.thumbnail-clear-checkbox');
    if (checkbox) checkbox.checked = false;
    const overlay = parentCard.querySelector('.card-deleted-overlay');
    if (overlay) {
      overlay.classList.remove('is-active', 'active', 'show');
      overlay.style.setProperty('display', 'none', 'important');
    }
  });
}

/**
 * 7B. Extra Product Images - Gallery Cards Grid & Dropzone
 */
function initGalleryDropzoneGrid() {
  const dropzone = document.getElementById('gallery_primary_dropzone');
  const multiInput = document.getElementById('gallery_multi_file_input');
  if (!dropzone || !multiInput) return;

  // Drag and drop states on Gallery Dropzone
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-over');
    });
  });

  ['dragleave', 'dragend'].forEach(eventName => {
    dropzone.addEventListener(eventName, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');
    });
  });

  // Handle dropped files onto Gallery Dropzone
  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
      handleGalleryFiles(e.dataTransfer.files);
    }
  });

  // Handle multi-file selection via file picker
  multiInput.addEventListener('change', function (e) {
    if (multiInput.files && multiInput.files.length) {
      handleGalleryFiles(multiInput.files);
      multiInput.value = ''; // Reset for next selection
    }
  });

  // Multi-file handler function
  function handleGalleryFiles(files) {
    const totalFormsInput = document.getElementById('id_gallery-TOTAL_FORMS');
    if (!totalFormsInput) return;

    const dynamicContainer = document.getElementById('gallery_dynamic_cards_container');
    const hiddenContainer = document.getElementById('gallery_hidden_forms_container');
    if (!dynamicContainer || !hiddenContainer) return;

    let addedCount = 0;

    Array.from(files).forEach(file => {
      if (!file.type.startsWith('image/')) return;

      const idx = parseInt(totalFormsInput.value, 10);
      totalFormsInput.value = idx + 1;

      // 1. Create real hidden file input for Django formset
      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'file';
      hiddenInput.name = `gallery-${idx}-image`;
      hiddenInput.id = `id_gallery-${idx}-image`;
      hiddenInput.style.display = 'none';

      try {
        const dt = new DataTransfer();
        dt.items.add(file);
        hiddenInput.files = dt.files;
        hiddenContainer.appendChild(hiddenInput);
      } catch (err) {
        console.error('DataTransfer assignment error:', err);
      }

      // 2. Create preview card in grid
      const card = document.createElement('div');
      card.className = 'shopkart-preview-card gallery-image-card gallery-dynamic-card';
      card.id = `gallery_dynamic_card_${idx}`;
      card.dataset.formIndex = idx;
      card.style.cssText = 'min-height: 235px; border-radius: 18px; border: 1px solid #86efac; background: #ffffff; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.12); display: flex; flex-direction: column; overflow: hidden; position: relative; transition: all 0.2s ease;';

      const objectUrl = URL.createObjectURL(file);
      card.innerHTML = `
        <div style="position: absolute; top: 10px; left: 10px; right: 10px; display: flex; align-items: center; justify-content: space-between; z-index: 4;">
          <span class="badge" style="background: #16a34a; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 6px; padding: 3px 7px;">
            <i class="fas fa-check" style="margin-right: 3px;"></i> Ready
          </span>
          <button type="button" class="card-dynamic-remove-btn" data-form-index="${idx}" title="Remove photo">
            <i class="fas fa-times" style="font-size: 12px;"></i>
          </button>
        </div>
        <div class="card-image-wrapper" style="flex: 1; min-height: 165px; background: #f0fdf4; display: flex; align-items: center; justify-content: center; padding: 10px; position: relative;">
          <img src="${objectUrl}" alt="${file.name}" class="preview-img" style="max-width: 100%; max-height: 155px; object-fit: contain; border-radius: 12px;" />
        </div>
        <div class="card-footer-info" style="padding: 8px 12px; background: #ffffff; border-top: 1px solid #dcfce7; display: flex; align-items: center; justify-content: space-between;">
          <span class="card-filename" style="font-size: 11px; font-weight: 600; color: #166534; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${file.name}">
            ${file.name}
          </span>
          <span style="font-size: 10.5px; font-weight: 600; color: #22c55e;">
            ${Math.round(file.size / 1024)} KB
          </span>
        </div>
      `;

      dynamicContainer.appendChild(card);
      addedCount++;
    });

    if (addedCount > 0) {
      updateGalleryCountBadge();
      showAdminToast(`📸 Added ${addedCount} gallery photo(s)! Save to confirm.`, 'brand');
    }
  }

  // Sync existing gallery cards initial state with checkbox states on page load
  const existingCards = document.querySelectorAll('.gallery-image-card:not(.gallery-dynamic-card)');
  existingCards.forEach(c => {
    const trashBtn = c.querySelector('.btn-gallery-trash');
    const deleteId = trashBtn ? trashBtn.dataset.deleteId : null;
    const checkbox = deleteId ? document.getElementById(deleteId) : null;
    const overlay = c.querySelector('.gallery-deleted-overlay');
    if (checkbox && checkbox.checked) {
      if (overlay) {
        overlay.classList.add('is-active', 'active', 'show');
        overlay.style.setProperty('display', 'flex', 'important');
      }
    } else {
      if (overlay) {
        overlay.classList.remove('is-active', 'active', 'show');
        overlay.style.setProperty('display', 'none', 'important');
      }
    }
  });
  updateGalleryCountBadge();

  // Remove dynamically added photo card
  document.addEventListener('click', function (e) {
    const removeBtn = e.target.closest('.card-dynamic-remove-btn');
    if (!removeBtn) return;
    const idx = removeBtn.dataset.formIndex;
    const card = document.getElementById(`gallery_dynamic_card_${idx}`);
    if (card) card.remove();
    const hiddenInput = document.getElementById(`id_gallery-${idx}-image`) || document.querySelector(`input[name$="-${idx}-image"]`);
    if (hiddenInput) {
      hiddenInput.remove();
    }
    updateGalleryCountBadge();
  });

  // Delete existing gallery card via trash button
  document.addEventListener('click', function (e) {
    const trashBtn = e.target.closest('.btn-gallery-trash');
    if (!trashBtn) return;
    const deleteId = trashBtn.dataset.deleteId;
    const cardIndex = trashBtn.dataset.cardIndex;
    const checkbox = document.getElementById(deleteId);
    if (checkbox) checkbox.checked = true;
    const overlay = document.getElementById(`gallery_del_overlay_${cardIndex}`);
    if (overlay) {
      overlay.classList.add('is-active', 'active', 'show');
      overlay.style.setProperty('display', 'flex', 'important');
    }
    updateGalleryCountBadge();
  });

  // Undo deletion of existing gallery card
  document.addEventListener('click', function (e) {
    const undoBtn = e.target.closest('.btn-gallery-undo');
    if (!undoBtn) return;
    const deleteId = undoBtn.dataset.deleteId;
    const cardIndex = undoBtn.dataset.cardIndex;
    const checkbox = document.getElementById(deleteId);
    if (checkbox) checkbox.checked = false;
    const overlay = document.getElementById(`gallery_del_overlay_${cardIndex}`);
    if (overlay) {
      overlay.classList.remove('is-active', 'active', 'show');
      overlay.style.setProperty('display', 'none', 'important');
    }
    updateGalleryCountBadge();
  });

  // Helper to update counter badge
  function updateGalleryCountBadge() {
    const countBadge = document.getElementById('gallery_images_count');
    if (!countBadge) return;
    const existingCards = document.querySelectorAll('.gallery-image-card:not(.gallery-dynamic-card)');
    let activeExistingCount = 0;
    existingCards.forEach(c => {
      const trashBtn = c.querySelector('.btn-gallery-trash');
      const deleteId = trashBtn ? trashBtn.dataset.deleteId : null;
      const checkbox = deleteId ? document.getElementById(deleteId) : null;
      const overlay = c.querySelector('.gallery-deleted-overlay');
      const isDeleted = (checkbox && checkbox.checked) || (overlay && (
        overlay.classList.contains('is-active') ||
        overlay.classList.contains('active') ||
        overlay.style.display === 'flex'
      ));
      if (!isDeleted) {
        activeExistingCount++;
      }
    });
    const dynamicCards = document.querySelectorAll('.gallery-dynamic-card');
    countBadge.textContent = activeExistingCount + dynamicCards.length;
  }
}

/**
 * 8. Order Fulfillment Studio Enhancements
 */
function initOrderFulfillmentStudio() {
  // Tracking number copy buttons
  document.addEventListener('click', function (e) {
    const copyBtn = e.target.closest('.btn-copy-tracking');
    if (!copyBtn) return;
    const tracking = copyBtn.dataset.tracking;
    if (!tracking) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(tracking).then(() => {
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check" style="color: #16a34a;"></i> Copied!';
        setTimeout(() => {
          copyBtn.innerHTML = originalHtml;
        }, 2000);
      });
    } else {
      prompt('Copy Tracking Number:', tracking);
    }
  });
}

/**
 * 9. Product Media & Merchandising Interactive Studio
 * (Exact Match to media_1788691746590.jpg)
 */
function initProductMediaMerchandisingUI() {
  const rootCard = document.querySelector('.product-media-merchandising-card');
  if (!rootCard) return;

  const fileInput = document.getElementById('id_product_image');
  const dropzone = document.getElementById('pmm-dropzone');
  const previewFrame = document.getElementById('pmm-preview-frame');
  const previewImg = document.getElementById('product-main-preview-img');
  const emptyPlaceholder = document.getElementById('pmm-empty-placeholder');
  const expandBtn = document.getElementById('pmm-expand-btn');
  const changeBtn = document.getElementById('btn-pmm-change-image');
  const fileInfoWrap = document.getElementById('pmm-new-file-info');
  const fileNameLabel = document.getElementById('pmm-new-file-name');

  const lightboxModal = document.getElementById('pmm-lightbox-modal');
  const lightboxImg = document.getElementById('pmm-lightbox-img');
  const lightboxBackdrop = document.getElementById('pmm-lightbox-backdrop');
  const lightboxClose = document.getElementById('pmm-lightbox-close');

  // Helper to update preview from File
  function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      if (previewImg) {
        previewImg.src = e.target.result;
        previewImg.style.display = 'block';
      }
      if (lightboxImg) {
        lightboxImg.src = e.target.result;
      }
      if (emptyPlaceholder) {
        emptyPlaceholder.style.display = 'none';
      }
      if (expandBtn) {
        expandBtn.style.display = 'flex';
      }
      if (fileNameLabel) {
        fileNameLabel.textContent = file.name;
      }
      if (fileInfoWrap) {
        fileInfoWrap.style.display = 'flex';
      }
      if (changeBtn) {
        changeBtn.textContent = 'Change Image';
      }

      // Uncheck clear checkbox if present
      const clearCheckbox = document.getElementById('product_image-clear_id');
      if (clearCheckbox) {
        clearCheckbox.checked = false;
      }
    };
    reader.readAsDataURL(file);
  }

  // Trigger input on button click
  if (changeBtn && fileInput) {
    changeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      fileInput.click();
    });
  }

  // Trigger input on dropzone click
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', function (e) {
      if (e.target !== changeBtn) {
        fileInput.click();
      }
    });
  }

  // Native input change listener
  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        handleFileSelect(this.files[0]);
      }
    });
  }

  // Drag & drop on dropzone and preview frame
  const dropTargets = [dropzone, previewFrame].filter(Boolean);
  dropTargets.forEach(target => {
    ['dragenter', 'dragover'].forEach(eventName => {
      target.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (dropzone) dropzone.classList.add('pmm-dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      target.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (dropzone) dropzone.classList.remove('pmm-dragover');
      });
    });

    target.addEventListener('drop', function (e) {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        const file = e.dataTransfer.files[0];
        if (file.type.startsWith('image/')) {
          if (fileInput) {
            fileInput.files = e.dataTransfer.files;
          }
          handleFileSelect(file);
        }
      }
    });
  });

  // Lightbox Modal Handlers
  if (expandBtn && lightboxModal) {
    expandBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      lightboxModal.style.display = 'flex';
    });
  }

  function closeLightbox() {
    if (lightboxModal) {
      lightboxModal.style.display = 'none';
    }
  }

  if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
  if (lightboxBackdrop) lightboxBackdrop.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lightboxModal && lightboxModal.style.display === 'flex') {
      closeLightbox();
    }
  });

  // Merchandising Flags Syncing
  const flags = [
    { inputId: 'id_trending', cardId: 'card_flag_trending', activeClass: 'active-flag-trending' },
    { inputId: 'id_featured', cardId: 'card_flag_featured', activeClass: 'active-flag-featured' },
    { inputId: 'id_is_bestseller', cardId: 'card_flag_is_bestseller', activeClass: 'active-flag-bestseller' },
    { inputId: 'id_ui_new_arrival', cardId: 'card_flag_new_arrival', activeClass: 'active-flag-newarrival' }
  ];

  flags.forEach(f => {
    const input = document.getElementById(f.inputId);
    const card = document.getElementById(f.cardId);
    if (!card) return;

    function syncFlagState() {
      if (input && input.checked) {
        card.classList.add(f.activeClass);
      } else {
        card.classList.remove(f.activeClass);
      }
    }

    if (input) {
      input.addEventListener('change', syncFlagState);
      syncFlagState();
    }

    // Whole card click toggles switch
    card.addEventListener('click', function (e) {
      if (!e.target.closest('.pmm-ios-switch')) {
        if (input) {
          input.checked = !input.checked;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });
  });

  // Product Visibility Syncing (Active Switch)
  const uiActiveSwitch = document.getElementById('ui_toggle_active');
  const realStatusInput = document.getElementById('id_status');
  const visibilityCard = document.getElementById('card_product_visibility');
  const titleText = document.getElementById('pmm-visibility-title-text');
  const descText = document.getElementById('pmm-visibility-desc-text');

  function syncVisibilityState() {
    if (!uiActiveSwitch || !visibilityCard) return;

    const isActive = uiActiveSwitch.checked;
    // In DB: status=False is Active, status=True is Hidden
    if (realStatusInput) {
      realStatusInput.checked = !isActive;
    }

    if (isActive) {
      visibilityCard.classList.add('active-visibility-green');
      if (titleText) titleText.textContent = 'Active';
      if (descText) descText.textContent = 'Product is visible to customers';
    } else {
      visibilityCard.classList.remove('active-visibility-green');
      if (titleText) titleText.textContent = 'Inactive / Draft';
      if (descText) descText.textContent = 'Product is hidden from customers';
    }
  }

  if (uiActiveSwitch) {
    uiActiveSwitch.addEventListener('change', syncVisibilityState);
    syncVisibilityState();
  }

  if (visibilityCard && uiActiveSwitch) {
    visibilityCard.addEventListener('click', function (e) {
      if (!e.target.closest('.pmm-ios-switch')) {
        uiActiveSwitch.checked = !uiActiveSwitch.checked;
        uiActiveSwitch.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  }
}



