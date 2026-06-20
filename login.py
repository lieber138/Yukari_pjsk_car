# login.py
import asyncio
from twikit import Client

async def main():
    client = Client(language='ja-JP')
    await client.login(
        auth_info_1='',
        auth_info_2='',  # 如果上面填的是用户名，这里填邮箱
        password=''
    )
    client.save_cookies('cookies.json')
    print('登录成功，cookie 已保存')

asyncio.run(main())
