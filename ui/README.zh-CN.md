# Stock Analysis UI

[English](README.md) | [中文](README.zh-CN.md)

这是 Stock Analysis 的 SvelteKit 前端。用于浏览 A 股股票、查看财务与评分结果，并通过聊天界面获取分析。

该前端主要由 Claude Opus 4.5 与 GPT-5.1-Codex-Max 辅助生成。

## 功能

- **股票浏览**：按代码、公司名、板块、行业筛选
- **股票详情**：评分、指标、CNInfo 与 Yahoo 数据汇总
- **AI 聊天界面**：基于 `/chat` 的流式对话
- **双语切换**：顶部支持 `EN/中文`
- **响应式布局**：适配桌面与移动端

## 前置条件

- `Node.js 18+`
- FastAPI 后端已运行（默认 `http://localhost:8000`）

## 开始使用

### 安装

```bash
pnpm install
# 或: npm install
```

### 开发

启动开发服务器：

```bash
pnpm run dev
# 或: npm run dev
```

访问 `http://localhost:5173`。

### 类型检查

```bash
pnpm run check
# 或: npm run check
```

监视模式：

```bash
pnpm run check:watch
# 或: npm run check:watch
```

### 构建

```bash
pnpm run build
# 或: npm run build
```

本地预览：

```bash
pnpm run preview
# 或: npm run preview
```

## API 集成

前端通过 `/api` 访问后端，并在开发环境下代理到 `http://localhost:8000`（见 `vite.config.ts`）。可通过 `APP_BACKEND_HOST` 与 `APP_BACKEND_PORT` 覆盖代理目标。

### 使用的端点

- `GET /stocks` - 股票列表与筛选
- `GET /stocks/{code}` - 股票详情（CNInfo + Yahoo）
- `GET /analysis` - 分析结果列表
- `GET /analysis/{code}` - 单只股票分析详情
- `POST /chat` - 流式聊天（SSE）

## 技术栈

- **SvelteKit 2**
- **Svelte 5**
- **TypeScript**
- **Vite**

## License

同主项目 License。
