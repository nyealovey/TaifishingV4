#!/bin/bash

# SSL证书验证脚本
# 用于验证外部购买的SSL证书

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "🔍 SSL证书验证脚本"
    echo "=================================="
    echo "用法: $0 [选项] [证书文件]"
    echo ""
    echo "选项:"
    echo "  -c, --cert FILE     证书文件路径"
    echo "  -k, --key FILE      私钥文件路径"
    echo "  -d, --domain DOMAIN 验证域名"
    echo "  -p, --port PORT     验证端口 (默认: 443)"
    echo "  -t, --timeout SEC   超时时间 (默认: 10)"
    echo "  -v, --verbose       详细输出"
    echo "  -h, --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 chint.com.pem chint.com.key"
    echo "  $0 -c chint.com.pem -k chint.com.key -d chint.com"
    echo "  $0 -d chint.com -p 443"
}

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_verbose() {
    if [ "$VERBOSE" = "true" ]; then
        echo -e "${BLUE}🔍 $1${NC}"
    fi
}

# 验证证书文件格式
verify_cert_format() {
    local cert_file="$1"
    
    log_verbose "验证证书文件格式: $cert_file"
    
    if ! openssl x509 -in "$cert_file" -text -noout > /dev/null 2>&1; then
        log_error "证书文件格式无效: $cert_file"
        return 1
    fi
    
    log_success "证书文件格式有效"
    return 0
}

# 验证私钥文件格式
verify_key_format() {
    local key_file="$1"
    
    log_verbose "验证私钥文件格式: $key_file"
    
    if ! openssl rsa -in "$key_file" -check -noout > /dev/null 2>&1; then
        log_error "私钥文件格式无效: $key_file"
        return 1
    fi
    
    log_success "私钥文件格式有效"
    return 0
}

# 验证证书和私钥匹配
verify_cert_key_match() {
    local cert_file="$1"
    local key_file="$2"
    
    log_verbose "验证证书和私钥匹配"
    
    local cert_mod=$(openssl x509 -noout -modulus -in "$cert_file" | openssl md5)
    local key_mod=$(openssl rsa -noout -modulus -in "$key_file" | openssl md5)
    
    if [ "$cert_mod" != "$key_mod" ]; then
        log_error "证书和私钥不匹配"
        return 1
    fi
    
    log_success "证书和私钥匹配"
    return 0
}

# 检查证书有效期
check_cert_validity() {
    local cert_file="$1"
    
    log_verbose "检查证书有效期"
    
    local not_before=$(openssl x509 -in "$cert_file" -noout -startdate | cut -d= -f2)
    local not_after=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
    local current_date=$(date)
    
    log_info "证书有效期:"
    echo "  开始时间: $not_before"
    echo "  结束时间: $not_after"
    
    # 检查是否过期
    if ! openssl x509 -in "$cert_file" -checkend 0 > /dev/null 2>&1; then
        log_error "证书已过期"
        return 1
    fi
    
    # 检查是否即将过期（30天内）
    if ! openssl x509 -in "$cert_file" -checkend 2592000 > /dev/null 2>&1; then
        log_warning "证书将在30天内过期"
    fi
    
    log_success "证书在有效期内"
    return 0
}

# 显示证书详细信息
show_cert_details() {
    local cert_file="$1"
    
    log_info "证书详细信息:"
    echo "=================================="
    
    # 基本信息
    echo "📜 证书信息:"
    openssl x509 -in "$cert_file" -text -noout | grep -E "(Subject:|Issuer:|Serial Number:|Version:)" | sed 's/^/  /'
    
    echo ""
    echo "📅 有效期:"
    openssl x509 -in "$cert_file" -text -noout | grep -E "(Not Before:|Not After:)" | sed 's/^/  /'
    
    echo ""
    echo "🔐 密钥信息:"
    openssl x509 -in "$cert_file" -text -noout | grep -E "(Public Key Algorithm:|Public-Key:)" | sed 's/^/  /'
    
    echo ""
    echo "🌐 域名信息:"
    openssl x509 -in "$cert_file" -text -noout | grep -A 10 "Subject Alternative Name" | grep -E "(DNS:|IP Address:)" | sed 's/^/  /'
    
    echo ""
    echo "🔒 扩展信息:"
    openssl x509 -in "$cert_file" -text -noout | grep -A 5 "X509v3 extensions" | grep -E "(Key Usage:|Extended Key Usage:|Basic Constraints:)" | sed 's/^/  /'
}

# 验证域名匹配
verify_domain_match() {
    local cert_file="$1"
    local domain="$2"
    
    if [ -z "$domain" ]; then
        return 0
    fi
    
    log_verbose "验证域名匹配: $domain"
    
    # 获取证书中的域名
    local cert_domains=$(openssl x509 -in "$cert_file" -text -noout | grep -A 10 "Subject Alternative Name" | grep -E "DNS:" | sed 's/.*DNS://g' | tr -d ' ' | tr ',' '\n')
    
    # 检查域名是否匹配
    local match_found="false"
    while IFS= read -r cert_domain; do
        if [ -n "$cert_domain" ]; then
            # 支持通配符匹配
            if [[ "$domain" == $cert_domain ]] || [[ "$cert_domain" == *"*"* && "$domain" =~ ^${cert_domain//\*/.*}$ ]]; then
                match_found="true"
                break
            fi
        fi
    done <<< "$cert_domains"
    
    if [ "$match_found" = "false" ]; then
        log_error "域名不匹配: $domain"
        log_info "证书支持的域名:"
        echo "$cert_domains" | sed 's/^/  /'
        return 1
    fi
    
    log_success "域名匹配: $domain"
    return 0
}

# 验证在线证书
verify_online_cert() {
    local domain="$1"
    local port="$2"
    local timeout="$3"
    
    if [ -z "$domain" ]; then
        return 0
    fi
    
    log_verbose "验证在线证书: $domain:$port"
    
    # 检查域名解析
    if ! nslookup "$domain" > /dev/null 2>&1; then
        log_warning "域名解析失败: $domain"
        return 1
    fi
    
    # 检查端口连通性
    if ! timeout "$timeout" bash -c "echo > /dev/tcp/$domain/$port" 2>/dev/null; then
        log_warning "端口连接失败: $domain:$port"
        return 1
    fi
    
    # 获取在线证书信息
    local online_cert=$(echo | timeout "$timeout" openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | openssl x509 -text -noout 2>/dev/null)
    
    if [ -z "$online_cert" ]; then
        log_warning "无法获取在线证书信息"
        return 1
    fi
    
    log_success "在线证书验证通过"
    
    # 显示在线证书信息
    if [ "$VERBOSE" = "true" ]; then
        echo "🌐 在线证书信息:"
        echo "$online_cert" | grep -E "(Subject:|Issuer:|Not Before:|Not After:)" | sed 's/^/  /'
    fi
    
    return 0
}

# 生成证书报告
generate_cert_report() {
    local cert_file="$1"
    local key_file="$2"
    local domain="$3"
    
    log_info "生成证书报告..."
    
    local report_file="ssl_cert_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "SSL证书验证报告"
        echo "生成时间: $(date)"
        echo "=================================="
        echo ""
        
        echo "证书文件: $cert_file"
        echo "私钥文件: $key_file"
        echo "验证域名: ${domain:-N/A}"
        echo ""
        
        echo "证书信息:"
        openssl x509 -in "$cert_file" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
        echo ""
        
        echo "域名信息:"
        openssl x509 -in "$cert_file" -text -noout | grep -A 10 "Subject Alternative Name" | grep -E "(DNS:|IP Address:)"
        echo ""
        
        echo "密钥信息:"
        openssl x509 -in "$cert_file" -text -noout | grep -E "(Public Key Algorithm:|Public-Key:)"
        
    } > "$report_file"
    
    log_success "证书报告已生成: $report_file"
}

# 主验证函数
verify_certificate() {
    local cert_file="$1"
    local key_file="$2"
    local domain="$3"
    local port="$4"
    local timeout="$5"
    
    log_info "开始验证SSL证书..."
    echo "=================================="
    
    local validation_passed="true"
    
    # 验证证书文件格式
    if ! verify_cert_format "$cert_file"; then
        validation_passed="false"
    fi
    
    # 验证私钥文件格式
    if [ -n "$key_file" ] && [ -f "$key_file" ]; then
        if ! verify_key_format "$key_file"; then
            validation_passed="false"
        fi
        
        # 验证证书和私钥匹配
        if ! verify_cert_key_match "$cert_file" "$key_file"; then
            validation_passed="false"
        fi
    fi
    
    # 检查证书有效期
    if ! check_cert_validity "$cert_file"; then
        validation_passed="false"
    fi
    
    # 验证域名匹配
    if ! verify_domain_match "$cert_file" "$domain"; then
        validation_passed="false"
    fi
    
    # 验证在线证书
    if ! verify_online_cert "$domain" "$port" "$timeout"; then
        validation_passed="false"
    fi
    
    # 显示证书详细信息
    if [ "$VERBOSE" = "true" ]; then
        show_cert_details "$cert_file"
    fi
    
    # 生成报告
    generate_cert_report "$cert_file" "$key_file" "$domain"
    
    echo ""
    if [ "$validation_passed" = "true" ]; then
        log_success "证书验证通过！"
        return 0
    else
        log_error "证书验证失败！"
        return 1
    fi
}

# 解析命令行参数
parse_arguments() {
    local cert_file=""
    local key_file=""
    local domain=""
    local port="443"
    local timeout="10"
    local verbose="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--cert)
                cert_file="$2"
                shift 2
                ;;
            -k|--key)
                key_file="$2"
                shift 2
                ;;
            -d|--domain)
                domain="$2"
                shift 2
                ;;
            -p|--port)
                port="$2"
                shift 2
                ;;
            -t|--timeout)
                timeout="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                if [ -z "$cert_file" ]; then
                    cert_file="$1"
                    key_file="${1%.*}.key"
                fi
                shift
                ;;
        esac
    done
    
    # 设置全局变量
    VERBOSE="$verbose"
    
    # 检查必需参数
    if [ -z "$cert_file" ]; then
        log_error "请指定证书文件"
        show_help
        exit 1
    fi
    
    # 执行验证
    verify_certificate "$cert_file" "$key_file" "$domain" "$port" "$timeout"
}

# 主函数
main() {
    echo "🔍 SSL证书验证脚本"
    echo "=================================="
    
    # 检查依赖
    if ! command -v openssl > /dev/null 2>&1; then
        log_error "OpenSSL未安装，请先安装OpenSSL"
        exit 1
    fi
    
    # 解析参数并执行
    parse_arguments "$@"
}

# 运行主函数
main "$@"
