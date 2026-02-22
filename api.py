import requests
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 请求头伪装成浏览器，避免被B站反爬，cos代号47
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
_lock = threading.Lock()


def extract_uid(input_str: str) -> int | None:
    """
    从输入中提取UID：
    - 纯数字 -> 直接返回
    - URL如 https://space.bilibili.com/24474955 -> 提取数字
    """
    input_str = input_str.strip()

    # 尝试直接解析为数字
    if input_str.isdigit():
        return int(input_str)

    # 从URL中提取
    match = re.search(r'space\.bilibili\.com/(\d+)', input_str)
    if match:
        return int(match.group(1))

    # 兜底：提取任意数字串
    match = re.search(r'(\d{5,})', input_str)
    if match:
        return int(match.group(1))

    return None


def check_uid_exists(uid: int, timeout: int = 5) -> bool:
    """检查UID是否存在（账号未注销）"""
    try:
        url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
        resp = SESSION.get(url, timeout=timeout)
        data = resp.json()
        # code=0 表示用户存在
        return data.get("code") == 0
    except Exception:
        return False


def get_uid_info(uid: int, timeout: int = 5) -> dict | None:
    """获取UID的公开信息"""
    try:
        url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
        resp = SESSION.get(url, timeout=timeout)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {})
        return None
    except Exception:
        return None


def batch_check_uids(uid_list: list, max_workers: int = 8) -> dict:
    """
    多线程拿来批量检查UID是否存在
    返回 {uid: bool} 字典
    """
    results = {}

    def check_one(uid):
        exists = check_uid_exists(uid)
        with _lock:
            results[uid] = exists

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_one, uid): uid for uid in uid_list}
        for future in as_completed(futures):
            future.result()  # 等待完成

    return results