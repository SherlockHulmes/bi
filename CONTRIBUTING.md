# 贡献指南

感谢您对 BI 工具箱项目的关注！

## 如何贡献

### 报告问题

- 使用 [GitHub Issues](https://github.com/SherlockHulmes/bi/issues) 报告 Bug
- 请提供详细的复现步骤、错误信息和环境信息

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "feat: 添加xxx功能"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 提交规范

请遵循以下提交信息格式：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/SherlockHulmes/bi.git
cd bi

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python manage.py migrate

# 4. 创建管理员
python manage.py createsuperuser

# 5. 启动开发服务器
python manage.py runserver
```

### 代码规范

- Python 代码遵循 PEP 8
- 提交前确保代码能正常运行
- 新功能请添加相应的测试

## 许可证

本项目使用 [MIT 许可证](LICENSE)，贡献的代码也将遵循此许可证。