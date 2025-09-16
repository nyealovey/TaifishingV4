/* 泰摸鱼吧 - 实例列表页面脚本 */

let deleteInstanceId = null;

/**
 * 实例列表页面初始化
 */
function initializeInstancesList() {
    console.log('实例列表页面初始化');
    setupEventListeners();
    setupUploadMethodToggle();
    initializeTooltips();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 删除确认按钮
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', handleDeleteInstance);
    }

    // 批量创建表单
    const batchCreateForm = document.getElementById('batchCreateForm');
    if (batchCreateForm) {
        batchCreateForm.addEventListener('submit', handleBatchCreate);
    }

    // 文件选择处理
    const csvFileInput = document.getElementById('csvFile');
    if (csvFileInput) {
        csvFileInput.addEventListener('change', handleFileSelect);
    }
}

/**
 * 设置上传方式切换
 */
function setupUploadMethodToggle() {
    const uploadMethodRadios = document.querySelectorAll('input[name="uploadMethod"]');
    uploadMethodRadios.forEach(radio => {
        radio.addEventListener('change', toggleUploadMethod);
    });
}

/**
 * 初始化工具提示
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 测试数据库连接
 */
function testConnection(instanceId) {
    if (!instanceId) {
        showAlert('warning', '实例ID无效');
        return;
    }

    const testBtn = event.target.closest('button');
    const originalHtml = testBtn.innerHTML;
    
    testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    testBtn.disabled = true;

    fetchWithCSRF(`/instances/api/instances/${instanceId}/test`)
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || '连接测试成功');
        } else {
            showAlert('danger', data.error || '连接测试失败');
        }
    })
    .catch(error => {
        console.error('连接测试失败:', error);
        showAlert('danger', '连接测试失败: ' + error.message);
    })
    .finally(() => {
        testBtn.innerHTML = originalHtml;
        testBtn.disabled = false;
    });
}

/**
 * 同步实例账户
 */
function syncInstance(instanceId) {
    if (!instanceId) {
        showAlert('warning', '实例ID无效');
        return;
    }

    const syncBtn = event.target.closest('button');
    const originalHtml = syncBtn.innerHTML;
    
    syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    syncBtn.disabled = true;

    fetchWithCSRF(`/instances/${instanceId}/sync`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success || data.message) {
            showAlert('success', data.message || '账户同步成功');
        } else {
            showAlert('danger', data.error || '账户同步失败');
        }
    })
    .catch(error => {
        console.error('账户同步失败:', error);
        showAlert('danger', '账户同步失败: ' + error.message);
    })
    .finally(() => {
        syncBtn.innerHTML = originalHtml;
        syncBtn.disabled = false;
    });
}

/**
 * 删除实例
 */
function deleteInstance(instanceId, instanceName) {
    deleteInstanceId = instanceId;
    document.getElementById('deleteInstanceName').textContent = instanceName;
    
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    deleteModal.show();
}

/**
 * 处理删除实例确认
 */
function handleDeleteInstance() {
    if (!deleteInstanceId) return;

    const confirmBtn = document.getElementById('confirmDelete');
    const originalText = confirmBtn.textContent;
    
    confirmBtn.textContent = '删除中...';
    confirmBtn.disabled = true;

    fetchWithCSRF(`/instances/${deleteInstanceId}`, {
        method: 'DELETE'
    })
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || '实例删除成功');
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            // 刷新页面
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('danger', data.error || '删除失败');
        }
    })
    .catch(error => {
        console.error('删除实例失败:', error);
        showAlert('danger', '删除失败: ' + error.message);
    })
    .finally(() => {
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        deleteInstanceId = null;
    });
}

/**
 * 切换上传方式
 */
function toggleUploadMethod() {
    const fileUploadArea = document.getElementById('fileUploadArea');
    const jsonInputArea = document.getElementById('jsonInputArea');
    const selectedMethod = document.querySelector('input[name="uploadMethod"]:checked').value;

    if (selectedMethod === 'file') {
        fileUploadArea.style.display = 'block';
        jsonInputArea.style.display = 'none';
    } else {
        fileUploadArea.style.display = 'none';
        jsonInputArea.style.display = 'block';
    }
}

/**
 * 处理文件选择
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    const previewDiv = document.getElementById('csvPreview');
    
    if (!file) {
        previewDiv.innerHTML = '';
        return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
        showAlert('warning', '请选择CSV格式的文件');
        event.target.value = '';
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const csv = e.target.result;
        const lines = csv.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
            showAlert('warning', 'CSV文件至少需要包含标题行和一行数据');
            return;
        }

        // 显示预览
        let previewHtml = '<div class="mt-3"><h6>文件预览（前5行）：</h6><div class="table-responsive"><table class="table table-sm table-bordered">';
        
        lines.slice(0, Math.min(5, lines.length)).forEach((line, index) => {
            const cells = line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
            previewHtml += '<tr>';
            cells.forEach(cell => {
                previewHtml += `<${index === 0 ? 'th' : 'td'}>${escapeHtml(cell)}</${index === 0 ? 'th' : 'td'}>`;
            });
            previewHtml += '</tr>';
        });
        
        previewHtml += '</table></div></div>';
        previewDiv.innerHTML = previewHtml;
    };
    
    reader.readAsText(file);
}

/**
 * 处理批量创建
 */
function handleBatchCreate(event) {
    event.preventDefault();
    
    const selectedMethod = document.querySelector('input[name="uploadMethod"]:checked').value;
    
    if (selectedMethod === 'file') {
        submitFileUpload();
    } else {
        submitJsonInput();
    }
}

/**
 * 提交文件上传
 */
function submitFileUpload() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];

    if (!file) {
        showAlert('warning', '请选择要上传的CSV文件');
        return;
    }

    const formData = new FormData();
    formData.append('csv_file', file);

    const btn = document.querySelector('#batchCreateModal .btn-primary');
    const originalText = btn.textContent;

    btn.textContent = '创建中...';
    btn.disabled = true;

    fetchWithCSRF('/instances/batch-create', {
        method: 'POST',
        body: formData
    })
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            if (data.errors && data.errors.length > 0) {
                showAlert('warning', `部分实例创建失败：\n${data.errors.join('\n')}`);
            }
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('batchCreateModal')).hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('danger', data.error);
        }
    })
    .catch(error => {
        console.error('批量创建失败:', error);
        showAlert('danger', '批量创建失败: ' + error.message);
    })
    .finally(() => {
        btn.textContent = originalText;
        btn.disabled = false;
    });
}

/**
 * 提交JSON输入
 */
function submitJsonInput() {
    const dataText = document.getElementById('batchInstancesData').value.trim();

    if (!dataText) {
        showAlert('warning', '请输入实例数据');
        return;
    }

    try {
        const instances = JSON.parse(dataText);

        if (!Array.isArray(instances)) {
            showAlert('warning', '实例数据必须是数组格式');
            return;
        }

        if (instances.length === 0) {
            showAlert('warning', '至少需要提供一个实例');
            return;
        }

        const btn = document.querySelector('#batchCreateModal .btn-primary');
        const originalText = btn.textContent;

        btn.textContent = '创建中...';
        btn.disabled = true;

        fetchWithCSRF('/instances/batch-create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ instances: instances })
        })
        .then(data => {
            if (data.success) {
                showAlert('success', data.message);
                if (data.errors && data.errors.length > 0) {
                    showAlert('warning', `部分实例创建失败：\n${data.errors.join('\n')}`);
                }
                // 关闭模态框
                bootstrap.Modal.getInstance(document.getElementById('batchCreateModal')).hide();
                setTimeout(() => location.reload(), 1000);
            } else {
                showAlert('danger', data.error);
            }
        })
        .catch(error => {
            console.error('批量创建失败:', error);
            showAlert('danger', '批量创建失败: ' + error.message);
        })
        .finally(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        });

    } catch (error) {
        showAlert('danger', 'JSON格式错误，请检查输入数据');
    }
}

/**
 * 显示提示消息
 */
function showAlert(type, message) {
    // 移除现有的提示
    const existingAlerts = document.querySelectorAll('.alert-dismissible');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // 插入到页面顶部
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
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
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '未知';
    return new Date(dateString).toLocaleString('zh-CN');
}

/**
 * 批量操作功能
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const rowCheckboxes = document.querySelectorAll('input[name="selected_instances"]');
    
    rowCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBatchActions();
}

/**
 * 更新批量操作按钮状态
 */
function updateBatchActions() {
    const selectedCheckboxes = document.querySelectorAll('input[name="selected_instances"]:checked');
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

/**
 * 批量测试连接
 */
function batchTestConnection() {
    const selectedCheckboxes = document.querySelectorAll('input[name="selected_instances"]:checked');
    const instanceIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (instanceIds.length === 0) {
        showAlert('warning', '请先选择要测试的实例');
        return;
    }

    const testBtn = event.target;
    const originalText = testBtn.textContent;
    
    testBtn.textContent = '测试中...';
    testBtn.disabled = true;

    Promise.all(instanceIds.map(id => 
        fetchWithCSRF(`/instances/api/instances/${id}/test`)
    ))
    .then(results => {
        const successCount = results.filter(r => r.success).length;
        const failCount = results.length - successCount;
        
        if (failCount === 0) {
            showAlert('success', `批量测试完成，${successCount}个实例连接正常`);
        } else {
            showAlert('warning', `批量测试完成，${successCount}个成功，${failCount}个失败`);
        }
    })
    .catch(error => {
        console.error('批量测试失败:', error);
        showAlert('danger', '批量测试失败');
    })
    .finally(() => {
        testBtn.textContent = originalText;
        testBtn.disabled = false;
    });
}

/**
 * 批量同步账户
 */
function batchSyncAccounts() {
    const selectedCheckboxes = document.querySelectorAll('input[name="selected_instances"]:checked');
    const instanceIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (instanceIds.length === 0) {
        showAlert('warning', '请先选择要同步的实例');
        return;
    }

    if (!confirm(`确定要同步选中的${instanceIds.length}个实例的账户吗？`)) {
        return;
    }

    const syncBtn = event.target;
    const originalText = syncBtn.textContent;
    
    syncBtn.textContent = '同步中...';
    syncBtn.disabled = true;

    Promise.all(instanceIds.map(id => 
        fetchWithCSRF(`/instances/${id}/sync`, { method: 'POST' })
    ))
    .then(results => {
        const successCount = results.filter(r => r.success || r.message).length;
        const failCount = results.length - successCount;
        
        if (failCount === 0) {
            showAlert('success', `批量同步完成，${successCount}个实例同步成功`);
        } else {
            showAlert('warning', `批量同步完成，${successCount}个成功，${failCount}个失败`);
        }
        
        // 刷新页面显示最新数据
        setTimeout(() => location.reload(), 2000);
    })
    .catch(error => {
        console.error('批量同步失败:', error);
        showAlert('danger', '批量同步失败');
    })
    .finally(() => {
        syncBtn.textContent = originalText;
        syncBtn.disabled = false;
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeInstancesList();
});
