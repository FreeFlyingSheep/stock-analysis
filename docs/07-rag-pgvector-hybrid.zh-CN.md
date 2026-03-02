# RAG + pgvector + 混合检索

[English](07-rag-pgvector-hybrid.md) | [中文](07-rag-pgvector-hybrid.zh-CN.md)

## 技术介绍

- **RAG**：面向年报文本问答，补齐 LLM 对财报细节的可追溯证据。
- **pgvector**：向量存储和相似度检索。
- **pg_textsearch(BM25)**：关键词匹配。
- **Hybrid + RRF**：语义与关键词结果融合排序。

## 具体实现细节

### 报告入库流水线

`agent/ingest.py` 实现主要步骤：

- 从 MinIO `raw` 桶下载 PDF
- PyMuPDF 提取文本
- 标题/段落切分 + overlap 分块
- 计算 embedding
- 写入 `report_chunks`（含 `doc_id/doc_version/chunk_no`）

分块关键参数：

- `CHUNK_MAX_CHARS = 300`
- `CHUNK_OVERLAP = 50`
- `PIPELINE_VERSION = v1.1.0`

### 检索实现

`services/report.py` 提供三类检索：

- `search_semantic`：向量余弦距离
- `search_bm25`：BM25 排序
- `search_hybrid`：二者召回后经 `RRF` 融合

`agent/retriever.py` 对外统一返回格式化 chunk 文本。

### API 与 Agent 接入

- `POST /reports/retrieve` 默认走 `retrieve_hybrid`
- Agent 在需要时通过工具调用该能力

## 当前可能存在的问题

- 当前分块策略是启发式规则，复杂财报排版下可能损失语义完整性。
- RRF 参数固定，未按 query 类型动态调权。
- 检索返回主要是文本拼接，结构化证据（页码、段落置信度）利用不足。

## 后续改进思路

- 引入可配置分块策略（章节感知、表格感知、版面感知）。
- 基于离线评测集，自动调优 `semantic_top_n/bm25_top_n/rrf_k`。
- 增加重排器（cross-encoder）提升最终相关性。
- 对回答附带更明确引用信息（来源页码、chunk id、文档版本）。
- 引入专用向量数据库（如 Milvus）并对比性能与功能差异。
