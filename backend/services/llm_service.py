# backend/services/llm_service.py
from openai import OpenAI
from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, LLM_MODEL

# 初始化通义千问客户端（兼容 OpenAI 接口格式）
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL
)


def call_llm(prompt: str, temperature: float = 0.1, system_prompt: str = None) -> str:
    """调用通义千问 API

    Args:
        prompt: 用户提示词
        temperature: 温度值，越低输出越稳定（Cypher 生成建议 0.1，回答建议 0.3）
        system_prompt: 系统提示词（可选）

    Returns:
        LLM 返回的文本
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # 测试
    result = call_llm("1+1 等于几？请用中文回答")
    print(f"LLM 返回：{result}")
