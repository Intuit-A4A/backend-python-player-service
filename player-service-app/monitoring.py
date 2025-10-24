"""
Production Monitoring for API Performance
Demonstrates how to monitor and address slow API responses
"""

import time
import logging
from functools import wraps
from flask import g, request
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)

# ========================================
# Configuration
# ========================================

# Thresholds for slow API detection
SLOW_API_THRESHOLD_MS = 500  # 500ms - anything slower is "slow"
CRITICAL_API_THRESHOLD_MS = 2000  # 2 seconds - critical slow
TIMEOUT_THRESHOLD_MS = 5000  # 5 seconds - timeout

# In production, these would be in environment variables or config service
ALERTING_ENABLED = True
METRICS_ENABLED = True


# ========================================
# Performance Metrics Collection
# ========================================

class PerformanceMetrics:
    """
    Collect performance metrics for monitoring
    
    In production, this would integrate with:
    - Prometheus for metrics collection
    - Grafana for dashboards
    - PagerDuty/Opsgenie for alerting
    """
    
    def __init__(self):
        # In-memory storage for demo
        # Production: Use Prometheus, CloudWatch, Datadog
        self.metrics = {
            'request_count': 0,
            'slow_request_count': 0,
            'error_count': 0,
            'total_latency_ms': 0,
            'endpoint_stats': {}
        }
    
    def record_request(self, endpoint: str, method: str, duration_ms: float, 
                      status_code: int, trace_id: str):
        """
        Record request metrics
        
        In production, this would:
        - Send to Prometheus (counter, histogram)
        - Log to structured logging system (Splunk, ELK)
        - Update real-time dashboards
        """
        self.metrics['request_count'] += 1
        self.metrics['total_latency_ms'] += duration_ms
        
        # Track per-endpoint statistics
        endpoint_key = f"{method}:{endpoint}"
        if endpoint_key not in self.metrics['endpoint_stats']:
            self.metrics['endpoint_stats'][endpoint_key] = {
                'count': 0,
                'slow_count': 0,
                'total_latency': 0,
                'max_latency': 0,
                'p95_latency': [],  # Store recent latencies for percentile
            }
        
        stats = self.metrics['endpoint_stats'][endpoint_key]
        stats['count'] += 1
        stats['total_latency'] += duration_ms
        stats['max_latency'] = max(stats['max_latency'], duration_ms)
        stats['p95_latency'].append(duration_ms)
        
        # Keep only last 100 samples for p95 calculation
        if len(stats['p95_latency']) > 100:
            stats['p95_latency'] = stats['p95_latency'][-100:]
        
        # Detect slow requests
        if duration_ms > SLOW_API_THRESHOLD_MS:
            self.metrics['slow_request_count'] += 1
            stats['slow_count'] += 1
            
            # Log slow request for investigation
            logger.warning(
                f"[{trace_id}] SLOW API: {method} {endpoint} took {duration_ms:.2f}ms "
                f"(threshold: {SLOW_API_THRESHOLD_MS}ms)",
                extra={
                    'trace_id': trace_id,
                    'endpoint': endpoint,
                    'method': method,
                    'duration_ms': duration_ms,
                    'status_code': status_code,
                    'alert': 'slow_api'
                }
            )
            
            # Critical slow - immediate alert
            if duration_ms > CRITICAL_API_THRESHOLD_MS:
                logger.error(
                    f"[{trace_id}] CRITICAL SLOW API: {method} {endpoint} took {duration_ms:.2f}ms",
                    extra={
                        'trace_id': trace_id,
                        'endpoint': endpoint,
                        'method': method,
                        'duration_ms': duration_ms,
                        'status_code': status_code,
                        'alert': 'critical_slow_api',
                        'severity': 'high'
                    }
                )
                
                if ALERTING_ENABLED:
                    self._send_alert(
                        severity='high',
                        message=f"Critical slow API: {method} {endpoint} took {duration_ms:.2f}ms",
                        trace_id=trace_id
                    )
        
        # Detect errors
        if status_code >= 500:
            self.metrics['error_count'] += 1
    
    def _send_alert(self, severity: str, message: str, trace_id: str):
        """
        Send alert to monitoring system
        
        In production:
        - PagerDuty for on-call engineers
        - Slack for team notifications
        - Email for summaries
        """
        logger.critical(
            f"ALERT [{severity.upper()}]: {message}",
            extra={
                'trace_id': trace_id,
                'severity': severity,
                'alert_type': 'performance',
                'action_required': True
            }
        )
        
        # Production implementation:
        # pagerduty.trigger_incident(severity=severity, message=message)
        # slack.send_message(channel='#alerts', message=message)
    
    def get_stats(self) -> Dict:
        """Get current metrics for dashboard"""
        avg_latency = (
            self.metrics['total_latency_ms'] / self.metrics['request_count']
            if self.metrics['request_count'] > 0
            else 0
        )
        
        slow_percentage = (
            (self.metrics['slow_request_count'] / self.metrics['request_count']) * 100
            if self.metrics['request_count'] > 0
            else 0
        )
        
        # Calculate p95 per endpoint
        endpoint_stats = {}
        for endpoint, stats in self.metrics['endpoint_stats'].items():
            p95_samples = sorted(stats['p95_latency'])
            p95_index = int(len(p95_samples) * 0.95)
            p95 = p95_samples[p95_index] if p95_samples else 0
            
            endpoint_stats[endpoint] = {
                'count': stats['count'],
                'slow_count': stats['slow_count'],
                'avg_latency_ms': stats['total_latency'] / stats['count'] if stats['count'] > 0 else 0,
                'max_latency_ms': stats['max_latency'],
                'p95_latency_ms': p95,
                'slow_percentage': (stats['slow_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            }
        
        return {
            'total_requests': self.metrics['request_count'],
            'slow_requests': self.metrics['slow_request_count'],
            'error_count': self.metrics['error_count'],
            'avg_latency_ms': round(avg_latency, 2),
            'slow_percentage': round(slow_percentage, 2),
            'endpoint_stats': endpoint_stats,
            'thresholds': {
                'slow_ms': SLOW_API_THRESHOLD_MS,
                'critical_ms': CRITICAL_API_THRESHOLD_MS
            }
        }


# Global metrics instance (in production, use Prometheus)
metrics = PerformanceMetrics()


# ========================================
# Performance Monitoring Decorator
# ========================================

def monitor_performance(f):
    """
    Decorator to monitor endpoint performance
    
    Usage:
        @app.route('/endpoint')
        @monitor_performance
        def my_endpoint():
            pass
    
    This automatically:
    - Measures request duration
    - Logs slow requests
    - Collects metrics
    - Triggers alerts if needed
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Start timer
        start_time = time.time()
        
        try:
            # Execute endpoint
            response = f(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get status code
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = 200
            
            # Record metrics
            metrics.record_request(
                endpoint=request.endpoint or request.path,
                method=request.method,
                duration_ms=duration_ms,
                status_code=status_code,
                trace_id=getattr(g, 'trace_id', 'unknown')
            )
            
            return response
            
        except Exception as e:
            # Record error
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_request(
                endpoint=request.endpoint or request.path,
                method=request.method,
                duration_ms=duration_ms,
                status_code=500,
                trace_id=getattr(g, 'trace_id', 'unknown')
            )
            raise
    
    return decorated_function


# ========================================
# How to Address Slow APIs in Production
# ========================================

class SlowAPIRemediation:
    """
    Strategies to address slow APIs in production with minimal downtime
    
    Interview talking points:
    - How to detect slow APIs
    - How to investigate root causes
    - How to fix without downtime
    - How to prevent recurrence
    """
    
    @staticmethod
    def detection_strategy() -> Dict:
        """
        How to detect slow APIs in production
        """
        return {
            'monitoring': {
                '1_metrics': 'RED metrics (Rate, Errors, Duration) via Prometheus',
                '2_logging': 'Structured logs with latency in Splunk/ELK',
                '3_tracing': 'Distributed tracing with Jaeger/X-Ray',
                '4_apm': 'Application Performance Monitoring (New Relic, Datadog)',
                '5_synthetic': 'Synthetic monitoring (Pingdom, uptime checks)'
            },
            'alerting': {
                '1_threshold': f'Alert if p95 latency > {SLOW_API_THRESHOLD_MS}ms for 5 minutes',
                '2_anomaly': 'Alert on sudden latency increase (2x baseline)',
                '3_error_rate': 'Alert if error rate > 1%',
                '4_channels': 'PagerDuty for on-call, Slack for team'
            },
            'dashboards': {
                '1_real_time': 'Grafana dashboard with p50, p95, p99 latency',
                '2_per_endpoint': 'Breakdown by endpoint, method',
                '3_trends': 'Historical trends to identify patterns',
                '4_correlations': 'Show CPU, memory, DB connections alongside latency'
            }
        }
    
    @staticmethod
    def investigation_steps() -> Dict:
        """
        How to investigate slow API root causes
        """
        return {
            'step_1_identify_endpoint': {
                'action': 'Which endpoint is slow?',
                'tools': ['Metrics dashboard', 'Logs aggregation'],
                'time': '5 minutes'
            },
            'step_2_check_traces': {
                'action': 'Where is time spent? (DB query, external API, computation)',
                'tools': ['Distributed tracing (Jaeger)', 'APM flame graphs'],
                'time': '10 minutes'
            },
            'step_3_analyze_patterns': {
                'action': 'When does it occur? (specific times, user patterns)',
                'tools': ['Time series graphs', 'Correlation analysis'],
                'time': '10 minutes'
            },
            'step_4_identify_cause': {
                'common_causes': [
                    'N+1 query problem',
                    'Missing database index',
                    'Large payload serialization',
                    'External API timeout',
                    'Inefficient algorithm',
                    'Memory leak causing GC pauses',
                    'Database connection pool exhaustion',
                    'Cache miss storm'
                ],
                'time': '15 minutes'
            }
        }
    
    @staticmethod
    def remediation_strategies() -> Dict:
        """
        How to fix slow APIs with minimal downtime
        """
        return {
            'immediate_mitigations': {
                '1_increase_timeout': {
                    'action': 'Temporarily increase timeout to prevent cascading failures',
                    'downtime': 'None',
                    'risk': 'Low',
                    'example': 'Change timeout from 1s to 5s while investigating'
                },
                '2_scale_horizontally': {
                    'action': 'Add more instances to handle load',
                    'downtime': 'None',
                    'risk': 'Low',
                    'example': 'Scale from 3 to 10 pods in Kubernetes'
                },
                '3_enable_circuit_breaker': {
                    'action': 'Protect downstream services from overload',
                    'downtime': 'Partial (failing fast)',
                    'risk': 'Medium',
                    'example': 'Istio circuit breaker on slow service'
                },
                '4_throttle_traffic': {
                    'action': 'Rate limit to prevent overload',
                    'downtime': 'Partial (some requests rejected)',
                    'risk': 'Medium',
                    'example': 'API Gateway rate limiting'
                }
            },
            'short_term_fixes': {
                '1_add_caching': {
                    'action': 'Cache slow queries in Redis',
                    'downtime': 'None (deploy with feature flag)',
                    'risk': 'Low',
                    'time': '1-2 hours',
                    'example': 'Cache player lookups for 5 minutes'
                },
                '2_add_database_index': {
                    'action': 'Add missing index on frequently queried column',
                    'downtime': 'None (online index creation)',
                    'risk': 'Low',
                    'time': '30 minutes',
                    'example': 'CREATE INDEX idx_country ON players(birthCountry)'
                },
                '3_optimize_query': {
                    'action': 'Fix N+1 queries, add pagination, limit results',
                    'downtime': 'None (canary deployment)',
                    'risk': 'Low',
                    'time': '2-4 hours',
                    'example': 'Use eager loading, add LIMIT clause'
                },
                '4_async_processing': {
                    'action': 'Move slow operation to background job',
                    'downtime': 'None (feature flag)',
                    'risk': 'Medium',
                    'time': '4-8 hours',
                    'example': 'Queue AI query processing, return job ID'
                }
            },
            'long_term_fixes': {
                '1_database_optimization': {
                    'action': 'Partition tables, add read replicas, upgrade hardware',
                    'downtime': 'None (with proper planning)',
                    'risk': 'Medium',
                    'time': '1-2 days'
                },
                '2_architecture_refactor': {
                    'action': 'Move to microservices, add CQRS pattern, event sourcing',
                    'downtime': 'None (strangler pattern)',
                    'risk': 'High',
                    'time': 'Weeks'
                },
                '3_cdn_offloading': {
                    'action': 'Move static content to CDN, edge caching',
                    'downtime': 'None',
                    'risk': 'Low',
                    'time': '1-2 days'
                }
            },
            'deployment_strategy': {
                'canary_deployment': {
                    'description': 'Deploy fix to 5% traffic, monitor, gradually increase',
                    'downtime': 'None',
                    'rollback_time': '< 1 minute',
                    'best_for': 'Performance optimizations, query changes'
                },
                'blue_green_deployment': {
                    'description': 'Deploy to new environment, switch traffic',
                    'downtime': 'None',
                    'rollback_time': '< 1 minute',
                    'best_for': 'Major changes, infrastructure updates'
                },
                'feature_flags': {
                    'description': 'Deploy code off, enable gradually via config',
                    'downtime': 'None',
                    'rollback_time': '< 10 seconds',
                    'best_for': 'New features, experimental fixes'
                }
            }
        }
    
    @staticmethod
    def prevention_strategies() -> Dict:
        """
        How to prevent slow APIs from recurring
        """
        return {
            'proactive_monitoring': [
                'Performance budgets (p95 < 500ms)',
                'Load testing in staging',
                'Synthetic monitoring',
                'Capacity planning based on trends'
            ],
            'development_practices': [
                'Performance testing in CI/CD',
                'Code reviews focus on query efficiency',
                'Database query EXPLAIN analysis',
                'N+1 query detection in tests',
                'Profiling slow tests'
            ],
            'architecture': [
                'Caching strategy (Redis, CDN)',
                'Read replicas for read-heavy workloads',
                'Connection pooling',
                'Async processing for heavy operations',
                'Circuit breakers for external dependencies'
            ],
            'continuous_improvement': [
                'Regular performance audits',
                'Post-mortems for incidents',
                'Performance dashboards in standups',
                'SLO/SLA tracking'
            ]
        }


# ========================================
# Example Usage in Interview
# ========================================

def example_monitored_endpoint():
    """
    Example of how to use monitoring in your endpoint
    
    In interview, show this pattern:
    1. Decorator automatically monitors performance
    2. If slow, logs are generated
    3. Metrics are collected
    4. Alerts are triggered
    5. Dashboard updates in real-time
    """
    
    @monitor_performance
    def get_players():
        # Simulate work
        time.sleep(0.6)  # Simulates slow query (> 500ms threshold)
        return {"data": []}
    
    # When this endpoint is called:
    # - Duration measured: 600ms
    # - Slow API warning logged (> 500ms)
    # - Metrics recorded
    # - If critical (> 2s), alert sent
    
    return get_players()


if __name__ == '__main__':
    # Demo the monitoring system
    print("=== Performance Monitoring Demo ===\n")
    
    print("1. Detection Strategy:")
    print(json.dumps(SlowAPIRemediation.detection_strategy(), indent=2))
    
    print("\n2. Investigation Steps:")
    print(json.dumps(SlowAPIRemediation.investigation_steps(), indent=2))
    
    print("\n3. Remediation Strategies:")
    print(json.dumps(SlowAPIRemediation.remediation_strategies(), indent=2))
    
    print("\n4. Prevention Strategies:")
    print(json.dumps(SlowAPIRemediation.prevention_strategies(), indent=2))

