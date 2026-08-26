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
        const maxBytes = 40 * 1024 * 1024;
        if (file.size > maxBytes) {
            const limitMsg = (window.i18nTexts && window.i18nTexts.sizeLimitError) || 'Ukuran berkas melebihi batas maksimum 40 MB.';
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
            if (dropzoneIdle) dropzoneIdle.classList.remove('hidden');
            if (dropzoneLoading) dropzoneLoading.classList.add('hidden');
            alert('Network error while uploading.');
        };

        xhr.send(formData);
    }

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
