"""内部 PDF 知识库的语料辅助模块。"""

from thesis_agent.corpus.catalog import load_catalog, sync_catalog
from thesis_agent.corpus.internal_pdf_loader import load_internal_pdf_documents

__all__ = ["load_catalog", "load_internal_pdf_documents", "sync_catalog"]
