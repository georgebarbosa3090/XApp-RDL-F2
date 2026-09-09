from typing import Any

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    Counter = Histogram = Gauge = _DummyMetric
    def start_http_server(port): pass

class MetricsServer:
    def __init__(self, port: int = 8081):
        self.port = port
        self._init_metrics()

    def _init_metrics(self):
        # RMR
        self.rmr_rx = Counter('rdl_rmr_messages_received_total', 'Total RMR messages received')
        self.rmr_tx = Counter('rdl_rmr_messages_sent_total', 'Total RMR messages sent')
        self.rmr_errors = Counter('rdl_rmr_message_errors_total', 'Total RMR message errors')
        
        # KPM
        self.kpm_ind = Counter('rdl_kpm_indications_total', 'Total KPM indications received')
        self.kpm_decode_err = Counter('rdl_kpm_decode_errors_total', 'Total KPM decode errors')
        
        # Subscriptions
        self.subs_total = Counter('rdl_subscriptions_total', 'Total subscriptions created')
        self.subs_failures = Counter('rdl_subscription_failures_total', 'Total subscription failures')
        
        # RDL Logic
        self.action_proposals = Counter('rdl_action_proposals_total', 'Total action proposals received')
        self.conflicts = Counter('rdl_conflicts_detected_total', 'Total conflicts detected', ['type'])
        self.decisions = Counter('rdl_decisions_total', 'Total decisions made', ['strategy'])
        
        # Control
        self.ctrl_req = Counter('rdl_control_requests_total', 'Total control requests sent')
        self.ctrl_ack = Counter('rdl_control_ack_total', 'Total control acks received')
        self.ctrl_fail = Counter('rdl_control_failures_total', 'Total control failures')
        self.ctrl_timeout = Counter('rdl_control_timeouts_total', 'Total control timeouts')
        
        # Latency
        self.decision_latency = Histogram('rdl_decision_latency_seconds', 'Decision latency')
        self.control_latency = Histogram('rdl_control_latency_seconds', 'Control latency')
        self.e2e_latency = Histogram('rdl_e2e_loop_latency_seconds', 'E2E loop latency')
        
        # Gauges
        self.active_e2_nodes = Gauge('rdl_active_e2_nodes', 'Active E2 nodes')
        self.active_xapps = Gauge('rdl_active_xapps', 'Active xApps')
        self.active_subs = Gauge('rdl_active_subscriptions', 'Active subscriptions')
        self.ready_state = Gauge('rdl_ready', 'Is RDL ready (1 or 0)')

    def record_kpm(self):
        self.kpm_ind.inc()

    def update_active_xapps(self, count: int):
        self.active_xapps.set(count)

    def record_conflict(self, conflict: Any):
        ctype = getattr(conflict, "conflict_type", None)
        cname = getattr(ctype, "name", str(ctype)) if ctype else "UNKNOWN"
        self.conflicts.labels(type=cname).inc()

    def record_resolution(self, resolution: Any, latency_s: float):
        strat = getattr(resolution, "strategy_used", None)
        sname = getattr(strat, "name", str(strat)) if strat else "UNKNOWN"
        self.decisions.labels(strategy=sname).inc()
        self.decision_latency.observe(latency_s)

    def start(self):
        if HAS_PROMETHEUS:
            try:
                start_http_server(self.port)
            except Exception:
                pass

MetricsCollector = MetricsServer
