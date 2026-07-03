# Incident Report – ALERT-5G-2026-0005-WEB  
**Detection Timestamp:** 2026‑07‑03 T13:31:01 Z  
**Alert ID:** ALERT‑5G‑2026‑0005‑WEB  
**Affected Component:** Near‑RT RIC Management Dashboard / API  

---

## 1. Threat Contextualization  

| Item | Description |
|------|-------------|
| **Threat Class** | Web‑based probing / low‑impact enumeration |
| **Target** | Near‑RT RIC (RAN Intelligent Controller) Management Dashboard / API – the web interface that operators use to configure, monitor, and manage RIC services. |
| **Implications for 5G** | The RIC is a critical control plane element that orchestrates RAN functions. Even a low‑impact probe can reveal API endpoints, authentication mechanisms, or configuration data that a later attacker could exploit to gain privileged access, disrupt RIC services, or pivot into the broader 5G core. |

---

## 2. Observation Analysis  

| Field | Value | Interpretation |
|-------|-------|----------------|
| **ip_proto / proto** | 6 / tcp / http | Standard HTTP traffic over TCP. |
| **conn_state** | SF (closed) | Connection terminated normally. |
| **duration** | 0.154 s | Very short session – typical of automated probes. |
| **src_bytes / dst_bytes** | 138 / 686 | Small request, moderate response (likely error page). |
| **src_pkts / dst_pkts** | 12 / 10 | Few packets – consistent with a single HTTP request/response. |
| **src_ip_bytes / dst_ip_bytes** | 916 / 1908 | Source sent more bytes than destination, again indicating a request‑heavy probe. |
| **history** | “ShADTadtfF” | Packet‑state history shows a single SYN‑ACK‑FIN sequence – a quick, stateless interaction. |

**Summary:** The traffic pattern is a brief, stateless HTTP request that returned an error response. The small payloads and short duration suggest automated scanning rather than a sustained attack.

---

## 3. Model Explanation (SHAP‑Based)

The Random Forest model assigned a **100 % confidence** to the *web* threat class. The SHAP evidence shows the following top‑5 contributions:

| Rank | Feature | SHAP Value | Direction | Impact on Prediction |
|------|---------|------------|-----------|----------------------|
| 1 | `http_status_error` | **‑0.0749** | Negative | Indicates the response was an error (e.g., 404/403), a hallmark of probing. |
| 2 | `files_total_bytes` | **‑0.0582** | Negative | Low total file size – typical of automated enumeration. |
| 3 | `is_GET_mthd` | **‑0.0544** | Negative | GET requests are used for information gathering. |
| 4 | `is_file_transfered` | **‑0.0391** | Negative | No file transfer – again consistent with probing. |
| 5 | `dst_bytes` | **+0.0250** | Positive | Slightly larger response size, but still within error‑page range. |

**Why the model flagged this as a web threat:**

- The **negative contributions** from error status, small file size, GET method, and lack of file transfer collectively push the decision toward *web probing*.
- The **positive contribution** from `dst_bytes` is modest and does not offset the negative evidence.
- The overall SHAP sum is strongly negative, driving the prediction to the *web* class with full confidence.

---

## 4. MITRE ATT&CK Correlation  

| ATT&CK Tactic | Technique | Rationale |
|---------------|-----------|-----------|
| **Reconnaissance** | T1046 – Network Service Scanning | Automated HTTP requests to discover API endpoints. |
| **Initial Access** | T1071.001 – Web Protocols | Use of HTTP GET to interact with the RIC web interface. |
| **Discovery** | T1087 – Account Discovery (indirect) | Probing may reveal authentication mechanisms or user roles. |
| **Command & Control** | T1071.001 – Web Protocols | Potential future use of the same channel for C2. |

---

## 5. Severity Level – **Medium**

- **Justification:**  
  - The SHAP evidence shows a clear pattern of automated probing, but no evidence of successful exploitation, data exfiltration, or persistence.  
  - The attack is confined to a single short session with no malicious payload.  
  - However, the target is a critical 5G control plane component; repeated or coordinated probes could lead to credential discovery or privilege escalation.  
  - Therefore, a *Medium* severity is appropriate: the threat is real and potentially escalating, but not yet causing damage.

---

## 6. Immediate Mitigation & Response  

| Action | Rationale (SHAP‑based) |
|--------|------------------------|
| **Block source IP** | The probe used a single GET request with an error status; blocking prevents further enumeration. |
| **Rate‑limit the RIC API** | Prevents automated scanners from hammering the endpoint; mitigates the `http_status_error` pattern. |
| **Enable WAF rules for HTTP error responses** | Detects and blocks repeated error‑page requests. |
| **Audit authentication logs** | Look for repeated failed logins or unusual GET patterns that could indicate credential discovery. |
| **Notify RIC operators** | They should verify that the API is still protected and that no unauthorized changes have been made. |

---

## 7. Long‑Term Countermeasures  

1. **API Hardening**  
   - Enforce strict authentication (OAuth2, mutual TLS).  
   - Require CSRF tokens for state‑changing requests.  
   - Implement JSON Web Token (JWT) validation with short lifetimes.

2. **Network Segmentation**  
   - Place the RIC management interface in a separate DMZ with limited inbound access.  
   - Use 5G core‑specific ACLs to restrict traffic to known management IPs.

3. **Continuous Monitoring**  
   - Deploy anomaly detection for HTTP error rates and request patterns.  
   - Correlate with other logs (firewall, IDS/IPS) to detect coordinated scans.

4. **Patch Management**  
   - Keep the RIC software and underlying OS up‑to‑date to eliminate known web‑exploitable vulnerabilities.

5. **Security Awareness**  
   - Train operators to recognize and respond to anomalous API activity.

---

## 8. Human Review Required  

**YES** – The alert involves a critical 5G control plane component. Even though the current activity is low‑impact probing, the potential for escalation warrants human analyst review to confirm no hidden payloads or lateral movement attempts.

---