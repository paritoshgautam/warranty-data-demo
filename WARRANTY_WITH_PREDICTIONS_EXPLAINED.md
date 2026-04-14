# warranty_with_predictions.parquet - Complete Explanation

## 📄 **What Is This File?**

`warranty_with_predictions.parquet` is the **processed and enriched warranty data** that contains:
- Original warranty data (28 columns)
- ML-generated features (30 additional columns)
- **Total: 58 columns, 12,615 records**

---

## 👨‍💻 **Who Generates It?**

### **Generator: ML Training Pipeline**

**File**: `backend/ml/pipeline.py`  
**Class**: `WarrantyMLPipeline`  
**Method**: `run_full_pipeline()`

**Code Location**:
```python
# backend/ml/pipeline.py, lines 435-440

def run_full_pipeline(self, save_output=True):
    # ... (processing steps)
    
    # 11. Save processed data
    if save_output:
        output_path = self.data_path.parent / 'processed' / 'warranty_with_predictions.parquet'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
```

---

## ⏰ **When Is It Generated?**

### **Trigger: Manual Training Command**

You must **manually run** the training script:

```bash
cd backend
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

### **Frequency: On-Demand Only**

❌ **NOT automatic**  
❌ **NOT on backend startup**  
❌ **NOT on schedule**  
✅ **ONLY when you run training script**

---

## 🔄 **Complete Generation Flow**

```
1. USER RUNS COMMAND
   cd backend
   python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp

2. TRAINING SCRIPT STARTS
   backend/train_model.py
   ↓
   Creates WarrantyMLPipeline instance
   ↓
   Calls pipeline.run_full_pipeline(save_output=True)

3. ML PIPELINE EXECUTES (11 Steps)
   
   Step 1: Load Excel
   ├─ Reads: data/warranty_dump.xlsx
   └─ Result: 12,615 rows, 28 columns
   
   Step 2: Preprocess Text
   ├─ Combines description fields
   └─ Result: +2 columns (combined_text, assigned_flag)
   
   Step 3: TF-IDF Vectorization
   ├─ Converts text to numbers
   └─ Result: 1000 features
   
   Step 4: K-means Clustering
   ├─ Groups similar issues
   └─ Result: 50 clusters (0-49)
   
   Step 5: Generate Cluster Labels
   ├─ Creates human-readable names
   └─ Result: +2 columns (cluster_id, rca_cluster_label)
   
   Step 6: Rule-Based Categorization
   ├─ Keyword matching
   └─ Result: +1 column (category_rule_based)
   
   Step 7: Enhanced NLP Categorization
   ├─ Keyword extraction, ECU mapping
   └─ Result: +4 columns (issue_type_enhanced, system_area, 
                          affected_component, problem_type)
   
   Step 8: Advanced NLP (spaCy + Sentiment)
   ├─ NER, SVO extraction, sentiment analysis
   └─ Result: +5 columns (action_type_nlp, severity_score,
                          severity_level, sentiment_polarity,
                          issue_summary_nlp)
   
   Step 9: Add Derived Fields
   ├─ Status normalization
   └─ Result: +3 columns (normalized_status, assignment_status,
                          resolution_status)
   
   Step 10: Save Models
   ├─ Saves: tfidf_vectorizer.pkl
   ├─ Saves: kmeans_model.pkl
   └─ Saves: scaler.pkl
   
   Step 11: Save Processed Data ⭐
   ├─ Location: data/processed/warranty_with_predictions.parquet
   ├─ Format: Parquet (compressed, fast)
   └─ Result: 12,615 rows, 58 columns

4. FILE CREATED
   data/processed/warranty_with_predictions.parquet
   ↓
   Ready to be loaded by backend API
```

---

## 📊 **What's Inside the File?**

### **58 Total Columns**

#### **Original Columns (28)** - From Excel
```
- Issue Number
- Issue Description
- RCA Description
- ECU
- Affected Vehicle/Project: Model
- Model Year
- Issue Color Status
- Issue Manager
- RCA: Solver Lead
- Detection Date
- Dark Green Date
- ... (18 more)
```

#### **ML-Generated Columns (30)** - Added by Pipeline

**Clustering (2)**:
- `cluster_id`: 0-49
- `rca_cluster_label`: "Display Issue", "Settings Problem", etc.

**Rule-Based (1)**:
- `category_rule_based`: "Infotainment & Connectivity", "ADAS & Safety", etc.

**Enhanced NLP (4)**:
- `issue_type_enhanced`: "Infotainment - Voice Activate Inability"
- `system_area`: "Infotainment", "Body Control", etc.
- `affected_component`: "Display", "Voice", "Settings", etc.
- `problem_type`: "Absence", "Failure", "Inability", etc.

**Advanced NLP (5)** ⭐ NEW:
- `action_type_nlp`: "Activation", "Display", "Update", etc.
- `severity_score`: 0.0 to 1.0
- `severity_level`: "Critical", "High", "Medium", "Low"
- `sentiment_polarity`: -1.0 to 1.0
- `issue_summary_nlp`: "Cannot activate Voice Recognition"

**Derived Fields (3)**:
- `normalized_status`: "Open" or "Closed"
- `assignment_status`: "Assigned" or "Unassigned"
- `resolution_status`: "Resolved" or "Unresolved"

**Text Processing (2)**:
- `combined_text`: Preprocessed text for ML
- `assigned_flag`: Boolean assignment indicator

**Metadata (13)**:
- Various date fields, detection info, etc.

---

## 🔄 **When Do You Need to Regenerate It?**

### **Regenerate When**:

✅ **New raw data arrives**
```bash
# New warranty_dump.xlsx uploaded
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

✅ **ML model changes**
```bash
# Changed clustering parameters
python train_model.py --data ../data/warranty_dump.xlsx --n-clusters 100
```

✅ **NLP improvements**
```bash
# Added new keywords or ECU mappings
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

✅ **Categorization updates**
```bash
# Modified rule-based categories
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

### **DON'T Regenerate When**:

❌ Backend restarts (uses existing file)  
❌ Frontend changes (doesn't affect data)  
❌ API changes (doesn't affect data)  
❌ UI updates (doesn't affect data)  

---

## 🚀 **How Backend Uses This File**

### **Backend Startup Sequence**

```
1. BACKEND STARTS
   uvicorn api.main:app --reload

2. LIFESPAN MANAGER RUNS
   api/main.py: lifespan()
   ↓
   Creates DataService()

3. DATA SERVICE LOADS FILE
   api/services/data_service.py: load_data()
   ↓
   Reads: data/processed/warranty_with_predictions.parquet
   ↓
   Loads into memory: 12,615 records, 58 columns

4. DATA PREPARED
   _prepare_data()
   ↓
   Adds runtime fields
   ↓
   Fills NaN values

5. CACHED IN MEMORY
   self._data = df
   ↓
   Ready for API requests

6. API READY
   Listening on http://localhost:8000
   ↓
   <50ms response time (data already in memory)
```

**Key Point**: Backend **reads** the file, it doesn't **generate** it!

---

## 📁 **File Location**

```
mvp-warranty-data/
└── data/
    └── processed/
        └── warranty_with_predictions.parquet  ⭐ HERE
```

**Full Path**: `c:\Users\admin\Documents\mvp-warranty-data\data\processed\warranty_with_predictions.parquet`

---

## 🔍 **How to Check the File**

### **Check if File Exists**
```bash
# Windows
dir c:\Users\admin\Documents\mvp-warranty-data\data\processed\warranty_with_predictions.parquet

# PowerShell
Test-Path c:\Users\admin\Documents\mvp-warranty-data\data\processed\warranty_with_predictions.parquet
```

### **Check File Size**
```bash
# Should be ~5-10 MB
ls -lh data/processed/warranty_with_predictions.parquet
```

### **Inspect File Contents**
```python
import pandas as pd

df = pd.read_parquet('data/processed/warranty_with_predictions.parquet')

print(f"Records: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"\nColumn names:\n{df.columns.tolist()}")
print(f"\nSample record:\n{df.iloc[0]}")
```

### **Check Advanced NLP Fields**
```python
# Check if advanced NLP was applied
advanced_nlp_fields = [
    'action_type_nlp',
    'severity_score',
    'severity_level',
    'sentiment_polarity',
    'issue_summary_nlp'
]

for field in advanced_nlp_fields:
    if field in df.columns:
        print(f"✓ {field}: {df[field].notna().sum():,} records")
    else:
        print(f"✗ {field}: NOT FOUND")
```

---

## ⏱️ **Generation Time**

| Configuration | Time | Output |
|---------------|------|--------|
| **Without Advanced NLP** | ~30 seconds | 53 columns |
| **With Advanced NLP** | ~5-10 minutes | 58 columns |

**Current Training** (running now):
```
Started: 8:23 PM
Expected completion: 8:28-8:33 PM
Status: Processing advanced NLP (spaCy)
```

---

## 🎯 **Summary**

### **Quick Facts**

| Question | Answer |
|----------|--------|
| **Who generates it?** | `backend/ml/pipeline.py` (WarrantyMLPipeline) |
| **When?** | When you run `python train_model.py` |
| **How often?** | Manually, on-demand only |
| **What's inside?** | 12,615 records, 58 columns (original + ML features) |
| **Where?** | `data/processed/warranty_with_predictions.parquet` |
| **Used by?** | Backend API (loads on startup) |
| **Size?** | ~5-10 MB (compressed Parquet format) |

### **Key Workflow**

```
Raw Data (Excel)
    ↓ [Manual: python train_model.py]
ML Pipeline Processing (~5-10 min)
    ↓
warranty_with_predictions.parquet (Generated)
    ↓ [Automatic: on backend startup]
Backend Loads into Memory
    ↓
API Serves Data (<50ms)
    ↓
Frontend Displays Charts
```

---

**The file is generated by the ML training pipeline and used by the backend API!** 🎉
