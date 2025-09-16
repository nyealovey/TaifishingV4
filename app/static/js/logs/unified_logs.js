/* 泰摸鱼吧 - 统一日志中心脚本 */

// 全局变量
let currentPage = 1;
let totalPages = 1;
let isLoading = false;
let autoRefreshInterval = null;

/**
 * 页面初始化
 */
function initializeUnifiedLogs() {
    console.log('统一日志中心初始化');
    
    loadLogs();
    loadLogModules();
    loadLogStats();
    loadDebugStatus();
    
    setupEventListeners();
    initializeAutoRefresh();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 绑定筛选器事件
    const levelFilter = document.getElementById('levelFilter');
    const moduleFilter = document.getElementById('moduleFilter');
    const timeFilter = document.getElementById('timeFilter');
    const searchInput = document.getElementById('searchInput');

    if (levelFilter) levelFilter.addEventListener('change', searchLogs);
    if (moduleFilter) moduleFilter.addEventListener('change', searchLogs);
    if (timeFilter) timeFilter.addEventListener('change', searchLogs);
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchLogs();
            }
        });
    }

    // DEBUG按钮事件监听
    const debugBtn = document.getElementById('debugToggleBtn');
    if (debugBtn) {
        debugBtn.addEventListener('click', handleDebugClick);
        console.log('DEBUG按钮事件监听器已绑定');
    } else {
        console.error('找不到DEBUG按钮');
    }

    // 页面卸载时清理定时器
    window.addEventListener('beforeunload', function() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
    });
}

/**
 * 初始化自动刷新
 */
function initializeAutoRefresh() {
    // 每30秒自动刷新统计数据
    autoRefreshInterval = setInterval(() => {
        loadLogStats();
    }, 30000);
}

/**
 * 加载日志列表
 */
function loadLogs(page = 1) {
    if (isLoading) return;
    
    isLoading = true;
    currentPage = page;
    
    const level = document.getElementById('levelFilter')?.value || '';
    const module = document.getElementById('moduleFilter')?.value || '';
    const hours = document.getElementById('timeFilter')?.value || '24';
    const search = document.getElementById('searchInput')?.value || '';
    
    const params = new URLSearchParams({
        page: page,
        per_page: 50,
        level: level,
        module: module,
        hours: hours,
        q: search
    });
    
    // 显示加载状态
    showLoadingState();
    
    fetchWithCSRF(`/logs/api/structlog/search?${params}`)
    .then(data => {
        if (data.success) {
            displayLogs(data.data.logs);
            updatePagination(data.data.pagination);
        } else {
            showAlert('加载日志失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading logs:', error);
        showAlert('加载日志失败: ' + error.message, 'danger');
    })
    .finally(() => {
        hideLoadingState();
        isLoading = false;
    });
}

/**
 * 显示加载状态
 */
function showLoadingState() {
    const tbody = document.getElementById('logsTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div class="loading-logs">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="mt-2 mb-0">正在加载日志数据...</p>
                    </div>
                </td>
            </tr>
        `;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoadingState() {
    // 加载状态会在displayLogs中被替换，这里不需要额外操作
}

/**
 * 显示日志列表
 */
function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div class="empty-logs">
                        <i class="fas fa-inbox"></i>
                        <h5>暂无日志数据</h5>
                        <p class="text-muted">当前筛选条件下没有找到日志记录</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td class="log-timestamp">${formatDateTime(log.timestamp)}</td>
            <td>
                <span class="badge log-level-badge bg-${getLevelBadgeClass(log.level)}">${log.level}</span>
            </td>
            <td>
                <code class="log-module-code">${log.module || 'N/A'}</code>
            </td>
            <td class="log-message" title="${escapeHtml(log.message)}">
                ${highlightSearch(escapeHtml(log.message))}
            </td>
            <td>
                ${log.context && Object.keys(log.context).length > 0 ? 
                    `<button class="btn btn-sm btn-outline-info log-context-btn" onclick="showLogContext('${log.id}')" title="查看上下文">
                        <i class="fas fa-list"></i> 查看
                    </button>` : 
                    '<span class="text-muted">无</span>'
                }
            </td>
            <td>
                <div class="log-actions">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary log-detail-btn" onclick="showLogDetail('${log.id}')" title="查看详情">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${log.traceback ? 
                            `<button class="btn btn-sm btn-outline-danger log-traceback-btn" onclick="showLogTraceback('${log.id}')" title="查看堆栈追踪">
                                <i class="fas fa-bug"></i>
                            </button>` : ''
                        }
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * 更新分页
 */
function updatePagination(pagination) {
    const paginationEl = document.getElementById('logsPagination');
    if (!paginationEl) return;
    
    totalPages = pagination.pages;
    
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一页
    if (pagination.has_prev) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadLogs(${pagination.prev_num}); return false;">上一页</a>
            </li>
        `;
    }
    
    // 页码显示逻辑
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(totalPages, pagination.page + 2);
    
    // 如果开始页不是第1页，显示第1页和省略号
    if (startPage > 1) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadLogs(1); return false;">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHTML += `
                <li class="page-item disabled">
                    <span class="page-link">…</span>
                </li>
            `;
        }
    }
    
    // 显示页码范围
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadLogs(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // 如果结束页不是最后一页，显示省略号和最后一页
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `
                <li class="page-item disabled">
                    <span class="page-link">…</span>
                </li>
            `;
        }
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadLogs(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // 下一页
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadLogs(${pagination.next_num}); return false;">下一页</a>
            </li>
        `;
    }
    
    // 分页信息
    paginationHTML += `
        <li class="page-item disabled">
            <span class="page-link text-muted">
                第 ${pagination.page} 页，共 ${totalPages} 页 (${pagination.total} 条记录)
            </span>
        </li>
    `;
    
    paginationEl.innerHTML = paginationHTML;
}

/**
 * 加载日志模块列表
 */
function loadLogModules() {
    fetchWithCSRF('/logs/api/structlog/modules')
    .then(data => {
        if (data.success) {
            const select = document.getElementById('moduleFilter');
            if (select) {
                const currentValue = select.value;
                select.innerHTML = '<option value="">全部模块</option>' + 
                    data.data.map(module => `<option value="${escapeHtml(module)}">${escapeHtml(module)}</option>`).join('');
                select.value = currentValue;
            }
        }
    })
    .catch(error => console.error('Error loading modules:', error));
}

/**
 * 加载日志统计
 */
function loadLogStats() {
    fetchWithCSRF('/logs/api/structlog/stats')
    .then(data => {
        if (data.success) {
            const stats = data.data;
            updateStatsDisplay(stats);
        }
    })
    .catch(error => console.error('Error loading stats:', error));
}

/**
 * 更新统计显示
 */
function updateStatsDisplay(stats) {
    const elements = {
        'totalLogs': stats.total_logs || 0,
        'errorLogs': stats.error_count || 0,
        'warningLogs': stats.warning_count || 0,
        'infoLogs': stats.info_count || 0
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            // 添加动画效果
            element.style.transition = 'all 0.3s ease';
            element.textContent = formatNumber(value);
        }
    });
}

/**
 * 搜索日志
 */
function searchLogs() {
    loadLogs(1);
}

/**
 * 显示日志详情
 */
function showLogDetail(logId) {
    fetchWithCSRF(`/logs/api/structlog/detail/${logId}`)
    .then(data => {
        if (data.success) {
            displayLogDetail(data.data);
        } else {
            showAlert('获取日志详情失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading log detail:', error);
        showAlert('获取日志详情失败: ' + error.message, 'danger');
    });
}

/**
 * 显示日志上下文
 */
function showLogContext(logId) {
    fetchWithCSRF(`/logs/api/structlog/detail/${logId}`)
    .then(data => {
        if (data.success) {
            displayLogContext(data.data);
        } else {
            showAlert('获取日志上下文失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading log context:', error);
        showAlert('获取日志上下文失败: ' + error.message, 'danger');
    });
}

/**
 * 显示日志详情模态框
 */
function displayLogDetail(log) {
    const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
    const modalTitle = document.getElementById('logDetailModalLabel');
    const modalBody = document.getElementById('logDetailContent');
    
    modalTitle.innerHTML = `<i class="fas fa-info-circle me-2"></i>日志详情 - ID: ${log.id}`;
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-clock me-2"></i>时间信息</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>时间戳:</strong></td>
                        <td>${log.formatted_timestamp || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td><strong>创建时间:</strong></td>
                        <td>${log.formatted_created_at || 'N/A'}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-tag me-2"></i>基本信息</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>级别:</strong></td>
                        <td><span class="badge bg-${getLevelBadgeClass(log.level)}">${log.level}</span></td>
                    </tr>
                    <tr>
                        <td><strong>模块:</strong></td>
                        <td><code>${log.module || 'N/A'}</code></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-comment me-2"></i>消息内容</h6>
                <div class="alert alert-light">
                    <pre class="mb-0 log-content">${escapeHtml(log.message || 'N/A')}</pre>
                </div>
            </div>
        </div>
        
        ${log.traceback ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-bug me-2"></i>堆栈追踪</h6>
                <div class="alert alert-danger">
                    <pre class="mb-0 log-content">${escapeHtml(log.traceback)}</pre>
                </div>
            </div>
        </div>
        ` : ''}
        
        ${log.context && Object.keys(log.context).length > 0 ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-list me-2"></i>上下文信息</h6>
                <div class="alert alert-info">
                    <pre class="mb-0 log-context-json">${JSON.stringify(log.context, null, 2)}</pre>
                </div>
            </div>
        </div>
        ` : ''}
    `;
    
    modal.show();
}

/**
 * 显示日志上下文模态框
 */
function displayLogContext(log) {
    const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
    const modalTitle = document.getElementById('logDetailModalLabel');
    const modalBody = document.getElementById('logDetailContent');
    
    modalTitle.innerHTML = `<i class="fas fa-list me-2"></i>日志上下文 - ID: ${log.id}`;
    
    if (log.context && Object.keys(log.context).length > 0) {
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-12">
                    <h6><i class="fas fa-info-circle me-2"></i>基本信息</h6>
                    <table class="table table-sm">
                        <tr>
                            <td><strong>日志ID:</strong></td>
                            <td>${log.id}</td>
                        </tr>
                        <tr>
                            <td><strong>级别:</strong></td>
                            <td><span class="badge bg-${getLevelBadgeClass(log.level)}">${log.level}</span></td>
                        </tr>
                        <tr>
                            <td><strong>模块:</strong></td>
                            <td><code>${log.module || 'N/A'}</code></td>
                        </tr>
                        <tr>
                            <td><strong>时间:</strong></td>
                            <td>${log.formatted_timestamp || 'N/A'}</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-12">
                    <h6><i class="fas fa-list me-2"></i>上下文数据</h6>
                    <div class="alert alert-info">
                        <pre class="mb-0 log-context-json">${JSON.stringify(log.context, null, 2)}</pre>
                    </div>
                </div>
            </div>
        `;
    } else {
        modalBody.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                该日志没有上下文信息
            </div>
        `;
    }
    
    modal.show();
}

/**
 * 显示堆栈追踪
 */
function showLogTraceback(logId) {
    fetchWithCSRF(`/logs/api/structlog/detail/${logId}`)
    .then(data => {
        if (data.success) {
            displayLogTraceback(data.data);
        } else {
            showAlert('获取堆栈追踪失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading log traceback:', error);
        showAlert('获取堆栈追踪失败: ' + error.message, 'danger');
    });
}

/**
 * 显示堆栈追踪模态框
 */
function displayLogTraceback(log) {
    const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
    const modalTitle = document.getElementById('logDetailModalLabel');
    const modalBody = document.getElementById('logDetailContent');
    
    modalTitle.innerHTML = `<i class="fas fa-bug me-2"></i>堆栈追踪 - ID: ${log.id}`;
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-12">
                <h6><i class="fas fa-info-circle me-2"></i>基本信息</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>日志ID:</strong></td>
                        <td>${log.id}</td>
                    </tr>
                    <tr>
                        <td><strong>级别:</strong></td>
                        <td><span class="badge bg-${getLevelBadgeClass(log.level)}">${log.level}</span></td>
                    </tr>
                    <tr>
                        <td><strong>模块:</strong></td>
                        <td><code>${log.module || 'N/A'}</code></td>
                    </tr>
                    <tr>
                        <td><strong>时间:</strong></td>
                        <td>${log.formatted_timestamp || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td><strong>消息:</strong></td>
                        <td>${escapeHtml(log.message || 'N/A')}</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-bug me-2"></i>堆栈追踪</h6>
                <div class="alert alert-danger">
                    <pre class="mb-0 log-content">${escapeHtml(log.traceback || '无堆栈追踪信息')}</pre>
                </div>
            </div>
        </div>
    `;
    
    modal.show();
}

/**
 * 导出日志
 */
function exportUnifiedLogs() {
    const level = document.getElementById('levelFilter')?.value || '';
    const module = document.getElementById('moduleFilter')?.value || '';
    const hours = document.getElementById('timeFilter')?.value || '24';
    
    const params = new URLSearchParams({
        level: level,
        module: module,
        hours: hours,
        format: 'csv'
    });
    
    const url = `/logs/api/structlog/export?${params}`;
    
    // 创建隐藏的下载链接
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showAlert('导出任务已开始，请等待下载...', 'info');
}

/**
 * 刷新日志
 */
function refreshLogs() {
    loadLogs(currentPage);
    loadLogStats();
    showAlert('日志数据已刷新', 'success', 2000);
}

/**
 * DEBUG按钮点击处理
 */
function handleDebugClick(event) {
    console.log('handleDebugClick 被调用');
    event.preventDefault();
    event.stopPropagation();
    toggleDebugLogging();
}

/**
 * 加载DEBUG状态
 */
function loadDebugStatus() {
    fetchWithCSRF('/logs/api/debug-status')
    .then(data => {
        if (data.success) {
            updateDebugButton(data.data.enabled);
        } else {
            console.error('获取DEBUG状态失败:', data.message);
        }
    })
    .catch(error => {
        console.error('获取DEBUG状态失败:', error);
    });
}

/**
 * 切换DEBUG日志
 */
function toggleDebugLogging() {
    console.log('toggleDebugLogging 函数被调用');
    
    const button = document.getElementById('debugToggleBtn');
    if (!button) {
        console.error('找不到DEBUG按钮');
        return;
    }
    
    console.log('开始切换DEBUG状态...');
    
    // 禁用按钮防止重复点击
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>切换中...';
    
    fetchWithCSRF('/logs/api/debug-toggle', {
        method: 'POST'
    })
    .then(data => {
        console.log('响应数据:', data);
        if (data.success) {
            updateDebugButton(data.data.enabled);
            showAlert(data.data.message, 'success');
            // 刷新日志列表以显示新的DEBUG日志
            loadLogs(1);
        } else {
            showAlert('切换DEBUG日志失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('切换DEBUG日志失败:', error);
        showAlert('切换DEBUG日志失败: ' + error.message, 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        button.disabled = false;
        if (button.innerHTML.includes('切换中')) {
            button.innerHTML = originalText;
        }
    });
}

/**
 * 更新DEBUG按钮状态
 */
function updateDebugButton(enabled) {
    const button = document.getElementById('debugToggleBtn');
    const statusText = document.getElementById('debugStatusText');
    
    if (!button || !statusText) return;
    
    if (enabled) {
        button.className = 'btn debug-toggle-btn enabled';
        statusText.textContent = 'DEBUG: 启用';
    } else {
        button.className = 'btn debug-toggle-btn disabled';
        statusText.textContent = 'DEBUG: 关闭';
    }
    
    // 确保按钮可点击
    button.disabled = false;
}

/**
 * 工具函数
 */
function formatDateTime(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function getLevelBadgeClass(level) {
    const classes = {
        'DEBUG': 'secondary',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'danger',
        'CRITICAL': 'dark'
    };
    return classes[level] || 'secondary';
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function highlightSearch(text) {
    const searchTerm = document.getElementById('searchInput')?.value;
    if (!searchTerm || !text) return text;
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function showAlert(message, type = 'info', duration = 5000) {
    // 移除现有的提示
    const existingAlerts = document.querySelectorAll('.alert-dismissible');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '90px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '400px';
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // 自动隐藏
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeUnifiedLogs();
});
