# Machine Learning Enhancement Plan

## 🎯 **Objective**

Enhance the warranty analytics system with advanced machine learning capabilities:
1. **Issue Type Classifier**: Automatically predict issue categories
2. **BERT/Transformers**: Semantic understanding of issue descriptions
3. **Fix Prediction**: Learn from resolution descriptions to suggest fixes

---

## 📋 **Enhancement 1: Issue Type Classifier**

### **Goal**
Train a supervised classifier to predict issue types based on description text, replacing/augmenting rule-based categorization.

### **Approach**

#### **Phase 1: Data Preparation**
```python
# Use existing categorized data as training labels
Input: issue_description + rca_description
Labels: category_rule_based (11 categories)
Training set: 12,615 labeled examples
```

**Data Split**:
- Training: 80% (10,092 issues)
- Validation: 10% (1,262 issues)
- Test: 10% (1,261 issues)

#### **Phase 2: Model Selection**

**Option A: Traditional ML** (Fast, Interpretable)
```python
Models to try:
- Logistic Regression (baseline)
- Random Forest
- XGBoost
- LightGBM

Features:
- TF-IDF vectors (existing)
- ECU one-hot encoding
- Text length, word count
- Keyword presence flags
```

**Option B: Deep Learning** (Better accuracy)
```python
Models to try:
- CNN for text classification
- LSTM/GRU
- BiLSTM with attention
- FastText embeddings

Features:
- Word embeddings (300d)
- Character-level features
- ECU embeddings
```

#### **Phase 3: Training Pipeline**

```python
# backend/ml/issue_classifier.py

class IssueTypeClassifier:
    def __init__(self, model_type='xgboost'):
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        
    def prepare_features(self, df):
        """Extract features from text and metadata"""
        # TF-IDF features
        text_features = self.vectorizer.fit_transform(df['combined_text'])
        
        # ECU features
        ecu_features = pd.get_dummies(df['ecu'])
        
        # Combine features
        X = hstack([text_features, ecu_features])
        return X
    
    def train(self, X_train, y_train, X_val, y_val):
        """Train classifier with cross-validation"""
        if self.model_type == 'xgboost':
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='multi:softmax',
                num_class=11
            )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=10,
            verbose=True
        )
    
    def predict(self, X):
        """Predict issue category"""
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        return self.model.predict_proba(X)
```

#### **Phase 4: Evaluation Metrics**

```python
Metrics to track:
- Accuracy: Overall correctness
- Precision/Recall/F1: Per-category performance
- Confusion Matrix: Misclassification patterns
- Top-3 Accuracy: Is correct label in top 3 predictions?

Target Performance:
- Overall Accuracy: >85%
- Per-category F1: >0.80
- Top-3 Accuracy: >95%
```

#### **Phase 5: Integration**

```python
# In pipeline.py
def apply_ml_categorization(self, df):
    """Apply ML-based categorization"""
    X = self.classifier.prepare_features(df)
    
    # Get predictions and confidence
    predictions = self.classifier.predict(X)
    probabilities = self.classifier.predict_proba(X)
    
    df['category_ml_predicted'] = predictions
    df['category_ml_confidence'] = probabilities.max(axis=1)
    
    # Hybrid approach: Use ML if confident, else rule-based
    df['category_final'] = df.apply(
        lambda row: row['category_ml_predicted'] 
        if row['category_ml_confidence'] > 0.7 
        else row['category_rule_based'],
        axis=1
    )
    
    return df
```

### **Timeline**
- Week 1: Data prep, baseline model
- Week 2: Model experimentation
- Week 3: Hyperparameter tuning
- Week 4: Integration and testing

### **Expected Benefits**
- ✅ Better accuracy than rule-based (85%+ vs ~70%)
- ✅ Learns from patterns, not just keywords
- ✅ Confidence scores for predictions
- ✅ Handles new/unseen issue types better

---

## 📋 **Enhancement 2: BERT/Transformers for Semantic Understanding**

### **Goal**
Use pre-trained language models (BERT, RoBERTa) to understand semantic meaning of issue descriptions, not just keywords.

### **Approach**

#### **Phase 1: Model Selection**

**Option A: Pre-trained BERT** (Recommended)
```python
Models to try:
- bert-base-uncased (110M params)
- distilbert-base-uncased (66M params, faster)
- roberta-base (125M params, better performance)
- albert-base-v2 (12M params, efficient)

Best for: General text understanding
```

**Option B: Domain-Specific BERT**
```python
Models to try:
- SciBERT (scientific/technical text)
- PatentBERT (technical documentation)
- Custom fine-tuned BERT on automotive data

Best for: Automotive-specific terminology
```

#### **Phase 2: Fine-Tuning Pipeline**

```python
# backend/ml/bert_classifier.py

from transformers import (
    BertTokenizer, BertForSequenceClassification,
    Trainer, TrainingArguments
)
import torch

class BERTIssueClassifier:
    def __init__(self, model_name='bert-base-uncased', num_labels=11):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels
        )
        
    def tokenize_data(self, texts):
        """Tokenize text for BERT"""
        return self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
    
    def train(self, train_dataset, val_dataset):
        """Fine-tune BERT on warranty data"""
        training_args = TrainingArguments(
            output_dir='./models/bert_classifier',
            num_train_epochs=3,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=32,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=100,
            evaluation_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='f1',
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics
        )
        
        trainer.train()
        return trainer
    
    def predict(self, texts):
        """Predict with fine-tuned BERT"""
        inputs = self.tokenize_data(texts)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
            probabilities = torch.softmax(outputs.logits, dim=-1)
        
        return predictions, probabilities
    
    def get_embeddings(self, texts):
        """Extract BERT embeddings for similarity search"""
        inputs = self.tokenize_data(texts)
        
        with torch.no_grad():
            outputs = self.model.bert(**inputs)
            # Use [CLS] token embedding
            embeddings = outputs.last_hidden_state[:, 0, :]
        
        return embeddings
```

#### **Phase 3: Semantic Search & Similarity**

```python
# Use BERT embeddings for similar issue search

class SemanticIssueSearch:
    def __init__(self, bert_model):
        self.bert_model = bert_model
        self.issue_embeddings = None
        self.issue_index = None
        
    def build_index(self, df):
        """Build semantic search index"""
        # Get BERT embeddings for all issues
        texts = df['combined_text'].tolist()
        self.issue_embeddings = self.bert_model.get_embeddings(texts)
        self.issue_index = df['issue_number'].tolist()
        
    def find_similar_issues(self, query_text, top_k=10):
        """Find semantically similar issues"""
        # Get query embedding
        query_embedding = self.bert_model.get_embeddings([query_text])
        
        # Compute cosine similarity
        similarities = torch.cosine_similarity(
            query_embedding,
            self.issue_embeddings
        )
        
        # Get top-k most similar
        top_indices = torch.topk(similarities, k=top_k).indices
        
        return [self.issue_index[i] for i in top_indices]
```

#### **Phase 4: Multi-Task Learning**

```python
# Train BERT for multiple tasks simultaneously

class MultiTaskBERT:
    """
    Task 1: Issue category classification (11 classes)
    Task 2: Severity prediction (4 levels)
    Task 3: Resolution time prediction (regression)
    Task 4: Component extraction (NER)
    """
    
    def __init__(self):
        self.bert = BertModel.from_pretrained('bert-base-uncased')
        
        # Task-specific heads
        self.category_head = nn.Linear(768, 11)
        self.severity_head = nn.Linear(768, 4)
        self.time_head = nn.Linear(768, 1)
        self.ner_head = nn.Linear(768, num_entity_types)
    
    def forward(self, input_ids, attention_mask):
        # Get BERT embeddings
        outputs = self.bert(input_ids, attention_mask)
        pooled = outputs.pooler_output  # [CLS] token
        sequence = outputs.last_hidden_state  # All tokens
        
        # Task predictions
        category = self.category_head(pooled)
        severity = self.severity_head(pooled)
        time = self.time_head(pooled)
        ner = self.ner_head(sequence)
        
        return category, severity, time, ner
```

### **Timeline**
- Week 1-2: Setup, data prep, baseline fine-tuning
- Week 3-4: Hyperparameter tuning, optimization
- Week 5: Semantic search implementation
- Week 6: Multi-task learning experiments
- Week 7-8: Integration and testing

### **Expected Benefits**
- ✅ Understands context, not just keywords
- ✅ Handles synonyms and paraphrasing
- ✅ Better accuracy (90%+ vs 85%)
- ✅ Semantic search for similar issues
- ✅ Transfer learning from pre-trained knowledge

### **Challenges**
- ⚠️ Requires GPU for training (4-8 hours)
- ⚠️ Larger model size (~500MB vs 10MB)
- ⚠️ Slower inference (~100ms vs <1ms)
- ⚠️ Needs more computational resources

---

## 📋 **Enhancement 3: Fix Prediction from Resolution Descriptions**

### **Goal**
Learn from historical resolution descriptions to predict/suggest fixes for new issues.

### **Approach**

#### **Phase 1: Data Analysis**

```python
# Analyze resolution descriptions
df = pd.read_parquet('warranty_with_predictions.parquet')

# Check data quality
print(f"Issues with RCA: {df['rca_description'].notna().sum()}")
print(f"Resolved issues: {(df['resolution_status'] == 'Resolved').sum()}")

# Extract common fix patterns
fixes = df[df['resolution_status'] == 'Resolved']['rca_description']
```

**Expected Patterns**:
- Software updates: "Updated ECU software to version X.Y"
- Hardware replacement: "Replaced faulty component"
- Configuration changes: "Reconfigured settings"
- Calibration: "Recalibrated sensor"

#### **Phase 2: Fix Extraction & Classification**

```python
# backend/ml/fix_predictor.py

class FixPredictor:
    """Predict resolution actions from issue descriptions"""
    
    def __init__(self):
        self.fix_categories = {
            'software_update': ['update', 'upgrade', 'flash', 'reprogram'],
            'hardware_replacement': ['replace', 'swap', 'change', 'install new'],
            'configuration': ['configure', 'reconfigure', 'settings', 'parameter'],
            'calibration': ['calibrate', 'recalibrate', 'adjust', 'tune'],
            'reset': ['reset', 'reboot', 'restart', 'clear'],
            'investigation': ['investigate', 'analyze', 'root cause', 'debug']
        }
    
    def extract_fix_type(self, rca_text):
        """Extract fix category from RCA description"""
        if pd.isna(rca_text):
            return None
        
        text_lower = str(rca_text).lower()
        
        for fix_type, keywords in self.fix_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return fix_type
        
        return 'other'
    
    def prepare_training_data(self, df):
        """Prepare issue-fix pairs for training"""
        # Filter resolved issues with RCA
        resolved = df[
            (df['resolution_status'] == 'Resolved') & 
            (df['rca_description'].notna())
        ].copy()
        
        # Extract fix types
        resolved['fix_type'] = resolved['rca_description'].apply(
            self.extract_fix_type
        )
        
        # Create training pairs
        X = resolved['combined_text']  # Issue description
        y = resolved['fix_type']  # Fix category
        
        return X, y
```

#### **Phase 3: Sequence-to-Sequence Model**

```python
# Use T5 or BART for text generation

from transformers import T5ForConditionalGeneration, T5Tokenizer

class FixGenerator:
    """Generate fix suggestions using T5"""
    
    def __init__(self, model_name='t5-base'):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
    
    def prepare_data(self, df):
        """Prepare issue-fix pairs for T5"""
        # Format: "fix issue: <issue_description>"
        inputs = df['issue_description'].apply(
            lambda x: f"fix issue: {x}"
        )
        
        # Target: RCA description
        targets = df['rca_description']
        
        return inputs, targets
    
    def train(self, train_inputs, train_targets):
        """Fine-tune T5 on issue-fix pairs"""
        # Tokenize
        input_encodings = self.tokenizer(
            train_inputs.tolist(),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        
        target_encodings = self.tokenizer(
            train_targets.tolist(),
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors='pt'
        )
        
        # Training loop
        # ... (similar to BERT training)
    
    def generate_fix(self, issue_description):
        """Generate fix suggestion for new issue"""
        input_text = f"fix issue: {issue_description}"
        input_ids = self.tokenizer(
            input_text,
            return_tensors='pt'
        ).input_ids
        
        # Generate
        outputs = self.model.generate(
            input_ids,
            max_length=256,
            num_beams=5,
            early_stopping=True,
            temperature=0.7
        )
        
        fix_suggestion = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        return fix_suggestion
```

#### **Phase 4: Retrieval-Augmented Generation (RAG)**

```python
# Combine semantic search + generation

class RAGFixPredictor:
    """
    1. Find similar resolved issues (semantic search)
    2. Extract their fixes
    3. Generate new fix based on similar cases
    """
    
    def __init__(self, bert_model, fix_generator):
        self.bert_model = bert_model
        self.fix_generator = fix_generator
        self.resolved_issues = None
    
    def build_knowledge_base(self, df):
        """Build database of resolved issues"""
        self.resolved_issues = df[
            (df['resolution_status'] == 'Resolved') &
            (df['rca_description'].notna())
        ].copy()
        
        # Get embeddings
        self.resolved_embeddings = self.bert_model.get_embeddings(
            self.resolved_issues['combined_text'].tolist()
        )
    
    def predict_fix(self, new_issue_description):
        """Predict fix using RAG approach"""
        # Step 1: Find similar issues
        similar_indices = self.find_similar_issues(
            new_issue_description,
            top_k=5
        )
        
        # Step 2: Get their fixes
        similar_fixes = self.resolved_issues.iloc[similar_indices][
            'rca_description'
        ].tolist()
        
        # Step 3: Create context for generation
        context = f"""
        Issue: {new_issue_description}
        
        Similar resolved issues and their fixes:
        {chr(10).join([f"- {fix}" for fix in similar_fixes])}
        
        Suggested fix:
        """
        
        # Step 4: Generate fix
        suggested_fix = self.fix_generator.generate_fix(context)
        
        return {
            'suggested_fix': suggested_fix,
            'similar_issues': similar_indices,
            'similar_fixes': similar_fixes,
            'confidence': self.calculate_confidence(similar_indices)
        }
```

#### **Phase 5: Integration with UI**

```python
# Add fix prediction to API

@app.post("/api/predict/fix")
async def predict_fix(issue: IssueDescription):
    """Predict fix for a new issue"""
    prediction = fix_predictor.predict_fix(issue.description)
    
    return {
        'suggested_fix': prediction['suggested_fix'],
        'confidence': prediction['confidence'],
        'similar_cases': prediction['similar_issues'][:3],
        'fix_category': prediction['fix_type']
    }
```

**Frontend Display**:
```javascript
// Show fix suggestions in issue detail modal
<div className="fix-suggestion">
  <h4>💡 Suggested Fix</h4>
  <p>{suggestedFix}</p>
  <span className="confidence">
    Confidence: {(confidence * 100).toFixed(0)}%
  </span>
  
  <h5>Based on similar resolved issues:</h5>
  <ul>
    {similarCases.map(issue => (
      <li key={issue.id}>
        {issue.number}: {issue.fix}
      </li>
    ))}
  </ul>
</div>
```

### **Timeline**
- Week 1-2: Data analysis, fix extraction
- Week 3-4: Classification model training
- Week 5-6: T5/BART fine-tuning for generation
- Week 7-8: RAG implementation
- Week 9-10: API integration and UI
- Week 11-12: Testing and refinement

### **Expected Benefits**
- ✅ Automated fix suggestions for new issues
- ✅ Learn from historical resolutions
- ✅ Reduce time to resolution
- ✅ Knowledge transfer from experienced engineers
- ✅ Consistency in fix approaches

### **Challenges**
- ⚠️ RCA quality varies (may need cleaning)
- ⚠️ Not all issues have detailed resolutions
- ⚠️ Generated fixes need human validation
- ⚠️ Requires significant training data

---

## 📊 **Implementation Roadmap**

### **Phase 1: Foundation (Months 1-2)**
- ✅ Issue type classifier (XGBoost/LightGBM)
- ✅ Baseline evaluation metrics
- ✅ Integration with existing pipeline

### **Phase 2: BERT Integration (Months 3-4)**
- ✅ Fine-tune BERT for classification
- ✅ Semantic search implementation
- ✅ Embedding-based similarity

### **Phase 3: Fix Prediction (Months 5-6)**
- ✅ Fix extraction and classification
- ✅ T5/BART fine-tuning
- ✅ RAG implementation

### **Phase 4: Advanced Features (Months 7-8)**
- ✅ Multi-task learning
- ✅ Active learning for continuous improvement
- ✅ Confidence calibration
- ✅ Explainability (LIME/SHAP)

### **Phase 5: Production (Months 9-10)**
- ✅ Model serving optimization
- ✅ A/B testing
- ✅ Monitoring and retraining pipeline
- ✅ User feedback loop

---

## 🛠️ **Technical Stack**

### **Libraries & Frameworks**
```python
# Core ML
scikit-learn==1.3.0
xgboost==2.0.0
lightgbm==4.0.0

# Deep Learning
torch==2.0.0
transformers==4.30.0
sentence-transformers==2.2.0

# NLP
spacy==3.6.0
nltk==3.8.0
textblob==0.17.0

# Utilities
pandas==2.0.0
numpy==1.24.0
joblib==1.3.0
```

### **Hardware Requirements**

**Training**:
- GPU: NVIDIA RTX 3090 or better (24GB VRAM)
- RAM: 32GB minimum
- Storage: 100GB for models and data

**Inference**:
- CPU: 8 cores minimum
- RAM: 16GB
- GPU: Optional (10x faster)

---

## 📈 **Success Metrics**

### **Model Performance**
| Metric | Baseline | Target | Stretch |
|--------|----------|--------|---------|
| Classification Accuracy | 70% | 85% | 90% |
| Top-3 Accuracy | 85% | 95% | 98% |
| Fix Prediction Relevance | - | 70% | 80% |
| Semantic Search Precision@10 | - | 80% | 90% |

### **Business Impact**
- ⏱️ Reduce time to categorize: 5 min → 1 sec
- 🎯 Improve categorization accuracy: 70% → 90%
- 💡 Provide fix suggestions: 0% → 70% of cases
- 🔍 Enable semantic search: New capability
- 📊 Reduce manual effort: 50% reduction

---

## 🚀 **Quick Start Guide**

### **Step 1: Train Issue Classifier**
```bash
cd backend
python ml/train_classifier.py --model xgboost --data ../data/processed/warranty_with_predictions.parquet
```

### **Step 2: Fine-tune BERT**
```bash
python ml/train_bert.py --model bert-base-uncased --epochs 3 --batch-size 16
```

### **Step 3: Train Fix Predictor**
```bash
python ml/train_fix_predictor.py --model t5-base --data resolved_issues.csv
```

### **Step 4: Integrate with API**
```python
# In api/main.py
from ml.bert_classifier import BERTIssueClassifier
from ml.fix_predictor import RAGFixPredictor

bert_model = BERTIssueClassifier.load('models/bert_classifier')
fix_predictor = RAGFixPredictor.load('models/fix_predictor')
```

---

## 📚 **Resources & References**

### **Papers**
- BERT: "Attention is All You Need" (Vaswani et al., 2017)
- RoBERTa: "A Robustly Optimized BERT Pretraining Approach" (Liu et al., 2019)
- T5: "Exploring the Limits of Transfer Learning" (Raffel et al., 2020)
- RAG: "Retrieval-Augmented Generation" (Lewis et al., 2020)

### **Tutorials**
- Hugging Face Transformers: https://huggingface.co/docs/transformers
- Fine-tuning BERT: https://huggingface.co/course
- Text Classification: https://scikit-learn.org/stable/tutorial/text_analytics

### **Pre-trained Models**
- BERT models: https://huggingface.co/bert-base-uncased
- T5 models: https://huggingface.co/t5-base
- Domain-specific: https://huggingface.co/models

---

## ✅ **Summary**

This plan provides a comprehensive roadmap for enhancing the warranty analytics system with:

1. **Issue Type Classifier**: 85%+ accuracy, confidence scores
2. **BERT/Transformers**: Semantic understanding, 90%+ accuracy
3. **Fix Prediction**: Automated suggestions, RAG approach

**Total Timeline**: 8-10 months  
**Team Size**: 2-3 ML engineers  
**Budget**: $50K-100K (compute + resources)  

**ROI**: 50% reduction in manual effort, 20% faster resolution times, improved customer satisfaction

---

**Ready to transform warranty analytics with state-of-the-art ML!** 🚀
