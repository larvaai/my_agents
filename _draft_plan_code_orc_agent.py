import os
from openai import OpenAI

# 1. Cấu hình kết nối tới LM Studio Local Server
# Mặc định LM Studio chạy tại cổng 1234
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Tên chính xác của model đã load trong LM Studio (gemma-4-e4b)
# MODEL_NAME = "crow-9b-opus-4.6-distill-heretic_qwen3.5" 
MODEL_NAME = "qwen3.5-9b-claude-4.6-opus-uncensored-distilled" 

USER_TASK = """
Cho tôi các bước đơn giản nhất để giải một phương trình bậc hai ax^2 + bx + c = 0.
"""

# 2. Hàm gọi LLM để lấy câu trả lời
def call_llm(system_prompt, user_prompt, model="local-model"):
    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )
    return res.choices[0].message.content

PLAN_SYSTEM = """
Bạn là Plan Agent.
Nhiệm vụ của bạn là chia yêu cầu lớn thành các bước nhỏ, rõ ràng.
Không viết code.
Chỉ trả về danh sách bước.
"""

def plan_agent(task):
    return call_llm(PLAN_SYSTEM, task)

CODE_SYSTEM = """
Bạn là Code Agent.
Nhiệm vụ của bạn là viết code Python theo task cụ thể.
Không tự mở rộng yêu cầu.
Code phải ngắn, rõ, chạy được.
"""

def code_agent(task):
    return call_llm(CODE_SYSTEM, task)

def orchestrate(user_task):
    plan = plan_agent(user_task)

    print("PLAN:")
    print(plan)

    steps = plan.split("\n")

    for step in steps:
        if not step.strip():
            continue

        print("\nDOING:", step)
        code = code_agent(step)
        print(code)

orchestrate(USER_TASK)