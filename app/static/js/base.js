/* 泰摸鱼吧 - 基础脚本 */

/**
 * 加载应用信息
 */
async function loadAppInfo() {
    try {
        const response = await fetch('/admin/app-info');
        const data = await response.json();

        if (data.success && data.data) {
            const appName = data.data.app_name;

            // 更新左上角logo中的应用名称
            const appNameElement = document.getElementById('app-name');
            if (appNameElement) {
                appNameElement.textContent = appName;
            }

            // 更新底部版权信息中的应用名称
            const footerAppNameElement = document.getElementById('footer-app-name');
            if (footerAppNameElement) {
                footerAppNameElement.textContent = appName;
            }

            // 更新页面标题中的应用名称
            const pageTitleElement = document.getElementById('page-title');
            if (pageTitleElement) {
                pageTitleElement.textContent = appName + ' - 数据同步管理平台';
            }
        }
    } catch (error) {
        console.error('加载应用信息失败:', error);
    }
}

/**
 * 页面初始化
 */
function initializePage() {
    // 加载应用信息
    loadAppInfo();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化确认对话框
    initializeConfirmDialogs();
}

/**
 * 初始化Bootstrap工具提示
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 初始化确认对话框
 */
function initializeConfirmDialogs() {
    // 为所有带有data-confirm属性的元素添加确认对话框
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * 显示加载状态
 */
function showLoading(element, text = '加载中...') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.disabled = true;
        element.innerHTML = `<span class="loading"></span> ${text}`;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading(element, originalText) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.disabled = false;
        element.innerHTML = originalText;
    }
}

/**
 * 显示消息提示
 */
function showMessage(message, type = 'info', duration = 5000) {
    // 创建消息容器（如果不存在）
    let messageContainer = document.getElementById('message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.id = 'message-container';
        messageContainer.style.position = 'fixed';
        messageContainer.style.top = '90px';
        messageContainer.style.right = '20px';
        messageContainer.style.zIndex = '9999';
        messageContainer.style.maxWidth = '400px';
        document.body.appendChild(messageContainer);
    }

    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type} alert-dismissible fade show`;
    messageElement.style.marginBottom = '10px';
    messageElement.innerHTML = `
        <i class="fas fa-${getIconByType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // 添加到容器
    messageContainer.appendChild(messageElement);

    // 自动移除
    if (duration > 0) {
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, duration);
    }
}

/**
 * 根据类型获取图标
 */
function getIconByType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

/**
 * 格式化相对时间
 */
function formatRelativeTime(dateString) {
    if (!dateString) return '-';
    
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    
    return formatDateTime(dateString);
}

/**
 * 复制文本到剪贴板
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('已复制到剪贴板', 'success', 2000);
        return true;
    } catch (err) {
        console.error('复制失败:', err);
        showMessage('复制失败', 'error', 3000);
        return false;
    }
}

/**
 * 防抖函数
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(this, args);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 安全的JSON解析
 */
function safeJsonParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch (e) {
        console.warn('JSON解析失败:', e);
        return defaultValue;
    }
}

/**
 * 获取CSRF Token
 */
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

/**
 * 发送带CSRF Token的请求
 */
async function fetchWithCSRF(url, options = {}) {
    const token = getCSRFToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token,
        },
    };
    
    // 合并选项
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    return fetch(url, mergedOptions);
}

/**
 * 处理API响应
 */
async function handleApiResponse(response) {
    try {
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API响应处理失败:', error);
        throw error;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});
