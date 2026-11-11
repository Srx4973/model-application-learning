# 工具 1：天气查询（假装能查，先返回假数据）
def get_weather(city: str) -> str:
    # 真实场景下，这里会去调高德/百度的天气API
    if "太原" in city:
        return "太原今天晴，气温 28 度，微风。"
    return f"{city}今天多云，气温 25 度。"

# 工具 2：计算器
def calculate(expression: str) -> str:
    try:
        # 用 Python 自带的 eval 计算
        result = eval(expression)
        return f"计算结果是：{result}"
    except Exception as e:
        return f"计算失败：{e}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：太原、北京",
                    }
                },
                "required": ["city"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，例如：123 * 456",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式",
                    }
                },
                "required": ["expression"],
            },
        }
    }
]
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
URL = "https://api.qnaigc.com/v1/chat/completions"
MODEL = "qiniu/conatus-free"


def ask_agent(user_question):
    messages = [{"role": "user", "content": user_question}]

    # 1. 第一次请求：带上 tools 列表
    data = {
        "model": MODEL,
        "messages": messages,
        "tools": tools,  # 把说明书交给大模型
        "temperature": 0.1
    }

    resp = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}"}, json=data)
    response_data = resp.json()
    message = response_data["choices"][0]["message"]

    # 2. 判断大模型是不是要调工具
    if "tool_calls" in message:
        print("\n大模型决定调用工具！")
        messages.append(message)  # 把大模型的决策（包含 tool_calls）加进历史记录

        # 3. 你的程序负责干活
        for tool_call in message["tool_calls"]:
            func_name = tool_call["function"]["name"]
            # 获取大模型想要传的参数
            args = json.loads(tool_call["function"]["arguments"])
            print(f"准备执行：{func_name}，参数：{args}")

            # 执行本地函数
            if func_name == "get_weather":
                result = get_weather(args["city"])
            elif func_name == "calculate":
                result = calculate(args["expression"])
            else:
                result = "未知工具"

            # 4. 把执行结果包装成 "tool" 消息，塞回历史记录
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result
            })

        # 5. 第二次请求：把执行结果喂给大模型，让它做最终总结
        data["messages"] = messages
        # 第二次请求不需要再传 tools 了
        data.pop("tools", None)

        final_resp = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}"}, json=data)
        final_answer = final_resp.json()["choices"][0]["message"]["content"]
        return final_answer

    else:
        # 如果没调工具，直接返回大模型的回答
        return message["content"]


if __name__ == "__main__":
    # 测试 1：需要查天气
    print("用户：太原今天天气怎么样？")
    print("AI: ", ask_agent("太原今天天气怎么样？"))

    print("\n" + "=" * 30 + "\n")

    # 测试 2：需要计算
    print("用户：帮我算一下 123 乘 456 等于多少？")
    print("AI: ", ask_agent("帮我算一下 123 乘 456 等于多少？"))