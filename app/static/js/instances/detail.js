/* 泰摸鱼吧 - 实例详情页面脚本 */

/**
 * 实例详情页面初始化
 */
function initializeInstanceDetailPage() {
    // 页面加载完成，等待用户手动测试连接
    console.log('实例详情页面已加载');
}

/**
 * 测试数据库连接
 */
function testConnection() {
    const testBtn = event ? event.target : document.querySelector('button[onclick="testConnection()"]');
    if (!testBtn) return;
    
    const originalText = testBtn.innerHTML;
    const instanceId = getInstanceId();
    const instanceName = getInstanceName();

    // 记录操作开始日志
    if (typeof logUserAction === 'function') {
        logUserAction('开始测试连接', {
            operation: 'test_connection',
            instance_id: instanceId,
            instance_name: instanceName
        });
    }

    // 设置加载状态
    setTestButtonLoading(testBtn, true);

    // 获取CSRF token
    const csrfToken = getCSRFToken();

    fetch(`/instances/api/instances/${instanceId}/test`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                throw new Error('认证失败，请重新登录');
            } else if (response.status === 404) {
                throw new Error('API接口不存在');
            } else {
                throw new Error(`HTTP错误: ${response.status}`);
            }
        }
        return response.json();
    })
    .then(data => {
        handleTestResult(data, instanceId, instanceName);
    })
    .catch(error => {
        handleTestError(error, instanceId, instanceName);
    })
    .finally(() => {
        setTestButtonLoading(testBtn, false, originalText);
    });
}

/**
 * 处理测试成功结果
 */
function handleTestResult(data, instanceId, instanceName) {
    const statusBadge = document.getElementById('connectionStatus');
    const resultDiv = document.getElementById('testResult');
    const contentDiv = document.getElementById('testResultContent');

    if (data.success) {
        // 记录成功日志
        if (typeof logUserAction === 'function') {
            logUserAction('测试连接成功', {
                operation: 'test_connection',
                instance_id: instanceId,
                instance_name: instanceName,
                result: 'success',
                message: data.message || '数据库连接正常'
            });
        }

        // 更新状态显示
        if (statusBadge) {
            statusBadge.textContent = '正常';
            statusBadge.className = 'badge bg-success';
        }

        // 显示成功信息
        if (contentDiv) {
            contentDiv.innerHTML = createSuccessAlert(data.message || '数据库连接正常');
        }

        // 显示结果容器
        if (resultDiv) {
            resultDiv.style.display = 'block';
        }
    } else if (data.error) {
        handleTestFailure(data, instanceId, instanceName);
    }
}

/**
 * 处理测试失败结果
 */
function handleTestFailure(data, instanceId, instanceName) {
    const statusBadge = document.getElementById('connectionStatus');
    const resultDiv = document.getElementById('testResult');
    const contentDiv = document.getElementById('testResultContent');

    // 记录失败日志
    if (typeof logError === 'function') {
        logError('测试连接失败', {
            operation: 'test_connection',
            instance_id: instanceId,
            instance_name: instanceName,
            result: 'failed',
            error: data.error
        });
    }

    // 更新状态显示
    if (statusBadge) {
        statusBadge.textContent = '失败';
        statusBadge.className = 'badge bg-danger';
    }

    // 构建详细的错误信息
    const errorHtml = buildErrorMessage(data);

    // 显示错误信息
    if (contentDiv) {
        contentDiv.innerHTML = errorHtml;
    }

    // 显示结果容器
    if (resultDiv) {
        resultDiv.style.display = 'block';
    }
}

/**
 * 处理测试错误
 */
function handleTestError(error, instanceId, instanceName) {
    console.error('测试连接时发生错误:', error);

    // 记录错误日志
    if (typeof logError === 'function') {
        logError('测试连接异常', {
            operation: 'test_connection',
            instance_id: instanceId,
            instance_name: instanceName,
            result: 'error',
            error: error.message
        });
    }

    const statusBadge = document.getElementById('connectionStatus');
    const resultDiv = document.getElementById('testResult');
    const contentDiv = document.getElementById('testResultContent');

    // 更新状态显示
    if (statusBadge) {
        statusBadge.textContent = '异常';
        statusBadge.className = 'badge bg-warning';
    }

    // 显示错误信息
    if (contentDiv) {
        contentDiv.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>测试异常！</strong><br>
                ${error.message}
            </div>
        `;
    }

    // 显示结果容器
    if (resultDiv) {
        resultDiv.style.display = 'block';
    }
}

/**
 * 构建错误消息HTML
 */
function buildErrorMessage(data) {
    let errorHtml = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>连接失败！</strong><br>
            <strong>错误类型：</strong>${data.error}<br>
    `;

    // 添加详细信息
    if (data.details) {
        errorHtml += `<strong>详细信息：</strong>${data.details}<br>`;
    }

    // 添加解决方案
    if (data.solution) {
        errorHtml += `<strong>解决方案：</strong>${data.solution}<br>`;
    }

    // 添加错误类型
    if (data.error_type) {
        errorHtml += `<strong>错误类型：</strong>${data.error_type}<br>`;
    }

    // 添加SQL状态
    if (data.sql_state) {
        errorHtml += `<strong>SQL状态：</strong>${data.sql_state}<br>`;
    }

    // 添加错误代码
    if (data.error_code) {
        errorHtml += `<strong>错误代码：</strong>${data.error_code}<br>`;
    }

    errorHtml += '</div>';
    return errorHtml;
}

/**
 * 创建成功提示HTML
 */
function createSuccessAlert(message) {
    return `
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            <strong>连接成功！</strong><br>
            ${message}
        </div>
    `;
}

/**
 * 设置测试按钮加载状态
 */
function setTestButtonLoading(button, isLoading, originalText = null) {
    if (isLoading) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>测试中...';
        button.disabled = true;
    } else {
        button.innerHTML = originalText || '<i class="fas fa-plug me-2"></i>测试连接';
        button.disabled = false;
    }
}

/**
 * 获取实例ID
 */
function getInstanceId() {
    // 从URL中提取实例ID
    const pathParts = window.location.pathname.split('/');
    const instanceIndex = pathParts.indexOf('instances');
    if (instanceIndex !== -1 && pathParts[instanceIndex + 1]) {
        return parseInt(pathParts[instanceIndex + 1]);
    }
    
    // 从页面元素中获取
    const instanceElement = document.querySelector('[data-instance-id]');
    if (instanceElement) {
        return parseInt(instanceElement.getAttribute('data-instance-id'));
    }
    
    return null;
}

/**
 * 获取实例名称
 */
function getInstanceName() {
    const instanceElement = document.querySelector('[data-instance-name]');
    if (instanceElement) {
        return instanceElement.getAttribute('data-instance-name');
    }
    
    const titleElement = document.querySelector('.card-title');
    if (titleElement) {
        return titleElement.textContent.trim();
    }
    
    return '未知实例';
}

/**
 * 同步账户
 */
function syncAccounts() {
    const syncBtn = event ? event.target : document.querySelector('button[onclick="syncAccounts()"]');
    if (!syncBtn) return;
    
    const originalText = syncBtn.innerHTML;
    const instanceId = getInstanceId();
    const instanceName = getInstanceName();

    // 确认操作
    if (!confirm('确定要同步账户信息吗？')) {
        return;
    }

    // 记录操作开始日志
    if (typeof logUserAction === 'function') {
        logUserAction('开始同步账户', {
            operation: 'sync_accounts',
            instance_id: instanceId,
            instance_name: instanceName
        });
    }

    // 设置加载状态
    syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>同步中...';
    syncBtn.disabled = true;

    // 获取CSRF token
    const csrfToken = getCSRFToken();

    fetch(`/instances/${instanceId}/sync`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            if (typeof showMessage === 'function') {
                showMessage(data.message, data.result ? 'success' : 'error');
            } else {
                alert(data.message);
            }
        }
        
        // 记录结果日志
        if (typeof logUserAction === 'function') {
            logUserAction('同步账户完成', {
                operation: 'sync_accounts',
                instance_id: instanceId,
                instance_name: instanceName,
                result: data.result ? 'success' : 'failed',
                message: data.message
            });
        }
    })
    .catch(error => {
        console.error('同步账户时发生错误:', error);
        if (typeof showMessage === 'function') {
            showMessage('同步失败: ' + error.message, 'error');
        } else {
            alert('同步失败: ' + error.message);
        }
    })
    .finally(() => {
        syncBtn.innerHTML = originalText;
        syncBtn.disabled = false;
    });
}

/**
 * 显示变更历史
 */
function showHistory() {
    const instanceId = getInstanceId();
    
    if (typeof showMessage === 'function') {
        showMessage('变更历史功能正在开发中...', 'info');
    } else {
        alert('变更历史功能正在开发中...');
    }
}

/**
 * 获取CSRF Token的通用函数
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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeInstanceDetailPage();
});
