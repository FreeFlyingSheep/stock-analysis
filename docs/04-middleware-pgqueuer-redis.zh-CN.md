# 中间件（PgQueuer + Redis）

[English](04-middleware-pgqueuer-redis.md) | [中文](04-middleware-pgqueuer-redis.zh-CN.md)

## 技术介绍

- **PgQueuer**：基于 PostgreSQL 的任务队列，承载抓取与分析异步任务。
- **Redis**：承担缓存、分布式锁、消息发布订阅、流式会话缓冲。

## 具体实现细节

### PgQueuer 任务编排

`jobs/pgqueuer.py` 注册了关键任务入口：

- `crawl_stock_data`
- `analyze_stock_data`
- `update_stock_data`
- `analyze_all_stock_data`

其中 `update_stock_data` 会批量生成 crawl 子任务，并通过 `execute_after` 做错峰调度。

### Worker 运行形态

- Worker 启动时初始化 DB 会话、Adapter、规则引擎与 telemetry。
- 通过 `resources` 向各任务注入共享依赖。

### Redis 在聊天链路中的职责

- `run:*` 键控制同一消息的并发启动。
- `lock:*` 分布式锁避免并发写流。
- `buf:*` 列表缓存历史 token 事件。
- `channel:*` PubSub 实时推送 token 给 SSE 消费端。

## 当前可能存在的问题

- PgQueuer 的死信队列、任务优先级治理策略未文档化。
- Redis 键空间虽然有前缀，但尚未看到统一的容量治理与 key 观测面板。
- 聊天链路使用锁续租，若极端异常可能残留脏状态键。

## 后续改进思路

- 为任务队列补充重试策略矩阵（按错误类型区分）。
- 增加任务级指标：排队时长、失败率、重试次数、最终成功率。
- 建立 Redis key 生命周期治理（统一 TTL、定期扫描、告警阈值）。
- 为聊天任务增加恢复机制（例如 reconnect 后增量补发策略校验）。
- 为 Redis 启用高可用方案（哨兵或集群模式），并验证故障转移流程。
