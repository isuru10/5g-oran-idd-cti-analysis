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

---

## 🚀 Key Features
The platform provides the following core capabilities:
- **Data Engineering:** Applies hybrid sampling (SMOTE) to balance heavily skewed classes (`benign`, `bruteforce`, `ddos`, `dos`, `probe`, `web`).
- **Machine Learning:** Utilizes a Random Forest classifier achieving **91.66% overall accuracy**.
- **LLM Enrichment:** Integrates local `gemma3:4b-cloud` (via Ollama API) to transform technical observations into structured Incident Reports mapped to MITRE ATT&CK.
- **Explainable AI:** Uses `shap.TreeExplainer` to anchor the LLM's severity assessments to actual network feature metrics, ensuring transparent, evidence-based reporting.
- **Interactive Web Demo:** Features a Flask-based demonstration dashboard to simulate SOC workflows, strictly isolating "ground truth" labels from the LLM prompt to ensure evaluation integrity.

---

## 📦 Downloading the Repository & Git LFS
To keep the repository lightweight, all large machine learning models (`*.joblib`) and SQLite databases (`*.db`) are tracked using **Git Large File Storage (LFS)**.

**You must have Git LFS installed to pull the required data and model files!**

1. Install Git LFS for your operating system (e.g., `sudo apt install git-lfs` on Ubuntu, or `brew install git-lfs` on macOS).
2. Initialize Git LFS:
   ```bash
   git lfs install
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/isuru10/5g-oran-idd-cti-analysis.git
   cd 5g-oran-idd-cti-analysis
   ```
4. *If you already cloned the repository before installing LFS*, the large files will just be small text pointers. Run the following command to download the actual model and database binaries:
   ```bash
   git lfs pull
   ```

---

## 🛠️ Setup & Running the Demonstration

1. **Environment Setup:**
   Ensure you are using your configured virtual environment (e.g., Conda `cti` environment), then install the pip requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Demonstration Dashboard:**
   Start the Flask web application to interact with the LLM-assisted threat detection pipeline:
   ```bash
   python src/app.py
   ```
3. **Access the Interface:**
   Open your browser and navigate to `http://127.0.0.1:5000`. From there, you can select simulated 5G test events, view the SHAP evidence, and generate the final contextualized incident report.