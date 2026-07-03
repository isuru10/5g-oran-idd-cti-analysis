#!/bin/bash
# 5G O-RAN Workspace Initialization and Health Check

set -e

PYTHON_PATH="/home/isuru/miniconda3/envs/cti/bin/python3"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}=== 5G O-RAN Anomaly Detection & CTI: Health Check ===${NC}"

# 1. Check Python Interpreter
if [ -f "$PYTHON_PATH" ]; then
    echo -e "${GREEN}[PASS]${NC} Python interpreter found at $PYTHON_PATH"
else
    echo -e "${RED}[FAIL]${NC} Python interpreter NOT found at $PYTHON_PATH"
    exit 1
fi

# 2. Check SQLite Databases
DB_NETWORK="data/Network_Dataset.db"
DB_LOWER="data/Lower_Layer_Data.db"

if [ -f "$DB_NETWORK" ]; then
    echo -e "${GREEN}[PASS]${NC} Network database found at $DB_NETWORK"
else
    echo -e "${RED}[FAIL]${NC} Network database NOT found at $DB_NETWORK"
    exit 1
fi

if [ -f "$DB_LOWER" ]; then
    echo -e "${GREEN}[PASS]${NC} Lower layer database found at $DB_LOWER"
else
    echo -e "${RED}[WARNING]${NC} Lower layer database NOT found at $DB_LOWER (Optional)"
fi

# 3. Check Required Python Packages
echo "Checking Python package dependencies..."
$PYTHON_PATH -c "
libs = ['pandas', 'numpy', 'sklearn', 'imblearn', 'joblib', 'matplotlib', 'seaborn', 'sqlite3', 'shap', 'pypdf']
missing = []
for lib in libs:
    try:
        __import__(lib)
    except ImportError:
        missing.append(lib)

if missing:
    print(f'FAIL: Missing libraries: {missing}')
    exit(1)
else:
    print('PASS: All required libraries are installed.')
"

# 4. Check Model Artifacts
echo "Checking trained model and metadata artifacts..."
MODEL_FILES=(
    "models/random_forest_model.joblib"
    "models/scaler.joblib"
    "models/encoding_mappings.joblib"
    "models/target_mapping.joblib"
    "models/confusion_matrix.png"
    "data/cti_test_events.csv"
)

ALL_MODELS_OK=true
for file in "${MODEL_FILES[@]}"; do
    if [ -f "$file" ]; then
         echo -e "  ${GREEN}[OK]${NC} Found $file"
    else
         echo -e "  ${RED}[MISSING]${NC} $file"
         ALL_MODELS_OK=false
    fi
done

if [ "$ALL_MODELS_OK" = true ]; then
    echo -e "${GREEN}[PASS]${NC} Baseline models and prediction artifacts are ready."
else
    echo -e "${RED}[WARNING]${NC} Some baseline models or prediction artifacts are missing. Run the notebook to generate them."
fi

# 5. Check Pipeline Code Scripts
echo "Checking CTI pipeline source scripts..."
PIPELINE_SCRIPTS=(
    "src/cti_alert_generator.py"
    "src/cti_enrichment_llm.py"
    "src/cti_shap_explain.py"
)

ALL_SCRIPTS_OK=true
for script in "${PIPELINE_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
         echo -e "  ${GREEN}[OK]${NC} Found $script"
    else
         echo -e "  ${RED}[MISSING]${NC} $script"
         ALL_SCRIPTS_OK=false
    fi
done

if [ "$ALL_SCRIPTS_OK" = true ]; then
    echo -e "${GREEN}[PASS]${NC} Pipeline scripts are successfully integrated."
else
    echo -e "${RED}[FAIL]${NC} Critical pipeline source scripts are missing!"
    exit 1
fi

# 6. Check Generated JSON Alerts and Markdown Reports
echo "Checking generated CTI alerts and enriched reports..."
GENERATED_ASSETS=(
    "data/sample_alert_dos.json"
    "data/sample_alert_ddos.json"
    "data/sample_alert_probe.json"
    "data/sample_alert_bruteforce.json"
    "data/sample_alert_web.json"
    "data/sample_alert_dos_shap.json"
    "data/sample_alert_ddos_shap.json"
    "data/sample_alert_probe_shap.json"
    "data/sample_alert_bruteforce_shap.json"
    "data/sample_alert_web_shap.json"
    "data/incident_report_dos.md"
    "data/incident_report_ddos.md"
    "data/incident_report_probe.md"
    "data/incident_report_bruteforce.md"
    "data/incident_report_web.md"
    "data/incident_report_dos_shap.md"
    "data/incident_report_ddos_shap.md"
    "data/incident_report_probe_shap.md"
    "data/incident_report_bruteforce_shap.md"
    "data/incident_report_web_shap.md"
)

ALL_ASSETS_OK=true
MISSING_COUNT=0
for asset in "${GENERATED_ASSETS[@]}"; do
    if [ -f "$asset" ]; then
         continue
    else
         echo -e "  ${RED}[MISSING]${NC} $asset"
         ALL_ASSETS_OK=false
         MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

if [ "$ALL_ASSETS_OK" = true ]; then
    echo -e "${GREEN}[PASS]${NC} All 20/20 structured alerts and incident reports exist."
else
    echo -e "${RED}[WARNING]${NC} Missing $MISSING_COUNT generated alerts/reports. Run pipeline scripts to generate them."
fi

# 7. Check Ollama Connection & Cloud Model Registration
echo "Checking Ollama service and cloud model availability..."
if command -v ollama >/dev/null 2>&1; then
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} Ollama daemon is running on port 11434."
        if ollama list | grep -q "gpt-oss:20b-cloud"; then
            echo -e "  ${GREEN}[OK]${NC} Cloud model 'gpt-oss:20b-cloud' is registered and available."
            echo -e "${GREEN}[PASS]${NC} Ollama integration checks complete."
        else
            echo -e "  ${RED}[MISSING]${NC} Model 'gpt-oss:20b-cloud' not found in ollama list."
            echo -e "${RED}[WARNING]${NC} Pull the cloud model by running: ollama pull gpt-oss:20b-cloud"
        fi
    else
        echo -e "  ${RED}[OFFLINE]${NC} Ollama daemon is offline or port 11434 is closed."
        echo -e "${RED}[WARNING]${NC} Run: systemctl start ollama"
    fi
else
    echo -e "  ${RED}[MISSING]${NC} Ollama CLI not found on host."
fi

echo -e "${BLUE}=== Health Check Complete ===${NC}"
exit 0
