# LLM-Assisted Cyber Threat Intelligence for 5G O-RAN Security

**Final Comprehensive Report**

---

## 1. Introduction

The rapid adoption of 5G networks and the Open Radio Access Network (O-RAN) architecture has introduced significant advancements in network flexibility, interoperability, and intelligent control. However, this disaggregated architecture expands the attack surface, introducing new vulnerabilities across components such as the O-Cloud, Near-RT RIC, and O-CU/O-DU. While traditional AI-based Intrusion Detection Systems (IDS) can accurately detect anomalies and classify malicious traffic, their outputs are often opaque numerical predictions that lack actionable context for Security Operations Center (SOC) analysts.

This project bridges the gap between raw machine learning anomaly detection and actionable security response. By integrating a high-performance Random Forest threat detector with a Large Language Model (LLM) for Cyber Threat Intelligence (CTI) enrichment, we create a transparent pipeline that not only identifies threats but also contextualizes them. The LLM translates technical network observations into comprehensive hazard assessments, maps them to known attacker behaviors, and suggests targeted mitigations. To further reduce LLM hallucinations and enhance analyst trust, we incorporated SHAP (SHapley Additive exPlanations) to mandate that the LLM roots its severity assessments in concrete feature evidence.

## 2. Methodology

### 2.1 Dataset and Preprocessing
We utilized the **NetsLab-5GORAN-IDD** dataset, which consists of high-fidelity network logs reflecting various attack vectors against 5G O-RAN infrastructure. To ensure the model learns generalizable protocol behaviors rather than overfitting to the specific testbed environment, we systematically dropped host-specific identifiers (`uid`, `src_ip`, `dst_ip`, `src_port`, `dst_port`).

The initial dataset was heavily imbalanced, with normal traffic (Benign) and certain attacks like DoS dominating the distribution, while classes like Bruteforce were underrepresented. We applied a hybrid balancing approach:
1. **Downsampling:** Majority classes were capped at 50,000 samples.
2. **SMOTE Oversampling:** Synthetic Minority Over-sampling Technique (SMOTE) was applied to minority classes to bring them up to 50,000 samples.
This resulted in a perfectly balanced dataset of 300,000 events across six categories: `benign`, `bruteforce`, `ddos`, `dos`, `probe`, and `web`. Categorical features (`proto`, `service`, `conn_state`, `history`) were index-encoded and persisted to ensure consistent downstream mapping.

### 2.2 Machine Learning Model
We trained a standard Multi-class `RandomForestClassifier` using 100 decision trees. The data was scaled using a `StandardScaler` and split using an 80/20 stratified configuration. Random Forest was selected for its robustness against non-linear data distributions and its native compatibility with tree-based explainers like SHAP, which is crucial for our explanation-led pipeline.

### 2.3 CTI Alert Generation
Predicted events were processed to generate structured JSON CTI alerts. To maintain the integrity of the LLM analysis, the "true label" of the event was strictly withheld from the alert generation process. The structured alert explicitly maps the predicted threat to specific O-RAN architectural components:
*   `bruteforce` $\rightarrow$ O-Cloud Edge Server
*   `dos` / `ddos` $\rightarrow$ O-CU & UPF Data Plane
*   `web` $\rightarrow$ Near-RT RIC xApp Interfaces
*   `probe` $\rightarrow$ Management Interfaces (O-AM)

### 2.4 LLM Configuration and Threat Knowledge
For the CTI enrichment, we deployed `gemma3:4b-cloud` locally via the Ollama API. We utilized a rigid, instruction-tuned prompt that instructed the LLM to act as a Senior 5G Telecom Security Analyst. The prompt included contextual O-RAN knowledge, forcing the LLM to structure its output into standard sections: Incident Context, Threat Correlation (MITRE ATT&CK), Severity Assessment, Operational Impact, and Mitigation Directives.

## 3. Results

### 3.1 Machine Learning Evaluation
The Random Forest model achieved an **Overall Classification Accuracy of 91.66%** on the test set of 60,000 records.

**Classification Report:**
| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| Benign | 0.94 | 0.87 | 0.90 | 10000 |
| Bruteforce | 0.83 | 0.96 | 0.89 | 10000 |
| DDoS | 0.93 | 0.87 | 0.90 | 10000 |
| DoS | 0.84 | 0.91 | 0.88 | 10000 |
| Probe | 0.99 | 0.90 | 0.94 | 10000 |
| Web | 1.00 | 0.99 | 0.99 | 10000 |

**Confusion Matrix Analysis:**
While the model performs exceptionally well on distinct attacks like `web` and `probe`, the confusion matrix reveals that `dos` and `ddos` are occasionally misclassified as one another (e.g., True `dos` predicted as `ddos` 507 times). This is expected, as Denial of Service and Distributed Denial of Service share highly similar volumetric characteristics in higher-layer logs. Additionally, normal `benign` traffic is occasionally confused with `bruteforce` (1054 times), likely due to aggressive standard network retries mimicking login attempts.

### 3.2 Enriched CTI Alert Examples
The structured alerts effectively captured the primary prediction, confidence scores, and alternative predictions. For example, a `dos` alert clearly highlighted the target component as "O-CU & UPF Data Plane" and provided raw feature metrics (e.g., `dst_bytes`, `duration`) that served as the foundation for the LLM's subsequent analysis.

## 4. Discussion

### 4.1 LLM Output Quality
The `gemma3:4b-cloud` model produced highly actionable and professional incident reports. The model successfully contextualized the structured alerts, accurately mapped them to MITRE ATT&CK tactics (e.g., T1498 for Network Denial of Service), and provided concrete mitigations such as implementing rate-limiting in the O-CU layer or updating xApp firewall rules. 

### 4.2 Limitations and Hallucination Risks
One primary risk observed with generative LLMs in security is the tendency to hallucinate specific IP addresses or threat actor groups when none are provided. To mitigate this, our prompt explicitly forbade the invention of unobserved indicators. However, the LLM occasionally provided overly generalized mitigations that, while correct, lacked the strict technical specificity a seasoned O-RAN engineer might desire.

### 4.3 Possible Improvements
To further enhance the pipeline:
1.  **Specialized Fine-Tuning:** Fine-tuning a smaller, lightweight model (e.g., Llama 3 8B) exclusively on telecom security reports could improve the domain specificity of the mitigations while reducing inference costs.
2.  **RAG Integration:** Implementing Retrieval-Augmented Generation (RAG) linked to the latest 3GPP and O-RAN Alliance security specifications would allow the LLM to cite exact standard clauses in its mitigation recommendations.

## 5. Explainability (SHAP Integration)

To address the "black-box" nature of both the ML classifier and the LLM, we implemented a SHAP-based explanation-led approach. Using `shap.TreeExplainer`, we extracted the top three features contributing to the Random Forest prediction for every test event.

This SHAP evidence was embedded directly into the JSON CTI alert (e.g., `feature_1: duration (+0.15 impact)`). Crucially, the LLM prompt was modified to *require* the LLM to reference these specific SHAP values when assigning severity. When comparing reports generated with and without SHAP evidence, the SHAP-enriched reports demonstrated significantly higher analytical rigor. Instead of stating "The severity is high due to the nature of a DoS attack," the LLM stated, "The high severity is directly corroborated by the anomalous `dst_bytes` and `conn_state` metrics, which heavily influenced the anomaly detection system." This creates a verifiable chain of evidence from the raw network packet to the final SOC report.

## 6. Conclusion

This project successfully demonstrated that combining standard machine learning with structured LLM enrichment can dramatically improve the operational value of Intrusion Detection Systems in 5G O-RAN environments. By carefully balancing the dataset, maintaining strict separation of true labels from the LLM prompt, and mandating SHAP-based evidence references, we created a robust, transparent pipeline that not only detects threats with 91.66% accuracy but also empowers security analysts with immediate, contextualized intelligence.

---

## Deliverables

*   **GitHub Repository:** [Insert GitHub Repository Link Here]
*   **Demonstration Video:** [Insert Demo Video Link Here]
*   **Sample LLM Incident Report:** Please refer to `data/incident_report_dos.md` for a complete example of the LLM-generated CTI assessment.
