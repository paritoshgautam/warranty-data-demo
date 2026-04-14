"""
Training Script for BERT Issue Type Classifier
Fine-tunes BERT/DistilBERT on warranty data
"""
import argparse
import logging
import pandas as pd
import torch
from pathlib import Path
from ml.bert_classifier import BERTIssueClassifier

def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bert_training.log')
        ]
    )

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Train BERT Issue Type Classifier'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='../data/processed/warranty_with_predictions.parquet',
        help='Path to processed data file'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='distilbert-base-uncased',
        choices=['bert-base-uncased', 'distilbert-base-uncased'],
        help='BERT model to use'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=16,
        help='Batch size for training'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=2e-5,
        help='Learning rate'
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=512,
        help='Maximum sequence length'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set proportion'
    )
    parser.add_argument(
        '--val-size',
        type=float,
        default=0.1,
        help='Validation set proportion'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/models/bert_classifier',
        help='Directory to save models'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        choices=['cuda', 'cpu'],
        help='Device to use (auto-detect if not specified)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()

def main():
    """Main training function"""
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 80)
        logger.info(f"TRAINING BERT CLASSIFIER")
        logger.info("=" * 80)
        logger.info(f"Model: {args.model}")
        logger.info(f"Data: {args.data}")
        logger.info(f"Epochs: {args.epochs}")
        logger.info(f"Batch Size: {args.batch_size}")
        logger.info(f"Learning Rate: {args.learning_rate}")
        logger.info(f"Max Length: {args.max_length}")
        
        # Check GPU availability
        if torch.cuda.is_available():
            logger.info(f"GPU Available: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            logger.info("GPU Not Available - Using CPU (training will be slower)")
            logger.warning("⚠️  BERT training on CPU can take 30-60 minutes!")
            logger.warning("⚠️  Consider using a smaller model or GPU for faster training")
        
        logger.info("=" * 80)
        
        # Load data
        logger.info(f"\nLoading data from {args.data}...")
        df = pd.read_parquet(args.data)
        logger.info(f"Loaded {len(df):,} records")
        
        # Create classifier
        logger.info(f"\nInitializing {args.model}...")
        classifier = BERTIssueClassifier(
            model_name=args.model,
            max_length=args.max_length,
            device=args.device
        )
        
        # Train
        history = classifier.train(
            df,
            output_dir=args.output_dir,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            test_size=args.test_size,
            val_size=args.val_size
        )
        
        # Save model
        logger.info("\n" + "=" * 80)
        logger.info("SAVING MODEL")
        logger.info("=" * 80)
        
        classifier.save(args.output_dir)
        
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"\nModel: {args.model}")
        logger.info(f"Test Accuracy: {history['test_accuracy']:.4f} ({history['test_accuracy']*100:.2f}%)")
        logger.info(f"Test F1 Score: {history['test_f1']:.4f}")
        logger.info(f"Models saved to: {args.output_dir}")
        logger.info("=" * 80)
        
        return 0
    
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
