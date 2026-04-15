import os
from datetime import datetime
from urllib.parse import quote
import feedparser
import requests
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

다음 형식으로 한국어로 정리해라.

[출력 형식]
## 1. 오늘의 핵심 AI 뉴스
- 핵심 뉴스 5개를 bullet point로 정리

## 2. 왜 중요한가
- 3~5줄 bullet point로 정리

## 3. 취업 준비생 관점 메모
- 3줄 이내 bullet point로 정리

조건:
- 반드시 한국어
- 너무 장황하지 않게
- 디스코드에서 보기 좋게 정리
- 각 항목은 bullet point(-) 사용
"""

    response = client.responses.create(
        model="gpt-4o",
        input=prompt
    )

    return response.output_text


# 디스코드 메시지 포맷
def build_discord_message(summary):
    now = datetime.now()
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]
    date_str = f"{now.year}년 {now.month}월 {now.day}일 ({weekday_kr[now.weekday()]})"

    header = (
        f"🤖 **AI 뉴스 봇** | {date_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 **오늘의 AI 뉴스 브리핑**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )

    footer = "\n\n━━━━━━━━━━━━━━━━━━\n#AI #뉴스브리핑 #취업준비"

    message = header + summary + footer
    return message[:4000]  # embed description 최대 길이 고려


# 디스코드 전송
def send_to_discord(message):
    embed = {
        "title": "📢 오늘의 AI 뉴스 브리핑",
        "description": message,
        "color": 0x00FFCC,
        "footer": {
            "text": "AI 뉴스 봇"
        }
    }

    data = {
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=20)
    print("디스코드 전송 상태:", response.status_code)
    print("디스코드 응답:", response.text)
    response.raise_for_status()


# 실행
def main():
    print("웹훅 존재 여부:", DISCORD_WEBHOOK_URL is not None)

    articles = fetch_top_news(AI_NEWS_RSS)
    print("가져온 뉴스 개수:", len(articles))
    print("뉴스 샘플:", articles[:3])

    summary = summarize_news(articles)
    print("요약 결과 일부:", summary[:300])

    message = build_discord_message(summary)
    send_to_discord(message)


if __name__ == "__main__":
    main()
