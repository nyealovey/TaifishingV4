#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试时区问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.timezone import get_china_time, get_china_date, get_china_today, CHINA_TZ
from datetime import datetime
import pytz

def debug_timezone():
    """调试时区问题"""
    print("=== 调试时区问题 ===")
    
    # 1. 当前东八区时间
    china_now = get_china_time()
    print(f"当前东八区时间: {china_now}")
    
    # 2. 东八区日期
    china_date = get_china_date()
    print(f"东八区日期: {china_date}")
    
    # 3. 手动计算东八区今天的开始时间
    china_start = CHINA_TZ.localize(datetime.combine(china_date, datetime.min.time()))
    print(f"东八区今天的开始时间: {china_start}")
    
    # 4. 转换为UTC
    utc_start = china_start.astimezone(pytz.utc)
    print(f"转换为UTC: {utc_start}")
    
    # 5. 使用get_china_today()
    china_today_utc = get_china_today()
    print(f"get_china_today()结果: {china_today_utc}")
    
    # 6. 检查日期
    print(f"UTC开始时间的日期: {utc_start.date()}")
    print(f"get_china_today()的日期: {china_today_utc.date()}")

if __name__ == '__main__':
    debug_timezone()
