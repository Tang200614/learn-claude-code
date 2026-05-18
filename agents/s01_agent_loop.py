#!/usr/bin/env python3
# Harness: the loop -- the model's first connection to the real world.
"""
s01_agent_loop.py - 代理循环（Agent Loop）

一个 AI 编程代理的全部秘密就在于这个模式：

    while stop_reason == "tool_use":
        response = LLM(messages, tools)   # 调用大模型
        execute tools                     # 执行工具
        append results                    # 追加结果

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (循环继续)

这就是核心循环：把工具执行结果反馈给模型，
直到模型决定停止。生产级代理会在此基础上
添加策略、钩子和生命周期控制。
"""

# ========== 导入必要的库 ==========
import os
import subprocess

# 尝试导入 readline 库（用于命令行输入编辑）
try:
    import readline
    # #143 UTF-8 退格键修复（针对 macOS 的 libedit）
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
except ImportError:
    pass

from openai import OpenAI
from dotenv import load_dotenv

# ========== 初始化配置 ==========
# 加载 .env 文件中的环境变量（覆盖已存在的同名变量）
load_dotenv(override=True)

# 创建 OpenAI 客户端（这里配置为连接 Anthropic API）
client = OpenAI(
    api_key=os.getenv("ANTHROPIC_API_KEY"),    # 从环境变量读取 API 密钥
    base_url=os.getenv("ANTHROPIC_BASE_URL")  # 从环境变量读取 API 基础地址
)
MODEL = os.environ["MODEL_ID"]  # 要使用的模型 ID

# 系统提示词：告诉模型它的身份和行为准则
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

# ========== 定义可用的工具 ==========
# 这里只定义了一个 bash 工具，用于执行 shell 命令
TOOLS = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    }
}]


# ========== 执行 bash 命令的函数 ==========
def run_bash(command: str) -> str:
    """执行 shell 命令并返回输出结果"""
    # 安全检查：阻止一些危险命令
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"

    try:
        # 执行命令
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        # 合并标准输出和标准错误
        out = (r.stdout + r.stderr).strip()
        # 返回输出（限制最大长度为 50000 字符）
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


# ========== 核心模式：一个 while 循环，调用工具直到模型停止 ==========
def agent_loop(messages: list):
    """
    代理主循环

    参数:
        messages: 对话历史列表，包含用户消息、助手消息、工具结果等
    """
    while True:
        # 1. 调用大模型
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}] + messages,  # 系统提示词 + 历史对话
            tools=TOOLS,  # 告诉模型有哪些工具可用
            max_tokens=8000,  # 限制输出长度
        )
        choice = response.choices[0]  # 获取第一个（通常也是唯一的）选择

        # 2. 把助手的回复添加到对话历史中
        assistant_msg = {"role": "assistant", "content": choice.message.content}
        # 如果模型调用了工具，也要把工具调用信息添加进去
        if choice.message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in choice.message.tool_calls
            ]
        messages.append(assistant_msg)

        # 3. 如果模型没有调用工具，说明任务完成，退出循环
        if not choice.message.tool_calls:
            return

        # 4. 执行每个工具调用，收集结果
        for tc in choice.message.tool_calls:
            if tc.function.name == "bash":
                import json
                # 解析工具参数（JSON 格式）
                args = json.loads(tc.function.arguments)
                # 打印要执行的命令（黄色）
                print(f"\033[33m$ {args['command']}\033[0m")
                # 执行命令
                output = run_bash(args["command"])
                # 打印输出（只打印前 200 字符）
                print(output[:200])
                # 把工具执行结果添加到对话历史中
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,  # 对应工具调用的 ID
                    "content": output
                })


# ========== 主程序入口 ==========
if __name__ == "__main__":
    history = []  # 保存整个对话历史
    while True:
        try:
            # 获取用户输入（青色提示符）
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            # 用户按 Ctrl+C 或 Ctrl+D 退出
            break

        # 如果输入 q、exit 或空行，退出程序
        if query.strip().lower() in ("q", "exit", ""):
            break

        # 把用户输入添加到对话历史
        history.append({"role": "user", "content": query})
        # 运行代理循环
        agent_loop(history)
        # 获取并打印模型的最终回复
        response_content = history[-1]["content"]
        if response_content:
            print(response_content)
        print()
