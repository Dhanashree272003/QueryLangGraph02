import sqlite3

conn = sqlite3.connect('persistence/aiops.db')
c = conn.cursor()

# 1. Telemetry Metrics
c.execute("""
INSERT INTO telemetry_metrics (service, metric_name, metric_value, unit) 
VALUES ('auth-service', 'cpu_usage', 85.4, '%')
""")

c.execute("""
INSERT INTO telemetry_metrics (service, metric_name, metric_value, unit) 
VALUES ('payment-service', 'memory_usage', 92.1, '%')
""")

# 2. Classification / Incidents
c.execute("""
INSERT INTO classification_output (incident_id, service, failure_mode, confidence, root_cause) 
VALUES ('INC-101', 'payment-service', 'memory_leak', 0.95, 'Heap exhaustion in auth token cache')
""")

# 3. Severity
c.execute("""
INSERT INTO updated_severity (incident_id, service, initial_severity, updated_severity, escalation_reason) 
VALUES ('INC-101', 'payment-service', 'MEDIUM', 'CRITICAL', 'Cascading latency in payment gateway')
""")

# 4. Forecast
c.execute("""
INSERT INTO forecast (service, metric_name, forecast_value, time_to_failure_mins, anomaly_probability) 
VALUES ('auth-service', 'memory_usage', 94.2, 45.0, 0.92)
""")

# 5. Reliability
c.execute("""
INSERT INTO reliability (service, slo_percentage, uptime_percentage, error_budget_remaining) 
VALUES ('auth-service', 99.9, 99.95, 82.5)
""")

# 6. Feature Contribution
c.execute("""
INSERT INTO inference_outputs (incident_id, service, feature_name, importance_score, additional_metadata) 
VALUES ('INC-103', 'order-service', 'db_connection_pool_exhaustion', 0.89, 'High active connection count')
""")

conn.commit()
conn.close()
print("All AIOps tables populated successfully.")
