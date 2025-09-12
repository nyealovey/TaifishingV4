/**
 * 权限模态框组件
 * 提供统一的权限显示模态框功能
 */

/**
 * 显示权限模态框
 * @param {Object} permissions - 权限数据
 * @param {Object} account - 账户数据
 */
function showPermissionsModal(permissions, account) {
    console.log('showPermissionsModal 被调用');
    console.log('权限数据:', permissions);
    console.log('账户数据:', account);
    
    try {
        // 获取数据库类型
        const dbType = account.db_type;
        console.log('数据库类型:', dbType);
        
        // 检查权限对象的所有属性
        console.log('权限对象检查 - 所有属性:', Object.keys(permissions));
        
        // 创建或获取模态框
        let modal = document.getElementById('permissionsModal');
        if (!modal) {
            modal = createPermissionsModal();
            document.body.appendChild(modal);
        }
        
        // 更新模态框标题
        const titleElement = document.getElementById('permissionsModalTitle');
        if (titleElement) {
            titleElement.textContent = `账户权限详情 - ${account.username}`;
        }
        
        // 渲染权限内容
        const bodyElement = document.getElementById('permissionsModalBody');
        if (bodyElement) {
            bodyElement.innerHTML = renderPermissionsByType(permissions, dbType);
        }
        
        // 显示模态框
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        console.log('模态框显示完成');
    } catch (error) {
        console.error('showPermissionsModal 函数执行出错:', error);
        console.error('错误堆栈:', error.stack);
        if (window.showAlert) {
            window.showAlert('danger', '显示权限信息时发生错误: ' + error.message);
        }
    }
}

/**
 * 创建权限模态框HTML
 * @returns {HTMLElement} 模态框元素
 */
function createPermissionsModal() {
    const modalHtml = `
        <div class="modal fade" id="permissionsModal" tabindex="-1" aria-labelledby="permissionsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="permissionsModalLabel">
                            <i class="fas fa-shield-alt me-2"></i>
                            <span id="permissionsModalTitle">账户权限详情</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="permissionsModalBody">
                        <!-- 权限内容将动态渲染 -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = modalHtml;
    return tempDiv.firstElementChild;
}

/**
 * 根据数据库类型渲染权限
 * @param {Object} permissions - 权限数据
 * @param {string} dbType - 数据库类型
 * @returns {string} 渲染的HTML
 */
function renderPermissionsByType(permissions, dbType) {
    switch (dbType) {
        case 'mysql':
            return renderMySQLPermissions(permissions);
        case 'postgresql':
            return renderPostgreSQLPermissions(permissions);
        case 'oracle':
            return renderOraclePermissions(permissions);
        case 'sqlserver':
            return renderSQLServerPermissions(permissions);
        default:
            return renderDefaultPermissions(permissions, dbType);
    }
}

/**
 * 渲染MySQL权限
 * @param {Object} permissions - 权限数据
 * @returns {string} 渲染的HTML
 */
function renderMySQLPermissions(permissions) {
    return `
        <div class="mb-3">
            <h6><i class="fas fa-shield-alt text-primary me-2"></i>全局权限</h6>
            <div class="row">
                ${permissions.global_privileges && permissions.global_privileges.map ? permissions.global_privileges.map(perm => `
                    <div class="col-md-6 mb-2">
                        <span class="badge ${perm.granted ? 'bg-success' : 'bg-secondary'} me-2">
                            ${perm.granted ? '✓' : '✗'}
                        </span>
                        ${perm.privilege}
                    </div>
                `).join('') : '<p class="text-muted">无全局权限</p>'}
            </div>
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-database text-success me-2"></i>数据库权限</h6>
            ${permissions.database_privileges && permissions.database_privileges.length > 0 ? `
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>数据库</th>
                                <th>权限</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${permissions.database_privileges.map(db => `
                                <tr>
                                    <td>${db.database}</td>
                                    <td>
                                        ${db.privileges.map(priv => `
                                            <span class="badge bg-success me-1">${priv}</span>
                                        `).join('')}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p class="text-muted">无数据库权限</p>'}
        </div>
    `;
}

/**
 * 渲染PostgreSQL权限
 * @param {Object} permissions - 权限数据
 * @returns {string} 渲染的HTML
 */
function renderPostgreSQLPermissions(permissions) {
    return `
        <div class="mb-3">
            <h6><i class="fas fa-user-shield text-primary me-2"></i>角色属性</h6>
            ${permissions.role_attributes && permissions.role_attributes.length > 0 ? `
                <div class="row">
                    ${permissions.role_attributes.map(attr => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-primary me-2">
                                <i class="fas fa-user-cog me-1"></i>${attr}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无角色属性</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-database text-success me-2"></i>数据库权限</h6>
            ${permissions.database_privileges && permissions.database_privileges.length > 0 ? `
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>数据库</th>
                                <th>权限</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${permissions.database_privileges.map(db => `
                                <tr>
                                    <td>${db.database}</td>
                                    <td>
                                        ${db.privileges.map(priv => `
                                            <span class="badge bg-success me-1">${priv}</span>
                                        `).join('')}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p class="text-muted">无数据库权限</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-hdd text-info me-2"></i>表空间权限</h6>
            ${permissions.tablespace_privileges && permissions.tablespace_privileges.length > 0 ? `
                <div class="row">
                    ${permissions.tablespace_privileges.map(priv => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-info me-2">
                                <i class="fas fa-hdd me-1"></i>${priv}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无表空间权限</p>'}
        </div>
    `;
}

/**
 * 渲染Oracle权限
 * @param {Object} permissions - 权限数据
 * @returns {string} 渲染的HTML
 */
function renderOraclePermissions(permissions) {
    return `
        <div class="mb-3">
            <h6><i class="fas fa-crown text-primary me-2"></i>角色</h6>
            ${permissions.roles && permissions.roles.length > 0 ? `
                <div class="row">
                    ${permissions.roles.map(role => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-primary me-2">
                                <i class="fas fa-crown me-1"></i>${role}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无角色</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-shield-alt text-success me-2"></i>系统权限</h6>
            ${permissions.system_privileges && permissions.system_privileges.length > 0 ? `
                <div class="row">
                    ${permissions.system_privileges.map(priv => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-success me-2">
                                <i class="fas fa-shield-alt me-1"></i>${priv}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无系统权限</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-hdd text-info me-2"></i>表空间权限</h6>
            ${permissions.tablespace_privileges && permissions.tablespace_privileges.length > 0 ? `
                <div class="row">
                    ${permissions.tablespace_privileges.map(priv => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-info me-2">
                                <i class="fas fa-hdd me-1"></i>${priv}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无表空间权限</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-chart-pie text-warning me-2"></i>表空间配额</h6>
            ${permissions.tablespace_quotas && permissions.tablespace_quotas.length > 0 ? `
                <div class="row">
                    ${permissions.tablespace_quotas.map(quota => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-warning me-2">
                                <i class="fas fa-chart-pie me-1"></i>${quota}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无表空间配额</p>'}
        </div>
    `;
}

/**
 * 渲染SQL Server权限
 * @param {Object} permissions - 权限数据
 * @returns {string} 渲染的HTML
 */
function renderSQLServerPermissions(permissions) {
    return `
        <div class="mb-3">
            <h6><i class="fas fa-crown text-primary me-2"></i>服务器角色</h6>
            ${permissions.server_roles && permissions.server_roles.length > 0 ? `
                <div class="row">
                    ${permissions.server_roles.map(role => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-primary me-2">
                                <i class="fas fa-crown me-1"></i>${role}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无服务器角色</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-database text-info me-2"></i>数据库角色</h6>
            ${permissions.database_roles && Object.keys(permissions.database_roles).length > 0 ? `
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>数据库</th>
                                <th>角色</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(permissions.database_roles).map(([dbName, roles]) => `
                                <tr>
                                    <td>${dbName}</td>
                                    <td>
                                        ${roles.map(role => `
                                            <span class="badge bg-info me-1">${role}</span>
                                        `).join('')}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p class="text-muted">无数据库角色</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-shield-alt text-success me-2"></i>服务器权限</h6>
            ${permissions.server_permissions && permissions.server_permissions.length > 0 ? `
                <div class="row">
                    ${permissions.server_permissions.map(perm => `
                        <div class="col-md-6 mb-2">
                            <span class="badge bg-success me-2">
                                <i class="fas fa-shield-alt me-1"></i>${perm}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : '<p class="text-muted">无服务器权限</p>'}
        </div>
        <div class="mb-3">
            <h6><i class="fas fa-database text-warning me-2"></i>数据库权限</h6>
            ${permissions.database_privileges && Object.keys(permissions.database_privileges).length > 0 ? `
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>数据库</th>
                                <th>权限</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(permissions.database_privileges).map(([dbName, perms]) => `
                                <tr>
                                    <td>${dbName}</td>
                                    <td>
                                        ${perms.map(perm => `
                                            <span class="badge bg-warning me-1">${perm}</span>
                                        `).join('')}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p class="text-muted">无数据库权限</p>'}
        </div>
    `;
}

/**
 * 渲染默认权限（未知数据库类型）
 * @param {Object} permissions - 权限数据
 * @param {string} dbType - 数据库类型
 * @returns {string} 渲染的HTML
 */
function renderDefaultPermissions(permissions, dbType) {
    return `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            未知的数据库类型: ${dbType}
        </div>
        <div class="mb-3">
            <h6>权限数据</h6>
            <pre class="bg-light p-3">${JSON.stringify(permissions, null, 2)}</pre>
        </div>
    `;
}

// 导出到全局作用域
window.showPermissionsModal = showPermissionsModal;
window.createPermissionsModal = createPermissionsModal;
window.renderPermissionsByType = renderPermissionsByType;
