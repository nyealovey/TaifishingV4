/* 泰摸鱼吧 - 仪表板概览页面脚本 */

// 全局变量
let autoRefreshInterval = null;
let logTrendChart = null;
let isAutoRefreshEnabled = false;

/**
 * 页面初始化
 */
function initializeDashboard() {
    console.log('仪表板页面初始化');
    initCharts();
    setupEventListeners();
    // 不自动开启自动刷新，由用户手动控制
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 监听页面卸载事件，清理定时器
    window.addEventListener('beforeunload', function() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
    });

    // 监听窗口焦点事件，恢复自动刷新
    window.addEventListener('focus', function() {
        if (isAutoRefreshEnabled && !autoRefreshInterval) {
            startAutoRefresh();
        }
    });

    // 监听窗口失焦事件，暂停自动刷新以节省资源
    window.addEventListener('blur', function() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    });
}

/**
 * 初始化图表
 */
function initCharts() {
    try {
        initLogTrendChart();
    } catch (error) {
        console.error('初始化图表失败:', error);
        showErrorState('chart-error', '图表加载失败');
    }
}

/**
 * 初始化日志趋势图
 */
function initLogTrendChart() {
    const canvas = document.getElementById('logTrendChart');
    if (!canvas) {
        console.warn('未找到日志趋势图容器');
        return;
    }

    const ctx = canvas.getContext('2d');
    
    // 显示加载状态
    showLoadingState(canvas.parentElement);
    
    // 获取日志趋势数据
    fetchWithCSRF('/dashboard/api/charts?type=logs')
    .then(data => {
        const logTrend = data.log_trend || [];
        
        // 隐藏加载状态
        hideLoadingState(canvas.parentElement);
        
        // 创建图表
        logTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: logTrend.map(item => formatDate(item.date)),
                datasets: [{
                    label: '错误日志',
                    data: logTrend.map(item => item.error_count || 0),
                    borderColor: 'rgb(220, 53, 69)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }, {
                    label: '告警日志',
                    data: logTrend.map(item => item.warning_count || 0),
                    borderColor: 'rgb(255, 193, 7)',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    })
    .catch(error => {
        console.error('加载日志趋势数据失败:', error);
        hideLoadingState(canvas.parentElement);
        showErrorState(canvas.parentElement, '日志趋势数据加载失败');
    });
}

/**
 * 刷新仪表板数据
 */
function refreshDashboard() {
    const refreshButton = document.querySelector('button[onclick="refreshDashboard()"]');
    if (refreshButton) {
        const originalText = refreshButton.innerHTML;
        refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>刷新中...';
        refreshButton.disabled = true;

        // 刷新页面数据
        setTimeout(() => {
            location.reload();
        }, 500);
    } else {
        location.reload();
    }
}

/**
 * 切换自动刷新
 */
function toggleAutoRefresh() {
    const button = document.querySelector('button[onclick="toggleAutoRefresh()"]');
    
    if (autoRefreshInterval || isAutoRefreshEnabled) {
        stopAutoRefresh();
        if (button) {
            button.innerHTML = '<i class="fas fa-clock me-2"></i>自动刷新';
            button.className = 'btn btn-outline-info';
        }
        removeAutoRefreshIndicator();
    } else {
        startAutoRefresh();
        if (button) {
            button.innerHTML = '<i class="fas fa-pause me-2"></i>停止刷新';
            button.className = 'btn btn-warning';
        }
        showAutoRefreshIndicator();
    }
}

/**
 * 开始自动刷新
 */
function startAutoRefresh() {
    stopAutoRefresh(); // 先清除现有的定时器
    
    isAutoRefreshEnabled = true;
    autoRefreshInterval = setInterval(() => {
        refreshSystemStatus();
    }, 30000); // 30秒刷新一次
    
    console.log('自动刷新已启动');
}

/**
 * 停止自动刷新
 */
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    isAutoRefreshEnabled = false;
    console.log('自动刷新已停止');
}

/**
 * 刷新系统状态
 */
function refreshSystemStatus() {
    fetchWithCSRF('/dashboard/api/status')
    .then(data => {
        updateSystemStatus(data);
        console.log('系统状态更新成功');
    })
    .catch(error => {
        console.error('刷新系统状态失败:', error);
        if (typeof showMessage === 'function') {
            showMessage('系统状态刷新失败: ' + error.message, 'warning', 3000);
        }
    });
}

/**
 * 更新系统状态显示
 */
function updateSystemStatus(status) {
    if (!status || !status.system) {
        console.warn('系统状态数据格式错误');
        return;
    }

    try {
        // 更新CPU使用率
        updateResourceUsage('cpu', status.system.cpu);
        
        // 更新内存使用率
        updateResourceUsage('memory', status.system.memory);
        
        // 更新磁盘使用率
        updateResourceUsage('disk', status.system.disk);
        
        // 更新系统运行时间
        updateUptime(status.uptime);
        
        // 更新服务状态
        if (status.services) {
            updateServiceStatus(status.services);
        }
        
    } catch (error) {
        console.error('更新系统状态时出错:', error);
    }
}

/**
 * 更新资源使用率显示
 */
function updateResourceUsage(type, data) {
    let percent, usage;
    
    if (type === 'cpu') {
        percent = data;
        usage = `${percent.toFixed(1)}%`;
    } else if (type === 'memory') {
        percent = data.percent;
        usage = `${data.used}/${data.total}`;
    } else if (type === 'disk') {
        percent = data.percent;
        usage = `${data.used}/${data.total}`;
    } else {
        return;
    }

    // 更新徽章
    const badgeSelector = `.monitor-card .card-body .monitor-item:nth-child(${getResourceIndex(type)}) .badge`;
    const badge = document.querySelector(badgeSelector);
    if (badge) {
        badge.textContent = usage;
        badge.className = `badge bg-${getStatusClass(percent)}`;
    }

    // 更新进度条
    const progressSelector = `.monitor-card .card-body .monitor-item:nth-child(${getResourceIndex(type)}) .progress-bar`;
    const progressBar = document.querySelector(progressSelector);
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
        progressBar.className = `progress-bar bg-${getStatusClass(percent)}`;
    }
}

/**
 * 获取资源类型对应的索引
 */
function getResourceIndex(type) {
    const indices = { cpu: 1, memory: 2, disk: 3 };
    return indices[type] || 1;
}

/**
 * 根据使用率获取状态样式类
 */
function getStatusClass(percent) {
    if (percent > 80) return 'danger';
    if (percent > 60) return 'warning';
    return 'success';
}

/**
 * 更新系统运行时间
 */
function updateUptime(uptime) {
    const uptimeElement = document.querySelector('.monitor-card .card-body .mt-3 small');
    if (uptimeElement && uptime) {
        uptimeElement.innerHTML = `<i class="fas fa-clock me-1"></i>系统运行时间: ${uptime}`;
    }
}

/**
 * 更新服务状态
 */
function updateServiceStatus(services) {
    // 更新各个服务的状态指示器
    Object.keys(services).forEach(service => {
        const status = services[service];
        const indicator = document.querySelector(`.status-indicator.status-${service}`);
        if (indicator) {
            // 更新状态类
            indicator.className = `status-indicator status-${getServiceStatusClass(status)}`;
        }
        
        // 更新状态文本
        const statusText = document.querySelector(`[data-service="${service}"] .service-status-text`);
        if (statusText) {
            statusText.textContent = getServiceStatusText(status);
            statusText.className = `service-status-text text-${getServiceTextClass(status)}`;
        }
    });
}

/**
 * 获取服务状态样式类
 */
function getServiceStatusClass(status) {
    const statusMap = {
        'healthy': 'healthy',
        'running': 'healthy',
        'error': 'error',
        'stopped': 'error',
        'warning': 'warning'
    };
    return statusMap[status] || 'error';
}

/**
 * 获取服务状态文本
 */
function getServiceStatusText(status) {
    const textMap = {
        'healthy': '正常',
        'running': '运行中',
        'error': '异常',
        'stopped': '停止',
        'warning': '告警'
    };
    return textMap[status] || '未知';
}

/**
 * 获取服务状态文本样式类
 */
function getServiceTextClass(status) {
    const classMap = {
        'healthy': 'success',
        'running': 'success',
        'error': 'danger',
        'stopped': 'danger',
        'warning': 'warning'
    };
    return classMap[status] || 'secondary';
}

/**
 * 显示自动刷新指示器
 */
function showAutoRefreshIndicator() {
    let indicator = document.querySelector('.auto-refresh-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'auto-refresh-indicator';
        indicator.innerHTML = '<i class="fas fa-sync-alt me-1"></i>自动刷新中';
        document.body.appendChild(indicator);
    }
    indicator.style.display = 'block';
}

/**
 * 移除自动刷新指示器
 */
function removeAutoRefreshIndicator() {
    const indicator = document.querySelector('.auto-refresh-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * 显示加载状态
 */
function showLoadingState(container) {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    container.style.position = 'relative';
    container.appendChild(overlay);
}

/**
 * 隐藏加载状态
 */
function hideLoadingState(container) {
    const overlay = container.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * 显示错误状态
 */
function showErrorState(container, message) {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    
    if (container) {
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h5>加载失败</h5>
                <p>${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="location.reload()">
                    <i class="fas fa-refresh me-1"></i>重新加载
                </button>
            </div>
        `;
    }
}

/**
 * 格式化日期显示
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${month}-${day}`;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保Chart.js已加载
    if (typeof Chart !== 'undefined') {
        initializeDashboard();
    } else {
        console.error('Chart.js未加载，无法初始化图表');
    }
});
