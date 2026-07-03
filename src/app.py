import os
import json
import time
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
import shap
import joblib
from datetime import datetime
from flask import Flask, jsonify, request, render_template

# Mapping of threat classes to target O-RAN architecture components
COMPONENT_MAPPING = {
    'benign': 'None - Normal Operations',
    'dos': 'O-CU (Central Unit User/Control Plane) & UPF (User Plane Function)',
    'ddos': 'O-CU (Central Unit User/Control Plane) & UPF (User Plane Function)',
    'probe': 'O-RAN E2/O1 Interface (Near-RT RIC Discovery)',
    'bruteforce': 'O-Cloud Edge Server (Management Plane / Remote Shell Access)',
    'web': 'Near-RT RIC (RAN Intelligent Controller) Management Dashboard / API'
}

FEATURE_ORDER = [
    'proto', 'service', 'duration', 'src_bytes', 'dst_bytes', 
    'conn_state', 'missed_bytes', 'history', 'src_pkts', 
    'src_ip_bytes', 'dst_pkts', 'dst_ip_bytes', 'ip_proto', 
    'http_trans_depth', 'files_total_bytes', 'is_GET_mthd', 
    'http_status_error', 'is_file_transfered'
]

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load models at startup
models_dir = os.path.join(os.path.dirname(__file__), "../models")
rf_model = joblib.load(os.path.join(models_dir, "random_forest_model.joblib"))
scaler = joblib.load(os.path.join(models_dir, "scaler.joblib"))
encoding_mappings = joblib.load(os.path.join(models_dir, "encoding_mappings.joblib"))
target_mapping = joblib.load(os.path.join(models_dir, "target_mapping.joblib"))

# Initialize TreeExplainer
explainer = shap.TreeExplainer(rf_model)

def build_shap_prompt(alert_json):
    alert_str = json.dumps(alert_json, indent=2)
    prompt = f"""[System Instruction]
You are a Lead Cyber Threat Intelligence (CTI) analyst specializing in 5G Open RAN (O-RAN) security.
Analyze the following structured intrusion detection alert and generate an explanation-led incident report.

Strictly adhere to the following rules:
1. Do NOT invent indicators, IP addresses, domains, or network facts that are not present in the alert.
2. Contextualize the 5G/O-RAN threat based on the affected component and network features.
3. Map the attack behavior to MITRE ATT&CK concepts.
4. You MUST explicitly reference the provided **SHAP Explanation Evidence** to justify the assigned severity level and the recommended response. Explain how the top features (e.g. high packet rate or HTTP error status) influenced the model's detection.
5. Provide structured, clean Markdown with clear headings.

=== STRUCTURED DETECTOR ALERT WITH SHAP EVIDENCE ===
{alert_str}
=== END OF ALERT ===

Please provide the incident report containing:
1. **Threat Contextualization**: What is this threat class, what target component is affected, and what are its implications for the 5G network?
2. **Observation Analysis**: Analyze the network observations (protocol, state, packets, bytes, history).
3. **Model Explanation (SHAP-Based)**: Detail why the Random Forest model predicted this threat class, referencing the top 5 contributing features from the SHAP evidence.
4. **MITRE ATT&CK Correlation**: Map this behavior to specific MITRE ATT&CK tactics and techniques.
5. **Severity Level**: Assign Low, Medium, High, or Critical. **You must justify this level based on the SHAP feature contributions.**
6. **Immediate Mitigation & Response**: Actionable containment steps **justified by the SHAP feature findings**.
7. **Long-Term Countermeasures**: Hardening steps or architectural improvements.
8. **Human Review Required**: YES or NO, with clear justification.
"""
    return prompt

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events', methods=['GET'])
def get_events():
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    csv_path = os.path.join(data_dir, "cti_test_events.csv")
    df_events = pd.read_csv(csv_path)
    
    # Select 5 diverse events (one from each class)
    grouped = df_events.groupby('predicted_label')
    target_classes = ['dos', 'ddos', 'probe', 'bruteforce', 'web']
    selected_events = []
    
    for cls in target_classes:
        if cls in grouped.groups:
            row = grouped.get_group(cls).iloc[0]
            # Convert row to dict
            row_dict = row.to_dict()
            # Replace NaNs with None
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            row_dict['_id'] = f"{cls}-event"
            selected_events.append(row_dict)
            
    return jsonify(selected_events)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    event = data.get('event')
    if not event:
        return jsonify({"error": "No event provided"}), 400
        
    predicted_label = event['predicted_label']
    confidence = float(event['confidence'])
    affected_component = COMPONENT_MAPPING.get(predicted_label, "O-Cloud Network Infrastructure")
    
    alternatives = {}
    for k, v in event.items():
        if k.startswith('prob_'):
            label_name = k.replace('prob_', '')
            if label_name != predicted_label and float(v) > 0.001:
                alternatives[label_name] = round(float(v), 4)
                
    observations = {
        "ip_proto": int(event.get("ip_proto", 0) or 0),
        "proto": str(event.get("proto", "unknown") or "unknown"),
        "service": str(event.get("service", "none") or "none"),
        "conn_state": str(event.get("conn_state", "none") or "none"),
        "duration": float(event.get("duration", 0.0) or 0.0),
        "src_bytes": int(event.get("src_bytes", 0) or 0),
        "dst_bytes": int(event.get("dst_bytes", 0) or 0),
        "missed_bytes": int(event.get("missed_bytes", 0) or 0),
        "src_pkts": int(event.get("src_pkts", 0) or 0),
        "dst_pkts": int(event.get("dst_pkts", 0) or 0),
        "src_ip_bytes": int(event.get("src_ip_bytes", 0) or 0),
        "dst_ip_bytes": int(event.get("dst_ip_bytes", 0) or 0),
        "history": str(event.get("history", "none") or "none")
    }
    
    alert = {
        "alert_id": f"ALERT-5G-DEMO-{predicted_label.upper()}",
        "detection_timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "affected_network_component": affected_component,
        "predicted_threat_class": predicted_label,
        "true_threat_class": str(event.get("true_label", predicted_label)),
        "prediction_confidence": round(confidence, 4),
        "alternative_predictions": alternatives,
        "network_observations": observations
    }
    
    # SHAP Generation
    obs_numeric = {}
    for col in FEATURE_ORDER:
        val = observations.get(col)
        if col in encoding_mappings:
            obs_numeric[col] = encoding_mappings[col].get(str(val), 0)
        else:
            obs_numeric[col] = float(val) if val is not None else 0.0
            
    X_df = pd.DataFrame([obs_numeric])
    for col in FEATURE_ORDER:
        X_df[col] = pd.to_numeric(X_df[col], errors='coerce').fillna(0)
        
    X_scaled = scaler.transform(X_df)
    shap_vals = explainer.shap_values(X_scaled)
    
    class_idx = target_mapping['mapping'][predicted_label]
    if isinstance(shap_vals, list):
        inst_shap = shap_vals[class_idx][0]
    else:
        if len(shap_vals.shape) == 3:
            inst_shap = shap_vals[0, :, class_idx]
        else:
            inst_shap = shap_vals[0]
            
    contributions = []
    for name, val in zip(FEATURE_ORDER, inst_shap):
        contributions.append({
            "feature": name,
            "shap_value": float(val),
            "direction": "positive_contribution" if val > 0 else "negative_contribution"
        })
        
    contributions.sort(key=lambda x: abs(x['shap_value']), reverse=True)
    top_5 = contributions[:5]
    
    alert['shap_evidence'] = {
        "top_features": top_5,
        "evidence_summary": "Prediction driven by: " + ", ".join([f"{item['feature']} ({item['shap_value']:.4f})" for item in top_5])
    }
    
    return jsonify(alert)
    
@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    alert = request.json.get('alert', {})
    if isinstance(alert, dict):
        alert.pop('true_threat_class', None)
    prompt = build_shap_prompt(alert)
    
    model = "gpt-oss:20b-cloud"
    host = "http://localhost:11434"
    url = f"{host}/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            return jsonify({"report": res_json.get('response', '')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
