from django.contrib import admin
from django.contrib.admin import AdminSite


class BiToolkitAdminSite(AdminSite):
    site_header = 'BI 工具箱 · 管理后台'
    site_title = 'BI 工具箱管理'
    index_title = '系统管理'
    site_url = '/'


# 替换默认 admin site
admin_site = BiToolkitAdminSite(name='bi_admin')