import os
import json
import time
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
import shap
import joblib

# Mappings from raw label names to index numbers
FEATURE_ORDER = [
    'proto', 'service', 'duration', 'src_bytes', 'dst_bytes', 
    'conn_state', 'missed_bytes', 'history', 'src_pkts', 
    'src_ip_bytes', 'dst_pkts', 'dst_ip_bytes', 'ip_proto', 
    'http_trans_depth', 'files_total_bytes', 'is_GET_mthd', 
    'http_status_error', 'is_file_transfered'
]

def load_alert(class_name, data_dir="../data"):
    """Loads the structured F-03 JSON alert."""
    alert_path = os.path.join(data_dir, f"sample_alert_{class_name}.json")
    if not os.path.exists(alert_path):
        alert_path = alert_path.replace("../", "")
        if not os.path.exists(alert_path):
            raise FileNotFoundError(f"Could not locate alert JSON at {alert_path}")
    with open(alert_path, 'r') as f:
        return json.load(f)

def build_shap_prompt(alert_json):
    """Constructs the prompt forcing the LLM to reference SHAP evidence."""
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

def query_ollama(prompt, model="gpt-oss:20b-cloud", host="http://localhost:11434"):
    """Sends request to local Ollama API wrapper."""
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
            return res_json.get('response', '')
    except Exception as e:
        print(f"  [DEBUG] Ollama query failed for model '{model}': {e}")
        return None

def generate_fallback_shap_report(alert_json):
    """Generates fallback report with explicit SHAP evidence citations."""
    threat = alert_json['predicted_threat_class'].upper()
    comp = alert_json['affected_network_component']
    obs = alert_json['network_observations']
    conf = alert_json['prediction_confidence']
    timestamp = alert_json['detection_timestamp']
    shap_ev = alert_json['shap_evidence']
    
    top_feats_str = ", ".join([f"`{item['feature']}` (SHAP: {item['shap_value']:.4f})" for item in shap_ev['top_features']])
    
    report = f"""# 5G O-RAN Explanation-Led Incident Report (Ollama Fallback)
**Alert ID:** {alert_json['alert_id']}
**Generated Time:** {timestamp}
**Threat Classifier Prediction:** {threat} (Confidence: {conf*100:.2f}%)
**Affected Component:** {comp}

---

## 1. Threat Contextualization
The Random Forest classifier has flagged activities targeting the **{comp}** as **{threat}**.
In O-RAN architectures, this threat poses a risk to service availability or edge infrastructure security.

## 2. Observation Analysis
- **Service & Port:** Running `{obs['service']}` protocol on `{obs['proto']}` with connection state `{obs['conn_state']}`.
- **Traffic Profile:** Transmitted {obs['src_bytes']} bytes (in {obs['src_pkts']} packets) and received {obs['dst_bytes']} bytes (in {obs['dst_pkts']} packets).

## 3. Model Explanation (SHAP-Based)
The model's classification decision was strongly guided by the following top features:
{top_feats_str}
- The primary contributor was `{shap_ev['top_features'][0]['feature']}` with a SHAP score of `{shap_ev['top_features'][0]['shap_value']:.4f}`, representing a strong positive influence on the threat score.
- Secondary contributors included `{shap_ev['top_features'][1]['feature']}` and `{shap_ev['top_features'][2]['feature']}`. This confirms the decision relies on concrete network layer footprints.

## 4. MITRE ATT&CK Correlation
- **Tactic:** Defense Evasion / Discovery / Impact
- **Technique:** Specific techniques mapped to {threat}.

## 5. Severity Level: HIGH
- **Justification (SHAP-Driven):** The severity is high because the top contributing feature (`{shap_ev['top_features'][0]['feature']}`) exhibits anomalous values directly associated with unauthorized control/service exploitation.

## 6. Immediate Mitigation & Response
- Containment steps must prioritize mitigating the anomalies identified by the top features:
  1. Address the `{shap_ev['top_features'][0]['feature']}` anomaly by blocking offending IPs or limiting session parameters.
  2. Implement firewall filters for `{shap_ev['top_features'][1]['feature']}` abnormalities.

## 7. Long-Term Countermeasures
- Establish zero-trust boundaries around `{comp}`.
- Harden configurations to prevent exploitation of the features identified in the SHAP analysis.

## 8. Human Review Required: YES
- **Justification:** CTI reports must undergo security analyst validation to verify SHAP contributions against system events.
"""
    return report

def main():
    print("Starting SHAP Explainability & CTI Alert Integration (F-05)...")
    
    # 1. Load trained artifacts
    models_dir = "../models" if os.path.exists("../models") else "models"
    data_dir = "../data" if os.path.exists("../data") else "data"
    
    try:
        rf_model = joblib.load(os.path.join(models_dir, "random_forest_model.joblib"))
        scaler = joblib.load(os.path.join(models_dir, "scaler.joblib"))
        encoding_mappings = joblib.load(os.path.join(models_dir, "encoding_mappings.joblib"))
        target_mapping = joblib.load(os.path.join(models_dir, "target_mapping.joblib"))
        print("Loaded ML model, scaler, and metadata mappings.")
    except Exception as e:
        print(f"Error loading model artifacts: {e}")
        return
        
    # 2. Initialize TreeExplainer
    print("Initializing SHAP TreeExplainer (this may take a few seconds)...")
    explainer = shap.TreeExplainer(rf_model)
    print("SHAP TreeExplainer initialized.")
    
    classes = ['dos', 'ddos', 'probe', 'bruteforce', 'web']
    available_models = ["gpt-oss:20b-cloud", "llama3", "qwen2.5", "mistral"]
    
    for cls in classes:
        print(f"\n--- Calculating SHAP & Generating Explanation-Led Alert for: '{cls}' ---")
        
        # Load F-03 Alert
        try:
            alert = load_alert(cls, data_dir)
        except Exception as e:
            print(f"Failed to load alert: {e}")
            continue
            
        # 3. Format observations to scale and encode
        obs = alert['network_observations']
        obs_numeric = {}
        
        # Map back categories using encoding_mappings
        for col in FEATURE_ORDER:
            val = obs.get(col)
            if col in encoding_mappings:
                obs_numeric[col] = encoding_mappings[col].get(str(val), 0)
            else:
                obs_numeric[col] = float(val) if val is not None else 0.0
                
        # Build dataframe
        X_df = pd.DataFrame([obs_numeric])
        # Ensure correct column types
        for col in FEATURE_ORDER:
            X_df[col] = pd.to_numeric(X_df[col], errors='coerce').fillna(0)
            
        # Scale
        X_scaled = scaler.transform(X_df)
        
        # 4. Compute SHAP values
        shap_vals = explainer.shap_values(X_scaled)
        
        # Find prediction class index
        pred_label = alert['predicted_threat_class']
        class_idx = target_mapping['mapping'][pred_label]
        
        # Get shape values for the predicted class
        if isinstance(shap_vals, list):
            inst_shap = shap_vals[class_idx][0]
        else:
            if len(shap_vals.shape) == 3:
                inst_shap = shap_vals[0, :, class_idx]
            else:
                inst_shap = shap_vals[0]
                
        # Zip and sort by absolute influence
        contributions = []
        for name, val in zip(FEATURE_ORDER, inst_shap):
            contributions.append({
                "feature": name,
                "shap_value": float(val),
                "direction": "positive_contribution" if val > 0 else "negative_contribution"
            })
            
        # Sort by absolute SHAP value
        contributions.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        top_5 = contributions[:5]
        
        # Add to alert payload
        evidence_summary = "Prediction driven by: " + ", ".join([f"{item['feature']} ({item['shap_value']:.4f})" for item in top_5])
        alert['shap_evidence'] = {
            "top_features": top_5,
            "evidence_summary": evidence_summary
        }
        
        # Save enriched alert
        shap_alert_path = os.path.join(data_dir, f"sample_alert_{cls}_shap.json")
        with open(shap_alert_path, 'w') as f:
            json.dump(alert, f, indent=2)
        print(f"  Enriched SHAP Alert saved to: {shap_alert_path}")
        
        # 5. Build prompt and query
        prompt = build_shap_prompt(alert)
        
        start_time = time.time()
        report_content = None
        used_model = None
        
        for model in available_models:
            print(f"  Querying local Ollama with model '{model}' for explanation-led report...")
            report_content = query_ollama(prompt, model=model)
            if report_content:
                used_model = model
                break
                
        generation_time = time.time() - start_time
        
        if not report_content:
            print("  Ollama query failed. Generating explanation-led fallback report...")
            report_content = generate_fallback_shap_report(alert)
            used_model = "Template-Based Fallback Generator"
            
        # 6. Save report
        shap_report_path = os.path.join(data_dir, f"incident_report_{cls}_shap.md")
        with open(shap_report_path, 'w') as f:
            f.write(report_content)
            
        print(f"  [EXPORTED] SHAP Incident Report saved to: {shap_report_path}")
        print(f"    Model Used: {used_model}")
        print(f"    Generation Time: {generation_time:.4f} seconds")
        
    print("\nF-05: SHAP Explainability & CTI Alert Integration completed successfully.")

if __name__ == "__main__":
    main()
