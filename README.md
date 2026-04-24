# ThesisAgent

1 项目概览

1.1 项目简介

ThesisAgent 是一个面向论文主题探索、相似内容检索和结构检查的本地优先项目。公开版本使用 `data/samples/` 中的匿名 demo Markdown 样例，演示从文档 ingest、chunk 生成、TF-IDF 检索，到 Streamlit 界面搜索和主题分析的完整流程。

项目默认运行在 demo mode，不需要真实论文 PDF，也不依赖外部 API。internal mode 的代码保留在仓库中，用于私有部署时连接用户自己的本地论文库；公开文档只使用占位路径说明配置方式。

1.2 主要功能

(1) Demo mode

使用仓库内的匿名 Markdown 样例构建 chunk、metadata 和 TF-IDF index，适合快速演示项目的数据处理与检索流程。

(2) Internal mode

支持用户在仓库外部维护本地 PDF 论文库，通过 catalog、chunk 和 TF-IDF index 完成本地检索。公开仓库不包含任何真实论文数据。

(3) 本地检索与分析

基于 TF-IDF 进行相似片段检索，并在检索结果基础上提供主题重合度分析和结构检查。

(4) Streamlit UI

提供搜索、主题分析、结构检查，以及 internal mode 下的 PDF 操作入口。

(5) MockLLM

用于本地、确定性的报告生成演示，不需要外部 LLM 服务。

1.3 技术栈

- Python 3.11+
- Streamlit
- scikit-learn
- PyMuPDF
- python-dotenv

2 项目架构

2.1 数据处理流程

`thesis_agent.cli.ingest` 读取输入文档，将文档拆分为 chunk，并输出 JSONL 格式的 chunk 与 metadata。demo mode 使用 `data/samples/` 中的 Markdown 文件；internal mode 可以读取用户提供的 text-based PDF 和 catalog。

2.2 检索与分析流程

`thesis_agent.cli.build_index` 根据 chunk JSONL 构建 TF-IDF index。检索层读取 index 后返回相似片段；tools 层基于检索结果完成主题分析和结构检查；UI 层通过 Streamlit 展示结果。

2.3 Demo mode 与 Internal mode

demo mode 是公开仓库的默认运行方式，只依赖匿名 demo 样例。internal mode 用于私有部署，要求用户在仓库外部准备 PDF 目录、catalog 路径、chunk 路径和 index 路径。两种模式共享 ingest、retrieval、tools 和 UI 服务层。

3 快速开始

3.1 环境要求

建议使用 Python 3.11 或更高版本。首次运行前请创建虚拟环境，并在仓库根目录执行命令。

3.2 安装依赖

```powershell
python -m pip install -e ".[dev]"
```

3.3 可选开发检查

公开版不包含完整测试套件。若只需要确认 Python 文件可编译，可以运行：

```powershell
python -m compileall src app.py
```

3.4 启动 Demo

先从匿名 demo 样例生成本地 artifacts：

```powershell
python -m thesis_agent.cli.ingest --input data/samples --input-type markdown --language ja --output data/processed/chunks.jsonl --metadata-output data/metadata/documents.jsonl
python -m thesis_agent.cli.build_index --chunks data/processed/chunks.jsonl --output data/index/tfidf_index.pkl --language ja
```

再启动 Streamlit：

```powershell
python -m streamlit run app.py
```

4 内部论文库使用方式

4.1 数据目录准备

internal mode 使用仓库外部的本地数据目录。示例占位路径如下：

```text
D:\path\to\thesis_pdfs\raw
D:\path\to\thesis_work\catalog.csv
D:\path\to\thesis_work\processed\chunks.jsonl
D:\path\to\thesis_work\processed\tfidf_index.pkl
```

4.2 同步 catalog

```powershell
python -m thesis_agent.cli.sync_catalog --pdf-root D:\path\to\thesis_pdfs\raw --catalog D:\path\to\thesis_work\catalog.csv
```

4.3 ingest 论文

```powershell
python -m thesis_agent.cli.ingest --input D:\path\to\thesis_pdfs\raw --input-type pdf --language ja --catalog D:\path\to\thesis_work\catalog.csv --output D:\path\to\thesis_work\processed\chunks.jsonl --metadata-output D:\path\to\thesis_work\processed\documents.jsonl
```

4.4 构建索引

```powershell
python -m thesis_agent.cli.build_index --chunks D:\path\to\thesis_work\processed\chunks.jsonl --output D:\path\to\thesis_work\processed\tfidf_index.pkl --language ja
```

4.5 启动 internal mode

在 `.env` 中配置以下变量，然后启动 Streamlit：

```powershell
KB_MODE=internal
DOCUMENT_LANGUAGE=ja
UI_LANGUAGE=zh
LAB_PDF_ROOT=D:\path\to\thesis_pdfs\raw
LAB_CATALOG_PATH=D:\path\to\thesis_work\catalog.csv
LAB_CHUNKS_PATH=D:\path\to\thesis_work\processed\chunks.jsonl
LAB_INDEX_PATH=D:\path\to\thesis_work\processed\tfidf_index.pkl
LLM_PROVIDER=mock
RETRIEVER_TYPE=tfidf
ALLOW_EXTERNAL_LLM_FOR_PRIVATE_DATA=false
```

```powershell
python -m streamlit run app.py
```
