"""
Issue Type Classifier - ML-based categorization
Trains supervised models to predict issue categories from descriptions
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, f1_score, precision_recall_fscore_support
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb
import joblib
from pathlib import Path
import logging
from typing import Dict, Tuple, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class IssueTypeClassifier:
    """
    Supervised classifier for issue categorization
    Supports multiple algorithms: LogisticRegression, RandomForest, XGBoost, LightGBM
    """
    
    def __init__(self, model_type='xgboost', max_features=1000):
        """
        Initialize classifier
        
        Args:
            model_type: 'logistic', 'random_forest', 'xgboost', 'lightgbm'
            max_features: Maximum TF-IDF features
        """
        self.model_type = model_type
        self.max_features = max_features
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.feature_names = None
        self.training_history = {}
        
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare features and labels from dataframe
        
        Args:
            df: DataFrame with 'combined_text' and 'category_rule_based'
            
        Returns:
            X: Feature matrix
            y: Label array
            categories: List of category names
        """
        logger.info("Preparing training data...")
        
        # Filter out 'Other' category (too generic)
        df_filtered = df[df['category_rule_based'] != 'Other'].copy()
        
        logger.info(f"Total samples: {len(df_filtered)}")
        logger.info(f"Categories: {df_filtered['category_rule_based'].nunique()}")
        
        # Check for class imbalance
        category_counts = df_filtered['category_rule_based'].value_counts()
        logger.info("\nCategory distribution:")
        for cat, count in category_counts.items():
            logger.info(f"  {cat}: {count} ({count/len(df_filtered)*100:.1f}%)")
        
        # Prepare text features
        texts = df_filtered['combined_text'].fillna('').astype(str)
        
        # Initialize or use existing vectorizer
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=2,  # Ignore terms that appear in less than 2 documents
                max_df=0.95,  # Ignore terms that appear in more than 95% of documents
                stop_words='english',
                sublinear_tf=True  # Use sublinear term frequency scaling
            )
            X = self.vectorizer.fit_transform(texts)
            self.feature_names = self.vectorizer.get_feature_names_out()
        else:
            X = self.vectorizer.transform(texts)
        
        # Encode labels
        if self.label_encoder is None:
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(df_filtered['category_rule_based'])
        else:
            y = self.label_encoder.transform(df_filtered['category_rule_based'])
        
        categories = self.label_encoder.classes_.tolist()
        
        logger.info(f"Feature matrix shape: {X.shape}")
        logger.info(f"Number of categories: {len(categories)}")
        
        return X, y, categories
    
    def create_model(self, num_classes: int):
        """Create model based on model_type"""
        if self.model_type == 'logistic':
            return LogisticRegression(
                max_iter=1000,
                multi_class='multinomial',
                solver='lbfgs',
                class_weight='balanced',
                random_state=42
            )
        
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        
        elif self.model_type == 'xgboost':
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='multi:softmax',
                num_class=num_classes,
                eval_metric='mlogloss',
                random_state=42,
                n_jobs=-1
            )
        
        elif self.model_type == 'lightgbm':
            return lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                num_leaves=31,
                objective='multiclass',
                num_class=num_classes,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")
    
    def train(self, df: pd.DataFrame, test_size=0.2, val_size=0.1):
        """
        Train the classifier
        
        Args:
            df: Training dataframe
            test_size: Proportion for test set
            val_size: Proportion for validation set
        """
        logger.info("=" * 60)
        logger.info(f"Training {self.model_type.upper()} classifier")
        logger.info("=" * 60)
        
        # Prepare data
        X, y, categories = self.prepare_data(df)
        
        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=(test_size + val_size), 
            random_state=42, stratify=y
        )
        
        val_ratio = val_size / (test_size + val_size)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=(1 - val_ratio),
            random_state=42, stratify=y_temp
        )
        
        logger.info(f"\nData split:")
        logger.info(f"  Training: {X_train.shape[0]} samples")
        logger.info(f"  Validation: {X_val.shape[0]} samples")
        logger.info(f"  Test: {X_test.shape[0]} samples")
        
        # Create and train model
        self.model = self.create_model(num_classes=len(categories))
        
        logger.info(f"\nTraining {self.model_type} model...")
        
        if self.model_type in ['xgboost', 'lightgbm']:
            # Train with validation set for early stopping
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)
        
        # Evaluate on all sets
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 60)
        
        train_acc = self.evaluate(X_train, y_train, "Training")
        val_acc = self.evaluate(X_val, y_val, "Validation")
        test_acc = self.evaluate(X_test, y_test, "Test")
        
        # Detailed test set evaluation
        self.detailed_evaluation(X_test, y_test, categories)
        
        # Store training history
        self.training_history = {
            'model_type': self.model_type,
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'test_accuracy': test_acc,
            'num_samples': len(df),
            'num_features': X.shape[1],
            'num_categories': len(categories),
            'categories': categories,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        
        return self.training_history
    
    def evaluate(self, X, y, dataset_name="Test") -> float:
        """Evaluate model on a dataset"""
        y_pred = self.model.predict(X)
        accuracy = accuracy_score(y, y_pred)
        
        logger.info(f"\n{dataset_name} Set Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        return accuracy
    
    def detailed_evaluation(self, X_test, y_test, categories):
        """Detailed evaluation with classification report and confusion matrix"""
        y_pred = self.model.predict(X_test)
        
        # Classification report
        logger.info("\n" + "=" * 60)
        logger.info("CLASSIFICATION REPORT")
        logger.info("=" * 60)
        
        report = classification_report(
            y_test, y_pred,
            target_names=categories,
            digits=3
        )
        logger.info("\n" + report)
        
        # Per-category metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average=None
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("PER-CATEGORY PERFORMANCE")
        logger.info("=" * 60)
        
        metrics_df = pd.DataFrame({
            'Category': categories,
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1,
            'Support': support
        }).sort_values('F1-Score', ascending=False)
        
        logger.info("\n" + metrics_df.to_string(index=False))
        
        # Top-3 accuracy
        if hasattr(self.model, 'predict_proba'):
            y_proba = self.model.predict_proba(X_test)
            top3_pred = np.argsort(y_proba, axis=1)[:, -3:]
            top3_acc = np.mean([y_test[i] in top3_pred[i] for i in range(len(y_test))])
            logger.info(f"\nTop-3 Accuracy: {top3_acc:.4f} ({top3_acc*100:.2f}%)")
        
        # Confusion matrix (show top confusions)
        cm = confusion_matrix(y_test, y_pred)
        self.show_top_confusions(cm, categories)
    
    def show_top_confusions(self, cm, categories, top_n=5):
        """Show top misclassification pairs"""
        logger.info("\n" + "=" * 60)
        logger.info(f"TOP {top_n} MISCLASSIFICATIONS")
        logger.info("=" * 60)
        
        confusions = []
        for i in range(len(categories)):
            for j in range(len(categories)):
                if i != j and cm[i, j] > 0:
                    confusions.append({
                        'True': categories[i],
                        'Predicted': categories[j],
                        'Count': cm[i, j]
                    })
        
        confusions_df = pd.DataFrame(confusions).sort_values('Count', ascending=False).head(top_n)
        
        if len(confusions_df) > 0:
            logger.info("\n" + confusions_df.to_string(index=False))
        else:
            logger.info("\nNo misclassifications!")
    
    def predict(self, texts: List[str]) -> np.ndarray:
        """Predict categories for new texts"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X = self.vectorizer.transform(texts)
        y_pred = self.model.predict(X)
        
        return self.label_encoder.inverse_transform(y_pred)
    
    def predict_proba(self, texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict probabilities for new texts
        
        Returns:
            categories: Predicted categories
            probabilities: Confidence scores
        """
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError(f"{self.model_type} does not support probability prediction")
        
        X = self.vectorizer.transform(texts)
        y_proba = self.model.predict_proba(X)
        y_pred = np.argmax(y_proba, axis=1)
        
        categories = self.label_encoder.inverse_transform(y_pred)
        confidences = np.max(y_proba, axis=1)
        
        return categories, confidences
    
    def get_feature_importance(self, top_n=20) -> pd.DataFrame:
        """Get top important features for the model"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if hasattr(self.model, 'feature_importances_'):
            # Tree-based models
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            # Linear models
            importances = np.abs(self.model.coef_).mean(axis=0)
        else:
            logger.warning(f"{self.model_type} does not support feature importance")
            return None
        
        feature_importance = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': importances
        }).sort_values('Importance', ascending=False).head(top_n)
        
        return feature_importance
    
    def save(self, models_dir: str = 'data/models'):
        """Save model, vectorizer, and label encoder"""
        models_path = Path(models_dir)
        models_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save model
        model_file = models_path / f'issue_classifier_{self.model_type}_{timestamp}.pkl'
        joblib.dump(self.model, model_file)
        logger.info(f"Saved model to {model_file}")
        
        # Save vectorizer
        vectorizer_file = models_path / f'issue_vectorizer_{timestamp}.pkl'
        joblib.dump(self.vectorizer, vectorizer_file)
        logger.info(f"Saved vectorizer to {vectorizer_file}")
        
        # Save label encoder
        encoder_file = models_path / f'issue_label_encoder_{timestamp}.pkl'
        joblib.dump(self.label_encoder, encoder_file)
        logger.info(f"Saved label encoder to {encoder_file}")
        
        # Save training history
        history_file = models_path / f'issue_classifier_history_{timestamp}.json'
        with open(history_file, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        logger.info(f"Saved training history to {history_file}")
        
        # Save latest model paths
        latest_file = models_path / 'issue_classifier_latest.json'
        with open(latest_file, 'w') as f:
            json.dump({
                'model': str(model_file),
                'vectorizer': str(vectorizer_file),
                'label_encoder': str(encoder_file),
                'timestamp': timestamp,
                'model_type': self.model_type
            }, f, indent=2)
        logger.info(f"Saved latest model info to {latest_file}")
    
    @classmethod
    def load(cls, models_dir: str = 'data/models', timestamp: str = None):
        """Load saved model"""
        models_path = Path(models_dir)
        
        if timestamp is None:
            # Load latest
            latest_file = models_path / 'issue_classifier_latest.json'
            if not latest_file.exists():
                raise FileNotFoundError(f"No saved model found in {models_dir}")
            
            with open(latest_file, 'r') as f:
                info = json.load(f)
            
            model_file = Path(info['model'])
            vectorizer_file = Path(info['vectorizer'])
            encoder_file = Path(info['label_encoder'])
            model_type = info['model_type']
        else:
            # Load specific timestamp
            model_file = models_path / f'issue_classifier_{timestamp}.pkl'
            vectorizer_file = models_path / f'issue_vectorizer_{timestamp}.pkl'
            encoder_file = models_path / f'issue_label_encoder_{timestamp}.pkl'
            model_type = 'xgboost'  # Default
        
        # Create instance
        classifier = cls(model_type=model_type)
        
        # Load components
        classifier.model = joblib.load(model_file)
        classifier.vectorizer = joblib.load(vectorizer_file)
        classifier.label_encoder = joblib.load(encoder_file)
        classifier.feature_names = classifier.vectorizer.get_feature_names_out()
        
        logger.info(f"Loaded model from {model_file}")
        
        return classifier
