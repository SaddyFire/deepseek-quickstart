import os
from openai import OpenAI


# 从环境变量获取 DeepSeek API Key
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")

# 初始化 OpenAI 客户端（假设 DeepSeek 的 API 兼容 OpenAI 格式）
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1",  # DeepSeek API 的基地址
)

# 定义提示词
prompt = """请帮我用 HTML 生成一个五子棋游戏，所有代码都保存在一个 HTML 中。要求代码简洁完整，包含基本的游戏功能。"""
try:
    messages=[
            {"role": "system", "content": "你是一个专业的 Web 开发助手，擅长用 HTML/CSS/JavaScript 编写游戏。请生成简洁但完整的代码。"},
            {"role": "user", "content": prompt}
        ]
    html_content = ""
    max_iterations = 5
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f"正在生成内容，第 {iteration} 次迭代")
        # 调用 DeepSeek Chat API
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或 DeepSeek 提供的其他模型名称
            messages=messages,
            temperature=0.7,
            stream=False,
            max_tokens=4096
        )
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            if content:
                html_content += content
                print(f"已添加内容，当前总长度: {len(html_content)}")

            if finish_reason == "length":
                print("输出被截断，继续请求补充...")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "请继续完成上面的代码，不要重复之前的内容"})
            else:
                print(f"生成完成，原因: {finish_reason}")
                break
        else:
            print("未收到有效响应")
            break
    if html_content:
        with open("gomoku.md", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"五子棋游戏已保存为 gomoku.md {len(html_content)} 字符")
    else:
        raise Exception("未能生成 HTML 内容")

except Exception as e:
    print(f"调用 API 出错: {e}")