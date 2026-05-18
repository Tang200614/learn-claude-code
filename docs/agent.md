---
name: learn-claude-code-agent-memory
description: 记录 learn-claude-code 项目的协作约定、关键结论与风险
metadata:
  type: project
---

# Agent 记忆文档

## 关键模块记忆

### agents/s01_agent_loop.py
- 核心功能：基础 Agent Loop 实现
- 当前状态：已从 Anthropic SDK 切换为 OpenAI SDK 兼容格式
- 关键依赖：openai, python-dotenv

## 已知长期风险

（暂无）

## 当前维护方式

- 远程仓库：https://github.com/Tang200614/learn-claude-code.git
- 主要分支：main

## 最近十日时间线（北京时间）

### 2026-05-18
- 配置远程仓库为用户 fork：https://github.com/Tang200614/learn-claude-code.git
- 修改 s01_agent_loop.py：从 Anthropic SDK 迁移到 OpenAI SDK 格式
