/**
 * XeonStorage Uploader with Auth Gimmick & Dual Output Links (Direct & Gallery)
 * Supports Real-Time Upload Speed & Percentage Progress Meter
 */

window.pendingUploadFile = null;

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const dropzoneIdle = document.getElementById('dropzoneIdle');
    const dropzoneLoading = document.getElementById('dropzoneLoading');
    const uploadingFileName = document.getElementById('uploadingFileName');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadProgressText = document.getElementById('uploadProgressText');
    const uploadProgressSize = document.getElementById('uploadProgressSize');
    const uploadProgressSpeed = document.getElementById('uploadProgressSpeed');
    const resultContainer = document.getElementById('resultContainer');
    const directUrl = document.getElementById('directUrl');
    const galleryUrl = document.getElementById('galleryUrl');
    const fileSizeBadge = document.getElementById('fileSizeBadge');
    const openDirectBtn = document.getElementById('openDirectBtn');
    const openGalleryBtn = document.getElementById('openGalleryBtn');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dropzone-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            onFileSelected(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            onFileSelected(fileInput.files[0]);
        }
    });

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function onFileSelected(file) {
        const maxMb = window.maxUploadSizeMb || 1500;
        const maxBytes = maxMb * 1024 * 1024;
        if (file.size > maxBytes) {
            const limitMsg = (window.i18nTexts && window.i18nTexts.sizeLimitError) || `Ukuran berkas melebihi batas maksimum ${maxMb} MB.`;
            alert(limitMsg);
            return;
        }

        // Gimmick: If user is not logged in, hold the file and pop up login modal with notice
        if (!window.isUserLoggedIn) {
            window.pendingUploadFile = file;
            if (typeof openAuthModal === 'function') {
                openAuthModal('login', { notice: true });
            }
            return;
        }

        // User is logged in -> Start upload
        startUpload(file);
    }

    function startUpload(file) {
        window.isUploadingActive = true;
        if (dropzoneIdle) dropzoneIdle.classList.add('hidden');
        if (dropzoneLoading) dropzoneLoading.classList.remove('hidden');
        if (resultContainer) resultContainer.classList.add('hidden');
        if (uploadingFileName) uploadingFileName.textContent = `${file.name}`;
        if (uploadProgressBar) uploadProgressBar.style.width = '0%';
        if (uploadProgressText) uploadProgressText.textContent = '0%';
        if (uploadProgressSize) uploadProgressSize.textContent = `0 B / ${formatBytes(file.size)}`;
        if (uploadProgressSpeed) uploadProgressSpeed.textContent = '0 KB/s';

        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        let startTime = Date.now();
        let lastTime = startTime;
        let lastLoaded = 0;

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const now = Date.now();
                const timeDelta = (now - lastTime) / 1000;

                if (uploadProgressBar) uploadProgressBar.style.width = `${percent}%`;
                if (uploadProgressText) uploadProgressText.textContent = `${percent}%`;
                if (uploadProgressSize) uploadProgressSize.textContent = `${formatBytes(e.loaded)} / ${formatBytes(e.total)}`;

                if (timeDelta >= 0.25 || e.loaded === e.total) {
                    const bytesDelta = e.loaded - lastLoaded;
                    const speed = timeDelta > 0 ? bytesDelta / timeDelta : 0;
                    if (uploadProgressSpeed && speed > 0) {
                        uploadProgressSpeed.textContent = `${formatBytes(speed)}/s`;
                    }
                    lastLoaded = e.loaded;
                    lastTime = now;
                }
            }
        };

        xhr.onload = () => {
            window.isUploadingActive = false;
            if (dropzoneIdle) dropzoneIdle.classList.remove('hidden');
            if (dropzoneLoading) dropzoneLoading.classList.add('hidden');

            if (xhr.status === 200) {
                try {
                    const res = JSON.parse(xhr.responseText);
                    if (res.success && res.data) {
                        const d = res.data;
                        if (directUrl) directUrl.value = d.direct_url || d.url;
                        if (galleryUrl) galleryUrl.value = d.gallery_url || `/v/${d.id}`;
                        if (fileSizeBadge) fileSizeBadge.textContent = formatBytes(d.size);
                        if (openDirectBtn) openDirectBtn.href = d.direct_url || d.url;
                        if (openGalleryBtn) openGalleryBtn.href = d.gallery_url || `/v/${d.id}`;
                        if (resultContainer) {
                            resultContainer.classList.remove('hidden');
                            if (directUrl) directUrl.select();
                        }
                    } else {
                        alert(res.error || 'Upload error');
                    }
                } catch (e) {
                    alert('Error parsing server response.');
                }
            } else if (xhr.status === 401) {
                // Not authenticated
                window.pendingUploadFile = file;
                if (typeof openAuthModal === 'function') {
                    openAuthModal('login');
                }
            } else {
                try {
                    const res = JSON.parse(xhr.responseText);
                    alert(res.error || 'Upload failed with status ' + xhr.status);
                } catch (e) {
                    alert('Upload failed with status ' + xhr.status);
                }
            }
        };

        xhr.onerror = () => {
            window.isUploadingActive = false;
            if (dropzoneIdle) dropzoneIdle.classList.remove('hidden');
            if (dropzoneLoading) dropzoneLoading.classList.add('hidden');
            alert('Network error while uploading.');
        };

        xhr.onabort = () => {
            window.isUploadingActive = false;
            if (dropzoneIdle) dropzoneIdle.classList.remove('hidden');
            if (dropzoneLoading) dropzoneLoading.classList.add('hidden');
        };

        xhr.send(formData);
    }

    // Protection against accidental page reload / exit during active upload (Like Canva / Google Drive)
    window.addEventListener('beforeunload', (e) => {
        if (window.isUploadingActive) {
            e.preventDefault();
            const warning = (window.i18nTexts && window.i18nTexts.uploadWarning) || 'Proses unggah berkas sedang berlangsung! Jika Anda keluar atau memuat ulang halaman sekarang, unggahan akan dibatalkan dan berkas tidak akan tersimpan.';
            e.returnValue = warning;
            return warning;
        }
    });

    // Expose startUpload for pending file after login
    window.startPendingUpload = startUpload;
});

function copyDirectUrl() {
    const directUrl = document.getElementById('directUrl');
    const copyDirectBtnText = document.getElementById('copyDirectBtnText');
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Copied!';
    const strCopy = (window.i18nTexts && window.i18nTexts.copyKey) || 'Copy';

    if (!directUrl || !directUrl.value) return;
    navigator.clipboard.writeText(directUrl.value).then(() => {
        if (copyDirectBtnText) copyDirectBtnText.textContent = strCopied;
        setTimeout(() => {
            if (copyDirectBtnText) copyDirectBtnText.textContent = strCopy;
        }, 2000);
    });
}

function copyGalleryUrl() {
    const galleryUrl = document.getElementById('galleryUrl');
    const copyGalleryBtnText = document.getElementById('copyGalleryBtnText');
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Copied!';
    const strCopy = (window.i18nTexts && window.i18nTexts.copyKey) || 'Copy';

    if (!galleryUrl || !galleryUrl.value) return;
    navigator.clipboard.writeText(galleryUrl.value).then(() => {
        if (copyGalleryBtnText) copyGalleryBtnText.textContent = strCopied;
        setTimeout(() => {
            if (copyGalleryBtnText) copyGalleryBtnText.textContent = strCopy;
        }, 2000);
    });
}

// Mobile QR Modal Logic for Homepage
function openIndexQrModal(type) {
    const modal = document.getElementById('indexQrModal');
    const qrImg = document.getElementById('indexQrImage');
    const urlDisplay = document.getElementById('indexQrUrlDisplay');
    const typeLabel = document.getElementById('indexQrTypeLabel');
    if (!modal || !qrImg) return;

    let targetUrl = '';
    if (type === 'gallery') {
        const galEl = document.getElementById('galleryUrl');
        targetUrl = galEl ? galEl.value : '';
        if (typeLabel) typeLabel.textContent = 'Gallery URL';
    } else {
        const dirEl = document.getElementById('directUrl');
        targetUrl = dirEl ? dirEl.value : '';
        if (typeLabel) typeLabel.textContent = 'Direct Hotlink URL';
    }

    if (!targetUrl) return;

    const encoded = encodeURIComponent(targetUrl);
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encoded}&color=0f172a`;
    if (urlDisplay) urlDisplay.value = targetUrl;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeIndexQrModal() {
    const modal = document.getElementById('indexQrModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    document.body.style.overflow = '';
}

function copyIndexQrUrl(btn) {
    const urlDisplay = document.getElementById('indexQrUrlDisplay');
    if (!urlDisplay || !urlDisplay.value) return;
    const originalText = btn.innerHTML;
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Copied!';

    navigator.clipboard.writeText(urlDisplay.value).then(() => {
        btn.innerHTML = `<svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"></path></svg><span>${strCopied}</span>`;
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    });
}

function resetUploadCard() {
    const resultContainer = document.getElementById('resultContainer');
    const fileInput = document.getElementById('fileInput');
    const dropzoneIdle = document.getElementById('dropzoneIdle');
    if (resultContainer) resultContainer.classList.add('hidden');
    if (dropzoneIdle) dropzoneIdle.classList.remove('hidden');
    if (fileInput) fileInput.value = '';
}

// Close QR modal on click outside and escape
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('indexQrModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeIndexQrModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closeIndexQrModal();
            }
        });
    }
});

