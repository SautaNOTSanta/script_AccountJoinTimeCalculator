# calculator.py
import datetime
from anchors import parse_anchors

ANCHOR_DATA = parse_anchors()


def linear_interpolate(uid: int) -> datetime.datetime:
    anchors = ANCHOR_DATA

    if uid <= anchors[0][0]:
        return datetime.datetime.fromtimestamp(anchors[0][1])

    if uid >= anchors[-1][0]:
        uid_lo, ts_lo = anchors[-2]
        uid_hi, ts_hi = anchors[-1]
        ratio = (uid - uid_lo) / (uid_hi - uid_lo)
        estimated_ts = ts_lo + ratio * (ts_hi - ts_lo)
        return datetime.datetime.fromtimestamp(estimated_ts)

    # 二分查找左右锚点
    lo, hi = 0, len(anchors) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if anchors[mid][0] <= uid:
            lo = mid
        else:
            hi = mid

    uid_lo, ts_lo = anchors[lo]
    uid_hi, ts_hi = anchors[hi]
    ratio = (uid - uid_lo) / (uid_hi - uid_lo)
    estimated_ts = ts_lo + ratio * (ts_hi - ts_lo)
    return datetime.datetime.fromtimestamp(estimated_ts)


def calculate_join_time(uid: int) -> dict:
    estimated_dt = linear_interpolate(uid)
    anchors = ANCHOR_DATA

    min_dist = min(abs(uid - a[0]) for a in anchors)
    total_range = anchors[-1][0] - anchors[0][0]
    dist_ratio = min_dist / total_range

    if uid > 1500000000:
        confidence = "中"
        note = "较新账号，锚点数据稀疏，误差可能较大"
    elif dist_ratio > 0.05:
        confidence = "中"
        note = "距离最近锚点较远，误差可能在 1-3 个月"
    elif dist_ratio > 0.02:
        confidence = "高"
        note = "误差约在 2-4 周内"
    else:
        confidence = "非常高"
        note = "非常接近锚点，误差在 1 周内"

    age_days = (datetime.datetime.now() - estimated_dt).days

    return {
        "uid": uid,
        "estimated_date": estimated_dt.strftime("%Y年%m月%d日"),
        "estimated_datetime": estimated_dt,
        "year": estimated_dt.year,
        "month": estimated_dt.month,
        "confidence": confidence,
        "note": note,
        "account_age_days": age_days,
    }


def format_result(result: dict, username: str = None) -> str:
    import time
    current_ts = int(time.time())
    sep = "─" * 43
    lines = [
        sep,
        "   🎯  B站账号注册时间估算结果",
        sep,
    ]
    if username:
        lines.append(f"   👤  用户名    {username}")
    lines += [
        f"   🔢  UID       {result['uid']:,}",
        f"   📅  注册时间  {result['estimated_date']}",
        f"   ⏳  账号已有  约 {result['account_age_days']:,} 天"
        f"（{result['account_age_days'] // 365} 年）",
        f"   📊  置信度   {result['confidence']}",
        f"   💡  备注     {result['note']}",
        sep,
        f"   🕐  查询时间戳  {current_ts}  （Unix Timestamp）",
        sep,
    ]
    return "\n".join(lines)