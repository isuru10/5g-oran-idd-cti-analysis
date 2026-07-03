# CLAUDE.md

## Python Environment & Setup
- **Python Environment:** `/home/isuru/miniconda3/envs/cti/bin/python3`
- **Pip Environment:** `/home/isuru/miniconda3/envs/cti/bin/pip`
- **Install Dependencies:** `pip install -r requirements.txt`

## Execution & Verification Commands
- **Initialize & Verify Setup:** `bash init.sh`
- **Execute Jupyter Notebook:**
  ```bash
  /home/isuru/miniconda3/envs/cti/bin/python3 -m jupyter nbconvert --to notebook --execute --inplace src/exploratory_analysis.ipynb
  ```

## Code Style & Formatting
- **Python Style:** Follow standard PEP 8 rules.
- **Variable Names:** Use snake_case for functions, variables, and database fields. UPPER_CASE for constants.
- **Notebook Standards:** Maintain clear markdown cells introducing objectives for each code cell.
- **Relative Path Rule:** Inside `src/`, reference data and models as `../data/` and `../models/` respectively.
- **No Mocking:** All model outputs and evaluation figures must be fully computed and saved to disk.
