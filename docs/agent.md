---
name: learn-claude-code-agent-memory
description: 记录 learn-claude-code 项目的协作约定、关键结论与风险
metadata:
  type: project
---

# Agent 记忆文档

## 关键模块记忆

### agents/s01_agent_loop.py ~ s05_skill_loading.py, s_full.py
- 核心功能：各阶段 Agent 示例实现
- 当前状态：已从 Anthropic SDK 统一迁移为 OpenAI SDK 兼容格式
- 关键依赖：openai, python-dotenv

## 已知长期风险

（暂无）

## 当前维护方式

- 远程仓库：https://github.com/Tang200614/learn-claude-code.git
- 主要分支：main

## 最近十日时间线（北京时间）

### 2026-05-18
- 配置远程仓库为用户 fork：https://github.com/Tang200614/learn-claude-code.git
- 迁移所有 agent 文件（s01~s05, s_full）从 Anthropic SDK 到 OpenAI SDK 格式
- 提交并推送到 main 分支
- 为 [agents/s01_agent_loop.py](agents/s01_agent_loop.py) 添加详细中文注释，解释：
  - 核心架构（LLM→工具执行→结果反馈循环）
  - 每个函数与关键步骤的作用
  - 安全过滤、超时控制、输出限制机制
