# Agent Operating Manual (AGENTS.md)

Welcome, coding agent. This file describes the development environment, guidelines, and execution workflows for the **5G O-RAN Cyber Threat Intelligence (CTI)** project.

---

## 1. Project Overview
This repository contains a high-performance data engineering and threat detection pipeline for the `NetsLab-5GORAN-IDD` dataset. The pipeline preprocesses network logs, handles severe class imbalances using SMOTE, trains a Random Forest multi-class classifier, and prepares test event records for downstream LLM-assisted threat intelligence enrichment.

---

## 2. Directory Layout
Ensure you maintain this structure. Do not create ad-hoc files in the root folder.
```
.
├── AGENTS.md               # This operating manual
├── CLAUDE.md               # Standard command definitions (build/test/style)
├── init.sh                 # Environment setup and health check script
├── feature_list.json       # Structured progress and scope tracker
├── claude-progress.md      # Chronological session and handoff log
├── requirements.txt        # Python pip dependencies
├── data/
│   ├── Network_Dataset.db  # Primary higher-layer network SQLite DB
│   ├── Lower_Layer_Data.db # Secondary lower-layer SQLite DB
│   └── cti_test_events.csv # Generated test set predictions for CTI
├── models/
│   ├── random_forest_model.joblib # Trained RF model
│   ├── scaler.joblib              # StandardScaler instance
│   ├── encoding_mappings.joblib   # Categorical features mappings
│   ├── target_mapping.joblib      # Target labels mapping dict
│   └── confusion_matrix.png       # Visual evaluation matrix
└── src/
    ├── exploratory_analysis.ipynb              # Main data prep and baseline ML notebook
    └── 5G-NL-IDD-higher_layer_network_data.ipynb # Reference notebook
```

---

## 3. Development Workflow & Commands
Always use the configured Python virtual environment interpreter:
- **Python Executable:** `/home/isuru/miniconda3/envs/cti/bin/python3`
- **Pip Executable:** `/home/isuru/miniconda3/envs/cti/bin/pip`

### Key Execution Commands
- **Initialize & Health Check:** `bash init.sh`
- **Execute Notebook In-place:**
  ```bash
  /home/isuru/miniconda3/envs/cti/bin/python3 -m jupyter nbconvert --to notebook --execute --inplace src/exploratory_analysis.ipynb
  ```

---

## 4. Hard Constraints & Coding Rules
1. **Scope Boundaries:** Work on exactly one feature from `feature_list.json` at a time.
2. **Relative Paths:** Inside the `src/` directory, all references to databases and model artifacts must use relative parent paths (e.g. `../data/...`, `../models/...`).
3. **No Placeholders:** Write fully functional code. Do not use comments like `# TODO: implement this later`.
4. **Verification Gate:** Every session code modification must be verified by running the notebook/tests. Never declare victory early.
5. **State Updates:** Before finishing your turn, update `feature_list.json` and `claude-progress.md` with your progress and current state.
