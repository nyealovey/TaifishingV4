/* 泰摸鱼吧 - 实例统计页面脚本 */

let versionChart = null;
let statisticsInterval = null;

/**
 * 实例统计页面初始化
 */
function initializeInstanceStatistics() {
    console.log('实例统计页面初始化');
    createVersionChart();
    startAutoRefresh();
}

/**
 * 创建版本分布图
 */
function createVersionChart() {
    const ctx = document.getElementById('versionChart');
    if (!ctx) {
        console.warn('未找到版本图表容器');
        return;
    }
    
    // 获取版本统计数据（从服务器端渲染的数据）
    const versionStatsElement = document.getElementById('version-stats-data');
    let versionStats = [];
    
    if (versionStatsElement) {
        try {
            versionStats = JSON.parse(versionStatsElement.textContent);
        } catch (e) {
            console.error('解析版本统计数据失败:', e);
        }
    }
    
    if (!versionStats || versionStats.length === 0) {
        showEmptyChart(ctx);
        return;
    }
    
    // 准备图表数据
    const labels = versionStats.map(item => item.version || '未知版本');
    const data = versionStats.map(item => item.count || 0);
    const colors = generateColors(versionStats.length);
    
    // 创建饼图
    versionChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.backgrounds,
                borderColor: colors.borders,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 显示空图表
 */
function showEmptyChart(canvas) {
    const ctx = canvas.getContext('2d');
    ctx.font = '16px Arial';
    ctx.fillStyle = '#666';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('暂无版本统计数据', canvas.width / 2, canvas.height / 2);
}

/**
 * 生成图表颜色
 */
function generateColors(count) {
    const baseColors = [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
        '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3',
        '#d299c2', '#fef9d7', '#d69e2e', '#38a169'
    ];
    
    const backgrounds = [];
    const borders = [];
    
    for (let i = 0; i < count; i++) {
        const colorIndex = i % baseColors.length;
        backgrounds.push(baseColors[colorIndex] + '80'); // 50% opacity
        borders.push(baseColors[colorIndex]);
    }
    
    return { backgrounds, borders };
}

/**
 * 开始自动刷新
 */
function startAutoRefresh() {
    // 每60秒自动刷新统计数据
    statisticsInterval = setInterval(() => {
        refreshStatistics();
    }, 60000);
}

/**
 * 停止自动刷新
 */
function stopAutoRefresh() {
    if (statisticsInterval) {
        clearInterval(statisticsInterval);
        statisticsInterval = null;
    }
}

/**
 * 刷新统计数据
 */
function refreshStatistics() {
    fetchWithCSRF('/instances/api/statistics')
    .then(data => {
        if (data.success) {
            updateStatistics(data.data);
            console.log('统计数据刷新成功');
        } else {
            console.warn('刷新统计数据失败:', data.message);
        }
    })
    .catch(error => {
        console.error('刷新统计数据失败:', error);
    });
}

/**
 * 更新统计数据显示
 */
function updateStatistics(stats) {
    // 更新统计卡片
    updateStatCard('total-instances', stats.total_instances);
    updateStatCard('active-instances', stats.active_instances);
    updateStatCard('inactive-instances', stats.inactive_instances);
    updateStatCard('db-types-count', stats.db_types_count);
    
    // 如果版本统计数据发生变化，重新创建图表
    if (stats.version_stats && Array.isArray(stats.version_stats)) {
        updateVersionChart(stats.version_stats);
    }
}

/**
 * 更新统计卡片
 */
function updateStatCard(cardId, value) {
    const cardSelector = getStatCardSelector(cardId);
    const element = document.querySelector(cardSelector);
    
    if (element) {
        // 添加动画效果
        element.style.transition = 'all 0.3s ease';
        element.textContent = formatNumber(value || 0);
        
        // 短暂高亮效果
        element.style.transform = 'scale(1.05)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * 获取统计卡片选择器
 */
function getStatCardSelector(cardId) {
    const selectors = {
        'total-instances': '.card.bg-primary .card-title',
        'active-instances': '.card.bg-success .card-title',
        'inactive-instances': '.card.bg-warning .card-title',
        'db-types-count': '.card.bg-info .card-title'
    };
    return selectors[cardId] || '.card .card-title';
}

/**
 * 更新版本分布图
 */
function updateVersionChart(versionStats) {
    if (!versionChart || !versionStats.length) return;
    
    const labels = versionStats.map(item => item.version || '未知版本');
    const data = versionStats.map(item => item.count || 0);
    const colors = generateColors(versionStats.length);
    
    // 更新图表数据
    versionChart.data.labels = labels;
    versionChart.data.datasets[0].data = data;
    versionChart.data.datasets[0].backgroundColor = colors.backgrounds;
    versionChart.data.datasets[0].borderColor = colors.borders;
    
    // 重绘图表
    versionChart.update('active');
}

/**
 * 手动刷新统计数据
 */
function manualRefreshStats() {
    const refreshBtn = event?.target || document.querySelector('.btn-outline-primary');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>刷新中...';
        refreshBtn.disabled = true;
        
        refreshStatistics();
        
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
            if (typeof showMessage === 'function') {
                showMessage('统计数据已刷新', 'success', 2000);
            }
        }, 1000);
    }
}

/**
 * 导出统计数据
 */
function exportStatistics() {
    const data = {
        timestamp: new Date().toISOString(),
        total_instances: document.querySelector('.card.bg-primary .card-title')?.textContent || '0',
        active_instances: document.querySelector('.card.bg-success .card-title')?.textContent || '0',
        inactive_instances: document.querySelector('.card.bg-warning .card-title')?.textContent || '0',
        db_types_count: document.querySelector('.card.bg-info .card-title')?.textContent || '0'
    };
    
    const jsonData = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `instance_statistics_${new Date().toISOString().split('T')[0]}.json`;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    
    if (typeof showMessage === 'function') {
        showMessage('统计数据已导出', 'success', 2000);
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
 * 清理资源
 */
function cleanup() {
    stopAutoRefresh();
    
    if (versionChart) {
        versionChart.destroy();
        versionChart = null;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保Chart.js已加载
    if (typeof Chart !== 'undefined') {
        initializeInstanceStatistics();
    } else {
        console.error('Chart.js未加载，无法初始化图表');
    }
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    cleanup();
});
