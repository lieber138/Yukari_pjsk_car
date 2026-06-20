"""
YCM 发车搜索模块

搜索推特上的 プロセカ 发车推文，支持按歌曲/模式过滤。
"""

import logging
import tweepy

from twitter import BEARER_TOKEN

logger = logging.getLogger("ycm")

# 搜索用的基础关键词，🗝️ 确保是发车推文，-is:retweet 排除转推
BASE_QUERY = '🗝️ #プロセカ募集 -is:retweet'

# 过滤关键词映射，和 main.py 的 DICTIONARY 对应
# key 是用户可能输入的词，value 是推文里可能出现的词列表（满足任意一个即匹配）
FILTER_MAP = {
    "🦐": ["🦐"],
    "虾": ["🦐"],
    "龙": ["ロスエン"],
    "🐉": ["ロスエン"],
    "撒": ["sage"],
    "🍕": ["sage"],
    "omks": ["おまかせ"],
    "mv": ["MV"],
    "mv车": ["MV"],
    "长途": ["長時間周回"],
    "高速": ["高速周回"],
    "清火": ["火消し"],
    "消火": ["火消し"],
}


def get_client() -> tweepy.Client:
    return tweepy.Client(bearer_token=BEARER_TOKEN)


def tweet_matches_filter(tweet_text: str, filter_word: str) -> bool:
    """判断推文是否符合过滤条件"""
    filter_word = filter_word.strip().lower()

    # 在 FILTER_MAP 里找对应的关键词列表
    for key, values in FILTER_MAP.items():
        if filter_word == key.lower():
            return any(v in tweet_text for v in values)

    # 没找到映射就直接用原词匹配
    return filter_word in tweet_text.lower()


def parse_tweet(tweet_text: str, username: str, tweet_id: str) -> dict:
    """从推文文本里提取关键信息"""
    import re

    # 提取房间号（5位数字）
    room_match = re.search(r'🗝️[：:]?\s*(\d{5})', tweet_text)
    room = room_match.group(1) if room_match else "?????"

    # 提取招募人数
    people_match = re.search(r'@\s*([1-4])', tweet_text)
    people = people_match.group(1) if people_match else "?"

    # 提取模式/时间关键词
    mode = ""
    mode_keywords = [
        "sage", "🦐", "ロスエン", "おまかせ", "MV",
        "長時間周回", "高速周回", "火消し", "周回"
    ]
    for kw in mode_keywords:
        if kw in tweet_text:
            mode = kw
            break

    url = f"https://twitter.com/{username}/status/{tweet_id}"

    return {
        "room": room,
        "people": people,
        "mode": mode,
        "username": username,
        "url": url,
        "raw": tweet_text,
    }


def format_car(car: dict, index: int) -> str:
    """格式化单条发车信息"""
    mode_str = f" [{car['mode']}]" if car['mode'] else ""
    return (
        f"#{index} 🗝️{car['room']} @{car['people']}{mode_str}\n"
        f"👤 @{car['username']}\n"
        f"🔗 {car['url']}"
    )


def search_cars(filter_word: str = "", max_results: int = 10) -> str:
    """
    搜索发车推文，返回格式化后的消息字符串。
    filter_word 为空时返回所有发车推文。
    """
    client = get_client()

    try:
        response = client.search_recent_tweets(
            query=BASE_QUERY,
            max_results=max_results,
            tweet_fields=["author_id", "text"],
            expansions=["author_id"],
            user_fields=["username"],
        )
    except Exception:
        logger.exception("搜索发车推文失败")
        return "❌ 搜索失败，请检查网络或 API 配置"

    if not response.data:
        return "🔍 没有找到发车推文"

    # 建立 author_id → username 映射
    users = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            users[user.id] = user.username

    # 过滤推文
    cars = []
    for tweet in response.data:
        text = tweet.text
        if filter_word and not tweet_matches_filter(text, filter_word):
            continue
        username = users.get(tweet.author_id, "unknown")
        cars.append(parse_tweet(text, username, str(tweet.id)))

    if not cars:
        filter_hint = f"「{filter_word}」的" if filter_word else ""
        return f"🔍 没有找到{filter_hint}发车推文"

    # 拼装消息
    header = f"🚗 找到 {len(cars)} 条发车信息"
    if filter_word:
        header += f"（过滤：{filter_word}）"
    header += "\n───────────────"

    lines = [header]
    for i, car in enumerate(cars, 1):
        lines.append(format_car(car, i))
        lines.append("───────────────")

    return "\n".join(lines)