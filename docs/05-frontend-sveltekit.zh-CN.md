# 前端（SvelteKit）

[English](05-frontend-sveltekit.md) | [中文](05-frontend-sveltekit.zh-CN.md)

## 技术介绍

- 氛围编程（Vibe Coding），主要由 Claude Opus 4.5, GPT-5.1-Codex-Max 和 GPT-5 协同生成。
- SvelteKit 2 + Svelte 5 + TypeScript + Vite。
- 前端通过 `/api` 代理后端，开发环境可由 `vite.config.ts` 指向本地 API。
- 生产环境通过 Nginx 反向代理实现前后端统一域名。
- 生产发布模式使用 Node 服务。

## 具体实现细节

### 页面与功能结构

主要路由：

- `/stocks`：股票列表与筛选
- `/stocks/[code]`：股票详情
- `/chat`：对话页

主要模块：

- `src/lib/api.ts`：后端 API 与 SSE 封装
- `src/lib/chatHistory.ts`：会话历史本地管理
- `src/lib/components/*`：聊天、表格、浮窗组件

### 聊天流式消费

`streamChatMessage` 负责：

- 先调用 `POST /chat/start`
- 再连接 SSE stream
- 处理 `token/done/error/ping` 事件
- 断线指数退避重连（最多 10 次）

### 多语言支持

前端已有 `i18n.ts`，支持中英文切换。

## 当前可能存在的问题

- 会话历史依赖本地存储，跨设备一致性有限。
- 前端 API 错误分类仍以通用异常为主，缺少可观测错误码映射。
- SSE 在弱网场景下的重连与重放虽然实现，但缺少端到端压测数据。

## 后续改进思路

- 增加服务端会话同步策略（按用户账号或匿名 token）。
- 建立统一前端错误模型（业务码、可重试标识、用户提示策略）。
- 补充前端链路指标（SSE 连接成功率、重连次数、首 token 时延）。
- 引入契约测试，自动校验前后端接口字段变更。
