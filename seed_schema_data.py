"""
Seed Script for AIOps Persistence Database (aiops.db).

Executes persistence/schema.sql and populates mock dataset representing Inference Graph node outputs
and combinational pipeline results across all tables.
"""

import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "persistence", "aiops.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "persistence", "schema.sql")

def seed_database():
    print(f"Reading schema from: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Reset or open database
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute DDL statements
    cursor.executescript(schema_sql)

    # Ensure query_history table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id VARCHAR(100),
        user_query TEXT,
        parsed_intent TEXT,
        status VARCHAR(50),
        execution_time_ms REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Clear existing sample data to re-seed cleanly
    tables_to_clear = [
        "metrics", "logs", "traces", "severity",
        "node_feature_engineering", "node_preliminary_severity",
        "node_classification", "node_tumbling_window", "node_forecasting",
        "node_severity_update", "node_human_gate", "pipeline_results"
    ]
    for t in tables_to_clear:
        cursor.execute(f"DELETE FROM {t};")

    now = time.time()

    # 1. Raw Telemetry: metrics
    metrics_data = [
        ("ep-101", "memory_leak", "payment-service", "simulator", 60.0, now - 300, 78.5, 92.4, 1850.0, 450.0, 0.08, 95.0),
        ("ep-101", "memory_leak", "payment-service", "simulator", 120.0, now - 240, 82.1, 94.8, 1920.0, 520.0, 0.12, 96.2),
        ("ep-102", "cpu_saturation", "auth-service", "simulator", 60.0, now - 180, 96.5, 68.2, 450.0, 1200.0, 0.15, 98.1),
        ("ep-102", "cpu_saturation", "auth-service", "simulator", 120.0, now - 120, 98.9, 70.1, 480.0, 1450.0, 0.18, 99.4),
        ("ep-103", "db_connection_pool_exhaustion", "order-service", "simulator", 60.0, now - 60, 65.4, 75.0, 890.0, 850.0, 0.05, 80.0)
    ]
    for ep, fm, svc, src, el, ts, cpu, mem, heap, p99, err, saturation in metrics_data:
        cursor.execute("""
            INSERT INTO metrics (
                episode_id, failure_mode, service, source, elapsed_s, timestamp,
                cpu_utilization, memory_utilization, heap_mb, p99_latency, error_rate, cpu_saturation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ep, fm, svc, src, el, ts, cpu, mem, heap, p99, err, saturation))

    # 2. Raw Telemetry: logs
    cursor.execute("""
        INSERT INTO logs (episode_id, failure_mode, service, elapsed_s, timestamp, log_level, exception_type, log_message)
        VALUES ('ep-101', 'memory_leak', 'payment-service', 120.0, ?, 'ERROR', 'java.lang.OutOfMemoryError', 'Java heap space limit exceeded in token cache worker')
    """, (now - 240,))

    # 3. Raw Telemetry: traces
    cursor.execute("""
        INSERT INTO traces (episode_id, failure_mode, service, elapsed_s, timestamp, span_id, span_name, span_duration_ms, span_status, trace_id)
        VALUES ('ep-101', 'memory_leak', 'payment-service', 120.0, ?, 'span-901', 'POST /checkout', 1250.0, 'ERROR', 'tr-7782')
    """, (now - 240,))

    # 4. Raw Telemetry: severity
    cursor.execute("""
        INSERT INTO severity (episode_id, timestamp, elapsed_s, failure_mode, Severity, RawSeverity, WeightedScore, CriticalCount, WarningCount, Reason, RecommendedAction)
        VALUES ('ep-101', ?, 120.0, 'memory_leak', 'CRITICAL', 'HIGH', 88.5, 4, 2, 'Memory exhaustion leading to cascading latency spikes', 'Restart service pod and clear token cache')
    """, (now - 240,))

    # 5. Node 1: node_feature_engineering
    node_fe_data = [
        (1, "ep-101", "memory_leak", now - 300, 60.0, 78.5, 92.4, 1850.0, 450.0, 0.08, 15.0, 92.4, 3.0, 1),
        (2, "ep-101", "memory_leak", now - 240, 120.0, 82.1, 94.8, 1920.0, 520.0, 0.12, 18.0, 94.8, 5.0, 1),
        (3, "ep-102", "cpu_saturation", now - 180, 60.0, 96.5, 68.2, 450.0, 1200.0, 0.15, 96.5, 68.2, 2.0, 0)
    ]
    for cyc, ep, fm, ts, el, cpu, mem, heap, p99, err, log_cnt, log_crit, log_ex, log_nov in node_fe_data:
        cursor.execute("""
            INSERT INTO node_feature_engineering (
                cycle, episode_id, failure_mode, timestamp, elapsed_s,
                cpu_utilization, memory_utilization, heap_mb, p99_latency, error_rate,
                log_count, log_critical_count, log_has_exception, log_has_novel_template
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cyc, ep, fm, ts, el, cpu, mem, heap, p99, err, log_cnt, log_crit, log_ex, log_nov))

    # 6. Node 2: node_preliminary_severity
    cursor.execute("""
        INSERT INTO node_preliminary_severity (
            cycle, episode_id, failure_mode, timestamp, elapsed_s,
            preliminary_severity, severity_raw, weighted_score, critical_count, warning_count, blast_size, reason, recommended_action
        ) VALUES (2, 'ep-101', 'memory_leak', ?, 120.0, 'HIGH', 'HIGH', 82.5, 3, 1, 4, 'Rapid heap growth and error rates', 'Scale heap allocation')
    """, (now - 240,))

    # 7. Node 3: node_classification
    node_cls_data = [
        (1, "ep-101", "memory_leak", now - 300, 60.0, "memory_leak", 0.94),
        (2, "ep-101", "memory_leak", now - 240, 120.0, "memory_leak", 0.98),
        (3, "ep-102", "cpu_saturation", now - 180, 60.0, "cpu_saturation", 0.91)
    ]
    for cyc, ep, fm, ts, el, pf, prob in node_cls_data:
        cursor.execute("""
            INSERT INTO node_classification (cycle, episode_id, failure_mode, timestamp, elapsed_s, predicted_failure, prediction_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cyc, ep, fm, ts, el, pf, prob))

    # 8. Node 4: node_tumbling_window
    cursor.execute("""
        INSERT INTO node_tumbling_window (cycle, episode_id, failure_mode, timestamp, elapsed_s, dominant_state, vote_distribution, window_margin, window_full, window_size)
        VALUES (2, 'ep-101', 'memory_leak', ?, 120.0, 'memory_leak', '{"memory_leak": 9, "cpu_saturation": 1}', 0.80, 1, 10)
    """, (now - 240,))

    # 9. Node 5: node_forecasting
    node_fc_data = [
        (1, "ep-101", "memory_leak", now - 300, 60.0, "LinearTrendForecaster", 10, 300.0, 180.0, "heap_mb", 0.92, 1),
        (2, "ep-101", "memory_leak", now - 240, 120.0, "LinearTrendForecaster", 15, 300.0, 45.0, "heap_mb", 0.96, 1),
        (3, "ep-102", "cpu_saturation", now - 180, 60.0, "LinearTrendForecaster", 12, 300.0, 120.0, "cpu_utilization", 0.88, 1)
    ]
    for cyc, ep, fm, ts, el, alg, hist, hor, ttf, feat, conf, cross in node_fc_data:
        cursor.execute("""
            INSERT INTO node_forecasting (
                cycle, episode_id, failure_mode, timestamp, elapsed_s,
                algorithm_used, history_steps, forecast_horizon_s, time_to_failure, earliest_ttf_feature, forecast_confidence, threshold_crossed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cyc, ep, fm, ts, el, alg, hist, hor, ttf, feat, conf, cross))

    # 10. Node 6: node_severity_update
    node_su_data = [
        (1, "ep-101", "memory_leak", now - 300, 60.0, "HIGH", 0.92, 180.0, "heap_mb", "High", "Near", 1, "HIGH", "HIGH", 0, 0, 1, "Early warning stage"),
        (2, "ep-101", "memory_leak", now - 240, 120.0, "HIGH", 0.96, 45.0, "heap_mb", "High", "Imminent", 1, "CRITICAL", "CRITICAL", 1, 0, 2, "TTF < 60s trigger escalation to CRITICAL")
    ]
    for cyc, ep, fm, ts, el, p_sev, conf, ttf, feat, imp, urg, gate, cand, rev, esc, deesc, dwell, rsn in node_su_data:
        cursor.execute("""
            INSERT INTO node_severity_update (
                cycle, episode_id, failure_mode, timestamp, elapsed_s,
                preliminary_severity, forecast_confidence, time_to_failure, earliest_ttf_feature,
                impact_band, urgency_band, gate_passed, candidate_severity, revised_severity, is_escalated, is_deescalated, dwell_count, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cyc, ep, fm, ts, el, p_sev, conf, ttf, feat, imp, urg, gate, cand, rev, esc, deesc, dwell, rsn))

    # 11. Node 7: node_human_gate
    cursor.execute("""
        INSERT INTO node_human_gate (
            review_id, incident_id, episode_id, failure_mode, failure_label,
            old_severity, new_severity, final_severity, decision, operator, reason, confidence, ttf_seconds, impact_band, urgency_band, is_large_jump, recorded_at
        ) VALUES (
            'REV-901', 'INC-101', 'ep-101', 'memory_leak', 'Memory Leak Outage',
            'HIGH', 'CRITICAL', 'CRITICAL', 'APPROVED', 'auto_escalator', 'Automated approval based on TTF < 60s', 0.96, 45.0, 'High', 'Imminent', 0, datetime('now')
        )
    """)

    # 12. Combinational Snapshot Table: pipeline_results
    pipeline_data = [
        (1, "ep-101", "memory_leak", now - 300, 60.0, 78.5, 92.4, 1850.0, 0.08, 450.0, "HIGH", 82.5, "memory_leak", 0.94, "memory_leak", 180.0, 0.92, "HIGH", "HIGH", "REV-901", "APPROVED", "CRITICAL"),
        (2, "ep-101", "memory_leak", now - 240, 120.0, 82.1, 94.8, 1920.0, 0.12, 520.0, "HIGH", 88.5, "memory_leak", 0.98, "memory_leak", 45.0, 0.96, "CRITICAL", "CRITICAL", "REV-901", "APPROVED", "CRITICAL"),
        (3, "ep-102", "cpu_saturation", now - 180, 60.0, 96.5, 68.2, 450.0, 0.15, 1200.0, "HIGH", 75.0, "cpu_saturation", 0.91, "cpu_saturation", 120.0, 0.88, "HIGH", "HIGH", None, None, None)
    ]
    for cyc, ep, fm, ts, el, cpu, mem, heap, err, p99, p_sev, score, pf, prob, dom, ttf, f_conf, cand, rev, r_id, dec, final_s in pipeline_data:
        cursor.execute("""
            INSERT INTO pipeline_results (
                cycle, episode_id, failure_mode, timestamp, elapsed_s,
                fe_cpu_utilization, fe_memory_utilization, fe_heap_mb, fe_error_rate, fe_p99_latency,
                preliminary_severity, severity_weighted_score, predicted_failure, prediction_probability,
                dominant_state, time_to_failure, forecast_confidence, candidate_severity, revised_severity,
                hg_review_id, hg_decision, hg_final_severity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cyc, ep, fm, ts, el, cpu, mem, heap, err, p99, p_sev, score, pf, prob, dom, ttf, f_conf, cand, rev, r_id, dec, final_s))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
