# Incident Report – ALERT-5G-2026-0001-DOS  

| Field | Value |
|-------|-------|
| **Alert ID** | ALERT-5G-2026-0001-DOS |
| **Detection Timestamp** | 2026‑07‑03T13:31:01Z |
| **Affected Component** | O‑CU (Central Unit – User/Control Plane) & UPF (User Plane Function) |
| **Predicted Threat Class** | DoS (confidence 0.7607) |
| **Alternative Predictions** | DDoS 0.0805, Probe 0.1581 |
| **Protocol** | TCP (IP proto 6) |
| **Connection State** | REJ |
| **Duration** | 0.000115 s |
| **Packets** | Src 2 pkts, Dst 2 pkts |
| **Bytes** | Src 80 bytes, Dst 80 bytes |
| **History** | “Sr” (SYN sent → SYN‑REJ received) |

---

## 1. Threat Contextualization  

- **Threat Class** – The alert indicates a **Denial‑of‑Service (DoS)** attempt.  
- **Targeted Component** – The O‑CU and UPF are core control‑plane and user‑plane functions in a 5G Open RAN architecture.  
- **Implications** –  
  - **Service Availability**: Even a single SYN‑REJ can consume control‑plane resources (e.g., TCP half‑open connection tables) if repeated, potentially exhausting the O‑CU’s ability to process legitimate UE registrations or handovers.  
  - **Network Stability**: UPF is responsible for packet routing and QoS enforcement; a DoS on the control plane can cascade to user‑plane congestion, degrading overall network performance.  
  - **Security Posture**: Persistent DoS attempts may be a precursor to more sophisticated attacks (e.g., resource exhaustion leading to privilege escalation or lateral movement within the RAN).

---

## 2. Observation Analysis  

| Observation | Interpretation | Relevance to DoS |
|-------------|----------------|------------------|
| **TCP SYN‑REJ** (`conn_state: REJ`, `history: Sr`) | The source initiates a SYN; the destination immediately rejects. | Classic SYN‑flood pattern; the attacker sends many SYNs but never completes the handshake. |
| **Zero payload bytes** (`src_bytes: 0`, `dst_bytes: 0`) | No data exchange beyond the handshake. | Indicates a handshake‑only attack, typical of DoS. |
| **Very short duration** (`0.000115 s`) | The connection is closed almost instantly. | Consistent with a SYN‑REJ; the attacker is not waiting for a response. |
| **Minimal packet count** (`src_pkts: 2`, `dst_pkts: 2`) | Only SYN and SYN‑REJ exchanged. | No further traffic, reinforcing the DoS nature. |
| **IP bytes** (`src_ip_bytes: 80`, `dst_ip_bytes: 80`) | Small packet size (≈40 bytes each). | Typical of TCP handshake packets. |
| **Confidence & alternatives** | Primary prediction is DoS; low probabilities for DDoS or probe. | Suggests a single‑source DoS rather than a distributed attack. |

---

## 3. MITRE ATT&CK Correlation  

| MITRE ATT&CK Tactic | Technique | Rationale |
|---------------------|-----------|-----------|
| **Initial Access / Execution** | *T1499 – Resource Hijacking* (Enterprise) | The attacker consumes control‑plane resources by flooding with SYNs, preventing legitimate traffic. |
| **Impact** | *T1499 – Resource Hijacking* (Enterprise) | Directly disrupts network availability. |
| **Defense Evasion** | *T1071 – Application Layer Protocol* (Enterprise) | Uses legitimate TCP protocol to blend with normal traffic. |
| **Discovery** | *T1046 – Network Service Scanning* (Enterprise) | The attacker may probe for open ports before launching DoS. |
| **RAN‑specific** | *T1499 – Resource Hijacking* (RAN) | In the RAN ATT&CK matrix, DoS on O‑CU/UPF is mapped to “Resource Hijacking” under the “Availability” tactic. |

---

## 4. Severity Level – **High**  

- **Justification**:  
  - The attack targets critical 5G control‑plane components that are essential for UE connectivity.  
  - Even a single SYN‑REJ can trigger resource exhaustion if repeated, potentially leading to service outages.  
  - The confidence score (0.7607) and the clear DoS signature warrant immediate attention.  
  - While the attack appears single‑source, the impact on network availability is significant enough to be classified as **High** rather than Medium.

---

## 5. Immediate Mitigation & Response  

| Action | Owner | Deadline | Notes |
|--------|-------|----------|-------|
| **Block source IP** (if known) | Network Security | Within 5 min | Use firewall/ACL to drop SYNs from the offending IP. |
| **Rate‑limit SYN packets** on O‑CU/UPF interfaces | RAN Ops | Within 10 min | Configure SYN‑capping or TCP‑SYN‑proxy to mitigate further attempts. |
| **Enable SYN‑cookie** on affected nodes | RAN Ops | Within 15 min | Protects against SYN‑flood by deferring allocation until handshake completion. |
| **Increase connection‑table limits** temporarily | RAN Ops | Within 20 min | Allows the system to absorb a higher volume of half‑open connections. |
| **Deploy DoS detection module** (e.g., DPI, flow‑based) | Security Ops | Within 30 min | Provides real‑time alerts for similar patterns. |
| **Notify stakeholders** (RAN, core, service teams) | Incident Manager | Within 30 min | Ensure awareness of potential service degradation. |
| **Log and archive traffic** for forensic analysis | SOC | Within 1 h | Preserve packet captures for deeper investigation. |

---

## 6. Long‑Term Countermeasures  

| Category | Recommendation | Rationale |
|----------|----------------|-----------|
| **Architectural** | Deploy a **TCP‑SYN‑proxy** or **load‑balancer** in front of O‑CU/UPF to absorb initial handshake traffic. | Offloads resource‑intensive handshake processing from core nodes. |
| **Policy** | Implement **rate‑limiting** and **threshold‑based alerts** for SYN traffic per source IP. | Prevents single‑source or low‑volume DoS from escalating. |
| **Monitoring** | Integrate **flow‑based analytics** (NetFlow/IPFIX) with anomaly detection to detect abnormal SYN ratios. | Enables early detection of DoS patterns. |
| **Hardening** | Enable **TCP‑SYN‑cookies** and **TCP‑ACK‑scanning** on all RAN nodes. | Protects against SYN‑flood and other TCP‑based DoS. |
| **Redundancy** | Deploy **multiple O‑CU/UPF instances** behind a **service‑mesh** with automatic failover. | Maintains availability if one node is saturated. |
| **Testing** | Conduct regular **DoS resilience drills** (e.g., controlled SYN‑flood tests) to validate mitigation efficacy. | Ensures preparedness and identifies gaps. |
| **Governance** | Update **RAN security policy** to include DoS detection and response playbooks. | Provides clear guidance for future incidents. |

---

## 7. Human Review Required  

**YES** – The alert, while clearly indicating a DoS attempt, requires human validation to:

1. Confirm the source IP (not provided in the alert) and rule out legitimate traffic patterns (e.g., misconfigured devices).  
2. Assess whether the DoS is part of a larger campaign (e.g., coordinated multi‑node attack).  
3. Decide on escalation and potential coordination with external stakeholders (e.g., upstream ISPs, CERT).  

---

**Prepared by:**  
Lead CTI Analyst – 5G Open RAN Security  
Date: 2026‑07‑03  
---