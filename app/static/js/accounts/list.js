/* 泰摸鱼吧 - 账户列表页面脚本 */

/**
 * 账户列表页面初始化
 */
function initializeAccountsList() {
    console.log('账户列表页面初始化');
    setupEventListeners();
    initializeTooltips();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 监听搜索表单提交
    const searchForm = document.querySelector('form[method="GET"]');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }

    // 监听清除按钮
    const clearButton = document.querySelector('button[onclick*="location.href"]');
    if (clearButton) {
        clearButton.addEventListener('click', handleClearFilters);
    }
}

/**
 * 初始化工具提示
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
 * 同步所有账户
 */
function syncAllAccounts() {
    const btn = event.target;
    const originalText = btn.innerHTML;

    // 确认操作
    if (!confirm('确定要同步所有实例的账户吗？这可能需要一些时间。')) {
        return;
    }

    // 设置加载状态
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>同步中...';
    btn.disabled = true;

    // 获取CSRF token
    const csrfToken = getCSRFToken();

    fetchWithCSRF('/account-sync/sync-all', {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            // 同步完成后刷新页面显示最新数据
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else if (data.error) {
            showAlert('danger', data.error);
        } else {
            showAlert('warning', '同步操作未返回预期结果');
        }
    })
    .catch(error => {
        console.error('同步账户失败:', error);
        showAlert('danger', '同步失败: ' + error.message);
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

/**
 * 同步所有实例（向后兼容）
 */
function syncAllInstances() {
    syncAllAccounts();
}

/**
 * 同步单个实例的账户
 */
function syncInstance(instanceId) {
    if (!instanceId) {
        showAlert('warning', '实例ID无效');
        return;
    }

    const btn = event.target;
    const originalText = btn.innerHTML;

    // 确认操作
    if (!confirm('确定要同步该实例的账户吗？')) {
        return;
    }

    // 设置加载状态
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>同步中...';
    btn.disabled = true;

    fetchWithCSRF(`/instances/${instanceId}/sync`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success || data.message) {
            showAlert('success', data.message || '同步成功');
            // 刷新当前页面数据
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showAlert('danger', data.error || '同步失败');
        }
    })
    .catch(error => {
        console.error('同步实例失败:', error);
        showAlert('danger', '同步失败: ' + error.message);
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

/**
 * 查看账户详情
 */
function viewAccount(accountId) {
    if (!accountId) {
        showAlert('warning', '账户ID无效');
        return;
    }

    // 可以在这里实现账户详情查看功能
    showAlert('info', `查看账户 ${accountId} 的详情功能正在开发中...`);
}

/**
 * 查看账户权限
 */
function viewAccountPermissions(accountId, options = {}) {
    if (!accountId) {
        showAlert('warning', '账户ID无效');
        return;
    }

    // 调用权限查看组件
    if (typeof window.viewAccountPermissions === 'function') {
        window.viewAccountPermissions(accountId, options);
    } else {
        console.error('权限查看组件未加载');
        showAlert('error', '权限查看功能不可用');
    }
}

/**
 * 显示账户统计
 */
function showAccountStatistics() {
    // 直接跳转到账户统计页面
    window.location.href = '/account-static/';
}

/**
 * 处理搜索表单提交
 */
function handleSearchSubmit(event) {
    const form = event.target;
    const formData = new FormData(form);
    
    // 验证搜索条件
    const search = formData.get('search');
    if (search && search.trim().length < 2) {
        event.preventDefault();
        showAlert('warning', '搜索关键词至少需要2个字符');
        return false;
    }

    // 显示加载状态
    showLoadingState();
}

/**
 * 处理清除筛选器
 */
function handleClearFilters(event) {
    event.preventDefault();
    
    // 清空所有筛选器
    const form = document.querySelector('form[method="GET"]');
    if (form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'text' || input.type === 'search') {
                input.value = '';
            } else if (input.type === 'select-one') {
                input.selectedIndex = 0;
            }
        });
    }

    // 跳转到清空参数的URL
    const currentUrl = new URL(window.location);
    const cleanUrl = currentUrl.pathname;
    window.location.href = cleanUrl;
}

/**
 * 筛选数据库类型
 */
function filterByDbType(dbType) {
    const currentUrl = new URL(window.location);
    
    if (dbType) {
        currentUrl.searchParams.set('db_type', dbType);
    } else {
        currentUrl.searchParams.delete('db_type');
    }
    
    // 重置页码
    currentUrl.searchParams.delete('page');
    
    window.location.href = currentUrl.toString();
}

/**
 * 筛选环境
 */
function filterByEnvironment(environment) {
    const currentUrl = new URL(window.location);
    
    if (environment) {
        currentUrl.searchParams.set('environment', environment);
    } else {
        currentUrl.searchParams.delete('environment');
    }
    
    // 重置页码
    currentUrl.searchParams.delete('page');
    
    window.location.href = currentUrl.toString();
}

/**
 * 显示加载状态
 */
function showLoadingState() {
    const container = document.querySelector('.accounts-table-container');
    if (container) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-accounts">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">加载账户数据中...</p>
            </div>
        `;
        
        container.style.position = 'relative';
        container.appendChild(overlay);
    }
}

/**
 * 隐藏加载状态
 */
function hideLoadingState() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * 显示提示消息
 */
function showAlert(type, message) {
    // 移除现有的提示
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => {
        if (alert.classList.contains('alert-dismissible')) {
            alert.remove();
        }
    });

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${getIconByType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // 插入到页面顶部
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    } else {
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }

    // 5秒后自动移除
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

/**
 * 根据类型获取图标
 */
function getIconByType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * 获取CSRF Token
 */
function getCSRFToken() {
    // 先尝试从meta标签获取
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    // 再尝试从隐藏输入框获取
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    if (hiddenInput) {
        return hiddenInput.value;
    }
    
    console.warn('未找到CSRF token');
    return '';
}

/**
 * 安全的API请求
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
    
    const response = await fetch(url, mergedOptions);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}

/**
 * 表格排序功能
 */
function sortTable(columnIndex, sortType = 'string') {
    const table = document.querySelector('.accounts-table tbody');
    if (!table) return;

    const rows = Array.from(table.querySelectorAll('tr'));
    const currentSort = table.getAttribute('data-sort');
    const currentColumn = table.getAttribute('data-sort-column');
    
    let ascending = true;
    if (currentColumn == columnIndex && currentSort === 'asc') {
        ascending = false;
    }

    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();

        let comparison = 0;
        if (sortType === 'number') {
            comparison = parseFloat(aValue) - parseFloat(bValue);
        } else if (sortType === 'date') {
            comparison = new Date(aValue) - new Date(bValue);
        } else {
            comparison = aValue.localeCompare(bValue);
        }

        return ascending ? comparison : -comparison;
    });

    // 更新表格
    rows.forEach(row => table.appendChild(row));
    
    // 保存排序状态
    table.setAttribute('data-sort', ascending ? 'asc' : 'desc');
    table.setAttribute('data-sort-column', columnIndex);
}

/**
 * 批量操作功能
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const rowCheckboxes = document.querySelectorAll('input[name="selected_accounts"]');
    
    rowCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBatchActions();
}

/**
 * 更新批量操作按钮状态
 */
function updateBatchActions() {
    const selectedCheckboxes = document.querySelectorAll('input[name="selected_accounts"]:checked');
    const batchActionButtons = document.querySelectorAll('.batch-action-btn');
    
    const hasSelection = selectedCheckboxes.length > 0;
    batchActionButtons.forEach(btn => {
        btn.disabled = !hasSelection;
    });
    
    // 更新选择计数
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedCheckboxes.length;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAccountsList();
});
