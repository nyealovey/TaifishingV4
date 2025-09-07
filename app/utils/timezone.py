# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 时区工具模块
"""

from datetime import datetime, timezone, timedelta
import pytz

# 东八区时区
CHINA_TZ = pytz.timezone('Asia/Shanghai')

def get_china_time():
    """获取东八区当前时间"""
    return datetime.now(CHINA_TZ)

def utc_to_china(utc_dt):
    """将UTC时间转换为东八区时间"""
    if utc_dt is None:
        return None
    
    if utc_dt.tzinfo is None:
        # 如果没有时区信息，假设为UTC
        utc_dt = pytz.utc.localize(utc_dt)
    
    return utc_dt.astimezone(CHINA_TZ)

def china_to_utc(china_dt):
    """将东八区时间转换为UTC时间"""
    if china_dt is None:
        return None
    
    if china_dt.tzinfo is None:
        # 如果没有时区信息，假设为东八区
        china_dt = CHINA_TZ.localize(china_dt)
    
    return china_dt.astimezone(pytz.utc)

def format_china_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化东八区时间"""
    if dt is None:
        return None
    
    # 如果已经是字符串，尝试解析为datetime对象
    if isinstance(dt, str):
        try:
            # 尝试解析ISO格式字符串
            if 'T' in dt and ('+' in dt or 'Z' in dt):
                # ISO格式，包含时区信息
                from datetime import datetime
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            elif 'T' in dt:
                # ISO格式，无时区信息，假设为UTC
                from datetime import datetime
                dt = datetime.fromisoformat(dt)
                dt = pytz.utc.localize(dt)
            else:
                # 其他格式字符串，直接返回
                return dt
        except (ValueError, TypeError):
            # 解析失败，直接返回原字符串
            return dt
    
    china_dt = utc_to_china(dt)
    return china_dt.strftime(format_str)

def get_china_date():
    """获取东八区当前日期"""
    return get_china_time().date()

def get_china_today():
    """获取东八区今天的开始时间（UTC）"""
    china_today = get_china_date()
    china_start = CHINA_TZ.localize(datetime.combine(china_today, datetime.min.time()))
    return china_start.astimezone(pytz.utc)

def get_china_tomorrow():
    """获取东八区明天的开始时间（UTC）"""
    china_tomorrow = get_china_date() + timedelta(days=1)
    china_start = CHINA_TZ.localize(datetime.combine(china_tomorrow, datetime.min.time()))
    return china_start.astimezone(pytz.utc)
