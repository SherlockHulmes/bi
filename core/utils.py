import re
import logging
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from django.conf import settings

logger = logging.getLogger('core')

# ==================== 数据库引擎缓存 ====================
_engine_cache = {}


def get_rds_engine(db_config):
    """获取数据库引擎（从配置字典）
    
    Args:
        db_config: 数据库配置字典，包含 host/port/user/password/database/charset
    """
    cache_key = f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    if cache_key not in _engine_cache:
        password = quote_plus(db_config['password'])
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{password}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
        )
        _engine_cache[cache_key] = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        logger.info(f"数据库连接池已创建: {cache_key}")
    return _engine_cache[cache_key]


def get_engine_from_db_conn(db_conn):
    """从 DbConnection 模型实例获取引擎"""
    config = {
        'host': db_conn.host,
        'port': db_conn.port,
        'user': db_conn.username,
        'password': db_conn.password,
        'database': db_conn.database,
        'charset': db_conn.charset,
    }
    return get_rds_engine(config)


def get_default_engine():
    """获取默认数据库引擎（从 DbConnection 中第一个 is_default=True 或第一个激活的连接）"""
    from sql_scripts.models import DbConnection
    try:
        conn = DbConnection.objects.filter(is_active=True).first()
        if conn:
            return get_engine_from_db_conn(conn)
    except Exception:
        pass
    # 如果没有配置任何连接，使用 settings 中的 RDS_DB_CONFIG（兼容旧配置）
    if hasattr(settings, 'RDS_DB_CONFIG') and settings.RDS_DB_CONFIG.get('host'):
        return get_rds_engine(settings.RDS_DB_CONFIG)
    raise ValueError("未配置任何数据库连接，请先在管理后台 → 数据库连接 中添加")


def allowed_file(filename):
    """检查文件扩展名是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_UPLOAD_EXTENSIONS


def read_file_to_df(filepath, filename):
    """读取文件到 DataFrame，支持 CSV/XLSX/XLS"""
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        for enc in encodings:
            try:
                return pd.read_csv(filepath, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("无法识别 CSV 文件编码")
    elif ext == 'xlsx':
        return pd.read_excel(filepath, engine='openpyxl')
    elif ext == 'xls':
        return pd.read_excel(filepath, engine='xlrd')
    else:
        raise ValueError("不支持的文件格式")


def validate_table_name(name):
    """严格校验表名：只允许字母、数字、下划线，必须以 temp_ 或 dict_ 开头，长度 ≤ 64"""
    if not name or len(name) > 64:
        return False
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False
    if not (name.startswith('temp_') or name.startswith('dict_')):
        return False
    return True


def sanitize_column_name(name):
    """清理列名，移除危险字符，防止 XSS 和 SQL 异常"""
    if not isinstance(name, str):
        name = str(name)
    name = re.sub(r'[<>"\'&;\\\/]', '_', name)
    name = name.strip()
    return name if name else 'unnamed'


def deduplicate_columns(columns):
    """处理重复列名：添加后缀"""
    seen = {}
    final_columns = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            final_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            final_columns.append(col)
    return final_columns


def import_df_to_rds(df, table_name, if_exists='replace', db_config=None):
    """将 DataFrame 导入到 RDS MySQL"""
    engine = get_rds_engine(db_config)
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
        chunksize=1000,
        method='multi'
    )
    logger.info(f"成功导入 {len(df)} 行数据到表 {table_name}")


def execute_sql_on_engine(engine, sql_text):
    """在指定引擎上执行单条 SQL，返回结果（DataFrame）和列名"""
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text(sql_text))
        if result.returns_rows:
            rows = result.fetchall()
            columns = list(result.keys())
            return pd.DataFrame(rows, columns=columns), columns
        else:
            conn.commit()
            return None, []


def execute_sql_statements(engine, sql_content, max_rows=5000):
    """执行多条 SQL 语句（分号分隔），返回统一的结果结构。
    
    Args:
        engine: SQLAlchemy 引擎
        sql_content: SQL 内容（多条语句用分号分隔）
        max_rows: SELECT 结果最大保留行数
    
    Returns:
        tuple: (all_results, all_output_lines, total_affected, duration)
        - all_results: list of dict，每条 SQL 的结构化结果
        - all_output_lines: list of str，每条 SQL 的文本输出
        - total_affected: int，总影响行数
        - duration: float，总耗时(秒)
    """
    import time
    from sqlalchemy import text as sql_text
    
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    all_results = []
    all_output_lines = []
    total_affected = 0
    
    start_time = time.time()
    with engine.connect() as conn:
        for stmt in statements:
            result = conn.execute(sql_text(stmt))
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                result_data = {
                    'columns': columns,
                    'rows': [[str(v) if v is not None else None for v in row] for row in rows[:max_rows]],
                    'total_rows': len(rows),
                }
                all_results.append(result_data)
                header = '\t'.join(columns)
                lines = [header]
                for row in rows[:100]:
                    lines.append('\t'.join(str(v) for v in row))
                if len(rows) > 100:
                    lines.append(f'... 共 {len(rows)} 行，仅显示前 100 行')
                all_output_lines.append('\n'.join(lines))
                total_affected += len(rows)
            else:
                conn.commit()
                affected = result.rowcount if result.rowcount > 0 else 0
                total_affected += affected
                all_output_lines.append(f'影响行数: {affected}')
                all_results.append({'message': f'影响行数: {affected}'})
    
    duration = time.time() - start_time
    return all_results, all_output_lines, total_affected, duration
