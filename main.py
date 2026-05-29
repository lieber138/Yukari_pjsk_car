"""Core text conversion rules for the PJSK car bot.

This file is intentionally independent from NapCat/WebSocket code.  The bot
service in server.py imports do_transform() from here, so editing the wording,
keywords, or generated template usually only requires changing this file.
"""

import re
import random
DICTIONARY = {
    "🦐": "🦐",
    "虾": "🦐",
    "龙": "ロスエン",
    "🐉": "ロスエン",
    "撒": "sage",
    "🍕": "sage",
    "omks":"おまかせ",
    "mv车":"MV",
}

MODE_RULES = {
    "清火": "火消し",
    "消火": "火消し",
    "长途": "長時間周回",
    "高速": "高速周回"
}

tag_lines = [
    "#プロセカ募集 #プロセカ協力 #プロセカ",
    "#プロセカ協力 #プロセカ募集",
    "#プロセカ #プロセカ募集",
]

extra_lines = [
    "長時間歓迎",
    "途中退室OK",
    "スタンプ他と同じです",
    "SF気にしません",
    "難易度自由",
    "集まるまで待てる方",
    "条件違い解散"
]


def get_mode(raw):
    for k, v in MODE_RULES.items():
        if k in raw:
            return v
    return "周回"
    
def do_transform(text):
    """Convert one Chinese /发车 message body into the Japanese募集文案."""
    raw = text
    room_match = re.search(r'\d{5}', raw)
    room_number = room_match.group() if room_match else "XXXXX"
    
    people_match = re.search(r'(q|Q)\s*([1-4])', raw)
    wanted_players = people_match.group(2) if people_match else "1"
    
    host_match = re.search(r'(房主|主|车头)\s*(\d{3})', raw)
    host_line = "" 
    if host_match:
        host_line = f"主:{host_match.group(2)}%\n"  # 抓到了就自带换行
        
    clean = raw
    clean = re.sub(r'\d{5}', '', clean)  # 房间号
    clean = re.sub(r'(房主|主|车头)\s*\d{3}', '', clean)  # 房主    
    
    
    bonus_match = re.search(r'(\d{3})', clean)
    bonus_line = "" 
    if bonus_match:
        bonus_line = f"募:{bonus_match.group(1)}%↑\n"
    
    if bonus_match:
        clean= clean.replace(bonus_match.group(1), "")
    
            

    support_line = ""
    # 检查有没有“推”、“支援”或者“实效”
    # support判断用 raw（只判断有没有关键词）
    if "推" in raw or "支援" in raw or "实效" in raw:
    
        # support提数字用 clean（已经去掉房号/房主）
        support_match = re.search(r'(\d{3})', clean)
    
        if support_match:
            support_line = f"(支援います {support_match.group(1)}%)\n"
        else:
            support_line = "(支援います)\n"
    
    end_word = get_mode(raw)              
    
    # 用 clean 判断时间/次数，避免房间号 12345 被误识别成 45時まで。
    time_match = re.search(
        r'(?<![A-Za-z0-9])([\d一二三四五六七八九十]{1,2})[:点](\d{2})?分?(半)?',
        clean,
    )
    count_match = re.search(r'([\d一二三四五六七八九十]+)\s*(把|次|圈|回)', clean)
    
    if time_match:
        hour = time_match.group(1)
        minute = time_match.group(2)
        is_half = time_match.group(3)
        
        # 汉字数字转阿拉伯数字字典，防止拼出日文里奇怪的 "四時まで"
        cn_to_num = {
            "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
            "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
            "十一": "11", "十二": "12"
        }
        if hour in cn_to_num:
            hour = cn_to_num[hour] # 把 "四" 悄悄换成 "4"
            
        if is_half:
            end_word = f"{hour}時半まで"
        elif minute:
            end_word = f"{hour}時{minute}分まで"
        else:
            end_word = f"{hour}時まで"
            
    elif count_match:
        # 2. 如果指定了明确的次数（比如清火打3把）
        count_num = count_match.group(1)
        # 如果抓到的是汉字“十”，自动变成数字“10”
        cn_to_num = {"一": "1", "二": "2", "两": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}
        if count_num in cn_to_num:
            count_num = cn_to_num[count_num]
        end_word = f"{count_num}回"
        

    # 随机插一点小表情
    emoji_pool = ["✨", "🎶", "🙌", "🌟", "🎧", "💫"]
    
    # 复制一份，避免污染原列表
    lines = extra_lines.copy()
    
    # 30%概率随机给一句后面加emoji
    for i in range(len(lines)):
        if random.random() < 0.3:
            lines[i] += " " + random.choice(emoji_pool)
    
    # 打乱顺序
    random.shuffle(lines)
    
    # 拼接成文本
    extra_text = "\n".join(lines)
        
    jp_mode = ""  # 默认不填歌曲名
    for cn_word, jp_word in DICTIONARY.items():
        if cn_word in raw:
            jp_mode = jp_word
            break
    text = f""" ベテラン {jp_mode}{end_word} @{wanted_players}
    【代理】
    🗝️:{room_number}
    {support_line}
    {host_line}
    {bonus_line}
    {extra_text}
    
    {random.choice(tag_lines)}"""
    return text #  在函数末尾把文本 return 出来

# 运行 python main.py 时才会触发这里
if __name__ == "__main__":
    chinese_input = input("输入你的发车消息:\n ")
    print(do_transform(chinese_input))
