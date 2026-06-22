# 安全策略

## 报告漏洞

如果您发现本项目存在安全漏洞，请通过以下方式联系我们：

- **GitHub Issues**: 请在 [Issues](https://github.com/SherlockHulmes/bi/issues) 中提交，标题以 `[Security]` 开头
- **私密报告**: 可通过 GitHub 的私有漏洞报告功能（Private vulnerability reporting）

## 安全注意事项

### 部署前必须完成

1. **修改 SECRET_KEY**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   将生成的密钥设置为环境变量 `SECRET_KEY`

2. **关闭 DEBUG 模式**
   ```env
   DEBUG=False
   ```

3. **修改默认管理员密码**
   - 首次部署后立即修改 `admin/admin123` 默认密码

4. **配置 ALLOWED_HOSTS**
   ```env
   ALLOWED_HOSTS=your-domain.com,your-server-ip
   ```

5. **使用 HTTPS**
   - 生产环境建议配置 Nginx 反向代理并启用 SSL

### 数据安全

- `.env` 文件包含敏感信息，已被 `.gitignore` 排除，**切勿提交到 Git**
- 数据库连接密码在系统中以明文存储（Django Admin 配置），请限制 Admin 访问权限
- 用户上传的文件存储在 `media/` 目录，请确保该目录不被公开访问

### 已知安全限制

- 数据库连接信息（密码）在 Django Admin 中以明文存储，这是为了支持动态配置多个数据源
- 建议仅授权信任的管理员访问 Django Admin 后台

## 支持的版本

| 版本 | 支持状态 |
|------|---------|
| 最新版本 | ✅ 支持 |
| 旧版本 | ❌ 不支持 |

## 更新日志

安全更新将通过 GitHub Releases 发布。