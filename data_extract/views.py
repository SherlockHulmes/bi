import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from sqlalchemy import text as sql_text

from .models import QueryTemplate, QueryHistory
from sql_scripts.models import DbConnection
from core.utils import get_engine_from_db_conn, execute_sql_statements
from scheduler.models import ScheduledTaskLog

logger = logging.getLogger('data_extract')


@login_required
def query_home(request):
    """自助取数首页：拖拽查询构建器"""
    db_connections = DbConnection.objects.filter(is_active=True)
    templates = QueryTemplate.objects.filter(is_active=True).filter(
        is_public_q(request.user)
    )[:20]
    recent_history = QueryHistory.objects.filter(user=request.user)[:10]
    return render(request, 'data_extract/home.html', {
        'db_connections': db_connections,
        'templates': templates,
        'recent_history': recent_history,
    })


def is_public_q(user):
    """返回可访问的模板查询条件"""
    from django.db.models import Q
    return Q(is_public=True) | Q(created_by=user)


@login_required
def api_tables(request):
    """API：获取指定数据库的所有表"""
    db_id = request.GET.get('db_id')
    if not db_id:
        return JsonResponse({'error': '缺少 db_id 参数'}, status=400)

    try:
        db_conn = DbConnection.objects.get(pk=db_id, is_active=True)
    except DbConnection.DoesNotExist:
        return JsonResponse({'error': '数据库连接不存在'}, status=404)

    try:
        engine = get_engine_from_db_conn(db_conn)
        with engine.connect() as conn:
            result = conn.execute(sql_text(
                "SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS "
                "FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE' "
                "ORDER BY TABLE_NAME"
            ), {'db': db_conn.database})
            tables = []
            for row in result:
                tables.append({
                    'name': row[0],
                    'comment': row[1] or '',
                    'rows': int(row[2]) if row[2] else 0,
                    'db_name': db_conn.database,
                })
        return JsonResponse({'success': True, 'tables': tables, 'db_name': db_conn.database})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_columns(request):
    """API：获取指定表的字段列表"""
    db_id = request.GET.get('db_id')
    table_name = request.GET.get('table')
    if not db_id or not table_name:
        return JsonResponse({'error': '缺少参数'}, status=400)

    try:
        db_conn = DbConnection.objects.get(pk=db_id, is_active=True)
    except DbConnection.DoesNotExist:
        return JsonResponse({'error': '数据库连接不存在'}, status=404)

    try:
        engine = get_engine_from_db_conn(db_conn)
        with engine.connect() as conn:
            result = conn.execute(sql_text(
                "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT, IS_NULLABLE, COLUMN_KEY "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table "
                "ORDER BY ORDINAL_POSITION"
            ), {'db': db_conn.database, 'table': table_name})
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'comment': row[2] or '',
                    'nullable': row[3] == 'YES',
                    'is_key': row[4] in ('PRI', 'UNI'),
                })
        return JsonResponse({'success': True, 'columns': columns})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def query_execute(request):
    """执行查询（SQL模式或拖拽模式生成的SQL）"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求格式错误'}, status=400)

    db_id = data.get('db_id')
    sql = data.get('sql', '').strip()
    template_id = data.get('template_id')

    if not db_id:
        return JsonResponse({'error': '请选择数据库'}, status=400)
    if not sql:
        return JsonResponse({'error': 'SQL不能为空'}, status=400)

    # 安全检查：只允许 SELECT
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
        return JsonResponse({'error': '只允许 SELECT 查询'}, status=400)

    # 禁止危险关键字
    forbidden = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'GRANT']
    for kw in forbidden:
        if kw in sql_upper.split():
            return JsonResponse({'error': f'禁止使用 {kw} 语句'}, status=400)

    # 添加 LIMIT 保护
    if 'LIMIT' not in sql_upper:
        sql = sql.rstrip(';') + ' LIMIT 10000'

    try:
        db_conn = DbConnection.objects.get(pk=db_id, is_active=True)
    except DbConnection.DoesNotExist:
        return JsonResponse({'error': '数据库连接不存在'}, status=404)

    template = None
    if template_id:
        template = QueryTemplate.objects.filter(pk=template_id, is_active=True).first()

    try:
        engine = get_engine_from_db_conn(db_conn)
        all_results, all_output, total_affected, duration = execute_sql_statements(engine, sql, max_rows=10000)

        # 保存历史
        history = QueryHistory.objects.create(
            user=request.user,
            template=template,
            db_connection=db_conn,
            sql_executed=sql,
            row_count=total_affected,
            duration=round(duration, 2),
            status='success',
            result_json=json.dumps(all_results, ensure_ascii=False, default=str)[:500000],
        )

        # 记录到全局执行日志
        ScheduledTaskLog.objects.create(
            task_name=f'数据查询: {db_conn.name}',
            script_name=db_conn.database,
            sql_executed=sql,
            trigger_type='data_query',
            status='success',
            row_count=total_affected,
            duration=round(duration, 2),
            executed_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'results': all_results,
            'row_count': total_affected,
            'duration': round(duration, 2),
            'history_id': history.pk,
        })
    except Exception as e:
        QueryHistory.objects.create(
            user=request.user,
            template=template,
            db_connection=db_conn,
            sql_executed=sql,
            status='failed',
            error_message=str(e)[:2000],
        )

        ScheduledTaskLog.objects.create(
            task_name=f'数据查询: {db_conn.name}',
            script_name=db_conn.database,
            sql_executed=sql,
            trigger_type='data_query',
            status='failed',
            error_message=str(e)[:2000],
            executed_by=request.user,
        )

        return JsonResponse({'error': str(e)[:500]}, status=500)


@login_required
def template_list(request):
    """查询模板列表"""
    from django.db.models import Q
    templates = QueryTemplate.objects.filter(is_active=True).filter(
        Q(is_public=True) | Q(created_by=request.user)
    )
    categories = templates.values_list('category', flat=True).distinct()
    return render(request, 'data_extract/template_list.html', {
        'templates': templates,
        'categories': [c for c in categories if c],
    })


@login_required
def template_detail(request, pk):
    """模板详情/执行"""
    from django.db.models import Q
    template = get_object_or_404(
        QueryTemplate.objects.filter(is_active=True).filter(
            Q(is_public=True) | Q(created_by=request.user)
        ),
        pk=pk
    )
    return render(request, 'data_extract/template_detail.html', {
        'template': template,
    })


@login_required
def template_detail_api(request, pk):
    """模板详情 API（JSON）"""
    from django.db.models import Q
    template = get_object_or_404(
        QueryTemplate.objects.filter(is_active=True).filter(
            Q(is_public=True) | Q(created_by=request.user)
        ),
        pk=pk
    )
    return JsonResponse({
        'name': template.name,
        'description': template.description,
        'sql_template': template.sql_template,
        'db_connection_id': template.db_connection_id,
        'parameters': template.get_parameters(),
        'category': template.category,
        'visual_json': template.visual_json or '',
    })


@login_required
@require_POST
def save_template(request):
    """保存查询模板"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求格式错误'}, status=400)

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    db_id = data.get('db_id')
    sql = data.get('sql', '').strip()
    visual_json = data.get('visual_json', '')
    save_to_script = data.get('save_to_script', False)

    if not name:
        return JsonResponse({'error': '模板名称不能为空'}, status=400)
    if not db_id:
        return JsonResponse({'error': '请选择数据库'}, status=400)
    if not sql:
        return JsonResponse({'error': 'SQL不能为空'}, status=400)

    try:
        db_conn = DbConnection.objects.get(pk=db_id, is_active=True)
    except DbConnection.DoesNotExist:
        return JsonResponse({'error': '数据库连接不存在'}, status=404)

    template = QueryTemplate.objects.create(
        name=name,
        description=description,
        category=category,
        db_connection=db_conn,
        sql_template=sql,
        visual_json=visual_json,
        created_by=request.user,
    )

    script_created = False
    if save_to_script:
        from sql_scripts.models import SqlScript
        script = SqlScript.objects.create(
            name=f'[自助取数] {name}',
            description=f'从自助取数平台保存的查询模板: {description}',
            content=sql,
            target_db=db_conn,
            created_by=request.user,
        )
        script_created = True

    return JsonResponse({
        'success': True,
        'template_id': template.pk,
        'script_created': script_created,
    })


@login_required
@require_POST
def update_template(request):
    """更新已有模板"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求格式错误'}, status=400)

    template_id = data.get('template_id')
    if not template_id:
        return JsonResponse({'error': '缺少模板ID'}, status=400)

    try:
        template = QueryTemplate.objects.get(pk=template_id, created_by=request.user)
    except QueryTemplate.DoesNotExist:
        return JsonResponse({'error': '模板不存在或无权修改'}, status=404)

    sql = data.get('sql', '').strip()
    visual_json = data.get('visual_json', '')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not sql:
        return JsonResponse({'error': 'SQL不能为空'}, status=400)

    template.sql_template = sql
    template.visual_json = visual_json
    if name:
        template.name = name
    if description:
        template.description = description
    template.save()

    return JsonResponse({
        'success': True,
        'template_id': template.pk,
    })
