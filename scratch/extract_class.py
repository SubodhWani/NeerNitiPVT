import json
import os

notebook_path = r"c:\Projects\NeerNiti\notebooks\NeerNiti_UP_Model_Training.ipynb"
out_path = r"c:\Projects\NeerNiti\backend\app\ml\custom_model.py"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

source = ""
for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        content = "".join(cell.get('source', []))
        if 'class FactorizedPhysicsStackingEnsemble' in content:
            source = content
            break

with open(out_path, 'w', encoding='utf-8') as f:
    f.write("from sklearn.base import BaseEstimator, ClassifierMixin\n")
    f.write("import numpy as np\n")
    f.write("import pandas as pd\n")
    f.write("from xgboost import XGBClassifier\n")
    f.write("from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier\n")
    f.write("from sklearn.linear_model import LogisticRegression\n")
    f.write(source)

print("Extracted custom class successfully!")
