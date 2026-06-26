# LLM-Assisted Cyber Threat Intelligence for 5G O-RAN Security

An end-to-end framework that trains a multi-class machine learning model to detect network-layer threats in 5G Open RAN environments, converts those detections into structured Cyber Threat Intelligence (CTI) alerts, and enriches them using a local, lightweight Large Language Model (LLM) assisted by SHAP-based explainability evidence.

---

## 📌 Project Overview
AI-based intrusion detection systems (IDS) are excellent at flagging anomalies, but their raw outputs (e.g., specific probabilities or numeric vectors) lack the contextual depth required by Security Operations Center (SOC) analysts to understand a threat and coordinate an active response.

This project bridges that gap by implementing a pipeline that:
1. **Detects:** Classifies 5G network traffic anomalies using the `NetsLab-5GORAN-IDD` dataset (Higher-Layer Network Data).
2. **Structures:** Formats raw machine learning outputs into interoperable JSON-based CTI alert schemas.
3. **Explains (Bonus):** Extracts SHAP feature importances to provide concrete evidence behind the model's decision.
4. **Contextualizes:** Feeds the alert and evidence into a locally deployed LLM to generate an actionable, analyst-grade incident report.