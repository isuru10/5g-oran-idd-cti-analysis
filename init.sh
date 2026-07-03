#!/bin/bash
# 5G O-RAN Workspace Initialization and Health Check

set -e

PYTHON_PATH="/home/isuru/miniconda3/envs/cti/bin/python3"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0;3m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}=== 5G O-RAN Anomaly Detection: Health Check ===${NC}"

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
    echo -e "${GREEN}[PASS]${NC} Network dataset found at $DB_NETWORK"
else
    echo -e "${RED}[FAIL]${NC} Network dataset NOT found at $DB_NETWORK"
    exit 1
fi

if [ -f "$DB_LOWER" ]; then
    echo -e "${GREEN}[PASS]${NC} Lower layer dataset found at $DB_LOWER"
else
    echo -e "${RED}[WARNING]${NC} Lower layer dataset NOT found at $DB_LOWER (Optional)"
fi

# 3. Check Required Python Packages
echo "Checking Python package dependencies..."
$PYTHON_PATH -c "
libs = ['pandas', 'numpy', 'sklearn', 'imblearn', 'joblib', 'matplotlib', 'seaborn', 'sqlite3']
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

echo -e "${BLUE}=== Health Check Complete ===${NC}"
exit 0
