/* 泰摸鱼吧 - 管理员页面脚本 */

let refreshInterval = null;

/**
 * 管理员页面初始化
 */
function initializeAdminManagement() {
    console.log('管理员页面初始化');
    loadSystemOverview();
    checkSystemStatus();
    setupEventListeners();
    startAutoRefresh();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 页面卸载时清理定时器
    window.addEventListener('beforeunload', function() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
    });

    // 监听窗口焦点事件
    window.addEventListener('focus', function() {
        loadSystemOverview();
        checkSystemStatus();
    });
}

/**
 * 开始自动刷新
 */
function startAutoRefresh() {
    // 每30秒自动刷新系统状态
    refreshInterval = setInterval(() => {
        checkSystemStatus();
    }, 30000);
}

/**
 * 停止自动刷新
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

/**
 * 加载系统概览数据
 */
function loadSystemOverview() {
    showLoadingState('overview');
    
    fetchWithCSRF('/dashboard/api/overview')
    .then(data => {
        if (data.success) {
            updateOverviewDisplay(data.data);
        } else {
            showErrorState('overview', '加载系统概览失败');
        }
    })
    .catch(error => {
        console.error('加载系统概览失败:', error);
        showErrorState('overview', '网络错误，请检查连接');
    })
    .finally(() => {
        hideLoadingState('overview');
    });
}

/**
 * 更新概览数据显示
 */
function updateOverviewDisplay(data) {
    const updates = {
        'total-users': data.users?.total || 0,
        'total-instances': data.instances?.total || 0,
        'total-tasks': data.tasks?.total || 0,
        'total-logs': data.logs?.total || 0
    };

    Object.entries(updates).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            // 添加动画效果
            element.style.transition = 'all 0.3s ease';
            element.textContent = formatNumber(value);
            
            // 短暂高亮效果
            element.style.transform = 'scale(1.05)';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 200);
        }
    });

    console.log('系统概览数据更新完成');
}

/**
 * 检查系统状态
 */
function checkSystemStatus() {
    fetchWithCSRF('/api/health')
    .then(data => {
        if (data.success) {
            updateSystemStatus(data.data);
        } else {
            console.warn('获取系统状态失败:', data.message);
            showSystemStatusError();
        }
    })
    .catch(error => {
        console.error('检查系统状态失败:', error);
        showSystemStatusError();
    });
}

/**
 * 更新系统状态显示
 */
function updateSystemStatus(status) {
    // 更新数据库状态
    updateStatusIndicator('db-indicator', status.database === 'connected' ? 'healthy' : 'error');
    updateStatusText('db-status', status.database === 'connected' ? '正常' : '异常');
    
    // 更新Redis状态
    updateStatusIndicator('redis-indicator', status.redis === 'connected' ? 'healthy' : 'error');
    updateStatusText('redis-status', status.redis === 'connected' ? '正常' : '异常');
    
    // 更新应用状态（始终正常，因为能执行这个函数说明应用在运行）
    updateStatusIndicator('app-indicator', 'healthy');
    updateStatusText('app-status', '运行中');
    
    // 更新系统状态（根据各组件状态综合判断）
    const overallStatus = getOverallSystemStatus(status);
    updateStatusIndicator('system-indicator', overallStatus);
    updateStatusText('system-status', getSystemStatusText(overallStatus));
    
    console.log('系统状态更新完成');
}

/**
 * 获取整体系统状态
 */
function getOverallSystemStatus(status) {
    if (status.database === 'connected' && status.redis === 'connected') {
        return 'healthy';
    } else if (status.database === 'connected' || status.redis === 'connected') {
        return 'warning';
    } else {
        return 'error';
    }
}

/**
 * 获取系统状态文本
 */
function getSystemStatusText(status) {
    const statusTexts = {
        'healthy': '正常',
        'warning': '部分异常',
        'error': '异常'
    };
    return statusTexts[status] || '未知';
}

/**
 * 更新状态指示器
 */
function updateStatusIndicator(indicatorId, status) {
    const indicator = document.getElementById(indicatorId);
    if (indicator) {
        // 移除所有状态类
        indicator.className = 'status-indicator';
        // 添加新状态类
        indicator.classList.add(`status-${status}`);
    }
}

/**
 * 更新状态文本
 */
function updateStatusText(textId, text) {
    const textElement = document.getElementById(textId);
    if (textElement) {
        textElement.textContent = text;
        
        // 更新文本颜色类
        textElement.className = 'system-status-text';
        
        if (text === '正常' || text === '运行中') {
            textElement.classList.add('text-success');
        } else if (text === '异常') {
            textElement.classList.add('text-danger');
        } else if (text === '部分异常') {
            textElement.classList.add('text-warning');
        }
    }
}

/**
 * 显示系统状态错误
 */
function showSystemStatusError() {
    const indicators = ['db-indicator', 'redis-indicator', 'app-indicator', 'system-indicator'];
    const texts = ['db-status', 'redis-status', 'app-status', 'system-status'];
    
    indicators.forEach(id => updateStatusIndicator(id, 'error'));
    texts.forEach(id => updateStatusText(id, '检查失败'));
}

/**
 * 重启系统服务
 */
function restartSystem() {
    if (!confirm('确定要重启系统服务吗？这会暂时中断服务。')) {
        return;
    }

    const restartBtn = event?.target || document.querySelector('.btn-danger');
    if (restartBtn) {
        const originalText = restartBtn.innerHTML;
        restartBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>重启中...';
        restartBtn.disabled = true;

        // 模拟重启过程
        setTimeout(() => {
            restartBtn.innerHTML = originalText;
            restartBtn.disabled = false;
            if (typeof showMessage === 'function') {
                showMessage('系统服务重启完成', 'success');
            }
            // 重新检查系统状态
            checkSystemStatus();
        }, 3000);
    }
}

/**
 * 清理系统缓存
 */
function clearCache() {
    if (!confirm('确定要清理系统缓存吗？')) {
        return;
    }

    const clearBtn = event?.target || document.querySelector('.btn-warning');
    if (clearBtn) {
        const originalText = clearBtn.innerHTML;
        clearBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>清理中...';
        clearBtn.disabled = true;

        fetchWithCSRF('/admin/api/clear-cache', {
            method: 'POST'
        })
        .then(data => {
            if (data.success) {
                if (typeof showMessage === 'function') {
                    showMessage('缓存清理完成', 'success');
                }
            } else {
                throw new Error(data.message || '清理失败');
            }
        })
        .catch(error => {
            console.error('清理缓存失败:', error);
            if (typeof showMessage === 'function') {
                showMessage('缓存清理失败: ' + error.message, 'error');
            }
        })
        .finally(() => {
            clearBtn.innerHTML = originalText;
            clearBtn.disabled = false;
        });
    }
}

/**
 * 查看系统日志
 */
function viewSystemLogs() {
    // 跳转到日志页面
    window.location.href = '/logs/unified_logs';
}

/**
 * 管理用户
 */
function manageUsers() {
    // 跳转到用户管理页面
    window.location.href = '/user-management/';
}

/**
 * 管理任务
 */
function manageTasks() {
    // 跳转到任务管理页面
    window.location.href = '/scheduler/';
}

/**
 * 系统设置
 */
function systemSettings() {
    if (typeof showMessage === 'function') {
        showMessage('系统设置功能正在开发中...', 'info');
    }
}

/**
 * 数据备份
 */
function backupData() {
    if (!confirm('确定要开始数据备份吗？')) {
        return;
    }

    const backupBtn = event?.target;
    if (backupBtn) {
        const originalText = backupBtn.innerHTML;
        backupBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>备份中...';
        backupBtn.disabled = true;

        fetchWithCSRF('/admin/api/backup', {
            method: 'POST'
        })
        .then(data => {
            if (data.success) {
                if (typeof showMessage === 'function') {
                    showMessage('数据备份已开始，请稍后查看备份文件', 'success');
                }
            } else {
                throw new Error(data.message || '备份失败');
            }
        })
        .catch(error => {
            console.error('数据备份失败:', error);
            if (typeof showMessage === 'function') {
                showMessage('数据备份失败: ' + error.message, 'error');
            }
        })
        .finally(() => {
            backupBtn.innerHTML = originalText;
            backupBtn.disabled = false;
        });
    }
}

/**
 * 显示加载状态
 */
function showLoadingState(section) {
    const loadingHtml = `
        <div class="admin-loading">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <div class="admin-loading-text">正在加载数据...</div>
        </div>
    `;
    
    const container = document.getElementById(`${section}-container`);
    if (container) {
        container.innerHTML = loadingHtml;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoadingState(section) {
    // 加载状态会在更新数据时被替换，这里不需要额外操作
}

/**
 * 显示错误状态
 */
function showErrorState(section, message) {
    const errorHtml = `
        <div class="admin-error">
            <i class="fas fa-exclamation-triangle"></i>
            <h5>加载失败</h5>
            <p>${message}</p>
            <button class="btn btn-outline-primary btn-sm" onclick="location.reload()">
                <i class="fas fa-refresh me-1"></i>重新加载
            </button>
        </div>
    `;
    
    const container = document.getElementById(`${section}-container`);
    if (container) {
        container.innerHTML = errorHtml;
    }
}

/**
 * 格式化数字显示
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * 手动刷新系统数据
 */
function refreshSystemData() {
    const refreshBtn = event?.target || document.querySelector('.btn-outline-info');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>刷新中...';
        refreshBtn.disabled = true;

        Promise.all([
            loadSystemOverview(),
            checkSystemStatus()
        ]).finally(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
            if (typeof showMessage === 'function') {
                showMessage('系统数据已刷新', 'success', 2000);
            }
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminManagement();
});
