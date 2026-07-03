import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

def load_alert(class_name, data_dir="../data"):
    """Loads a structured JSON alert from the data directory."""
    alert_path = os.path.join(data_dir, f"sample_alert_{class_name}.json")
    if not os.path.exists(alert_path):
        # Fallback if run from root directory
        alert_path = alert_path.replace("../", "")
        if not os.path.exists(alert_path):
            raise FileNotFoundError(f"Could not locate alert JSON at {alert_path}")
    with open(alert_path, 'r') as f:
        return json.load(f)

def build_llm_prompt(alert_json):
    """Constructs the system-guided prompt containing the alert payload."""
    alert_str = json.dumps(alert_json, indent=2)
    prompt = f"""[System Instruction]
You are a Lead Cyber Threat Intelligence (CTI) analyst specializing in 5G Open RAN (O-RAN) security.
Analyze the following structured intrusion detection alert and generate a professional, analyst-grade incident report.

Strictly adhere to the following guidelines:
1. Do NOT invent indicators, IP addresses, domains, or network facts that are not present in the alert.
2. Contextualize the specific 5G/O-RAN threat based on the affected component and network observations.
3. Map the attack behavior to MITRE ATT&CK concepts (Enterprise, Mobile, or RAN).
4. Provide structured, clean Markdown with clear headings.

=== STRUCTURED DETECTOR ALERT ===
{alert_str}
=== END OF ALERT ===

Please provide the incident report containing:
1. **Threat Contextualization**: What is this threat class, what target component is affected, and what are its implications for the 5G network?
2. **Observation Analysis**: Analyze the network observations (protocol, state, packets, bytes, history) and explain how they characterize the threat.
3. **MITRE ATT&CK Correlation**: Map this behavior to specific MITRE ATT&CK tactics and techniques.
4. **Severity Level**: Assign Low, Medium, High, or Critical with a clear explanation of why.
5. **Immediate Mitigation & Response**: Actionable steps for containment and immediate response.
6. **Long-Term Countermeasures**: Hardening steps or architectural improvements.
7. **Human Review Required**: YES or NO, with clear justification.
"""
    return prompt

def query_ollama(prompt, model="gemma3:4b-cloud", host="http://localhost:11434"):
    """Sends a generate request to the local Ollama API endpoint."""
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

def generate_realistic_fallback_report(alert_json):
    """Generates a high-quality fallback incident report based on the specific alert observations."""
    threat = alert_json['predicted_threat_class'].upper()
    comp = alert_json['affected_network_component']
    obs = alert_json['network_observations']
    conf = alert_json['prediction_confidence']
    timestamp = alert_json['detection_timestamp']
    
    # Customize based on threat class
    if threat == 'BRUTEFORCE':
        mitre_mapping = "- **Tactic:** Credential Access (TA0006)\n- **Technique:** T1110 (Brute Force) - SSH/FTP login attempts"
        severity = "HIGH"
        severity_reason = f"The classifier predicted BRUTEFORCE with {conf*100:.2f}% confidence targeting critical management interfaces. Compromise of O-Cloud Edge Server administrative access leads to full control plane takeover."
        immediate_action = "1. **Terminate active session:** Terminate the offending TCP session state immediately.\n2. **Firewall Ban:** Add the source IP address associated with the connection to the edge firewall drop list.\n3. **Rotate Credentials:** Temporarily disable the targeted administrative account and initiate credentials rotation."
        long_term = "1. **Disable Password Auth:** Enforce SSH key-based authentication only.\n2. **Deploy Fail2ban:** Install intrusion prevention filters to rate limit and ban IPs showing consecutive login failures.\n3. **Multi-Factor Authentication:** Implement MFA for all O-Cloud management plane logins."
    elif threat == 'DOS' or threat == 'DDOS':
        mitre_mapping = f"- **Tactic:** Impact (TA0040)\n- **Technique:** T1498 (Network Service Denial of Service) - Flow flooding"
        severity = "CRITICAL"
        severity_reason = f"The classifier predicted {threat} with {conf*100:.2f}% confidence targeting O-CU & UPF plane. Exhausting resource pools halts user traffic and causes RAN partition."
        immediate_action = "1. **Rate Limiting:** Apply packet rate limiting on the UPF user plane for the subscriber or interface ID.\n2. **Dynamic Scaling:** Scale UPF slice capacity to absorb packet volume.\n3. **Traffic Scrubbing:** Redirect flow traffic through security scrubbing centers."
        long_term = "1. **Zero Trust slicing:** Implement isolation between network slices to prevent cross-slice exhaustion.\n2. **Robust Keep-Alive:** Configure aggressive protocol timeout thresholds for incomplete handshakes."
    elif threat == 'PROBE':
        mitre_mapping = "- **Tactic:** Discovery (TA0007)\n- **Technique:** T1046 (Network Service Scanning) - Port and service discovery"
        severity = "MEDIUM"
        severity_reason = f"The classifier predicted PROBE with {conf*100:.2f}% confidence targeting O-RAN E2/O1 interface. While it does not disrupt operations directly, scanning precedes active exploitation."
        immediate_action = "1. **Log traffic details:** Capture full packet logs of the scanning activity.\n2. **Filter interface access:** Strict firewall rules limiting access to RIC E2/O1 port bounds."
        long_term = "1. **Disable Unused Ports:** Secure O-RAN nodes by closing all non-essential communication ports.\n2. **Interface Encryption:** Enforce IPSec / TLS on all E2, O1, and A1 control interface paths."
    elif threat == 'WEB':
        mitre_mapping = "- **Tactic:** Initial Access (TA0001) / Privilege Escalation (TA0004)\n- **Technique:** T1190 (Exploit Public-Facing Application) - HTTP exploitation"
        severity = "HIGH"
        severity_reason = f"The classifier predicted WEB with {conf*100:.2f}% confidence targeting Near-RT RIC APIs. Web exploitation poses direct risks of unauthorized policy manipulation."
        immediate_action = "1. **API Gateway block:** Reject unauthorized or malformed HTTP requests.\n2. **Sandbox isolation:** Isolate targeted dashboard containers."
        long_term = "1. **API Authentication:** Enforce OAuth2 and JSON Web Tokens (JWT) for all Near-RT RIC dashboard queries.\n2. **WAF Deployment:** Position a Web Application Firewall in front of all O-RAN web portals."
    else:
        mitre_mapping = "- **Tactic:** General Access\n- **Technique:** Unknown"
        severity = "LOW"
        severity_reason = "Normal/benign traffic profile."
        immediate_action = "None required."
        long_term = "Continue baseline monitoring."

    report = f"""# 5G O-RAN Threat Intelligence Report (Ollama Fallback)
**Alert ID:** {alert_json['alert_id']}
**Generated Time:** {timestamp}
**Threat Classifier Prediction:** {threat} (Confidence: {conf*100:.2f}%)
**Affected Component:** {comp}

---

## 1. Threat Contextualization
The machine learning classifier has flagged network activity targeting the **{comp}** as a **{threat}** threat signature. 
- In the context of 5G O-RAN architectures, this vector represents a threat targeting the network layer.
- If successful, this attack could compromise system integrity, degrade service availability, or lead to unauthorized administrative control.

## 2. Observation Analysis
The network observations for this alert indicate:
- **Protocol & Service:** Utilized protocol `{obs['proto']}` running service `{obs['service']}`.
- **Connection State:** Connection ended with state `{obs['conn_state']}` (History signature: `{obs['history']}`).
- **Data Exchange volume:** Transmitted {obs['src_bytes']} bytes in {obs['src_pkts']} packets, and received {obs['dst_bytes']} bytes in {obs['dst_pkts']} packets.
- **Duration:** The connection duration was recorded as {obs['duration']} seconds.
These telemetry values match known features of a `{threat.lower()}` attack pattern, exhibiting abnormal payloads or connection durations.

## 3. MITRE ATT&CK Correlation
{mitre_mapping}

## 4. Severity Level: {severity}
- **Reasoning:** {severity_reason}

## 5. Immediate Mitigation & Response
{immediate_action}

## 6. Long-Term Countermeasures
{long_term}

## 7. Human Review Required: YES
- **Justification:** Any security incident altering configuration settings or blocking subscriber traffic must undergo human review by a Security Operations Center (SOC) analyst before final closure.
"""
    return report

def main():
    print("Starting LLM-Assisted CTI Enrichment Pipeline (F-04)...")
    
    classes = ['dos', 'ddos', 'probe', 'bruteforce', 'web']
    out_dir = "../data" if os.path.exists("../data") else "data"
    
    # Attempt to query local Ollama models in priority order
    available_models = ["gemma3:4b-cloud", "llama3", "qwen2.5", "mistral"]
    
    for cls in classes:
        print(f"\nProcessing Alert for Class: '{cls}'")
        
        # 1. Load Alert
        try:
            alert = load_alert(cls, out_dir)
        except Exception as e:
            print(f"  [ERROR] Failed to load alert: {e}")
            continue
            
        # 2. Build Prompt
        prompt = build_llm_prompt(alert)
        
        # 3. Query LLM and Measure Time
        start_time = time.time()
        report_content = None
        used_model = None
        
        # Try local Ollama
        for model in available_models:
            print(f"  Querying local Ollama using model '{model}'...")
            report_content = query_ollama(prompt, model=model)
            if report_content:
                used_model = model
                break
                
        generation_time = time.time() - start_time
        
        # 4. Fallback if Ollama is unavailable
        if not report_content:
            print("  Ollama unavailable or model not found. Generating high-quality fallback report...")
            report_content = generate_realistic_fallback_report(alert)
            used_model = "Template-Based Fallback Generator"
            
        # 5. Save report
        out_path = os.path.join(out_dir, f"incident_report_{cls}.md")
        with open(out_path, 'w') as f:
            f.write(report_content)
            
        print(f"  [EXPORTED] Incident report saved to: {out_path}")
        print(f"    Model Used: {used_model}")
        print(f"    Generation Time: {generation_time:.4f} seconds")
        
    print("\nF-04: LLM-assisted Threat Intelligence Enrichment completed successfully.")

if __name__ == "__main__":
    main()
