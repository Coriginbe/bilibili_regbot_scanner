"""
使用前先以调试端口启动 Chrome：
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
"""

import random
import re
import time
import os
from DrissionPage import ChromiumPage, ChromiumOptions


# ======================== 配置 ========================
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result.txt")
MIN_DELAY = 2
MAX_DELAY = 5
DEBUGGING_PORT = 9222


# ======================== 乱码用户名判定 ========================
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
    name_lower = name.lower()
    for surname in COMMON_SURNAMES:
        pattern = r'(?<![a-zA-Z])' + re.escape(surname) + r'(?![a-zA-Z])'
        if re.search(pattern, name_lower):
            return True
    return False


def contains_year_or_date(name: str) -> bool:
    if re.search(r'(19|20)\d{2}', name):
        return True
    if re.search(r'\d{6,8}', name):
        return True
    return False


def is_gibberish_name(name: str) -> bool:
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


# ======================== 数据提取 ========================

def get_username(page) -> str:
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
    """从 nav-statistics 区域提取粉丝数。"""
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
    """从 nav-statistics 区域提取关注数。"""
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
    """检测 main.space-main 区域是否有实际内容。"""
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


# ======================== 主逻辑 ========================
def main():
    print("=" * 55)
    print("   Bilibili UID 检查器 — 注册机账号筛选工具")
    print("=" * 55)

    while True:
        prefix_input = input("\n请输入 UID 的前缀数字（1位: 1-9，2位: 10-99）: ").strip()
        if prefix_input.isdigit() and 1 <= int(prefix_input) <= 99 and prefix_input[0] != '0':
            uid_prefix = int(prefix_input)
            prefix_len = len(prefix_input)
            break
        print("输入无效，请输入 1~9（一位）或 10~99（两位）的数字。")

    random_digits = 7 - prefix_len
    random_max = 10 ** random_digits - 1

    print(f"\n连接本地 Chrome (端口 {DEBUGGING_PORT})...")
    try:
        co = ChromiumOptions()
        co.set_local_port(DEBUGGING_PORT)
        page = ChromiumPage(co)
        print("成功连接 Chrome！")
    except Exception as e:
        print(f"连接 Chrome 失败: {e}")
        print(f'   请运行: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={DEBUGGING_PORT}')
        return

    checked = 0
    found = 0

    print(f"\n开始检查... (UID 前缀: {uid_prefix})")
    print(f"结果保存至: {OUTPUT_FILE}")
    print("-" * 55)

    try:
        while True:
            remaining = random.randint(0, random_max)
            uid = int(f"{uid_prefix}{remaining:0{random_digits}d}")

            url = f"https://space.bilibili.com/{uid}"

            try:
                page.get(url)
                time.sleep(2)

                username = get_username(page)
                checked += 1

                if not username:
                    print(f"  [{checked}] UID {uid} — 无法获取用户名，跳过")
                    delay = random.uniform(MIN_DELAY, MAX_DELAY)
                    time.sleep(delay)
                    continue

                result = check_registration_bot(page, username)
                d = result["details"]

                if result["is_bot"]:
                    found += 1
                    mark = "命中"
                    print(f"  [{checked}] {mark} UID:{uid} | {username} | 等级:{d['等级']} 粉丝:{d['粉丝']} 关注:{d['关注']} 有内容:{d['有内容']} (已命中 {found} 个)")
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                        f.write(f"UID: {uid} | 用户名: {username}\n")
                else:
                    mark = "    "
                    print(f"  [{checked}] {mark} UID:{uid} | {username} | 等级:{d['等级']} 粉丝:{d['粉丝']} 关注:{d['关注']} 有内容:{d['有内容']}")

            except Exception as e:
                checked += 1
                print(f"  [{checked}] UID {uid} — 访问出错: {e}")

            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 55}")
        print(f"手动停止")
        print(f"   共检查: {checked} 个 UID")
        print(f"   命中数: {found} 个")
        print(f"   结果文件: {OUTPUT_FILE}")
        print(f"{'=' * 55}")


if __name__ == "__main__":
    main()