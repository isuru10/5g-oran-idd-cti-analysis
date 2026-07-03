# Incident Report – ALERT-5G-2026-0003-PROBE  
**Detection Timestamp:** 2026‑07‑03 T13:31:01 Z  
**Detection Confidence:** 0.9854 (Probe)  

---

## 1. Threat Contextualization  
- **Threat Class:** *Probe* – a reconnaissance activity aimed at discovering services, interfaces, or vulnerabilities.  
- **Affected Component:** *O‑RAN E2/O1 Interface (Near‑RT RIC Discovery)* – the control plane channel that allows the Near‑Real‑Time RIC to discover and interact with O‑NodeB (gNB) and other RIC components.  
- **Implications for 5G/O‑RAN:**  
  - A probe on this interface indicates an adversary is mapping the RIC topology, potentially looking for mis‑configurations or unprotected endpoints.  
  - While the probe itself does not alter network state, it can precede more damaging actions such as credential harvesting, privilege escalation, or denial‑of‑service attacks on the RIC.  
  - In a multi‑tenant O‑RAN environment, discovery of RIC services can expose tenant boundaries and inter‑RIC communication paths.

---

## 2. Observation Analysis  
| Field | Value | Interpretation |
|-------|-------|----------------|
| **ip_proto / proto** | 17 / UDP | The traffic is UDP‑based, typical for lightweight discovery probes (e.g., ICMP‑like or custom UDP discovery). |
| **conn_state** | S0 | “Connection never established” – the probe never completed a handshake, consistent with a simple scan. |
| **duration** | 0.0 s | The session terminated immediately after packet transmission. |
| **src_pkts / dst_pkts** | 2 / 0 | Two packets sent from the source, none received back – a classic “send‑and‑forget” probe. |
| **src_bytes / dst_bytes** | 136 / 0 | Small payloads, no response data. |
| **dst_ip_bytes** | 0 | No data received from the destination. |
| **history** | D | “Destination unreachable” – the probe did not receive a reply, reinforcing the reconnaissance nature. |
| **missed_bytes** | 0 | No retransmissions or packet loss recorded. |

**Summary:** The flow is a minimal, one‑way UDP probe that never receives a response, typical of a reconnaissance scan targeting the E2/O1 interface.

---

## 3. Model Explanation (SHAP‑Based)  
The Random Forest model assigned a 98.54 % probability to *probe* based on the following top five features:

| Rank | Feature | SHAP Value | Direction | Contribution to Prediction |
|------|---------|------------|-----------|----------------------------|
| 1 | **src_pkts** | +0.1185 | Positive | Indicates multiple packets sent, a hallmark of scanning. |
| 2 | **dst_ip_bytes** | +0.0889 | Positive | Zero bytes received from the target, reinforcing the “no‑response” pattern. |
| 3 | **src_ip_bytes** | +0.0866 | Positive | Small outbound payload, typical of lightweight probes. |
| 4 | **proto** | +0.0737 | Positive | UDP protocol is commonly used for discovery. |
| 5 | **dst_bytes** | +0.0734 | Positive | No inbound data, confirming probe behavior. |

**How the SHAP evidence drives the prediction:**

- The **positive SHAP values** for all five features push the model’s output toward the *probe* class.  
- The magnitude of each contribution is modest but cumulative, reflecting a pattern that matches the probe signature in the training data.  
- No negative contributions (e.g., high `conn_state` or `duration`) counterbalance the probe signal, so the model confidently labels the event as reconnaissance.

---

## 4. MITRE ATT&CK Correlation  
| Tactic | Technique | ATT&CK ID | Relevance |
|--------|-----------|-----------|-----------|
| **Reconnaissance** | *Network Service Scanning* | T1046 | UDP probe targeting E2/O1 interface. |
| **Discovery** | *System Information Discovery* | T1082 | Implicit discovery of RIC services. |
| **Initial Access** | *Exploit Public-Facing Application* | T1190 | Potential precursor to exploitation of RIC services. |

*Note:* The alert does not indicate exploitation or lateral movement; it is strictly reconnaissance.

---

## 5. Severity Level  
**Low**  
- **Justification:**  
  - The event is a *probe* with no successful connection or data exchange.  
  - SHAP contributions, while positive, are small and cumulative; they indicate a typical reconnaissance pattern rather than an attack with immediate impact.  
  - No evidence of credential theft, data exfiltration, or service disruption.  
  - The affected interface is a control plane channel; a single probe does not compromise the RIC or the underlying 5G core.

---

## 6. Immediate Mitigation & Response  
| Action | Rationale (SHAP‑based) |
|--------|------------------------|
| **Block source IP** on the E2/O1 interface firewall. | `src_pkts` and `src_ip_bytes` are high relative to the target; blocking stops further reconnaissance attempts. |
| **Enable rate‑limiting** for UDP traffic on the E2/O1 port. | `proto` (UDP) and `src_pkts` indicate repeated lightweight probes; rate‑limiting reduces noise and potential DoS risk. |
| **Log and alert on subsequent probes** from the same IP or subnet. | `dst_ip_bytes` and `dst_bytes` are zero; repeated zero‑response patterns should trigger escalation. |
| **Verify RIC service configuration** (e.g., authentication, TLS). | Prevents exploitation if the probe is a precursor to credential‑guessing or MITM. |
| **Update IDS/IPS signatures** for O‑RAN E2/O1 discovery scans. | Enhances detection of similar probes in the future. |

---

## 7. Long‑Term Countermeasures  
1. **Implement Mutual TLS (mTLS) on E2/O1** – ensures only authenticated RICs can communicate.  
2. **Deploy a dedicated RIC Discovery Firewall** that only allows known RIC IPs and blocks unsolicited UDP probes.  
3. **Introduce Anomaly‑Based Detection** for UDP traffic patterns on the E2/O1 interface, leveraging machine‑learning models tuned to O‑RAN traffic.  
4. **Segment the RIC Control Plane** from the data plane using VLANs or SR‑IOV to limit lateral movement.  
5. **Regularly Audit RIC Configuration** for open ports, default credentials, and unnecessary services.  
6. **Integrate O‑RAN telemetry** into a centralized SIEM to correlate probe events with other reconnaissance indicators.

---

## 8. Human Review Required  
**YES**  
- **Justification:**  
  - Although the severity is low, the probe targets a critical control interface.  
  - Human analysts should confirm that the source IP is not a legitimate RIC or a misconfigured device.  
  - Review of RIC logs may reveal whether the probe is part of a broader reconnaissance campaign.  
  - Decision to block or allow traffic should consider operational dependencies and potential false positives.

---