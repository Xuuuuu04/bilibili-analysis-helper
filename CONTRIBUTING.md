# 贡献指南

感谢你对本项目的贡献兴趣！

## 开发环境

- Python 3.12+
- 建议使用虚拟环境（venv/conda 均可）

安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 运行（FastAPI）

```bash
uvicorn asgi:app --reload --host 0.0.0.0 --port 5000
```

## 测试

```bash
python -m pytest
```

## 代码风格

本项目使用以下工具保持一致性：

- ruff：静态检查与 import 排序
- black：代码格式化

本地检查示例：

```bash
python -m ruff check .
python -m black --check .
```

## 安全与隐私

- 不要提交任何密钥、Cookie、Token、个人信息到仓库
- `.env` 已被忽略；示例文件 `.env.example` 必须保持为空值占位
