# Category and Issue Type Assignment - Detailed Explanation

## Overview
The system uses a **hybrid approach** combining **rule-based categorization** and **ML clustering** to assign categories and issue types.

---

## Step-by-Step Process

### Step 1: Text Preprocessing
**Location**: `pipeline.py` → `preprocess_text()`

**What happens**:
1. Combines multiple text fields into one:
   - `issue_description`
   - `rca_description` 
   - `ecu`
   - `model`

2. Creates `combined_text` field:
   ```
   Example: "software update bcm body control module ram 1500"
   ```

3. Cleans the text:
   - Converts to lowercase
   - Removes special characters
   - Strips whitespace

---

### Step 2: Feature Extraction (TF-IDF)
**Location**: `pipeline.py` → `extract_features()`

**What happens**:
1. Uses TF-IDF (Term Frequency-Inverse Document Frequency) to convert text to numbers
2. Extracts 500 most important features
3. Considers 1-word and 2-word phrases (ngrams)
4. Removes common English stop words

**Example**:
```
Text: "software update bcm module"
→ TF-IDF Vector: [0.0, 0.45, 0.0, ..., 0.82, ..., 0.0]
                  (500 numbers representing word importance)
```

---

### Step 3: ML Clustering (K-Means)
**Location**: `pipeline.py` → `train_clustering()`

**What happens**:
1. Groups similar issues into 50 clusters using K-Means algorithm
2. Issues with similar TF-IDF vectors are grouped together
3. Each issue gets a `cluster_id` (0-49)

**Example**:
```
Issue 1: "software update bcm" → Cluster 7
Issue 2: "bcm software flash" → Cluster 7
Issue 3: "camera malfunction" → Cluster 23
```

---

### Step 4: Generate Cluster Labels
**Location**: `pipeline.py` → `generate_cluster_labels()`

**What happens**:
1. For each cluster, finds the top 3 most important words
2. Creates a human-readable label from those words
3. Stores in `rca_cluster_label` field

**Example**:
```
Cluster 7 top words: ["software", "update", "bcm"]
→ Label: "Software Update Bcm"
```

---

### Step 5: Rule-Based Categorization
**Location**: `pipeline.py` → `apply_rule_based_categorization()`

**What happens**:
1. Checks the `combined_text` against predefined keyword lists
2. Assigns to first matching category
3. Stores in `category_rule_based` field

**Category Rules**:

| Category | Keywords |
|----------|----------|
| **ADAS & Safety Systems** | adas, camera, radar, lidar, sensor, collision, blind spot, lane, parking, cruise control, emergency brake, safety |
| **Infotainment & Connectivity** | infotainment, display, screen, audio, bluetooth, usb, navigation, gps, radio, speaker, connectivity, wifi |
| **Powertrain & Engine** | engine, transmission, powertrain, motor, battery, hybrid, electric, fuel, exhaust, turbo, cylinder, piston |
| **Body & Exterior** | door, window, mirror, trunk, hood, bumper, paint, body, exterior, seal, weatherstrip, glass |
| **Interior & Comfort** | seat, climate, hvac, air conditioning, heater, interior, dashboard, console, trim, upholstery, comfort |
| **Electrical & Lighting** | light, headlight, taillight, electrical, wiring, fuse, relay, switch, bulb, led, indicator |
| **Chassis & Suspension** | suspension, brake, wheel, tire, steering, chassis, shock, strut, alignment, bearing |
| **BCM & Body Control** | bcm, body control, module, control unit, ecu |
| **IPC & Instrument Cluster** | ipc, instrument, cluster, gauge, speedometer, odometer, warning light, indicator |
| **Other** | (default if no keywords match) |

**Example**:
```
Text: "software update bcm body control module"
→ Contains "bcm" → Category: "BCM & Body Control"

Text: "camera system malfunction"
→ Contains "camera" → Category: "ADAS & Safety Systems"
```

---

### Step 6: Final Issue Type Assignment
**Location**: `pipeline.py` → `apply_rule_based_categorization()` (line 214-218)

**Logic**:
```python
if category_rule_based != 'Other':
    rca_cluster_label_final = category_rule_based
else:
    rca_cluster_label_final = rca_cluster_label
```

**What this means**:
- **Prefer rule-based category** if a keyword match was found
- **Fallback to ML cluster label** if no keywords matched (category = "Other")

---

## Example Walkthrough

### Example Issue from Your Screenshot:
```
Issue Number: ECIMS451889
Description: "Software update required for BCM module"
ECU: "BCM - Body Control Module"
Model: "RAM 1500 PICKUP"
```

### Processing Steps:

**Step 1: Text Preprocessing**
```
combined_text = "software update required for bcm module bcm body control module ram 1500 pickup"
```

**Step 2: TF-IDF Feature Extraction**
```
Vector: [0.0, 0.45, ..., 0.82, ..., 0.0]  (500 features)
```

**Step 3: ML Clustering**
```
K-Means assigns to Cluster 7 (based on similarity to other software/BCM issues)
```

**Step 4: Generate Cluster Label**
```
Cluster 7 top words: ["software", "update", "bcm"]
rca_cluster_label = "Software Update Bcm"
```

**Step 5: Rule-Based Categorization**
```
Check keywords in combined_text:
- Contains "bcm" ✓
- Matches category: "BCM & Body Control"

category_rule_based = "BCM & Body Control"
```

**Step 6: Final Assignment**
```
Since category_rule_based = "BCM & Body Control" (not "Other"):
rca_cluster_label_final = "BCM & Body Control"
```

### Final Result:
```
Category: "BCM & Body Control"
Issue Type: "BCM & Body Control"
```

---

## Why This Hybrid Approach?

### Advantages:

1. **Rule-Based (Keywords)**:
   - ✅ Consistent and predictable
   - ✅ Domain expert knowledge
   - ✅ Easy to understand and audit
   - ❌ Limited to predefined keywords
   - ❌ Misses nuanced patterns

2. **ML Clustering**:
   - ✅ Discovers hidden patterns
   - ✅ Groups similar issues automatically
   - ✅ Handles new/unknown issue types
   - ❌ Less interpretable
   - ❌ Requires training data

3. **Hybrid (Both)**:
   - ✅ Best of both worlds
   - ✅ Rule-based for known patterns
   - ✅ ML for unknown patterns
   - ✅ More robust and accurate

---

## Fields in the Data

After processing, each issue has these fields:

| Field | Description | Example |
|-------|-------------|---------|
| `combined_text` | Preprocessed text | "software update bcm module" |
| `cluster_id` | ML cluster number | 7 |
| `rca_cluster_label` | ML-generated label | "Software Update Bcm" |
| `category_rule_based` | Rule-based category | "BCM & Body Control" |
| `rca_cluster_label_final` | **Final issue type** | "BCM & Body Control" |

---

## How to Modify Categories

### To Add a New Category:

Edit `pipeline.py` → `apply_rule_based_categorization()`:

```python
category_rules = {
    'Your New Category': [
        'keyword1', 'keyword2', 'keyword3'
    ],
    # ... existing categories
}
```

### To Change Keywords:

Edit the keyword list for any category:

```python
'ADAS & Safety Systems': [
    'adas', 'camera', 'radar',
    'your_new_keyword'  # Add here
],
```

### To Retrain:

```bash
cd backend
python train_model.py --data ../data/processed/warranty_with_predictions.parquet --n-clusters 50
```

---

## Summary

**Category Assignment Flow**:
```
Raw Text
   ↓
Preprocess (clean, combine)
   ↓
TF-IDF (convert to numbers)
   ↓
K-Means Clustering (group similar)
   ↓
Generate Cluster Labels (top keywords)
   ↓
Rule-Based Check (keyword matching)
   ↓
Final Assignment (prefer rules, fallback to ML)
   ↓
category_rule_based + rca_cluster_label_final
```

**Key Point**: The system uses **rule-based categorization first**, and only uses **ML clustering** as a fallback for issues that don't match any predefined keywords.
