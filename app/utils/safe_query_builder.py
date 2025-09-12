"""
安全的SQL查询构建器
防止SQL注入攻击
"""

from typing import Any, Dict, List, Optional, Union


class SafeQueryBuilder:
    """安全的SQL查询构建器"""

    # 允许的字段名白名单
    MYSQL_USER_FIELDS = {
        "User",
        "Host",
        "plugin",
        "password_expired",
        "password_last_changed",
        "account_locked",
        "password_lifetime",
        "Select_priv",
        "Insert_priv",
        "Update_priv",
        "Delete_priv",
        "Create_priv",
        "Drop_priv",
        "Super_priv",
    }

    POSTGRES_ROLE_FIELDS = {
        "rolname",
        "rolsuper",
        "rolinherit",
        "rolcreaterole",
        "rolcreatedb",
        "rolcanlogin",
        "rolconnlimit",
        "rolvaliduntil",
        "rolbypassrls",
        "rolreplication",
    }

    SQLSERVER_PRINCIPAL_FIELDS = {"name", "type_desc", "is_disabled", "create_date", "modify_date"}

    ORACLE_USER_FIELDS = {"username", "authentication_type", "account_status", "created", "expiry_date", "profile"}

    @classmethod
    def build_mysql_user_query(cls, filter_conditions: Dict[str, Any]) -> tuple[str, List[Union[str, int, float]]]:
        """构建MySQL用户查询"""
        base_query = """
            SELECT 
                User as username,
                Host as host,
                'user' as account_type,
                '' as database_name,
                plugin as plugin,
                password_expired as password_expired,
                password_last_changed as password_last_changed,
                account_locked as account_locked,
                password_lifetime as password_lifetime,
                Select_priv as can_select,
                Insert_priv as can_insert,
                Update_priv as can_update,
                Delete_priv as can_delete,
                Create_priv as can_create,
                Drop_priv as can_drop,
                Super_priv as is_superuser
            FROM mysql.user
        """

        where_clauses = []
        params: List[Union[str, int, float]] = []

        for field, value in filter_conditions.items():
            if field in cls.MYSQL_USER_FIELDS:
                if isinstance(value, str):
                    where_clauses.append(f"{field} LIKE %s")
                    params.append(f"%{value}%")
                elif isinstance(value, (int, float)):
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
                elif isinstance(value, bool):
                    where_clauses.append(f"{field} = %s")
                    params.append(1 if value else 0)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY User, Host"

        return base_query, params

    @classmethod
    def build_postgres_role_query(
        cls, filter_conditions: Dict[str, Any]
    ) -> tuple[str, List[Union[str, int, float, bool]]]:
        """构建PostgreSQL角色查询"""
        base_query = """
            SELECT 
                rolname as username,
                rolsuper as is_superuser,
                rolinherit as can_inherit,
                rolcreaterole as can_create_role,
                rolcreatedb as can_create_db,
                rolcanlogin as can_login,
                rolconnlimit as conn_limit,
                CASE 
                    WHEN rolvaliduntil = 'infinity'::timestamp THEN NULL
                    ELSE rolvaliduntil 
                END as valid_until,
                rolbypassrls as can_bypass_rls,
                rolreplication as can_replicate
            FROM pg_roles
        """

        where_clauses = []
        params: List[Union[str, int, float, bool]] = []

        for field, value in filter_conditions.items():
            if field in cls.POSTGRES_ROLE_FIELDS:
                if isinstance(value, str):
                    where_clauses.append(f"{field} ILIKE %s")
                    params.append(f"%{value}%")
                elif isinstance(value, (int, float)):
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
                elif isinstance(value, bool):
                    where_clauses.append(f"{field} = %s")
                    params.append(value)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY rolname"

        return base_query, params

    @classmethod
    def build_sqlserver_principal_query(
        cls, filter_conditions: Dict[str, Any]
    ) -> tuple[str, List[Union[str, int, float, bool]]]:
        """构建SQL Server主体查询"""
        base_query = """
            SELECT 
                name as username,
                type_desc as account_type,
                'master' as database_name,
                is_disabled as is_disabled,
                create_date as created_date,
                modify_date as modified_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
        """

        where_clauses = []
        params: List[Union[str, int, float, bool]] = []

        for field, value in filter_conditions.items():
            if field in cls.SQLSERVER_PRINCIPAL_FIELDS:
                if isinstance(value, str):
                    where_clauses.append(f"{field} LIKE %s")
                    params.append(f"%{value}%")
                elif isinstance(value, (int, float)):
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
                elif isinstance(value, bool):
                    where_clauses.append(f"{field} = %s")
                    params.append(1 if value else 0)

        # 添加默认过滤条件
        where_clauses.append("(name = 'sa' OR name NOT LIKE 'NT %')")

        if where_clauses:
            base_query += " AND " + " AND ".join(where_clauses)

        base_query += " ORDER BY name"

        return base_query, params

    @classmethod
    def build_oracle_user_query(
        cls, filter_conditions: Dict[str, Any]
    ) -> tuple[str, List[Union[str, int, float, bool]]]:
        """构建Oracle用户查询"""
        base_query = """
            SELECT 
                username,
                authentication_type as account_type,
                '' as database_name,
                account_status,
                created,
                expiry_date,
                profile
            FROM dba_users
        """

        where_clauses = []
        params: List[Union[str, int, float, bool]] = []

        for field, value in filter_conditions.items():
            if field in cls.ORACLE_USER_FIELDS:
                if isinstance(value, str):
                    where_clauses.append(f"{field} LIKE %s")
                    params.append(f"%{value}%")
                elif isinstance(value, (int, float)):
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
                elif isinstance(value, bool):
                    where_clauses.append(f"{field} = %s")
                    params.append(1 if value else 0)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY username"

        return base_query, params
