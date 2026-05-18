#!/usr/bin/env python3
# Harness: 这个文件是 Agent 主循环的实现，负责输入循环，处理用户输入，调用 LLM，执行工具，追加结果。
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

# 启用命令行编辑支持
try:
    import readline
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
except ImportError:
    pass

from dotenv import load_dotenv
from anthropic import Anthropic

# 1. 加载环境变量
load_dotenv(override=True)

# 2.初始化客户端
# base_url可选，用getenv初始化，不填就使用默认的 Anthropic 客户端
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
# MODEL必填，用os.environ获取模型 ID，全大写表示"常量"
MODEL = os.environ["MODEL_ID"]

SYSTEM = f"你是一个编程助手，当前目录是 {os.getcwd()}. 使用 bash 命令执行任务。"

# 3. 添加工具定义
TOOLS = [
    {
        "name": "bash",
        "description": "Execute bash commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"}
            },
            "required": ["command"]
        }
    }
]

def run_bash(command: str) -> str:
    """执行 bash 命令"""
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(cmd in command for cmd in dangerous):
        return "Dangerous command detected!"
    try:
        result = subprocess.run(
            command,              # 要执行的命令，比如 "ls"
            shell=True,           # 通过 shell 执行（支持通配符等）
            capture_output=True,  # 捕获输出（stdout 和 stderr）
            text=True,            # 输出作为文本，不是二进制
            cwd=os.getcwd(),      # 在哪个目录执行
            timeout=120,            # 新加这一行！单位是秒！
            encoding="utf-8",
            errors="replace"
        )
        print("stdout: ", result.stdout, result.returncode)
        # 返回结果截断到 50000 字符上限
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if result.returncode == 0 else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except Exception as e:
        return f"Error: {e}"

# 3. 历史消息
messages = []

# 4.主循环
print("输入 'q' 退出")
while True:
    # 读取用户输入
    user_input = input("\n\033[36ms01 >> \033[0m")
    if user_input.lower() == "q":
        break
    # 加入历史
    messages.append({"role": "user", "content": user_input})
    # 第一次调用模型
    response = client.messages.create(
        system=SYSTEM,
        model=MODEL,
        max_tokens=100,
        messages=messages,
        tools=TOOLS
     )

    # 先把第一次回复加入历史！
    messages.append({"role": "assistant", "content": response.content})

    # 如果是 tool_use，执行工具
    if response.stop_reason == "tool_use":
        print(response.content)
        tool_result_content = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(block.input["command"])
                print(f"📤 输出: {output[:200]}")
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output
                })

        # 把工具结果作为 user 消息加入历史
        messages.append({"role": "user", "content": tool_result_content})

        # 再次调用模型
        print("\n🤔 把结果给 AI，让它继续...")
        response = client.messages.create(
            system=SYSTEM,
            model=MODEL,
            max_tokens=1000,
            messages=messages,
            tools=TOOLS
        )

        # 把第二次回复也加入历史
        messages.append({"role": "assistant", "content": response.content})

    # 显示最终文本回复
    for block in response.content:
        if block.type == "text":
            print(f"\nAI: {block.text}")
            break
    