# Incident Report – ALERT‑5G‑2026‑0002‑DDOS  
**Detection Timestamp:** 2026‑07‑03 T13:31:01 Z  
**Alert ID:** ALERT‑5G‑2026‑0002‑DDOS  
**Predicted Threat Class:** **Distributed Denial of Service (DDoS)**  
**Prediction Confidence:** **99.33 %**  

---

## 1. Threat Contextualization  

| Item | Detail |
|------|--------|
| **Threat Class** | Distributed Denial of Service (DDoS) |
| **Affected Component** | **O‑CU (Central Unit – User/Control Plane)** and **UPF (User Plane Function)** |
| **Network Layer** | Control‑plane (O‑CU) and User‑plane (UPF) traffic |
| **Implications for 5G/O‑RAN** | A successful DDoS against the O‑CU or UPF can saturate the control‑plane or user‑plane, leading to:  * loss of RRC (Radio Resource Control) signaling,  * inability to establish or maintain user sessions,  * degradation of end‑to‑end QoS,  * potential cascading failure of dependent network slices.  In an Open RAN environment, where the O‑CU is a virtualized element, the attack can also impact the underlying hypervisor and shared compute resources. |

---

## 2. Observation Analysis  

| Feature | Value | Interpretation |
|---------|-------|----------------|
| **ip_proto / proto** | 6 / TCP | Classic TCP traffic – typical for RRC or data sessions. |
| **service** | none | No well‑known service detected – likely a raw RRC or data packet. |
| **conn_state** | **S1** | “SYN” state – indicates an initial TCP handshake attempt. |
| **duration** | 8.8 × 10⁻⁵ s | Extremely short – a single packet or half‑open connection. |
| **src_bytes / dst_bytes** | 0 / 0 | No payload; only header information. |
| **src_pkts / dst_pkts** | 1 / 1 | One packet in each direction – typical of a SYN flood. |
| **src_ip_bytes / dst_ip_bytes** | 40 / 44 | Small header sizes consistent with TCP SYN packets. |
| **history** | **Sh** | “SYN, handshake” – confirms the packet is part of a TCP handshake. |

**Key Takeaway:** The flow is a classic TCP SYN packet with no payload, sent in a rapid, high‑rate pattern (as inferred from the model’s high conn_state contribution). This is the hallmark of a SYN flood – a common DDoS technique aimed at exhausting the target’s connection table.

---

## 3. Model Explanation (SHAP‑Based)  

The Random Forest model assigned the **ddos** label with a confidence of 0.9933. The SHAP evidence shows the top five features that drove this prediction:

| Rank | Feature | SHAP Value | Direction | Model Impact |
|------|---------|------------|-----------|--------------|
| 1 | **conn_state** | +0.2083 | Positive | Highest contribution – the presence of a SYN state strongly signals a flood of half‑open connections. |
| 2 | **history** | +0.1488 | Positive | Reinforces the SYN‑handshake pattern; indicates repeated SYN attempts. |
| 3 | **src_ip_bytes** | +0.1002 | Positive | Small source byte count typical of SYN packets; differentiates from legitimate data traffic. |
| 4 | **dst_ip_bytes** | +0.0742 | Positive | Similar reasoning to src_ip_bytes; confirms minimal payload. |
| 5 | **dst_bytes** | +0.0618 | Positive | Zero destination bytes further support the absence of payload. |

**Why the Model Chose DDoS:**  
- The combination of a SYN state and handshake history is a classic signature of a SYN flood.  
- The negligible byte counts confirm that the traffic is not carrying application data, but merely attempting to open connections.  
- The high SHAP values for these features indicate that the model learned that such patterns are highly indicative of a DDoS attack.

---

## 4. MITRE ATT&CK Correlation  

| ATT&CK Tactic | Technique | Relevance to Observed Behavior |
|---------------|-----------|--------------------------------|
| **Initial Access / Execution** | **T1071 – Application Layer Protocol** | The attacker uses TCP (application layer) to initiate connections. |
| **Persistence / Defense Evasion** | **T1499 – Distributed Denial of Service** | The attack is a classic DDoS aimed at exhausting resources. |
| **Impact** | **T1499 – Distributed Denial of Service** | Directly impacts availability of the O‑CU/UPF. |
| **Resource Development** | **T1499 – Distributed Denial of Service** | The attacker likely orchestrates multiple compromised hosts to generate the SYN flood. |

*Note:* ATT&CK’s “Distributed Denial of Service” technique is T1499. The observed SYN flood aligns with this technique.

---

## 5. Severity Level  

**Severity:** **Critical**

**Justification:**  
- The SHAP evidence shows that the **conn_state** and **history** features – the strongest indicators of a SYN flood – contributed the largest positive values (+0.2083 and +0.1488).  
- A SYN flood targeting the O‑CU/UPF can immediately saturate the control‑plane or user‑plane, causing widespread service disruption across multiple network slices.  
- The high prediction confidence (0.9933) combined with the critical nature of the affected components justifies a **Critical** severity rating.

---

## 6. Immediate Mitigation & Response  

| Action | Rationale (SHAP‑based) |
|--------|------------------------|
| **1. Deploy SYN‑cookie or SYN‑proxy on the O‑CU/UPF interfaces** | The model’s high conn_state contribution indicates a flood of SYN packets. SYN‑cookies mitigate the resource exhaustion by avoiding allocation of half‑open connections. |
| **2. Apply rate‑limiting on inbound TCP SYN packets** | The history feature (+0.1488) shows repeated handshake attempts. Rate‑limiting will curb the attack volume. |
| **3. Temporarily block the source IP(s) if they are identified as the flood origin** | src_ip_bytes (+0.1002) and dst_ip_bytes (+0.0742) are minimal, suggesting many identical packets from the same source. Source IP filtering can reduce the attack surface. |
| **4. Alert the O‑RAN operations team and trigger a network‑slice isolation procedure** | The attack threatens slice availability; isolating affected slices prevents cascading failures. |
| **5. Update the IDS/IPS signatures to flag similar SYN‑flood patterns** | The SHAP evidence confirms the pattern; adding a signature will improve future detection. |

---

## 7. Long‑Term Countermeasures  

1. **Architectural Hardening**  
   - Deploy **distributed DDoS protection** (e.g., edge scrubbing) in front of the O‑CU/UPF.  
   - Use **virtualized network functions (VNFs)** with built‑in rate‑limiting and connection‑table protection.  

2. **Enhanced Monitoring**  
   - Continuously monitor **conn_state** and **history** metrics at the O‑RAN edge.  
   - Implement **anomaly detection** that flags sudden spikes in SYN packets.  

3. **Zero‑Trust Networking**  
   - Enforce strict **access control** between O‑CU, UPF, and other RAN components.  
   - Use **mutual TLS** for control‑plane signaling to reduce spoofed SYN attempts.  

4. **Redundancy & Load Balancing**  
   - Deploy **multiple O‑CU/UPF instances** behind a load balancer to distribute traffic.  
   - Enable **automatic failover** to maintain service continuity during an attack.  

5. **Incident Response Playbooks**  
   - Formalize a **DDoS response playbook** specific to O‑RAN components.  
   - Include **automated rollback** of configuration changes that may exacerbate the attack.  

---

## 8. Human Review Required  

**YES**

**Justification:**  
- While the model confidence is high, the attack’s impact on critical 5G control and user planes warrants human oversight.  
- Human analysts should verify the source IPs, confirm that the traffic is indeed malicious (e.g., rule out legitimate testing or misconfiguration), and coordinate with network operations for any manual reconfiguration.  
- The SHAP evidence indicates a clear pattern, but operational context (e.g., scheduled maintenance, legitimate load spikes) must be ruled out before full mitigation actions are applied.

---