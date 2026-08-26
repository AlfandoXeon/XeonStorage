/**
 * XeonStorage Global Application JavaScript
 */

// Mobile Navigation Toggle
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    const hamburgerIcon = document.getElementById('hamburgerIcon');
    const closeIcon = document.getElementById('closeIcon');
    
    if (!mobileMenu) return;
    
    const isHidden = mobileMenu.classList.contains('hidden');
    if (isHidden) {
        mobileMenu.classList.remove('hidden');
        if (hamburgerIcon) hamburgerIcon.classList.add('hidden');
        if (closeIcon) closeIcon.classList.remove('hidden');
    } else {
        mobileMenu.classList.add('hidden');
        if (hamburgerIcon) hamburgerIcon.classList.remove('hidden');
        if (closeIcon) closeIcon.classList.add('hidden');
    }
}

// Global Auth Pop-Up Modal
function openAuthModal(mode = 'login', options = {}) {
    const authModal = document.getElementById('authModal');
    const authErrorBanner = document.getElementById('authErrorBanner');
    const authNoticeBanner = document.getElementById('authNoticeBanner');
    const authNoticeMsg = document.getElementById('authNoticeMsg');
    if (!authModal) return;

    if (authErrorBanner) authErrorBanner.classList.add('hidden');

    // Handle informative notice (e.g. upload gimmick)
    if (authNoticeBanner) {
        if (options && (options.notice || options.noticeText)) {
            if (authNoticeMsg && options.noticeText) {
                authNoticeMsg.textContent = options.noticeText;
            } else if (authNoticeMsg && window.i18nTexts && window.i18nTexts.authUploadNotice) {
                authNoticeMsg.textContent = window.i18nTexts.authUploadNotice;
            }
            authNoticeBanner.classList.remove('hidden');
        } else {
            authNoticeBanner.classList.add('hidden');
        }
    }

    switchAuthTab(mode);
    authModal.classList.remove('hidden');
    authModal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
    const authModal = document.getElementById('authModal');
    const authErrorBanner = document.getElementById('authErrorBanner');
    const authNoticeBanner = document.getElementById('authNoticeBanner');
    if (!authModal) return;

    authModal.classList.add('hidden');
    authModal.classList.remove('flex');
    if (authErrorBanner) authErrorBanner.classList.add('hidden');
    if (authNoticeBanner) authNoticeBanner.classList.add('hidden');
    document.body.style.overflow = '';
}

function switchAuthTab(mode) {
    const modalTitle = document.getElementById('modalTitle');
    const modalSubtitle = document.getElementById('modalSubtitle');
    const tabLoginBtn = document.getElementById('tabLoginBtn');
    const tabRegisterBtn = document.getElementById('tabRegisterBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const authErrorBanner = document.getElementById('authErrorBanner');

    if (authErrorBanner) authErrorBanner.classList.add('hidden');

    const textLoginTitle = window.i18nTexts ? window.i18nTexts.loginTitle : 'Sign In';
    const textLoginSub = window.i18nTexts ? window.i18nTexts.loginSub : 'Sign in to your account.';
    const textRegisterTitle = window.i18nTexts ? window.i18nTexts.registerTitle : 'Create Account';
    const textRegisterSub = window.i18nTexts ? window.i18nTexts.registerSub : 'Register for an account.';

    if (mode === 'register') {
        if (modalTitle) modalTitle.textContent = textRegisterTitle;
        if (modalSubtitle) modalSubtitle.textContent = textRegisterSub;
        if (tabRegisterBtn) {
            tabRegisterBtn.classList.add('border-brand-500', 'text-white');
            tabRegisterBtn.classList.remove('border-transparent', 'text-zinc-400');
        }
        if (tabLoginBtn) {
            tabLoginBtn.classList.remove('border-brand-500', 'text-white');
            tabLoginBtn.classList.add('border-transparent', 'text-zinc-400');
        }
        if (loginForm) loginForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('hidden');
    } else {
        if (modalTitle) modalTitle.textContent = textLoginTitle;
        if (modalSubtitle) modalSubtitle.textContent = textLoginSub;
        if (tabLoginBtn) {
            tabLoginBtn.classList.add('border-brand-500', 'text-white');
            tabLoginBtn.classList.remove('border-transparent', 'text-zinc-400');
        }
        if (tabRegisterBtn) {
            tabRegisterBtn.classList.remove('border-brand-500', 'text-white');
            tabRegisterBtn.classList.add('border-transparent', 'text-zinc-400');
        }
        if (registerForm) registerForm.classList.add('hidden');
        if (loginForm) loginForm.classList.remove('hidden');
    }
}

async function handleAuthSubmit(event, mode) {
    event.preventDefault();
    const authErrorBanner = document.getElementById('authErrorBanner');
    const authErrorMsg = document.getElementById('authErrorMsg');
    if (authErrorBanner) authErrorBanner.classList.add('hidden');

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.textContent : 'Submit';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '...';
    }

    const formData = new FormData(form);

    try {
        const response = await fetch('/' + mode, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        });

        const data = await response.json();
        if (response.ok && data.success) {
            if (window.pendingUploadFile && typeof window.startPendingUpload === 'function') {
                closeAuthModal();
                window.isUserLoggedIn = true;
                const fileToUpload = window.pendingUploadFile;
                window.pendingUploadFile = null;
                window.startPendingUpload(fileToUpload);
            } else {
                window.location.href = data.redirect || '/dashboard';
            }
        } else {
            if (authErrorMsg) authErrorMsg.textContent = data.error || 'Authentication failed.';
            if (authErrorBanner) authErrorBanner.classList.remove('hidden');
        }
    } catch (err) {
        if (authErrorMsg) authErrorMsg.textContent = 'Network or server error.';
        if (authErrorBanner) authErrorBanner.classList.remove('hidden');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
}

// Global Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize AOS Animation Library
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 650,
            easing: 'ease-out-cubic',
            once: true,
            offset: 25
        });
    }

    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) closeAuthModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && authModal && !authModal.classList.contains('hidden')) {
            closeAuthModal();
        }
    });

    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    const hasNotice = urlParams.get('notice') === 'upload';
    if (authParam === 'login' || authParam === 'register') {
        openAuthModal(authParam, { notice: hasNotice });
    }
});
