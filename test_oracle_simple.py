#!/usr/bin/env python3
"""
简单的Oracle查询测试
测试SELECT * FROM dba_users ORDER BY username; 查询
"""

import oracledb
import os
from datetime import datetime

def test_oracle_connection():
    """测试Oracle连接和查询"""
    
    # Oracle连接参数
    host = "10.10.100.207"
    port = 1521
    service_name = "ORCL"  # 或者使用SID
    username = "system"  # 使用system用户
    password = "oracle"  # 请替换为实际密码
    
    try:
        print("🚀 开始测试Oracle连接...")
        
        # 尝试使用thick模式
        try:
            print("🔧 尝试初始化thick模式...")
            oracledb.init_oracle_client()
            print("✅ thick模式初始化成功")
        except Exception as e:
            print(f"⚠️ thick模式初始化失败: {e}")
            print("🔄 继续使用thin模式...")
        
        # 构建连接字符串
        dsn = f"{host}:{port}/{service_name}"
        print(f"📡 连接字符串: {dsn}")
        
        # 尝试连接
        print("🔌 正在连接Oracle数据库...")
        conn = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        print("✅ 成功连接到Oracle数据库")
        
        # 执行查询
        cursor = conn.cursor()
        
        print("\n🔍 执行查询: SELECT * FROM dba_users ORDER BY username")
        cursor.execute("SELECT * FROM dba_users ORDER BY username")
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        print(f"\n📋 查询结果列: {columns}")
        
        # 获取前5条记录
        rows = cursor.fetchmany(5)
        
        if rows:
            print(f"\n📊 查询结果 (前5条记录):")
            print("=" * 100)
            
            # 打印表头
            header = " | ".join([f"{col:15}" for col in columns])
            print(header)
            print("-" * len(header))
            
            # 打印数据行
            for row in rows:
                row_str = " | ".join([f"{str(val):15}" for val in row])
                print(row_str)
            
            print("=" * 100)
            print(f"✅ 查询成功，共返回 {len(rows)} 条记录")
            
            # 获取总记录数
            cursor.execute("SELECT COUNT(*) FROM dba_users")
            total_count = cursor.fetchone()[0]
            print(f"📈 总用户数: {total_count}")
            
            # 测试权限查询
            print(f"\n🔍 测试权限查询...")
            
            # 测试dba_role_privs
            try:
                cursor.execute("SELECT COUNT(*) FROM dba_role_privs WHERE ROWNUM <= 1")
                count = cursor.fetchone()[0]
                print(f"✅ dba_role_privs 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ dba_role_privs 查询失败: {e}")
            
            # 测试dba_sys_privs
            try:
                cursor.execute("SELECT COUNT(*) FROM dba_sys_privs WHERE ROWNUM <= 1")
                count = cursor.fetchone()[0]
                print(f"✅ dba_sys_privs 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ dba_sys_privs 查询失败: {e}")
            
            # 测试dba_tab_privs
            try:
                cursor.execute("SELECT COUNT(*) FROM dba_tab_privs WHERE ROWNUM <= 1")
                count = cursor.fetchone()[0]
                print(f"✅ dba_tab_privs 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ dba_tab_privs 查询失败: {e}")
            
            # 测试dba_ts_quotas
            try:
                cursor.execute("SELECT COUNT(*) FROM dba_ts_quotas WHERE ROWNUM <= 1")
                count = cursor.fetchone()[0]
                print(f"✅ dba_ts_quotas 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ dba_ts_quotas 查询失败: {e}")
            
            # 测试session_roles
            try:
                cursor.execute("SELECT COUNT(*) FROM session_roles")
                count = cursor.fetchone()[0]
                print(f"✅ session_roles 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ session_roles 查询失败: {e}")
            
            # 测试session_privs
            try:
                cursor.execute("SELECT COUNT(*) FROM session_privs")
                count = cursor.fetchone()[0]
                print(f"✅ session_privs 查询成功: {count} 条记录")
            except Exception as e:
                print(f"❌ session_privs 查询失败: {e}")
            
        else:
            print("❌ 查询没有返回任何数据")
        
        cursor.close()
        conn.close()
        print(f"\n✅ 测试完成，连接已关闭")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始测试Oracle查询...")
    test_oracle_connection()
    print("\n🏁 测试完成")
