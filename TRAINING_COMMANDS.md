# Training Commands Reference

## ✅ **Correct Commands**

### **Full Training with Advanced NLP** (Recommended)
```bash
cd backend
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

**Time**: ~5-10 minutes  
**Output**: 58 fields including advanced NLP (severity, sentiment, action types)

---

### **Fast Training without Advanced NLP**
```bash
cd backend
python train_model.py --data ../data/warranty_dump.xlsx --no-advanced-nlp
```

**Time**: ~30 seconds  
**Output**: 53 fields (no spaCy processing)

---

## 📁 **File Paths**

### **From backend/ directory**:
```bash
# Correct ✅
--data ../data/warranty_dump.xlsx

# Wrong ❌
--data warranty_dump.xlsx  # File not in backend/ directory
```

### **From root directory**:
```bash
cd c:\Users\admin\Documents\mvp-warranty-data
python backend/train_model.py --data data/warranty_dump.xlsx --advanced-nlp
```

---

## 🔧 **All Available Options**

```bash
python train_model.py \
  --data ../data/warranty_dump.xlsx \
  --output data/processed/warranty_with_predictions.parquet \
  --models-dir data/models \
  --n-clusters 50 \
  --advanced-nlp \
  --verbose
```

### **Options**:
- `--data`: Path to input Excel file (required)
- `--output`: Path to output parquet file (default: data/processed/warranty_with_predictions.parquet)
- `--models-dir`: Directory to save models (default: data/models)
- `--n-clusters`: Number of K-means clusters (default: 50)
- `--advanced-nlp`: Enable spaCy + sentiment analysis (default: True)
- `--no-advanced-nlp`: Disable advanced NLP for faster training
- `--verbose`: Enable debug logging

---

## 📊 **What Gets Generated**

### **Output Files**:
```
data/
├── processed/
│   └── warranty_with_predictions.parquet  # 12,615 rows, 58 columns
└── models/
    ├── tfidf_vectorizer.pkl              # TF-IDF model
    ├── kmeans_model.pkl                  # K-means model
    └── scaler.pkl                        # Feature scaler

backend/
└── training.log                          # Training logs
```

### **New Data Fields** (with --advanced-nlp):
```
Basic Fields (28):
  - issue_number, issue_description, rca_description, ecu, etc.

ML Fields (25):
  - cluster_id, rca_cluster_label, category_rule_based
  
Enhanced NLP Fields (4):
  - issue_type_enhanced, system_area, affected_component, problem_type
  
Advanced NLP Fields (5):
  - action_type_nlp, severity_score, severity_level
  - sentiment_polarity, issue_summary_nlp

Derived Fields (3):
  - normalized_status, assignment_status, resolution_status
  
Total: 58 fields
```

---

## ⏱️ **Processing Time**

| Configuration | Time | Records/Second |
|---------------|------|----------------|
| Without Advanced NLP | ~30 sec | ~420 records/sec |
| With Advanced NLP | ~5-10 min | ~20-40 records/sec |

**Bottleneck**: spaCy processing (NER + dependency parsing)

---

## 🐛 **Common Errors**

### **Error 1: File Not Found**
```
FileNotFoundError: [Errno 2] No such file or directory: 'warranty_dump.xlsx'
```

**Solution**: Use correct relative path
```bash
# From backend/ directory
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp
```

---

### **Error 2: Unicode Encoding**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
```

**Solution**: Already fixed! Replaced emoji characters with [OK], [ERROR], [SUCCESS]

---

### **Error 3: spaCy Model Not Found**
```
OSError: [E050] Can't find model 'en_core_web_sm'
```

**Solution**: Download spaCy model
```bash
python -m spacy download en_core_web_sm
```

---

### **Error 4: Memory Error**
```
MemoryError: Unable to allocate array
```

**Solution**: Disable advanced NLP or process in batches
```bash
python train_model.py --data ../data/warranty_dump.xlsx --no-advanced-nlp
```

---

## 🚀 **After Training**

### **1. Verify Output**
```bash
cd backend
python verify_enhanced_categories.py
```

**Expected**:
```
✓ Enhanced categorization applied: True
✓ Advanced NLP applied: True
Total records: 12,615
```

---

### **2. Restart Backend**
```bash
cd backend
uvicorn api.main:app --reload
```

**Expected**:
```
INFO: Loaded 12,615 warranty records
INFO: Application startup complete
```

---

### **3. Refresh Frontend**
```
Ctrl + Shift + R  (hard refresh)
```

**Expected**:
- New "NLP Analysis" tab visible
- 4 new charts with data
- 10 filter dropdowns in modal

---

## 📝 **Training Log**

Check `training.log` for detailed output:
```bash
tail -f training.log
```

**Key Sections**:
```
1. Loading data
2. Preprocessing text
3. TF-IDF vectorization
4. K-means clustering
5. Generating cluster labels
6. Rule-based categorization
7. Enhanced NLP categorization
8. Advanced NLP analysis  ← Takes longest
9. Adding derived fields
10. Saving models
11. Saving processed data
```

---

## ✅ **Quick Start**

```bash
# 1. Navigate to backend
cd c:\Users\admin\Documents\mvp-warranty-data\backend

# 2. Train with advanced NLP
python train_model.py --data ../data/warranty_dump.xlsx --advanced-nlp

# 3. Wait ~5-10 minutes

# 4. Verify output
python verify_enhanced_categories.py

# 5. Restart backend
uvicorn api.main:app --reload

# 6. Hard refresh browser (Ctrl + Shift + R)
```

---

**That's it! Your warranty analytics platform now has state-of-the-art NLP capabilities!** 🎉
