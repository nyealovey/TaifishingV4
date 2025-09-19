# 外部SSL证书使用指南

## 🎯 概述

本指南介绍如何使用外部购买的SSL证书（如chint.com.pem和chint.com.key）替换自签名证书，实现生产级别的HTTPS访问。

## 🔐 支持的证书类型

### 1. 单域名证书
- **文件**: `chint.com.pem`, `chint.com.key`
- **域名**: chint.com
- **用途**: 单个域名访问

### 2. 通配符证书
- **文件**: `*.chint.com.pem`, `*.chint.com.key`
- **域名**: *.chint.com
- **用途**: 子域名访问

### 3. 多域名证书
- **文件**: `chint.com.pem`, `chint.com.key`
- **域名**: chint.com, www.chint.com, api.chint.com
- **用途**: 多个域名访问

### 4. 证书链文件
- **文件**: `chint.com.chain.pem`
- **用途**: 中间证书，提高兼容性

## 🚀 快速开始

### 1. 准备证书文件

将您购买的SSL证书文件放在项目根目录：

```bash
# 证书文件结构
TaifishV4/
├── chint.com.pem          # 证书文件
├── chint.com.key          # 私钥文件
└── chint.com.chain.pem    # 证书链文件（可选）
```

### 2. 验证证书

```bash
# 验证证书格式和有效性
./scripts/verify-ssl-cert.sh chint.com.pem chint.com.key

# 验证特定域名
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key -d chint.com

# 详细验证
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key -d chint.com -v
```

### 3. 更新证书到容器

```bash
# 使用默认文件名
./scripts/update-external-ssl.sh

# 指定证书文件
./scripts/update-external-ssl.sh -c chint.com.pem -k chint.com.key

# 指定证书名称
./scripts/update-external-ssl.sh -n chint.com -c chint.com.pem -k chint.com.key
```

### 4. 访问HTTPS应用

- **HTTPS访问**: https://chint.com
- **管理界面**: https://chint.com/admin
- **API接口**: https://chint.com/api

## 📁 文件结构

```
TaifishV4/
├── scripts/
│   ├── update-external-ssl.sh    # 外部证书更新脚本
│   ├── verify-ssl-cert.sh        # 证书验证脚本
│   └── ssl-backup.sh             # 证书备份脚本
├── nginx/local/
│   ├── conf.d/
│   │   ├── whalefall.conf                    # 自签名证书配置
│   │   └── whalefall-external-ssl.conf       # 外部证书配置模板
│   └── ssl/
│       ├── cert.pem              # 当前证书
│       ├── key.pem               # 当前私钥
│       └── backup/               # 证书备份目录
└── docs/deployment/
    └── EXTERNAL_SSL_CERTIFICATE.md  # 本文档
```

## ⚙️ 详细配置

### 1. 证书更新脚本

#### 基本用法
```bash
# 使用默认文件名 (chint.com.pem, chint.com.key)
./scripts/update-external-ssl.sh

# 指定证书文件
./scripts/update-external-ssl.sh -c mycert.pem -k mykey.key

# 指定证书名称
./scripts/update-external-ssl.sh -n mydomain.com -c mycert.pem -k mykey.key
```

#### 高级选项
```bash
# 强制更新（不备份）
./scripts/update-external-ssl.sh -f -c chint.com.pem -k chint.com.key

# 仅验证证书
./scripts/update-external-ssl.sh -v -c chint.com.pem -k chint.com.key

# 备份当前证书
./scripts/update-external-ssl.sh -b

# 恢复备份证书
./scripts/update-external-ssl.sh -r
```

### 2. 证书验证脚本

#### 基本验证
```bash
# 验证证书文件
./scripts/verify-ssl-cert.sh chint.com.pem chint.com.key

# 验证特定域名
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key -d chint.com
```

#### 在线验证
```bash
# 验证在线证书
./scripts/verify-ssl-cert.sh -d chint.com -p 443

# 验证特定端口
./scripts/verify-ssl-cert.sh -d chint.com -p 8443 -t 30
```

#### 详细验证
```bash
# 详细输出
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key -d chint.com -v
```

### 3. 证书备份脚本

#### 备份管理
```bash
# 备份当前证书
./scripts/ssl-backup.sh backup

# 指定备份名称
./scripts/ssl-backup.sh backup -n "chint_production"

# 列出所有备份
./scripts/ssl-backup.sh list

# 恢复最新备份
./scripts/ssl-backup.sh restore

# 恢复指定备份
./scripts/ssl-backup.sh restore -n "chint_production"
```

#### 清理管理
```bash
# 清理旧备份（保留5个）
./scripts/ssl-backup.sh clean

# 清理旧备份（保留3个）
./scripts/ssl-backup.sh clean -k 3

# 强制清理
./scripts/ssl-backup.sh clean -k 3 -f
```

#### 导入导出
```bash
# 导出证书到指定目录
./scripts/ssl-backup.sh export -d /backup/certs

# 从指定目录导入证书
./scripts/ssl-backup.sh import -d /backup/certs

# 同步证书到容器
./scripts/ssl-backup.sh sync
```

## 🔧 Nginx配置

### 1. 使用外部证书配置

编辑 `nginx/local/conf.d/whalefall-external-ssl.conf`：

```nginx
server {
    listen 443 ssl http2;
    server_name chint.com www.chint.com;
    
    # 外部SSL证书配置
    ssl_certificate /etc/nginx/ssl/chint.com.pem;
    ssl_certificate_key /etc/nginx/ssl/chint.com.key;
    
    # 证书链文件（如果CA提供了中间证书）
    ssl_trusted_certificate /etc/nginx/ssl/chint.com.chain.pem;
    
    # 其他配置...
}
```

### 2. 启用外部证书配置

```bash
# 重命名配置文件
mv nginx/local/conf.d/whalefall.conf nginx/local/conf.d/whalefall-self-signed.conf
mv nginx/local/conf.d/whalefall-external-ssl.conf nginx/local/conf.d/whalefall.conf

# 重启Nginx容器
docker-compose -f docker-compose.local.yml restart nginx
```

## 🧪 测试和验证

### 1. 证书验证测试

```bash
# 验证证书格式
openssl x509 -in chint.com.pem -text -noout

# 验证私钥格式
openssl rsa -in chint.com.key -check -noout

# 验证证书和私钥匹配
openssl x509 -noout -modulus -in chint.com.pem | openssl md5
openssl rsa -noout -modulus -in chint.com.key | openssl md5
```

### 2. HTTPS连接测试

```bash
# 测试HTTPS连接
curl -I https://chint.com

# 测试SSL握手
openssl s_client -connect chint.com:443 -servername chint.com

# 测试证书链
openssl s_client -connect chint.com:443 -showcerts
```

### 3. 浏览器测试

1. 打开浏览器访问 https://chint.com
2. 检查地址栏是否显示安全锁图标
3. 点击锁图标查看证书详情
4. 验证证书颁发者和有效期

## 🔒 安全配置

### 1. 文件权限设置

```bash
# 设置正确的文件权限
chmod 644 chint.com.pem
chmod 600 chint.com.key
chmod 644 chint.com.chain.pem

# 设置文件所有者
chown root:root chint.com.pem chint.com.key chint.com.chain.pem
```

### 2. 证书安全

```bash
# 定期检查证书有效期
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key

# 设置证书到期提醒
# 在crontab中添加：
# 0 9 * * 1 /path/to/scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key
```

### 3. 备份安全

```bash
# 定期备份证书
./scripts/ssl-backup.sh backup -n "weekly_backup_$(date +%Y%m%d)"

# 清理旧备份
./scripts/ssl-backup.sh clean -k 10
```

## 🐛 故障排除

### 常见问题

#### 1. 证书格式错误

**症状**: `unable to load certificate`

**解决方案**:
```bash
# 检查证书格式
openssl x509 -in chint.com.pem -text -noout

# 转换证书格式（如果需要）
openssl x509 -in chint.com.pem -outform PEM -out chint.com.pem
```

#### 2. 私钥不匹配

**症状**: `key values mismatch`

**解决方案**:
```bash
# 验证证书和私钥匹配
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key
```

#### 3. 证书链问题

**症状**: `certificate verify failed`

**解决方案**:
```bash
# 检查证书链
openssl s_client -connect chint.com:443 -showcerts

# 合并证书链
cat chint.com.pem chint.com.chain.pem > chint.com.full.pem
```

#### 4. 域名不匹配

**症状**: `certificate doesn't match`

**解决方案**:
1. 检查证书中的域名
2. 确保访问的域名与证书匹配
3. 使用正确的域名访问

### 日志分析

```bash
# 查看Nginx SSL日志
docker-compose -f docker-compose.local.yml logs nginx | grep ssl

# 查看SSL错误日志
tail -f userdata/nginx/logs/whalefall_external_ssl_error.log

# 查看SSL访问日志
tail -f userdata/nginx/logs/whalefall_external_ssl_access.log
```

## 📊 监控和维护

### 1. 证书监控

```bash
# 创建证书监控脚本
cat > monitor_cert.sh << 'EOF'
#!/bin/bash
if ! ./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key; then
    echo "SSL证书异常，请检查"
    # 发送告警邮件或通知
fi
EOF

chmod +x monitor_cert.sh
```

### 2. 自动备份

```bash
# 设置定时备份
crontab -e

# 添加以下行（每周备份）
0 2 * * 0 /path/to/scripts/ssl-backup.sh backup -n "weekly_$(date +\%Y\%m\%d)"
```

### 3. 证书续期

```bash
# 检查证书有效期
./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key

# 证书即将过期时，联系CA续期
# 续期后更新证书
./scripts/update-external-ssl.sh -c new_chint.com.pem -k new_chint.com.key
```

## 🌍 生产环境部署

### 1. 证书部署流程

1. **准备证书文件**
   ```bash
   # 将证书文件上传到服务器
   scp chint.com.pem chint.com.key user@server:/path/to/certs/
   ```

2. **验证证书**
   ```bash
   # 在服务器上验证证书
   ./scripts/verify-ssl-cert.sh -c chint.com.pem -k chint.com.key
   ```

3. **更新证书**
   ```bash
   # 更新证书到容器
   ./scripts/update-external-ssl.sh -c chint.com.pem -k chint.com.key
   ```

4. **测试访问**
   ```bash
   # 测试HTTPS访问
   curl -I https://chint.com
   ```

### 2. 高可用部署

```bash
# 多服务器证书同步
for server in server1 server2 server3; do
    scp chint.com.pem chint.com.key $server:/path/to/certs/
    ssh $server "./scripts/update-external-ssl.sh -c chint.com.pem -k chint.com.key"
done
```

## 📚 相关文档

- [SSL证书设置指南](SSL_CERTIFICATE_SETUP.md)
- [本地Nginx设置指南](LOCAL_NGINX_SETUP.md)
- [生产环境部署指南](PRODUCTION_DEPLOYMENT.md)
- [Docker生产环境部署](DOCKER_PRODUCTION_DEPLOYMENT.md)

## 🤝 贡献

如果您发现任何问题或有改进建议，请：

1. 创建Issue描述问题
2. 提交Pull Request
3. 更新相关文档

---

**注意**: 使用外部购买的SSL证书时，请确保证书文件的安全性和定期备份。
