import re
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
def do_transform(chinese_input):
    room_match = re.search(r'\d{5}', chinese_input)
    room_number = room_match.group() if room_match else "XXXXX"
    
    people_match = re.search(r'(q|Q)\s*([1-4])', chinese_input)
    wanted_players = people_match.group(2) if people_match else "1"
    
    host_match = re.search(r'(房主|主|车头)\s*(\d{3})', chinese_input)
    host_line = "" 
    if host_match:
        host_line = f"主:{host_match.group(2)}%\n"  # 抓到了就自带换行
    
    # 【募集加成核心修复】
    clean_input = chinese_input
    if host_match:
        clean_input = clean_input.replace(host_match.group(), "") # 删掉 房主250
    if room_match:
        clean_input = clean_input.replace(room_number, "")        # 重点：把 55555 房号也删掉！
    
    bonus_match = re.search(r'(\d{3})', clean_input)
    bonus_line = "" 
    if bonus_match:
        bonus_line = f"募:{bonus_match.group(1)}%↑\n"
    
    if bonus_match:
        clean_input = clean_input.replace(bonus_match.group(1), "")
    
    support_line = ""
    # 检查有没有“推”、“支援”或者“实效”
    if "推" in chinese_input or "支援" in chinese_input or "实效" in chinese_input:
        support_match = re.search(r'(\d{3})', clean_input)
        if support_match:
            # 完美还原你要求的日服网站格式：(支援います 256%)
            support_line = f"(支援います {support_match.group(1)}%)\n"
        else:
            support_line = f"(支援います)\n"    
    
    time_match = re.search(r'([\d一二三四五六七八九十]{1,2})[:点\s](\d{2})?分?(半)?', chinese_input)
    count_match = re.search(r'([\d一二三四五六七八九十]+)\s*(把|次|圈|回)', chinese_input)
    
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
        
    elif "清火" in chinese_input or "消火" in chinese_input:
        # 3. 如果没打数字，但提到了“清火”
        end_word = "火消し" # 日服清火专用词
        
    elif  "长途" in chinese_input:
        # 4. 如果提到了“冲榜”
        end_word = "長時間周回" # 长时间周回
    
    elif  "高速" in chinese_input:
        end_word = "高速周回"    
        
    else:
        # 5. 啥都没提，默认普通周回
        end_word = "周回"
        
    jp_mode = ""  # 默认不填歌曲名
    for cn_word, jp_word in DICTIONARY.items():
        if cn_word in chinese_input:
            jp_mode = jp_word
            break
    text = f""" ベテラン {jp_mode}{end_word} @{wanted_players}
    【代理】
    🗝️:{room_number}
    {support_line}
    {host_line}
    {bonus_line}
    長時間歓迎
    途中退室OK
    スタンプ他と同じです
    SF気にしません
    難易度自由
    集まるまで待てる方
    条件違い解散
    
    #プロセカ募集 #プロセカ協力 #プロセカ"""

    return text #  在函数末尾把文本 return 出来

# 运行 python main.py 时才会触发这里
if __name__ == "__main__":
    chinese_input = input("输入你的发车消息:\n ")
    print(do_transform(chinese_input))
