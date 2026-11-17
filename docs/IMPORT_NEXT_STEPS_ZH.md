# GitHub 第二阶段：原始代码已整理

这次上传的 `amazon internship.zip` 已经提供了原始源代码。GitHub-ready 包现包含：

- Week 1–8 的 **28 份原始 Colab Notebook**（按周归档，已清除单元格历史输出）
- Week 7 的 **FastAPI、Streamlit、测试、Docker 配置和运行脚本**
- Week 8 的最终修订版技术报告 PDF、追加的实验图表
- 本地运行模型/数据恢复工具，**不会把模型权重或商品数据上传到 GitHub**

## 上传 GitHub

1. 解压 `ecommerce-search-ranking-system-GitHub-ready.zip`。
2. 先审查所有源代码的著作权、雇主实习保密规定以及 dataset 权限。
3. 在 GitHub Desktop 打开现有仓库，将 ZIP 中的**文件夹内部内容**复制到本地仓库根目录。
4. 在 GitHub Desktop 中查看变更文件，只 Commit `.py`、`.ipynb`、`.md`、`.csv`（小型汇总表）、`.pdf`（已核查报告）、`.png` 等文件。
5. Commit 然后 Push。

## 本地运行 Demo（数据不上传）

```bash
python scripts/restore_local_runtime_artifacts.py --source "/path/to/amazon internship.zip"
cd app
python -m pip install -r requirements.txt
python -m uvicorn amazon_search_service.main:app --host 127.0.0.1 --port 8000
```

启动另一个终端，进入 `app/` 文件夹运行 `streamlit run streamlit_app.py`。首次运行可能需要下载 Transformers 权重。

**重要**：这些是原始历史代码，尚未经过环境安装、真实模型加载和在线端点的完整运行验证。
