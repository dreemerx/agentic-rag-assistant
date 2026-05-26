# Agentic RAG Assistant 项目说明

## 项目简介

Agentic RAG Assistant 是一个工业级 AI Agent 系统，集成了 RAG 知识库检索、工具调用、记忆管理和流式输出功能。

## 技术栈

- **后端**: Python 3.11+, FastAPI, LangGraph
- **前端**: Next.js 15, TypeScript, Tailwind CSS
- **向量数据库**: ChromaDB
- **Embedding 模型**: BAAI/bge-m3
- **Reranker 模型**: BAAI/bge-reranker-v2-m3
- **LLM Provider**: SiliconFlow, Qwen (通义千问), Ollama

## 核心功能

### 1. RAG 知识库
支持上传 PDF, TXT, DOCX, Markdown 文件，自动切分、向量化、存储，支持语义检索和重排序。

### 2. Agent Workflow
采用 LangGraph 构建状态图：Router → Retrieval/Tool → Plan → Generate → Reflect，支持最多 2 轮迭代优化。

### 3. 工具系统
- **Retrieval Tool**: 知识库检索，返回带引用的结果
- **Web Search Tool**: 基于 DuckDuckGo 的全网搜索
- **Calculator Tool**: 安全的数学表达式计算

### 4. 记忆管理
- **短期记忆**: 滑动窗口保留最近 N 轮对话
- **摘要记忆**: LLM 自动压缩历史对话为摘要

## 作者信息

本项目由 dreemerx 开发，GitHub 仓库地址：https://github.com/dreemerx/agentic-rag-assistant
