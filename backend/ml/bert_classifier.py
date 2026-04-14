"""
BERT-based Issue Type Classifier
Uses pre-trained BERT models for semantic understanding of warranty issues
"""
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    BertTokenizer, BertForSequenceClassification,
    DistilBertTokenizer, DistilBertForSequenceClassification,
    Trainer, TrainingArguments,
    EarlyStoppingCallback
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix
)
from pathlib import Path
import logging
from typing import Dict, Tuple, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class WarrantyIssueDataset(Dataset):
    """PyTorch Dataset for warranty issues"""
    
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class BERTIssueClassifier:
    """
    BERT-based classifier for warranty issue categorization
    Supports: bert-base-uncased, distilbert-base-uncased
    """
    
    def __init__(
        self,
        model_name='distilbert-base-uncased',
        num_labels=10,
        max_length=512,
        device=None
    ):
        """
        Initialize BERT classifier
        
        Args:
            model_name: 'bert-base-uncased' or 'distilbert-base-uncased'
            num_labels: Number of categories
            max_length: Maximum sequence length
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        self.model_name = model_name
        self.num_labels = num_labels
        self.max_length = max_length
        
        # Auto-detect device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        logger.info(f"Using device: {self.device}")
        
        # Initialize tokenizer and model
        if 'distilbert' in model_name.lower():
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
            self.model = DistilBertForSequenceClassification.from_pretrained(
                model_name,
                num_labels=num_labels
            )
        else:
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertForSequenceClassification.from_pretrained(
                model_name,
                num_labels=num_labels
            )
        
        self.model.to(self.device)
        
        self.label_encoder = None
        self.training_history = {}
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[List[str], np.ndarray, List[str]]:
        """
        Prepare texts and labels from dataframe
        
        Args:
            df: DataFrame with 'combined_text' and 'category_rule_based'
            
        Returns:
            texts: List of text strings
            labels: Encoded label array
            categories: List of category names
        """
        logger.info("Preparing training data...")
        
        # Filter out 'Other' category
        df_filtered = df[df['category_rule_based'] != 'Other'].copy()
        
        logger.info(f"Total samples: {len(df_filtered)}")
        logger.info(f"Categories: {df_filtered['category_rule_based'].nunique()}")
        
        # Prepare texts
        texts = df_filtered['combined_text'].fillna('').astype(str).tolist()
        
        # Encode labels
        if self.label_encoder is None:
            self.label_encoder = LabelEncoder()
            labels = self.label_encoder.fit_transform(df_filtered['category_rule_based'])
        else:
            labels = self.label_encoder.transform(df_filtered['category_rule_based'])
        
        categories = self.label_encoder.classes_.tolist()
        
        # Update num_labels if needed
        if len(categories) != self.num_labels:
            logger.warning(f"Updating num_labels from {self.num_labels} to {len(categories)}")
            self.num_labels = len(categories)
        
        logger.info(f"Number of categories: {len(categories)}")
        
        return texts, labels, categories
    
    def compute_metrics(self, pred):
        """Compute metrics for evaluation"""
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, preds, average='weighted'
        )
        acc = accuracy_score(labels, preds)
        
        return {
            'accuracy': acc,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
    
    def train(
        self,
        df: pd.DataFrame,
        output_dir='data/models/bert_classifier',
        num_epochs=3,
        batch_size=16,
        learning_rate=2e-5,
        warmup_steps=500,
        weight_decay=0.01,
        test_size=0.2,
        val_size=0.1
    ):
        """
        Fine-tune BERT on warranty data
        
        Args:
            df: Training dataframe
            output_dir: Directory to save model
            num_epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate
            warmup_steps: Warmup steps for scheduler
            weight_decay: Weight decay for regularization
            test_size: Proportion for test set
            val_size: Proportion for validation set
        """
        logger.info("=" * 60)
        logger.info(f"Fine-tuning {self.model_name.upper()}")
        logger.info("=" * 60)
        
        # Prepare data
        texts, labels, categories = self.prepare_data(df)
        
        # Split data
        texts_train, texts_temp, labels_train, labels_temp = train_test_split(
            texts, labels, test_size=(test_size + val_size),
            random_state=42, stratify=labels
        )
        
        val_ratio = val_size / (test_size + val_size)
        texts_val, texts_test, labels_val, labels_test = train_test_split(
            texts_temp, labels_temp, test_size=(1 - val_ratio),
            random_state=42, stratify=labels_temp
        )
        
        logger.info(f"\nData split:")
        logger.info(f"  Training: {len(texts_train)} samples")
        logger.info(f"  Validation: {len(texts_val)} samples")
        logger.info(f"  Test: {len(texts_test)} samples")
        
        # Create datasets
        train_dataset = WarrantyIssueDataset(
            texts_train, labels_train, self.tokenizer, self.max_length
        )
        val_dataset = WarrantyIssueDataset(
            texts_val, labels_val, self.tokenizer, self.max_length
        )
        test_dataset = WarrantyIssueDataset(
            texts_test, labels_test, self.tokenizer, self.max_length
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size * 2,
            warmup_steps=warmup_steps,
            weight_decay=weight_decay,
            learning_rate=learning_rate,
            logging_dir=f'{output_dir}/logs',
            logging_steps=100,
            eval_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='f1',
            greater_is_better=True,
            save_total_limit=2,
            report_to='none',  # Disable wandb/tensorboard
            fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
        )
        
        # Train
        logger.info(f"\nStarting training for {num_epochs} epochs...")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Learning rate: {learning_rate}")
        logger.info(f"Device: {self.device}")
        
        train_result = trainer.train()
        
        # Evaluate on test set
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATION ON TEST SET")
        logger.info("=" * 60)
        
        test_results = trainer.evaluate(test_dataset)
        
        logger.info(f"\nTest Accuracy: {test_results['eval_accuracy']:.4f} ({test_results['eval_accuracy']*100:.2f}%)")
        logger.info(f"Test F1 Score: {test_results['eval_f1']:.4f}")
        logger.info(f"Test Precision: {test_results['eval_precision']:.4f}")
        logger.info(f"Test Recall: {test_results['eval_recall']:.4f}")
        
        # Detailed evaluation
        self.detailed_evaluation(test_dataset, categories)
        
        # Store training history
        self.training_history = {
            'model_name': self.model_name,
            'test_accuracy': test_results['eval_accuracy'],
            'test_f1': test_results['eval_f1'],
            'test_precision': test_results['eval_precision'],
            'test_recall': test_results['eval_recall'],
            'num_samples': len(texts),
            'num_categories': len(categories),
            'categories': categories,
            'num_epochs': num_epochs,
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        
        return self.training_history
    
    def detailed_evaluation(self, test_dataset, categories):
        """Detailed evaluation with classification report"""
        self.model.eval()
        
        all_preds = []
        all_labels = []
        
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
        
        with torch.no_grad():
            for batch in test_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # Classification report
        logger.info("\n" + "=" * 60)
        logger.info("CLASSIFICATION REPORT")
        logger.info("=" * 60)
        
        report = classification_report(
            all_labels, all_preds,
            target_names=categories,
            digits=3
        )
        logger.info("\n" + report)
        
        # Top-3 accuracy
        top3_correct = 0
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
        
        with torch.no_grad():
            for batch in test_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1)
                top3_preds = torch.topk(probs, k=3, dim=1).indices
                
                for i, label in enumerate(labels):
                    if label in top3_preds[i]:
                        top3_correct += 1
        
        top3_acc = top3_correct / len(test_dataset)
        logger.info(f"\nTop-3 Accuracy: {top3_acc:.4f} ({top3_acc*100:.2f}%)")
    
    def predict(self, texts: List[str]) -> np.ndarray:
        """Predict categories for new texts"""
        self.model.eval()
        
        dataset = WarrantyIssueDataset(
            texts, [0] * len(texts), self.tokenizer, self.max_length
        )
        loader = DataLoader(dataset, batch_size=32, shuffle=False)
        
        all_preds = []
        
        with torch.no_grad():
            for batch in loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                outputs = self.model(input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                
                all_preds.extend(preds.cpu().numpy())
        
        return self.label_encoder.inverse_transform(all_preds)
    
    def predict_proba(self, texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict probabilities for new texts
        
        Returns:
            categories: Predicted categories
            probabilities: Confidence scores
        """
        self.model.eval()
        
        dataset = WarrantyIssueDataset(
            texts, [0] * len(texts), self.tokenizer, self.max_length
        )
        loader = DataLoader(dataset, batch_size=32, shuffle=False)
        
        all_probs = []
        
        with torch.no_grad():
            for batch in loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                outputs = self.model(input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1)
                
                all_probs.extend(probs.cpu().numpy())
        
        all_probs = np.array(all_probs)
        pred_indices = np.argmax(all_probs, axis=1)
        confidences = np.max(all_probs, axis=1)
        
        categories = self.label_encoder.inverse_transform(pred_indices)
        
        return categories, confidences
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Extract BERT embeddings for similarity search
        
        Returns:
            embeddings: [CLS] token embeddings
        """
        self.model.eval()
        
        dataset = WarrantyIssueDataset(
            texts, [0] * len(texts), self.tokenizer, self.max_length
        )
        loader = DataLoader(dataset, batch_size=32, shuffle=False)
        
        all_embeddings = []
        
        with torch.no_grad():
            for batch in loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                # Get hidden states
                outputs = self.model.bert(input_ids, attention_mask=attention_mask)
                # Use [CLS] token embedding
                cls_embeddings = outputs.last_hidden_state[:, 0, :]
                
                all_embeddings.extend(cls_embeddings.cpu().numpy())
        
        return np.array(all_embeddings)
    
    def save(self, save_dir='data/models/bert_classifier'):
        """Save model, tokenizer, and label encoder"""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save model and tokenizer
        model_path = save_path / f'bert_model_{timestamp}'
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(model_path)
        logger.info(f"Saved model to {model_path}")
        
        # Save label encoder
        import joblib
        encoder_file = save_path / f'bert_label_encoder_{timestamp}.pkl'
        joblib.dump(self.label_encoder, encoder_file)
        logger.info(f"Saved label encoder to {encoder_file}")
        
        # Save training history
        history_file = save_path / f'bert_history_{timestamp}.json'
        with open(history_file, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        logger.info(f"Saved training history to {history_file}")
        
        # Save latest model info
        latest_file = save_path / 'bert_classifier_latest.json'
        with open(latest_file, 'w') as f:
            json.dump({
                'model_path': str(model_path),
                'label_encoder': str(encoder_file),
                'timestamp': timestamp,
                'model_name': self.model_name
            }, f, indent=2)
        logger.info(f"Saved latest model info to {latest_file}")
    
    @classmethod
    def load(cls, load_dir='data/models/bert_classifier'):
        """Load saved model"""
        import joblib
        
        load_path = Path(load_dir)
        
        # Load latest model info
        latest_file = load_path / 'bert_classifier_latest.json'
        if not latest_file.exists():
            raise FileNotFoundError(f"No saved model found in {load_dir}")
        
        with open(latest_file, 'r') as f:
            info = json.load(f)
        
        model_path = Path(info['model_path'])
        encoder_file = Path(info['label_encoder'])
        model_name = info['model_name']
        
        # Load label encoder first to get num_labels
        label_encoder = joblib.load(encoder_file)
        num_labels = len(label_encoder.classes_)
        
        # Create instance
        classifier = cls(model_name=model_name, num_labels=num_labels)
        
        # Load model and tokenizer
        if 'distilbert' in model_name.lower():
            classifier.model = DistilBertForSequenceClassification.from_pretrained(model_path)
            classifier.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        else:
            classifier.model = BertForSequenceClassification.from_pretrained(model_path)
            classifier.tokenizer = BertTokenizer.from_pretrained(model_path)
        
        classifier.model.to(classifier.device)
        classifier.label_encoder = label_encoder
        
        logger.info(f"Loaded model from {model_path}")
        
        return classifier
