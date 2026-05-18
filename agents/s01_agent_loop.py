#!/usr/bin/env python3
# Harness: the loop -- the model's first connection to the real world.
"""
s01_agent_loop.py - The Agent Loop

The entire secret of an AI coding agent in one pattern:

    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)

This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
"""

import os
import subprocess

# 启用命令行编辑支持（readline：历史记录、方向键编辑等
try:
    import readline
    # #143 UTF-8 退格键修复（针对 macOS libedit）
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
except ImportError:
    pass

from anthropic import Anthropic
from dotenv import load_dotenv

# 加载环境变量（从 .env 文件
load_dotenv(override=True)

# 如果配置 API 客户端：如果指定了自定义 base_url 则移除默认 auth token
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

# 初始化 Anthropic 客户端（兼容 OpenAI SDK 格式
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

# 系统提示词：定义 Agent 的身份和行为
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

# 工具定义：只有一个 bash 工具，用于执行 shell 命令
TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]


def run_bash(command: str) -> str:
    """执行 bash 命令执行器（带安全过滤）"""
    # 危险命令黑名单
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        # 执行命令：当前目录、捕获输出、文本模式、120秒超时
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        # 合并标准输出和标准错误
        out = (r.stdout + r.stderr).strip()
        # 返回结果截断到 50000 字符上限
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


# -- 核心模式：一个 while 循环，调用工具直到模型停止 --
def agent_loop(messages: list):
    """Agent 主循环：LLM 调用 → 工具执行 → 结果反馈 → 循环继续"""
    while True:
        # 调用 LLM：传入消息历史、系统提示、工具定义
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        # 追加助手回复到消息历史
        messages.append({"role": "assistant", "content": response.content})
        # 如果模型没有调用工具，说明任务完成，退出循环
        if response.stop_reason != "tool_use":
            return
        # 执行每个工具调用，收集结果
        results = []
        for block in response.content:
            if block.type == "tool_use":
                # 高亮显示要执行的命令（黄色）
                print(f"\033[33m$ {block.input['command']}\033[0m")
                # 执行命令
                output = run_bash(block.input["command"])
                # 显示输出（最多 200 字符）
                print(output[:200])
                # 构建工具结果消息
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output})
        # 将工具结果追加到消息历史，继续循环
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    # 对话历史记录
    history = []
    # 主输入循环
    while True:
        try:
            # 读取用户输入（青色提示符）
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D 或 Ctrl+C 退出
            break
        # 退出命令检测
        if query.strip().lower() in ("q", "exit", ""):
            break
        # 将用户查询加入历史
        history.append({"role": "user", "content": query})
        # 运行 Agent 循环
        agent_loop(history)
        # 显示最终回复（最后一条或多条文本块）
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
