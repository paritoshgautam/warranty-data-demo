# Fix: Incorrect Categorization Issue

## Problem
The data shows "Radio Software Update Issues" for issues that don't mention "radio" because:
1. Using **old processed data** with stale predictions
2. Missing `combined_text` field (preprocessing didn't run)
3. Old labels don't match current categorization logic

## Solution

### Step 1: Find Your Raw Data Source
You need the **original raw data** before any ML processing. This should be:
- `data/raw/warranty_data.csv` OR
- `data/raw/warranty_data.parquet` OR
- Your original data export file

### Step 2: Retrain from Scratch

```bash
cd backend

# Option A: If you have raw data file
python train_model.py --data ../data/raw/warranty_data.csv --n-clusters 50

# Option B: If raw data is in a different location
python train_model.py --data /path/to/your/raw_data.csv --n-clusters 50
```

### Step 3: Verify the Fix

After retraining, check:

```bash
python investigate_issue.py
```

You should now see:
- ✅ `combined_text` field populated with actual text
- ✅ `category_rule_based` matching keywords in the text
- ✅ `rca_cluster_label_final` following the logic (rule-based first, ML fallback)

## Current Categorization Logic

The system should work like this:

```
Raw Text: "Software update required for BCM module"
    ↓
Combined Text: "software update bcm body control module"
    ↓
Check Keywords: Contains "bcm" → Matches "BCM & Body Control"
    ↓
Final: "BCM & Body Control" (NOT "Radio Software Update")
```

## Why This Happened

The file `warranty_with_predictions.parquet` contains:
- **Old predictions** from a previous training run
- **Different categorization logic** than current code
- **Missing preprocessing** (no combined_text field)

When you retrain from raw data, the new logic will apply correctly.

## Expected Results After Fix

For issue ECIMS451889:
- **Before**: "Radio Software Update Issues" (incorrect, from old data)
- **After**: "BCM & Body Control" or "General Software Issues" (correct, based on actual content)

## If You Don't Have Raw Data

If the raw data file is not available, you'll need to:

1. **Export fresh data** from your source system
2. **Place it in** `data/raw/` folder
3. **Run training** as shown above

The processed file (`warranty_with_predictions.parquet`) should **never be used as input** for training - it's the **output** of training.
