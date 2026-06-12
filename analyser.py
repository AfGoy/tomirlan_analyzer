# analyser.py
import os
import time
from groq import Groq, RateLimitError
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SEP = " | "

def analyse_messages(messages: list[str]) -> str:
    messages_text = SEP.join(messages)
    system_prompt = f"Выяви общие темы массива сообщений в чате. Сделай краткую сводку. Сообщения разделяются через {SEP}"

    for attempt in range(3):  # 3 попытки
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": messages_text}
                ]
            )
            return response.choices[0].message.content

        except RateLimitError:
            if attempt < 2:
                time.sleep(5)
                continue
            return "Превышен лимит запросов, попробуйте через минуту."

        except Exception as e:
            return f"Ошибка: {e}"