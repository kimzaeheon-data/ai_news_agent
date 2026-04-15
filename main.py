import os
from datetime import datetime
from urllib.parse import quote
import feedparser
import requests
import json
from openai import OpenAI

# 설정
query = quote("AI OR 인공지능 OR LLM OR 생성형AI OR ChatGPT")
AI_NEWS_RSS = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 없습니다.")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL가 없습니다.")

client = OpenAI(api_key=OPENAI_API_KEY)


# 뉴스 가져오기
def fetch_top_news(rss_url, max_items=10):
    feed = feedparser.parse(rss_url)

    articles = []
    for entry in feed.entries[:max_items]:
        articles.append(entry.get("title", ""))

    return articles


# 뉴스 요약
def summarize_news(articles):
    news_text = "\n".join(
        [f"{i+1}. {title}" for i, title in enumerate(articles)]
    )

    prompt = f"""
아래는 오늘의 AI 뉴스 제목이다.

{news_text}

아래 형식의 JSON으로만 답해라.
설명은 쓰지 말고 JSON만 출력해라.

{{
  "핵심뉴스": [
    "문장1",
    "문장2",
    "문장3",
    "문장4",
    "문장5"
  ],
  "왜중요한가": [
    "문장1",
    "문장2",
    "문장3"
  ],
  "취업관점": [
    "문장1",
    "문장2",
    "문장3"
  ]
}}

조건:
- 반드시 한국어
- 각 문장은 bullet point로 바로 쓸 수 있게 짧고 명확하게
- 제목(예: ## 1. 오늘의 핵심 AI 뉴스) 쓰지 말 것
"""

    response = client.responses.create(
        model="gpt-4o",
        input=prompt
    )

    return response.output_text


# 디스코드 메시지 포맷
def build_discord_message(summary_text):
    data = json.loads(summary_text)

    now = datetime.now()
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]
    date_str = f"{now.year}년 {now.month}월 {now.day}일 ({weekday_kr[now.weekday()]})"

    def to_bullets(items):
        return "\n".join([f"• {item}" for item in items])

    embed = {
        "title": "📢 오늘의 AI 뉴스 브리핑",
        "description": f"🤖 **AI 뉴스 봇** | {date_str}",
        "color": 0x00FFCC,
        "fields": [
            {
                "name": "🧠 핵심 뉴스",
                "value": to_bullets(data["핵심뉴스"])[:1000],
                "inline": False
            },
            {
                "name": "📊 왜 중요한가",
                "value": to_bullets(data["왜중요한가"])[:1000],
                "inline": False
            },
            {
                "name": "🚀 취업 관점",
                "value": to_bullets(data["취업관점"])[:1000],
                "inline": False
            }
        ],
        "footer": {
            "text": "AI 뉴스 봇 · #AI #뉴스브리핑 #취업준비"
        }
    }

    return embed


# 디스코드 전송
def send_to_discord(embed):
    data = {
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=20)
    print("디스코드 전송 상태:", response.status_code)
    print("디스코드 응답:", response.text)
    response.raise_for_status()


# 실행
def main():
    articles = fetch_top_news(AI_NEWS_RSS)
    print("가져온 뉴스 개수:", len(articles))
    print("뉴스 샘플:", articles[:3])

    summary_text = summarize_news(articles)
    print("요약 결과 일부:", summary_text[:300])

    embed = build_discord_message(summary_text)
    send_to_discord(embed)


if __name__ == "__main__":
    main()
