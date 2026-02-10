# Prompts Directory

This directory contains prompt templates for the stock analysis agent, organized into structured YAML files for better maintainability and internationalization.

## Structure

Prompts are organized into three YAML files by category:

- **agent.yaml**: Core agent and user interaction prompts
  - `chat`: Main system prompt for the chat agent
  - `user`: Template for formatting user queries
  - `page`: Template for incorporating page context

- **retrieval.yaml**: RAG pipeline retrieval and grading prompts
  - `rewrite`: Query rewriting for retrieval optimization
  - `grade`: Document relevance grading
  - `grade_input`: Template for assembling grade input payload
  - `grade_no_documents`: Fallback text when no documents are retrieved

- **errors.yaml**: Error messages and agent limit notifications
  - `error_max_steps_specific`: Error text when step limit is reached
  - `error_max_steps_best_effort`: Fallback text for final best-effort answer
  - `error_tool_not_found`: Error text for missing tool names
  - `error_tool_failed`: Error text for tool execution failures
  - `error_tool_call_limit_reached`: Error text for tool-call budget hit
  - `error_retrieve_call_limit_reached`: Error text for retrieve-call budget hit

## Format

Each YAML file follows this structure:

```yaml
metadata:
  version: "1.0.0"
  description: "Description of the prompt category"
  last_updated: "YYYY-MM-DD"

prompts:
  prompt_name:
    description: "Brief description of the prompt"
    en-US: |
      English prompt content here
    zh-CN: |
      中文提示词内容
```
