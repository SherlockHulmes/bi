import re
import logging

logger = logging.getLogger('data_lineage')


def parse_event_sql(sql, known_db_names=None):
    """
    解析事件 SQL，提取目标表和源表。
    
    支持格式：
    - DO REPLACE INTO target_table SELECT ... FROM source_table
    - DO INSERT INTO target_table SELECT ... FROM source_table
    - INSERT INTO target_table SELECT ... FROM source_table
    - REPLACE INTO target_table SELECT ... FROM source_table
    
    参数:
        sql: 要解析的 SQL
        known_db_names: 已知的数据库名集合（不区分大小写），不会被当作表名
    
    返回: {
        'target_tables': ['table1', ...],
        'source_tables': ['db.table1', ...],
    }
    """
    result = {
        'target_tables': [],
        'source_tables': [],
    }
    
    # 构建已知数据库名的大写集合
    known_dbs_upper = set()
    if known_db_names:
        known_dbs_upper = {n.upper() for n in known_db_names}

    if not sql:
        return result

    # 去掉 DO 前缀（MySQL EVENT 格式：DO REPLACE INTO ...）
    sql = re.sub(r'^\s*DO\s+', '', sql, flags=re.IGNORECASE)
    sql = sql.strip()
    sql_upper = sql.upper()

    # 提取 CTE 名称（WITH name AS (...), name2 AS (...)）
    # 使用 \s* 允许逗号后无空格（如 `,detail AS (`）
    cte_names = set()
    for m in re.finditer(r'(?:WITH|,)\s*(\w+)\s+AS\s*\(', sql, re.IGNORECASE):
        cte_names.add(m.group(1))
    if cte_names:
        logger.info(f"[解析] 检测到 CTE: {cte_names}")

    # 提取目标表：REPLACE INTO / INSERT INTO 后面的表名
    # 第一个模式匹配 db.table 格式，第二个模式匹配单独的表名
    # 第二个模式使用 (?!\.) 负向前瞻，避免把 db.table 中的 db 误识别为表名
    target_patterns = [
        r'(?:REPLACE\s+INTO|INSERT\s+INTO)\s+`?(\w+)`?\.`?(\w+)`?',
        r'(?:REPLACE\s+INTO|INSERT\s+INTO)\s+`?(\w+)`?(?![\w.])',
    ]
    for pattern in target_patterns:
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                table = match[1] if match[1] else match[0]
            else:
                table = match
            if table.upper() not in ('SELECT', 'SET', 'VALUES', 'INTO') and table.upper() not in known_dbs_upper:
                result['target_tables'].append(table)

    # 去重
    result['target_tables'] = list(dict.fromkeys(result['target_tables']))

    # 排除的关键字和数据库名（不会被当作表名）
    exclude_words = {'SELECT', 'DUAL', 'INFORMATION_SCHEMA', 'SET', 'VALUES', 'ON', 'AS'}

    # 提取源表：优先匹配 db.table 格式
    source_pattern = r'(?:FROM|JOIN)\s+`?(\w+)`?\.`?(\w+)`?'
    matches = re.findall(source_pattern, sql, re.IGNORECASE)
    db_names_found = set()  # 记录所有出现在 db.table 格式中的数据库名
    for match in matches:
        db_name = match[0]
        table_name = match[1]
        if db_name.upper() not in exclude_words:
            full_name = f"{db_name}.{table_name}"
            if full_name not in result['source_tables']:
                result['source_tables'].append(full_name)
            db_names_found.add(db_name)

    # 将发现的数据库名也加入排除列表，防止后续被误识别为表名
    all_exclude = exclude_words | {n.upper() for n in db_names_found}

    # 将已知数据库名和 CTE 名称也加入排除列表
    all_exclude = all_exclude | known_dbs_upper | {n.upper() for n in cte_names}

    # 提取单独的表名（FROM/JOIN 后面没有 db. 前缀的表）
    # 使用 (?![\w.]) 避免正则回溯把 db.table 中的部分 db 误识别为表名
    source_pattern2 = r'(?:FROM|JOIN)\s+`?(\w+)`?(?![\w.])(?:\s|$|WHERE|GROUP|ORDER|LIMIT|ON|LEFT|RIGHT|INNER|CROSS|HAVING)'
    matches2 = re.findall(source_pattern2, sql, re.IGNORECASE)
    for table in matches2:
        if table.upper() not in all_exclude:
            if table not in result['source_tables']:
                result['source_tables'].append(table)

    return result


def get_table_columns(engine, db_name, table_name):
    """
    从 information_schema 读取表的字段信息。
    返回: [{"name": "col", "type": "int", "comment": "注释"}, ...]
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table "
                "ORDER BY ORDINAL_POSITION"
            ), {'db': db_name, 'table': table_name})
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'comment': row[2] or '',
                })
            return columns
    except Exception as e:
        logger.warning(f"读取字段信息失败 {db_name}.{table_name}: {e}")
        return []


def get_table_comment(engine, db_name, table_name):
    """获取表注释"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT TABLE_COMMENT FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table"
            ), {'db': db_name, 'table': table_name})
            row = result.fetchone()
            return row[0] if row and row[0] else ''
    except Exception as e:
        logger.warning(f"读取表注释失败 {db_name}.{table_name}: {e}")
        return ''