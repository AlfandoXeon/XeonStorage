/**
 * XeonStorage Dashboard JavaScript
 * Handles Dropzone Upload with Real-Time Speed & Progress Indicators, API Key Management, and File Details Modal Window
 */

let shouldReloadOnModalClose = false;

document.addEventListener('DOMContentLoaded', () => {
    const dashDropzone = document.getElementById('dashDropzone');
    const dashFileInput = document.getElementById('dashFileInput');
    const dashIdle = document.getElementById('dashIdle');
    const dashLoading = document.getElementById('dashLoading');
    const dashUploadStatus = document.getElementById('dashUploadStatus');
    const dashProgressBar = document.getElementById('dashProgressBar');
    const dashProgressPercent = document.getElementById('dashProgressPercent');
    const dashProgressSize = document.getElementById('dashProgressSize');
    const dashProgressSpeed = document.getElementById('dashProgressSpeed');
    const fileDetailModal = document.getElementById('fileDetailModal');

    if (dashDropzone && dashFileInput) {
        dashDropzone.addEventListener('click', () => dashFileInput.click());

        ['dragenter', 'dragover'].forEach(name => {
            dashDropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dashDropzone.classList.add('dropzone-active');
            });
        });

        ['dragleave', 'drop'].forEach(name => {
            dashDropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dashDropzone.classList.remove('dropzone-active');
            });
        });

        dashDropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files.length > 0) {
                handleDashUpload(e.dataTransfer.files[0]);
            }
        });

        dashFileInput.addEventListener('change', (e) => {
            if (dashFileInput.files.length > 0) {
                handleDashUpload(dashFileInput.files[0]);
            }
        });
    }

    // Modal click-outside & Escape key handlers
    if (fileDetailModal) {
        fileDetailModal.addEventListener('click', (e) => {
            if (e.target === fileDetailModal) closeFileModal();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !fileDetailModal.classList.contains('hidden')) {
                closeFileModal();
            }
        });
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function handleDashUpload(file) {
        const maxMb = window.maxUploadSizeMb || 1500;
        const maxBytes = maxMb * 1024 * 1024;
        if (file.size > maxBytes) {
            const limitMsg = (window.i18nTexts && window.i18nTexts.sizeLimitError) || `Ukuran berkas melebihi batas maksimum ${maxMb} MB.`;
            alert(limitMsg);
            return;
        }

        if (dashIdle) dashIdle.classList.add('hidden');
        if (dashLoading) dashLoading.classList.remove('hidden');
        if (dashUploadStatus) dashUploadStatus.textContent = `${file.name}`;
        if (dashProgressBar) dashProgressBar.style.width = '0%';
        if (dashProgressPercent) dashProgressPercent.textContent = '0%';
        if (dashProgressSize) dashProgressSize.textContent = `0 B / ${formatBytes(file.size)}`;
        if (dashProgressSpeed) dashProgressSpeed.textContent = '0 KB/s';

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

                if (dashProgressBar) dashProgressBar.style.width = `${percent}%`;
                if (dashProgressPercent) dashProgressPercent.textContent = `${percent}%`;
                if (dashProgressSize) dashProgressSize.textContent = `${formatBytes(e.loaded)} / ${formatBytes(e.total)}`;

                if (timeDelta >= 0.25 || e.loaded === e.total) {
                    const bytesDelta = e.loaded - lastLoaded;
                    const speed = timeDelta > 0 ? bytesDelta / timeDelta : 0;
                    if (dashProgressSpeed && speed > 0) {
                        dashProgressSpeed.textContent = `${formatBytes(speed)}/s`;
                    }
                    lastLoaded = e.loaded;
                    lastTime = now;
                }
            }
        };

        xhr.onload = () => {
            if (dashIdle) dashIdle.classList.remove('hidden');
            if (dashLoading) dashLoading.classList.add('hidden');

            if (xhr.status === 200) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.success && data.data) {
                        // Upload completed -> Pop up details window immediately!
                        shouldReloadOnModalClose = true;
                        showFileModal({
                            id: data.data.id,
                            name: data.data.name,
                            size: data.data.size,
                            mime_type: data.data.mime_type,
                            created_at: new Date().toISOString().slice(0, 10),
                            direct_url: data.data.direct_url || data.data.url,
                            gallery_url: data.data.gallery_url || `/v/${data.data.id}`
                        });
                    } else {
                        alert(data.error || 'Upload failed');
                    }
                } catch (e) {
                    alert('Error parsing server response.');
                }
            } else {
                try {
                    const data = JSON.parse(xhr.responseText);
                    alert(data.error || 'Upload failed with status ' + xhr.status);
                } catch (e) {
                    alert('Upload failed with status ' + xhr.status);
                }
            }
        };

        xhr.onerror = () => {
            if (dashIdle) dashIdle.classList.remove('hidden');
            if (dashLoading) dashLoading.classList.add('hidden');
            alert('Network error while uploading file.');
        };

        xhr.send(formData);
    }
});

function showFileModal(fileData) {
    const fileDetailModal = document.getElementById('fileDetailModal');
    if (!fileDetailModal || !fileData) return;

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    const modalFileName = document.getElementById('modalFileName');
    const modalPropSize = document.getElementById('modalPropSize');
    const modalPropMime = document.getElementById('modalPropMime');
    const modalPropId = document.getElementById('modalPropId');
    const modalPropDate = document.getElementById('modalPropDate');
    const modalDirectUrlInput = document.getElementById('modalDirectUrlInput');
    const modalGalleryUrlInput = document.getElementById('modalGalleryUrlInput');
    const modalOpenDirectBtn = document.getElementById('modalOpenDirectBtn');
    const modalOpenGalleryBtn = document.getElementById('modalOpenGalleryBtn');
    const modalDownloadBtn = document.getElementById('modalDownloadBtn');
    const modalPreviewBox = document.getElementById('modalPreviewBox');

    const host = window.location.origin;
    const directUrl = fileData.direct_url ? fileData.direct_url : `${host}/f/${fileData.id}`;
    const galleryUrl = fileData.gallery_url ? fileData.gallery_url : `${host}/v/${fileData.id}`;
    const mime = (fileData.mime_type || '').toLowerCase();
    const fileName = fileData.name || 'File';
    const ext = fileName.split('.').pop().toLowerCase();

    if (modalFileName) modalFileName.textContent = fileName;
    if (modalPropSize) modalPropSize.textContent = `${formatBytes(fileData.size)} (${fileData.size || 0} bytes)`;
    if (modalPropMime) modalPropMime.textContent = fileData.mime_type || '-';
    if (modalPropId) modalPropId.textContent = fileData.id || '-';
    if (modalPropDate) modalPropDate.textContent = (fileData.created_at || '').slice(0, 10) || 'Today';

    if (modalDirectUrlInput) modalDirectUrlInput.value = directUrl;
    if (modalGalleryUrlInput) modalGalleryUrlInput.value = galleryUrl;

    if (modalOpenDirectBtn) modalOpenDirectBtn.href = directUrl;
    if (modalOpenGalleryBtn) modalOpenGalleryBtn.href = galleryUrl;
    if (modalDownloadBtn) {
        modalDownloadBtn.href = directUrl;
        modalDownloadBtn.download = fileName;
    }

    // Render Preview Box based on MIME
    if (modalPreviewBox) {
        if (mime.startsWith('image/') || ['png','jpg','jpeg','gif','webp','svg','ico'].includes(ext)) {
            modalPreviewBox.innerHTML = `
                <img src="${directUrl}" alt="${fileName}" class="max-h-40 rounded-lg object-contain mx-auto shadow-md" onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'text-center text-xs text-zinc-500 py-4 font-mono\\'>Pratinjau gambar tidak tersedia</div>';">
            `;
        } else if (mime.startsWith('video/') || ['mp4','webm','mov'].includes(ext)) {
            modalPreviewBox.innerHTML = `
                <video controls class="max-h-40 rounded-lg mx-auto bg-black"><source src="${directUrl}" type="${mime}"></video>
            `;
        } else if (mime.startsWith('audio/') || ['mp3','wav','ogg','m4a'].includes(ext)) {
            modalPreviewBox.innerHTML = `
                <div class="w-full text-center py-2 space-y-2">
                    <div class="text-xs text-zinc-400 font-mono">${fileName}</div>
                    <audio controls class="w-full"><source src="${directUrl}" type="${mime}"></audio>
                </div>
            `;
        } else {
            modalPreviewBox.innerHTML = `
                <div class="text-center py-4 space-y-1">
                    <svg class="w-10 h-10 text-zinc-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"></path>
                    </svg>
                    <div class="text-xs font-mono text-zinc-400 font-medium">${fileName}</div>
                </div>
            `;
        }
    }

    fileDetailModal.classList.remove('hidden');
    fileDetailModal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeFileModal() {
    const fileDetailModal = document.getElementById('fileDetailModal');
    if (fileDetailModal) {
        fileDetailModal.classList.add('hidden');
        fileDetailModal.classList.remove('flex');
    }
    document.body.style.overflow = '';

    if (shouldReloadOnModalClose) {
        shouldReloadOnModalClose = false;
        window.location.reload();
    }
}

function copyModalField(fieldId, btn) {
    const field = document.getElementById(fieldId);
    if (!field || !field.value) return;

    const originalText = btn.textContent;
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Tersalin!';

    navigator.clipboard.writeText(field.value).then(() => {
        btn.textContent = strCopied;
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}

function copyText(text, btn) {
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Tersalin!';
    navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = strCopied;
        setTimeout(() => { btn.textContent = original; }, 1500);
    });
}

function copyNewKey() {
    const field = document.getElementById('newKeyField');
    const text = document.getElementById('copyKeyText');
    const strCopied = (window.i18nTexts && window.i18nTexts.copied) || 'Tersalin!';
    const strCopy = (window.i18nTexts && window.i18nTexts.copyKey) || 'Salin';

    if (!field) return;
    navigator.clipboard.writeText(field.value).then(() => {
        if (text) text.textContent = strCopied;
        setTimeout(() => { if (text) text.textContent = strCopy; }, 2000);
    });
}
