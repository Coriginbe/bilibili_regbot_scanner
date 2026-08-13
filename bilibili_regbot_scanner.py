import random
import re
import time
import os
from DrissionPage import ChromiumPage, ChromiumOptions


OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result.txt")
MIN_DELAY = 2
MAX_DELAY = 5
DEBUGGING_PORT = 9222


COMMON_WORDS = [
    "the", "ing", "tion", "ment", "able", "ness", "ful", "less",
    "game", "love", "cool", "star", "fire", "dark", "blue", "king",
    "play", "hero", "wolf", "fox", "cat", "dog", "sky", "moon",
    "sun", "ice", "war", "pro", "max", "boy", "girl", "man",
    "fan", "god", "ace", "top", "big", "red", "hot", "old",
    "new", "one", "two", "day", "way", "eye", "her", "his",
    "you", "not", "all", "can", "out", "use", "how", "its",
    "may", "did", "get", "has", "him", "see", "now", "come",
    "than", "like", "just", "over", "know", "back", "only",
    "good", "some", "time", "very", "when", "with", "make",
    "hand", "high", "keep", "last", "long", "much", "own",
    "say", "she", "too", "any", "same", "tell", "each",
    "bilibili", "bili", "video", "anime", "music", "live",
    "rabbit", "kitty", "panda", "tiger", "dragon", "shadow",
    "night", "super", "moon", "star", "fire", "ice", "dark",
    "blue", "king", "hero", "wolf", "fox", "cat", "dog",
]

COMMON_SURNAMES = [
    "chen", "wang", "zhang", "liu", "yang", "huang", "zhao", "zhou", "wu",
    "xu", "sun", "ma", "zhu", "hu", "guo", "lin", "he", "gao", "zheng",
    "liang", "xie", "song", "tang", "han", "cao", "deng", "xiao",
    "cheng", "cai", "peng", "pan", "yuan", "yu", "dong", "ye", "du",
    "ding", "jiang", "shen", "fan", "lu", "wei", "su", "jia",
    "zou", "xiong", "meng", "qin", "yan", "qiu", "hou", "yin", "shi",
    "gu", "ji", "mo", "li", "tan", "cui", "xue", "lei", "he",
    "ni", "tang", "hao", "kong", "bai", "kang", "wan", "ou",
    "fang", "li", "zhou", "ning", "qin", "zeng", "xue",
]

VOWELS = set("aeiou")


def contains_surname(name: str) -> bool:
    """检测用户名是否包含常见中文姓氏"""
    name_lower = name.lower()
    for surname in COMMON_SURNAMES:
        pattern = r'(?<![a-zA-Z])' + re.escape(surname) + r'(?![a-zA-Z])'
        if re.search(pattern, name_lower):
            return True
    return False


def contains_year_or_date(name: str) -> bool:
    """检测用户名是否包含年份或日期格式的数字"""
    if re.search(r'(19|20)\d{2}', name):
        return True
    if re.search(r'\d{6,8}', name):
        return True
    return False


def is_gibberish_name(name: str) -> bool:
    """
    判断用户名是否为随机生成的乱码字符串
    判定依据：仅含小写字母和数字、长度6-16位、辅音比例大于60%、不含常见词汇
    """
    if not re.fullmatch(r"[a-z0-9]+", name):
        return False
    if not (6 <= len(name) <= 16):
        return False
    
    letters_only = re.sub(r"[0-9]", "", name)
    if len(letters_only) < 4:
        return False
    
    consonant_count = sum(1 for ch in letters_only.lower() if ch not in VOWELS)
    if consonant_count / len(letters_only) <= 0.60:
        return False
    
    name_lower = name.lower()
    for word in COMMON_WORDS:
        if word in name_lower:
            return False
    
    if contains_surname(name):
        return False
    if contains_year_or_date(name):
        return False
    
    return True


def get_username(page) -> str:
    """从页面中提取用户名"""
    try:
        name_elem = page.ele("css:div.nickname", timeout=5)
        if name_elem:
            return name_elem.text.strip()
        name_elem = page.ele("css:[class*='nickname']", timeout=3)
        if name_elem:
            return name_elem.text.strip()
        return ""
    except Exception:
        return ""


def get_user_level(page) -> int:
    """从 i.level-icon 提取用户等级"""
    try:
        level_elem = page.ele("css:i.level-icon", timeout=5)
        if level_elem:
            cls = level_elem.attr("class") or ""
            match = re.search(r"user_level_(\d)", cls)
            if match:
                return int(match.group(1))
        level_elem = page.ele("css:i[class*='user_level_']", timeout=3)
        if level_elem:
            cls = level_elem.attr("class") or ""
            match = re.search(r"user_level_(\d)", cls)
            if match:
                return int(match.group(1))
        return -1
    except Exception:
        return -1


def get_fans_count(page) -> int:
    """从 div.nav-statistics 提取粉丝数"""
    try:
        nav_stat = page.ele("css:div.nav-statistics", timeout=3)
        if nav_stat:
            items = nav_stat.eles("css:a.nav-statistics__item")
            for item in items:
                text_elem = item.ele("css:span.nav-statistics__item-text", timeout=1)
                if text_elem and "粉丝" in text_elem.text:
                    num_elem = item.ele("css:span.nav-statistics__item-num", timeout=1)
                    if num_elem:
                        return int(num_elem.text)
        return -1
    except Exception:
        return -1


def get_following_count(page) -> int:
    """从 div.nav-statistics 提取粉丝数"""
    try:
        nav_stat = page.ele("css:div.nav-statistics", timeout=3)
        if nav_stat:
            items = nav_stat.eles("css:a.nav-statistics__item")
            for item in items:
                text_elem = item.ele("css:span.nav-statistics__item-text", timeout=1)
                if text_elem and "关注" in text_elem.text:
                    num_elem = item.ele("css:span.nav-statistics__item-num", timeout=1)
                    if num_elem:
                        return int(num_elem.text)
        return -1
    except Exception:
        return -1


def has_user_content(page) -> bool:
    """检测 main.space-main 区域是否存在内容"""
    try:
        main_elem = page.ele("css:main.space-main", timeout=3)
        if not main_elem:
            main_elem = page.ele("css:[class*='space-main']", timeout=3)
        if main_elem:
            main_html = main_elem.html
        else:
            main_html = page.html

        empty_patterns = [
            "还没投过稿",
            "这里什么也没有",
            "什么都没有",
            "暂无内容",
            "还没有动态",
            "还没有收藏",
            "还没有追番",
        ]
        for pattern in empty_patterns:
            if pattern in main_html:
                return False

        content_keywords = [
            "投稿", "动态", "收藏", "追番", "追剧",
            "视频", "播放", "点赞", "投币",
        ]
        for keyword in content_keywords:
            if keyword in main_html:
                return True

        if main_elem:
            if main_elem.ele("css:[class*='video-card']", timeout=1):
                return True
            if main_elem.ele("css:[class*='dynamic-item']", timeout=1):
                return True
            if main_elem.ele("css:[class*='bangumi-card']", timeout=1):
                return True

        return False
    except Exception:
        return False


def check_registration_bot(page, username: str) -> dict:
    """
    评估用户是否为注册机账号
    判定条件：乱码用户名、等级0、粉丝数0、关注数0、无内容
    返回值包含 is_bot 布尔标识及用户详情
    """
    result = {
        "is_bot": False,
        "details": {}
    }

    is_gibberish = is_gibberish_name(username)

    level = get_user_level(page)
    result["details"]["等级"] = f"Lv{level}" if level >= 0 else "未知"

    fans = get_fans_count(page)
    result["details"]["粉丝"] = fans if fans >= 0 else "未知"

    following = get_following_count(page)
    result["details"]["关注"] = following if following >= 0 else "未知"

    has_content = has_user_content(page)
    result["details"]["有内容"] = "是" if has_content else "否"

    if (is_gibberish and level == 0 and fans == 0 and 
        following == 0 and not has_content):
        result["is_bot"] = True

    return result


def get_scan_mode() -> tuple:
    """
    获取用户输入的扫描模式
    返回：(模式类型, UID位数/起始UID, 结束UID)
    模式类型：'fixed' 固定位数随机扫描，'custom' 自定义范围扫描
    """
    print("\n请选择扫描模式:")
    print("  1) 固定位数随机扫描")
    print("  2) 自定义范围扫描")
    
    while True:
        choice = input("请输入选项 (1-2): ").strip()
        if choice == "1":
            return get_fixed_digits()
        elif choice == "2":
            return get_custom_range()
        else:
            print("无效选项，请重新选择")


def get_fixed_digits() -> tuple:
    """获取用户指定的 UID 位数，返回 ('fixed', 位数, None, None)"""
    
    while True:
        digits_input = input("请输入 UID 位数 (6-10): ").strip()
        if not digits_input.isdigit():
            print("请输入有效的数字")
            continue
        digits = int(digits_input)
        if 6 <= digits <= 10:
            return ("fixed", digits, None, None)
        else:
            print("位数必须在 6-10 之间")


def get_custom_range() -> tuple:
    """获取用户自定义的 UID 起止范围，返回 ('custom', None, 起始UID, 结束UID)"""
    while True:
        try:
            min_uid = int(input("请输入起始 UID (如: 1000000): ").strip())
            max_uid = int(input("请输入结束 UID (如: 1999999): ").strip())
            if min_uid < 100000 or max_uid > 9999999999:
                print("UID 范围应在 100000 ~ 9999999999 之间")
                continue
            if min_uid > max_uid:
                print("起始 UID 不能大于结束 UID")
                continue
            if min_uid < 100000:
                print("UID 至少为 6 位 (100000)")
                continue
            break
        except ValueError:
            print("请输入有效的数字")
    
    return ("custom", None, min_uid, max_uid)


def get_prefix(uid_digits: int) -> tuple:
    """获取用户指定的 UID 前缀，返回前缀值、前缀长度及随机后缀参数"""
    min_prefix = 10 ** (uid_digits - 1)
    max_prefix = (10 ** uid_digits) - 1
    
    print(f"\nUID 位数: {uid_digits} 位 ({min_prefix} ~ {max_prefix})")
    
    while True:
        prefix_input = input(f"\n请输入 UID 的前缀数字 (1-{uid_digits-1} 位，不能以0开头): ").strip()
        if not prefix_input.isdigit():
            print("请输入纯数字")
            continue
        if prefix_input[0] == '0':
            print("前缀不能以 0 开头")
            continue
        if len(prefix_input) >= uid_digits:
            print(f"前缀位数不能超过 {uid_digits-1} 位")
            continue
        if len(prefix_input) == 0:
            print("请输入有效前缀")
            continue
        
        uid_prefix = int(prefix_input)
        prefix_len = len(prefix_input)
        random_digits = uid_digits - prefix_len
        random_max = 10 ** random_digits - 1
        
        return uid_prefix, prefix_len, random_digits, random_max


def connect_chrome(port: int) -> ChromiumPage:
    """连接至指定端口的 Chrome 远程调试实例"""
    try:
        co = ChromiumOptions()
        co.set_local_port(port)
        page = ChromiumPage(co)
        return page
    except Exception as e:
        print(f"连接 Chrome 失败: {e}")
        print(f'   请运行: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port}')
        raise


def scan_random_uids(page, uid_digits: int, uid_prefix: int, 
                     prefix_len: int, random_digits: int, random_max: int):
    """在指定前缀范围内执行随机 UID 扫描"""
    checked = 0
    found = 0
    
    print(f"\n开始随机扫描... (UID 前缀: {uid_prefix}, 位数: {uid_digits})")
    print(f"结果保存至: {OUTPUT_FILE}")
    print("-" * 55)
    
    try:
        while True:
            remaining = random.randint(0, random_max)
            uid = int(f"{uid_prefix}{remaining:0{random_digits}d}")
            
            if uid < 10 ** (uid_digits - 1) or uid > 10 ** uid_digits - 1:
                continue
            
            checked, found = process_uid(page, uid, checked, found)
            
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print_summary(checked, found)


def scan_custom_range(page, min_uid: int, max_uid: int):
    """在自定义范围内执行线性 UID 扫描"""
    checked = 0
    found = 0
    uid = min_uid
    
    print(f"\n开始线性扫描... ({min_uid} ~ {max_uid})")
    print(f"结果保存至: {OUTPUT_FILE}")
    print("-" * 55)
    
    try:
        while uid <= max_uid:
            checked, found = process_uid(page, uid, checked, found)
            
            uid += 1
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print_summary(checked, found, min_uid, uid - 1)


def process_uid(page, uid: int, checked: int, found: int) -> tuple:
    """处理单个 UID 的检查流程，返回更新后的已检查和命中计数"""
    url = f"https://space.bilibili.com/{uid}"
    
    try:
        page.get(url)
        time.sleep(2)
        
        username = get_username(page)
        checked += 1
        
        if not username:
            print(f"  [{checked}]      UID:{uid} — 无法获取用户名，跳过")
            return checked, found
        
        result = check_registration_bot(page, username)
        details = result["details"]
        
        if result["is_bot"]:
            found += 1
            print(f"  [{checked}] 命中 UID:{uid} | {username} | 等级:{details['等级']} 粉丝:{details['粉丝']} 关注:{details['关注']} 有内容:{details['有内容']} (已命中 {found} 个)")
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"UID: {uid} | 用户名: {username}\n")
        else:
            print(f"  [{checked}]      UID:{uid} | {username} | 等级:{details['等级']} 粉丝:{details['粉丝']} 关注:{details['关注']} 有内容:{details['有内容']}")
        
        return checked, found
        
    except Exception as e:
        checked += 1
        print(f"  [{checked}]      UID:{uid} — 访问出错: {e}")
        return checked, found


def print_summary(checked: int, found: int, start_uid: int = None, end_uid: int = None):
    """输出扫描统计摘要"""
    print(f"\n\n{'=' * 55}")
    print(f"扫描停止")
    print(f"   共检查: {checked} 个 UID")
    print(f"   命中数: {found} 个")
    if start_uid is not None and end_uid is not None:
        print(f"   扫描范围: {start_uid} ~ {end_uid}")
    print(f"   结果文件: {OUTPUT_FILE}")
    print(f"{'=' * 55}")


def main():
    mode, param1, param2, param3 = get_scan_mode()
    
    print(f"\n连接本地 Chrome (端口 {DEBUGGING_PORT})...")
    page = connect_chrome(DEBUGGING_PORT)
    print("成功连接 Chrome！")
    
    if mode == "fixed":
        uid_digits = param1
        uid_prefix, prefix_len, random_digits, random_max = get_prefix(uid_digits)
        scan_random_uids(page, uid_digits, uid_prefix, prefix_len, random_digits, random_max)
    else:
        min_uid = param2
        max_uid = param3
        scan_custom_range(page, min_uid, max_uid)


if __name__ == "__main__":
    main()