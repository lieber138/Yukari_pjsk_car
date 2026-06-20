"""Twitter 发推模块

通过 tweepy 库调用 Twitter API v2 发推。
"""

import tweepy

# ── 把你的五个 key 填在这里 ──────────────────────────────
CONSUMER_KEY        = "2keeAgWV1IDtBkgCwtb6Fe2jR"
CONSUMER_SECRET     ="P1ao24i3No9bKmCij0R5pUcdf6cmePrFls0rSPv9Pxxy9feGMt"
ACCESS_TOKEN        = "2007381108531568640-SuLnZnuhvG6hgS8anlHV4wtSHiBlKU"
ACCESS_TOKEN_SECRET = "lSIqrsxhkEMMRL6jfOhmZl5qUyGyoIY4T1bUDwwfRPKJJ"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAOnz%2BAEAAAAAM2PK2lWD8RDwzjUjEUTY8svlyEw%3DYEzI7uEeJrqrTxrgu7Gmg7kkgehps0mt09ahxrClMQoMfuqMPU"
# Bearer Token 只用于只读操作，发推用不到，可以不填
# ────────────────────────────────────────────────────────


def get_client() -> tweepy.Client:
    """创建并返回一个 tweepy 客户端（每次调用都新建，避免状态问题）"""
    return tweepy.Client(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )


def post_tweet(text: str) -> str:
    """
    发一条推文，返回推文链接。
    失败时抛出异常，由调用方处理。
    """
    client = get_client()
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return f"https://twitter.com/i/web/status/{tweet_id}" 