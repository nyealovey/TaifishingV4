# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 性能监控和优化系统
提供实时性能监控、瓶颈分析和自动优化建议
"""

import time
import psutil
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from collections import defaultdict, deque
from dataclasses import dataclass
from app.constants import SystemConstants

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    metadata: Dict[str, Any] = None

@dataclass
class PerformanceAlert:
    """性能告警数据类"""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    threshold: float
    current_value: float
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.alerts = deque(maxlen=100)
        self.monitoring = False
        self.monitor_thread = None
        self.start_time = time.time()
        
        # 性能阈值
        self.thresholds = {
            'cpu_percent': SystemConstants.CPU_WARNING_THRESHOLD,
            'memory_percent': SystemConstants.MEMORY_WARNING_THRESHOLD,
            'response_time': SystemConstants.SLOW_API_THRESHOLD,
            'query_time': SystemConstants.SLOW_QUERY_THRESHOLD,
            'disk_percent': 90.0,
            'connection_count': 100
        }
        
        # 性能计数器
        self.counters = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'queries_total': 0,
            'queries_slow': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def start_monitoring(self, interval: int = 30):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("性能监控已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            self._record_metric('cpu_percent', cpu_percent, '%')
            
            # 内存指标
            memory = psutil.virtual_memory()
            self._record_metric('memory_percent', memory.percent, '%')
            self._record_metric('memory_available', memory.available / 1024 / 1024, 'MB')
            self._record_metric('memory_total', memory.total / 1024 / 1024, 'MB')
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._record_metric('disk_percent', disk_percent, '%')
            self._record_metric('disk_free', disk.free / 1024 / 1024, 'MB')
            
            # 网络指标
            network = psutil.net_io_counters()
            self._record_metric('bytes_sent', network.bytes_sent / 1024, 'KB')
            self._record_metric('bytes_recv', network.bytes_recv / 1024, 'KB')
            
            # 进程指标
            process = psutil.Process()
            self._record_metric('process_memory', process.memory_info().rss / 1024 / 1024, 'MB')
            self._record_metric('process_cpu', process.cpu_percent(), '%')
            
            # 运行时间
            uptime = time.time() - self.start_time
            self._record_metric('uptime', uptime, 'seconds')
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def _record_metric(self, metric_type: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """记录性能指标"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self.metrics_history[metric_type].append(metric)
    
    def _check_thresholds(self):
        """检查性能阈值"""
        for metric_type, threshold in self.thresholds.items():
            if metric_type in self.metrics_history and self.metrics_history[metric_type]:
                latest_metric = self.metrics_history[metric_type][-1]
                
                if latest_metric.value > threshold:
                    self._create_alert(
                        alert_type=f"{metric_type}_high",
                        severity="warning" if latest_metric.value < threshold * 1.5 else "critical",
                        message=f"{metric_type} 超过阈值: {latest_metric.value:.2f}{latest_metric.unit} > {threshold}{latest_metric.unit}",
                        threshold=threshold,
                        current_value=latest_metric.value,
                        metadata={'metric_type': metric_type}
                    )
    
    def _create_alert(self, alert_type: str, severity: str, message: str, 
                     threshold: float, current_value: float, metadata: Dict[str, Any] = None):
        """创建性能告警"""
        alert = PerformanceAlert(
            timestamp=datetime.utcnow(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            threshold=threshold,
            current_value=current_value,
            metadata=metadata or {}
        )
        self.alerts.append(alert)
        
        # 记录告警日志
        if severity == "critical":
            logger.critical(f"性能告警: {message}")
        else:
            logger.warning(f"性能告警: {message}")
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """记录请求性能"""
        self.counters['requests_total'] += 1
        
        if 200 <= status_code < 400:
            self.counters['requests_success'] += 1
        else:
            self.counters['requests_error'] += 1
        
        # 记录响应时间
        self._record_metric('response_time', duration, 'seconds', {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code
        })
        
        # 检查慢请求
        if duration > self.thresholds['response_time']:
            self._create_alert(
                alert_type="slow_request",
                severity="warning",
                message=f"慢请求: {method} {endpoint} 耗时 {duration:.3f}秒",
                threshold=self.thresholds['response_time'],
                current_value=duration,
                metadata={'endpoint': endpoint, 'method': method}
            )
    
    def record_query(self, query_type: str, duration: float, success: bool = True):
        """记录查询性能"""
        self.counters['queries_total'] += 1
        
        if not success:
            self.counters['queries_error'] += 1
        
        # 记录查询时间
        self._record_metric('query_time', duration, 'seconds', {
            'query_type': query_type,
            'success': success
        })
        
        # 检查慢查询
        if duration > self.thresholds['query_time']:
            self.counters['queries_slow'] += 1
            self._create_alert(
                alert_type="slow_query",
                severity="warning",
                message=f"慢查询: {query_type} 耗时 {duration:.3f}秒",
                threshold=self.thresholds['query_time'],
                current_value=duration,
                metadata={'query_type': query_type}
            )
    
    def record_cache_operation(self, operation: str, hit: bool):
        """记录缓存操作"""
        if hit:
            self.counters['cache_hits'] += 1
        else:
            self.counters['cache_misses'] += 1
        
        self._record_metric('cache_hit_rate', 
                          self.counters['cache_hits'] / (self.counters['cache_hits'] + self.counters['cache_misses']) * 100,
                          '%', {'operation': operation})
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            'uptime': time.time() - self.start_time,
            'counters': self.counters.copy(),
            'current_metrics': {},
            'recent_alerts': [],
            'performance_score': self._calculate_performance_score()
        }
        
        # 当前指标
        for metric_type, metrics in self.metrics_history.items():
            if metrics:
                latest = metrics[-1]
                summary['current_metrics'][metric_type] = {
                    'value': latest.value,
                    'unit': latest.unit,
                    'timestamp': latest.timestamp.isoformat()
                }
        
        # 最近告警
        for alert in list(self.alerts)[-10:]:
            summary['recent_alerts'].append({
                'timestamp': alert.timestamp.isoformat(),
                'type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message
            })
        
        return summary
    
    def _calculate_performance_score(self) -> int:
        """计算性能评分 (0-100)"""
        score = 100
        
        # 基于当前指标调整评分
        for metric_type, threshold in self.thresholds.items():
            if metric_type in self.metrics_history and self.metrics_history[metric_type]:
                latest = self.metrics_history[metric_type][-1]
                if latest.value > threshold:
                    # 超过阈值越多，扣分越多
                    penalty = min(20, (latest.value - threshold) / threshold * 20)
                    score -= penalty
        
        # 基于错误率调整评分
        if self.counters['requests_total'] > 0:
            error_rate = self.counters['requests_error'] / self.counters['requests_total']
            score -= error_rate * 30
        
        # 基于慢查询率调整评分
        if self.counters['queries_total'] > 0:
            slow_query_rate = self.counters['queries_slow'] / self.counters['queries_total']
            score -= slow_query_rate * 20
        
        return max(0, min(100, int(score)))
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []
        
        # 基于性能指标生成建议
        if 'memory_percent' in self.metrics_history and self.metrics_history['memory_percent']:
            latest_memory = self.metrics_history['memory_percent'][-1]
            if latest_memory.value > 80:
                suggestions.append({
                    'type': 'memory',
                    'priority': 'high',
                    'title': '内存使用率过高',
                    'description': f'当前内存使用率: {latest_memory.value:.1f}%',
                    'suggestions': [
                        '检查内存泄漏',
                        '优化数据查询',
                        '增加内存缓存清理频率',
                        '考虑增加服务器内存'
                    ]
                })
        
        if 'cpu_percent' in self.metrics_history and self.metrics_history['cpu_percent']:
            latest_cpu = self.metrics_history['cpu_percent'][-1]
            if latest_cpu.value > 80:
                suggestions.append({
                    'type': 'cpu',
                    'priority': 'high',
                    'title': 'CPU使用率过高',
                    'description': f'当前CPU使用率: {latest_cpu.value:.1f}%',
                    'suggestions': [
                        '优化算法复杂度',
                        '减少不必要的计算',
                        '使用异步处理',
                        '考虑负载均衡'
                    ]
                })
        
        # 基于慢查询生成建议
        if self.counters['queries_slow'] > 0:
            suggestions.append({
                'type': 'database',
                'priority': 'medium',
                'title': '存在慢查询',
                'description': f'发现 {self.counters["queries_slow"]} 个慢查询',
                'suggestions': [
                    '添加数据库索引',
                    '优化SQL查询语句',
                    '使用查询缓存',
                    '考虑读写分离'
                ]
            })
        
        # 基于缓存命中率生成建议
        if self.counters['cache_hits'] + self.counters['cache_misses'] > 0:
            hit_rate = self.counters['cache_hits'] / (self.counters['cache_hits'] + self.counters['cache_misses'])
            if hit_rate < 0.7:
                suggestions.append({
                    'type': 'cache',
                    'priority': 'medium',
                    'title': '缓存命中率较低',
                    'description': f'当前缓存命中率: {hit_rate:.1%}',
                    'suggestions': [
                        '增加缓存时间',
                        '优化缓存键策略',
                        '预热常用数据',
                        '检查缓存配置'
                    ]
                })
        
        return suggestions

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

# 性能监控装饰器
def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录请求性能
            if hasattr(func, '__name__'):
                performance_monitor.record_request(
                    endpoint=func.__name__,
                    method=getattr(func, '__method__', 'UNKNOWN'),
                    duration=duration,
                    status_code=200
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录错误请求
            if hasattr(func, '__name__'):
                performance_monitor.record_request(
                    endpoint=func.__name__,
                    method=getattr(func, '__method__', 'UNKNOWN'),
                    duration=duration,
                    status_code=500
                )
            
            raise
    
    return wrapper

# 查询性能监控装饰器
def monitor_query_performance(query_type: str = "unknown"):
    """查询性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                performance_monitor.record_query(query_type, duration, True)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_query(query_type, duration, False)
                raise
        
        return wrapper
    return decorator

# 缓存性能监控装饰器
def monitor_cache_performance(operation: str = "unknown"):
    """缓存性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 判断缓存是否命中（这里简化处理）
                hit = duration < 0.01  # 如果执行时间很短，认为是缓存命中
                performance_monitor.record_cache_operation(operation, hit)
                
                return result
                
            except Exception as e:
                performance_monitor.record_cache_operation(operation, False)
                raise
        
        return wrapper
    return decorator

# 自动优化建议生成器
class OptimizationAdvisor:
    """优化建议生成器"""
    
    @staticmethod
    def analyze_performance_data(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析性能数据并生成优化建议"""
        suggestions = []
        
        # 分析内存使用模式
        if 'memory_percent' in metrics:
            memory_trend = OptimizationAdvisor._analyze_trend(metrics['memory_percent'])
            if memory_trend == 'increasing':
                suggestions.append({
                    'category': 'memory',
                    'priority': 'high',
                    'title': '内存使用呈上升趋势',
                    'description': '内存使用量持续增长，可能存在内存泄漏',
                    'actions': [
                        '检查长时间运行的任务',
                        '优化数据结构和算法',
                        '增加内存监控和告警'
                    ]
                })
        
        # 分析响应时间模式
        if 'response_time' in metrics:
            response_trend = OptimizationAdvisor._analyze_trend(metrics['response_time'])
            if response_trend == 'increasing':
                suggestions.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': '响应时间呈上升趋势',
                    'description': 'API响应时间持续增长，影响用户体验',
                    'actions': [
                        '优化数据库查询',
                        '增加缓存层',
                        '使用异步处理',
                        '考虑CDN加速'
                    ]
                })
        
        return suggestions
    
    @staticmethod
    def _analyze_trend(values: List[float]) -> str:
        """分析数值趋势"""
        if len(values) < 3:
            return 'stable'
        
        recent_avg = sum(values[-3:]) / 3
        earlier_avg = sum(values[:3]) / 3
        
        if recent_avg > earlier_avg * 1.1:
            return 'increasing'
        elif recent_avg < earlier_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'
