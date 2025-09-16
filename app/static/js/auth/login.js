/* 泰摸鱼吧 - 登录页面脚本 */

/**
 * 登录页面初始化
 */
function initializeLoginPage() {
    // 密码显示/隐藏切换
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            const icon = this.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }

    // 表单提交处理
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
    }

    // 快速登录功能（开发环境）
    initializeQuickLogin();
}

/**
 * 处理登录表单提交
 */
function handleLoginSubmit(e) {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        e.preventDefault();
        if (typeof showWarningAlert === 'function') {
            showWarningAlert('请输入用户名和密码');
        } else {
            alert('请输入用户名和密码');
        }
        return;
    }

    // 显示加载状态
    const submitBtn = this.querySelector('button[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>登录中...';
        submitBtn.disabled = true;

        // 如果登录失败，恢复按钮状态
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 3000);
    }
}

/**
 * 初始化快速登录功能（开发环境）
 */
function initializeQuickLogin() {
    // 如果当前是开发环境，添加快速填充功能
    const quickLoginCard = document.querySelector('.card:last-child .card-body');
    if (quickLoginCard) {
        const quickButton = document.createElement('button');
        quickButton.type = 'button';
        quickButton.className = 'btn btn-outline-primary btn-sm mt-2';
        quickButton.innerHTML = '<i class="fas fa-bolt me-1"></i>快速填充';
        quickButton.onclick = quickFillCredentials;
        
        quickLoginCard.appendChild(quickButton);
    }
}

/**
 * 快速填充登录凭据
 */
function quickFillCredentials() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (usernameInput) {
        usernameInput.value = 'admin';
    }
    if (passwordInput) {
        passwordInput.value = 'Admin123';
    }
    
    // 聚焦到登录按钮
    const loginButton = document.querySelector('button[type="submit"]');
    if (loginButton) {
        loginButton.focus();
    }
}

/**
 * 验证用户名格式
 */
function validateUsername(username) {
    // 用户名长度3-20位，允许字母、数字、下划线
    const pattern = /^[a-zA-Z0-9_]{3,20}$/;
    return pattern.test(username);
}

/**
 * 验证密码强度
 */
function validatePassword(password) {
    // 密码至少6位
    if (password.length < 6) {
        return { valid: false, message: '密码至少需要6位字符' };
    }
    
    // 可以添加更多密码复杂度验证
    return { valid: true, message: '密码格式正确' };
}

/**
 * 实时验证表单
 */
function enableRealTimeValidation() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (usernameInput) {
        usernameInput.addEventListener('blur', function() {
            const username = this.value.trim();
            if (username && !validateUsername(username)) {
                this.classList.add('is-invalid');
                showFieldError(this, '用户名格式不正确（3-20位字母、数字、下划线）');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }
    
    if (passwordInput) {
        passwordInput.addEventListener('blur', function() {
            const password = this.value;
            if (password) {
                const validation = validatePassword(password);
                if (!validation.valid) {
                    this.classList.add('is-invalid');
                    showFieldError(this, validation.message);
                } else {
                    this.classList.remove('is-invalid');
                    hideFieldError(this);
                }
            }
        });
    }
}

/**
 * 显示字段错误信息
 */
function showFieldError(field, message) {
    hideFieldError(field); // 先清除现有错误
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * 隐藏字段错误信息
 */
function hideFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeLoginPage();
    enableRealTimeValidation();
});
