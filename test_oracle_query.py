#!/usr/bin/env python3
"""
测试Oracle查询语句
测试SELECT * FROM dba_users ORDER BY username; 查询
"""

import oracledb
import json
from app import create_app
from app.services.database_service import DatabaseService

def test_oracle_query():
    """测试Oracle dba_users查询"""
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 获取Oracle实例信息
        db_service = DatabaseService()
        
        # 查找Oracle实例
        from app.models.instance import Instance
        oracle_instances = Instance.query.filter_by(db_type='oracle').all()
        
        if not oracle_instances:
            print("❌ 没有找到Oracle实例")
            return
        
        print(f"🔍 找到 {len(oracle_instances)} 个Oracle实例")
        
        for instance in oracle_instances:
            print(f"\n📊 测试实例: {instance.name} ({instance.host}:{instance.port})")
            
            try:
                # 建立连接
                conn = db_service._get_oracle_connection(instance)
                if not conn:
                    print(f"❌ 无法连接到实例 {instance.name}")
                    continue
                    
                print(f"✅ 成功连接到实例 {instance.name}")
                
                # 执行查询
                cursor = conn.cursor()
                
                print("\n🔍 执行查询: SELECT * FROM dba_users ORDER BY username")
                cursor.execute("SELECT * FROM dba_users ORDER BY username")
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description]
                print(f"\n📋 查询结果列: {columns}")
                
                # 获取前10条记录
                rows = cursor.fetchmany(10)
                
                if rows:
                    print(f"\n📊 查询结果 (前10条记录):")
                    print("=" * 80)
                    
                    # 打印表头
                    header = " | ".join([f"{col:15}" for col in columns])
                    print(header)
                    print("-" * len(header))
                    
                    # 打印数据行
                    for row in rows:
                        row_str = " | ".join([f"{str(val):15}" for val in row])
                        print(row_str)
                    
                    print("=" * 80)
                    print(f"✅ 查询成功，共返回 {len(rows)} 条记录")
                    
                    # 获取总记录数
                    cursor.execute("SELECT COUNT(*) FROM dba_users")
                    total_count = cursor.fetchone()[0]
                    print(f"📈 总用户数: {total_count}")
                    
                else:
                    print("❌ 查询没有返回任何数据")
                
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
                
                cursor.close()
                conn.close()
                print(f"✅ 测试完成，连接已关闭")
                
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始测试Oracle查询...")
    test_oracle_query()
    print("\n🏁 测试完成")