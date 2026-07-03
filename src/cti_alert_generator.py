import os
import json
from datetime import datetime
import pandas as pd

# Mapping of threat classes to target O-RAN architecture components
COMPONENT_MAPPING = {
    'benign': 'None - Normal Operations',
    'dos': 'O-CU (Central Unit User/Control Plane) & UPF (User Plane Function)',
    'ddos': 'O-CU (Central Unit User/Control Plane) & UPF (User Plane Function)',
    'probe': 'O-RAN E2/O1 Interface (Near-RT RIC Discovery)',
    'bruteforce': 'O-Cloud Edge Server (Management Plane / Remote Shell Access)',
    'web': 'Near-RT RIC (RAN Intelligent Controller) Management Dashboard / API'
}

def load_test_events(csv_path="../data/cti_test_events.csv"):
    """Loads the serialized test event predictions."""
    if not os.path.exists(csv_path):
        # Fallback if run from root directory
        csv_path = csv_path.replace("../", "")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Could not locate test events CSV at {csv_path}")
    return pd.read_csv(csv_path)

def generate_cti_alert(event_row, alert_id):
    """Formats a test event into a structured JSON alert without leaking the true label."""
    # Create realistic timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Get predicted label and confidence
    predicted_label = event_row['predicted_label']
    confidence = float(event_row['confidence'])
    
    # Identify affected component
    affected_component = COMPONENT_MAPPING.get(predicted_label, "O-Cloud Network Infrastructure")
    
    # Collect alternative predictions (excluding the true label, mapping prob_*)
    alternatives = {}
    for col in event_row.index:
        if col.startswith('prob_'):
            label_name = col.replace('prob_', '')
            prob_val = float(event_row[col])
            # Only record alternative predictions if they differ from predicted label and are > 0.1%
            if label_name != predicted_label and prob_val > 0.001:
                alternatives[label_name] = round(prob_val, 4)
                
    # Gather network observations
    observations = {
        "ip_proto": int(event_row.get("ip_proto", 0)),
        "proto": str(event_row.get("proto", "unknown")),
        "service": str(event_row.get("service", "none")),
        "conn_state": str(event_row.get("conn_state", "none")),
        "duration": float(event_row.get("duration", 0.0)),
        "src_bytes": int(event_row.get("src_bytes", 0)),
        "dst_bytes": int(event_row.get("dst_bytes", 0)),
        "missed_bytes": int(event_row.get("missed_bytes", 0)),
        "src_pkts": int(event_row.get("src_pkts", 0)),
        "dst_pkts": int(event_row.get("dst_pkts", 0)),
        "src_ip_bytes": int(event_row.get("src_ip_bytes", 0)),
        "dst_ip_bytes": int(event_row.get("dst_ip_bytes", 0)),
        "history": str(event_row.get("history", "none"))
    }
    
    # Construct alert payload (True label must NOT be present)
    alert = {
        "alert_id": alert_id,
        "detection_timestamp": timestamp,
        "affected_network_component": affected_component,
        "predicted_threat_class": predicted_label,
        "prediction_confidence": round(confidence, 4),
        "alternative_predictions": alternatives,
        "network_observations": observations
    }
    return alert

def main():
    print("Initializing Structured CTI Alert Generator (F-03)...")
    
    # Load events
    try:
        df_events = load_test_events()
        print(f"Loaded {len(df_events)} test events successfully.")
    except Exception as e:
        print(f"Error: {e}")
        return
        
    # Group by predicted label to isolate one representative attack instance per class
    grouped = df_events.groupby('predicted_label')
    selected_rows = []
    
    # We want one instance of each attack class: dos, ddos, probe, bruteforce, web
    target_classes = ['dos', 'ddos', 'probe', 'bruteforce', 'web']
    for cls in target_classes:
        if cls in grouped.groups:
            selected_rows.append(grouped.get_group(cls).iloc[0])
            
    if not selected_rows:
        print("No attack labels found in prediction data. Selecting default first row.")
        selected_rows = [df_events.iloc[0]]
        
    out_dir = "../data" if os.path.exists("../data") else "data"
    
    for idx, row in enumerate(selected_rows):
        label = row['predicted_label']
        alert_id = f"ALERT-5G-2026-{idx+1:04d}-{label.upper()}"
        
        # Build alert
        alert = generate_cti_alert(row, alert_id)
        
        # Verify true label is not leaked
        assert "true_label" not in alert, "Security check failed: true_label found in alert payload!"
        
        # Save to file
        out_path = os.path.join(out_dir, f"sample_alert_{label}.json")
        with open(out_path, 'w') as f:
            json.dump(alert, f, indent=2)
            
        print(f"  [EXPORTED] Threat '{label}' alert saved to: {out_path}")
        print(f"    Alert ID: {alert['alert_id']}")
        print(f"    Confidence: {alert['prediction_confidence']}")
        print(f"    Target: {alert['affected_network_component']}\n")
        
    print("F-03: Structured CTI Alert Generation completed successfully.")

if __name__ == "__main__":
    main()
