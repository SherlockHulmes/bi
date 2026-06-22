import os
import re
import logging
import json
import pandas as pd
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.shortcuts import render
from sqlalchemy import text

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import redirect
from .models import FileUpload, ExternalLink, DashboardCard
from .utils import (
    allowed_file, read_file_to_df, validate_table_name,
    sanitize_column_name, deduplicate_columns,
    import_df_to_rds, get_engine_from_db_conn, get_default_engine
)
from sql_scripts.models import DbConnection

logger = logging.getLogger('core')


def _secure_filename(filename):
    """替代 werkzeug 的 secure_filename"""
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    filename = re.sub(r'[\s]+', '_', filename)
    filename = filename.strip('._')
    return filename


@login_required
def homepage(request):
    """主页仪表盘"""
    links = ExternalLink.objects.filter(is_active=True)
    cards = DashboardCard.objects.filter(is_active=True)
    return render(request, 'core/homepage.html', {
        'links': links,
        'cards': cards,
    })


@login_required
def import_data(request):
    """数据导入页面"""
    db_connections = DbConnection.objects.filter(is_active=True)
    return render(request, 'core/import_data.html', {'db_connections': db_connections})


@login_required
@require_POST
def preview(request):
    """文件上传预览"""
    FileUpload.cleanup_stale()

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': '没有文件'})

    file = request.FILES['file']
    if file.name == '':
        return JsonResponse({'success': False, 'error': '文件名为空'})
    if not allowed_file(file.name):
        return JsonResponse({'success': False, 'error': '仅支持 CSV, XLSX, XLS'})

    filename = _secure_filename(file.name)
    if not filename:
        return JsonResponse({'success': False, 'error': '文件名不合法'})

    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    try:
        with open(filepath, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        file_size = os.path.getsize(filepath)
        logger.info(f"文件已上传: {filename} ({file_size} bytes) by {request.user}")

        df = read_file_to_df(filepath, filename)

        safe_columns = [sanitize_column_name(c) for c in df.columns]
        final_columns = deduplicate_columns(safe_columns)
        df.columns = final_columns

        preview_data = df.head(10).where(pd.notnull(df.head(10)), None).to_dict('records')

        file_upload = FileUpload.objects.create(
            original_name=file.name,
            stored_path=filepath,
            file_size=file_size,
            uploaded_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'columns': final_columns,
            'preview': preview_data,
            'total_rows': len(df),
            'file_token': str(file_upload.id),
            'filename': file.name,
        })
    except Exception as e:
        logger.error(f"文件预览失败: {filename}, 错误: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def change_password(request):
    """修改密码"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(old_password):
            messages.error(request, '当前密码错误')
        elif len(new_password) < 8:
            messages.error(request, '新密码长度不能少于8位')
        elif new_password != confirm_password:
            messages.error(request, '两次输入的密码不一致')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, '密码修改成功！')
            return redirect('core:change_password')

    return render(request, 'accounts/change_password.html')


@login_required
def loan_schedule(request):
    """还款计划明细页面"""
    return render(request, 'core/loan_schedule.html')


@login_required
@require_POST
def do_import(request):
    """数据导入到目标数据库 API"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '请求数据格式错误'})

    file_token = data.get('file_token')
    table_name = data.get('table_name', '').strip()
    if_exists = data.get('if_exists', 'replace')
    custom_columns = data.get('custom_columns')
    target_db_id = data.get('target_db_id')

    # 表名校验（严格限制不变）
    if not validate_table_name(table_name):
        return JsonResponse({
            'success': False,
            'error': '表名不合法：必须以 temp_ 或 dict_ 开头，只包含字母、数字、下划线，且长度 ≤ 64'
        })

    if if_exists not in ('replace', 'append', 'fail'):
        return JsonResponse({'success': False, 'error': 'if_exists 参数不合法'})

    # 确定目标数据库引擎
    try:
        if target_db_id:
            db_conn = DbConnection.objects.get(pk=target_db_id, is_active=True)
            engine = get_engine_from_db_conn(db_conn)
        else:
            engine = get_default_engine()
    except DbConnection.DoesNotExist:
        return JsonResponse({'success': False, 'error': '选择的数据库连接不存在或已禁用'})

    # 查找文件记录
    try:
        file_upload = FileUpload.objects.get(id=file_token, is_imported=False)
    except FileUpload.DoesNotExist:
        return JsonResponse({'success': False, 'error': '文件已过期或无效，请重新上传'})

    filepath = file_upload.stored_path
    if not os.path.exists(filepath):
        file_upload.delete()
        return JsonResponse({'success': False, 'error': '文件已过期，请重新上传'})

    try:
        df = read_file_to_df(filepath, file_upload.original_name)

        if custom_columns and len(custom_columns) == len(df.columns):
            safe_columns = [sanitize_column_name(c) for c in custom_columns]
            if len(set(safe_columns)) != len(safe_columns):
                return JsonResponse({'success': False, 'error': '存在重复的列名，请修改后重试'})
            if any(not c or c == 'unnamed' for c in safe_columns):
                return JsonResponse({'success': False, 'error': '存在空列名，请修改后重试'})
            df.columns = safe_columns

        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False,
            chunksize=1000,
            method='multi'
        )
        logger.info(f"成功导入 {len(df)} 行数据到表 {table_name} by {request.user}")

        # 表名已经 validate_table_name 校验过，使用参数化查询
        with engine.connect() as conn:
            imported_preview = pd.read_sql(
                text(f"SELECT * FROM `{table_name}` LIMIT 10"),
                conn
            )
        preview_data = imported_preview.where(pd.notnull(imported_preview), None).to_dict('records')

        file_upload.is_imported = True
        file_upload.save()
        file_upload.delete_file()

        return JsonResponse({
            'success': True,
            'message': f'成功导入 {len(df)} 行数据到表 `{table_name}`',
            'preview': preview_data,
            'columns': imported_preview.columns.tolist(),
        })
    except Exception as e:
        logger.error(f"数据导入失败: table={table_name}, 错误: {e}")
        file_upload.delete_file()
        file_upload.delete()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def dashboard_card_data(request, card_id):
    """大屏卡片数据 API：执行SQL返回结果"""
    try:
        card = DashboardCard.objects.get(pk=card_id, is_active=True)
    except DashboardCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': '卡片不存在'})

    # 获取SQL：优先使用自定义SQL，其次使用关联脚本
    sql = card.sql_query.strip()
    if not sql and card.sql_script:
        sql = card.sql_script.get_sql_content().strip()
    if not sql:
        return JsonResponse({'success': False, 'error': '未配置SQL'})

    # 获取数据库连接
    db_conn = card.db_connection
    if not db_conn and card.sql_script:
        db_conn = card.sql_script.target_db
    if not db_conn:
        return JsonResponse({'success': False, 'error': '未配置数据库连接'})

    try:
        engine = get_engine_from_db_conn(db_conn)
        df = pd.read_sql(text(sql), engine)
        columns = df.columns.tolist()
        rows = df.where(pd.notnull(df), None).to_dict('records')
        return JsonResponse({
            'success': True,
            'columns': columns,
            'rows': rows,
            'card_type': card.card_type,
            'title': card.title,
        })
    except Exception as e:
        logger.error(f"大屏卡片数据查询失败: card={card_id}, 错误: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
