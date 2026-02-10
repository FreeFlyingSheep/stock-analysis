# 提示词管理

本目录包含股票分析智能体的提示词模板，采用结构化的YAML文件组织，以便更好地维护和国际化。

## 结构

提示词按类别组织到三个YAML文件中：

- **agent.yaml**: 核心智能体和用户交互提示词
  - `chat`: 聊天智能体的主系统提示词
  - `user`: 用户查询格式化模板
  - `page`: 页面上下文整合模板

- **retrieval.yaml**: RAG管道检索和评分提示词
  - `rewrite`: 检索优化的查询重写
  - `grade`: 文档相关性评分
  - `grade_input`: 评分输入负载组装模板
  - `grade_no_documents`: 无文档检索时的回退文本

- **errors.yaml**: 错误消息和智能体限制通知
  - `error_max_steps_specific`: 达到步骤限制时的错误文本
  - `error_max_steps_best_effort`: 最终尽力而为回答的回退文本
  - `error_tool_not_found`: 工具未找到的错误文本
  - `error_tool_failed`: 工具执行失败的错误文本
  - `error_tool_call_limit_reached`: 达到工具调用预算的错误文本
  - `error_retrieve_call_limit_reached`: 达到检索调用预算的错误文本

## 格式

每个YAML文件遵循以下结构：

```yaml
metadata:
  version: "1.0.0"
  description: "提示词类别的描述"
  last_updated: "YYYY-MM-DD"

prompts:
  prompt_name:
    description: "提示词的简要描述"
    en-US: |
      English prompt content here
    zh-CN: |
      中文提示词内容
```
