"""
Training Script for Issue Type Classifier
Trains ML models to predict issue categories
"""
import argparse
import logging
import pandas as pd
from pathlib import Path
from ml.issue_classifier import IssueTypeClassifier

def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('classifier_training.log')
        ]
    )

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Train Issue Type Classifier'
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
        default='xgboost',
        choices=['logistic', 'random_forest', 'xgboost', 'lightgbm'],
        help='Model type to train'
    )
    parser.add_argument(
        '--max-features',
        type=int,
        default=1000,
        help='Maximum TF-IDF features'
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
        '--models-dir',
        type=str,
        default='data/models',
        help='Directory to save models'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--compare-all',
        action='store_true',
        help='Train and compare all model types'
    )
    
    return parser.parse_args()

def train_single_model(args, model_type):
    """Train a single model"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info(f"TRAINING {model_type.upper()} CLASSIFIER")
    logger.info("=" * 80)
    logger.info(f"Data: {args.data}")
    logger.info(f"Max Features: {args.max_features}")
    logger.info(f"Test Size: {args.test_size}")
    logger.info(f"Validation Size: {args.val_size}")
    logger.info("=" * 80)
    
    # Load data
    logger.info(f"\nLoading data from {args.data}...")
    df = pd.read_parquet(args.data)
    logger.info(f"Loaded {len(df):,} records")
    
    # Create classifier
    classifier = IssueTypeClassifier(
        model_type=model_type,
        max_features=args.max_features
    )
    
    # Train
    history = classifier.train(
        df,
        test_size=args.test_size,
        val_size=args.val_size
    )
    
    # Show feature importance
    logger.info("\n" + "=" * 80)
    logger.info("TOP 20 IMPORTANT FEATURES")
    logger.info("=" * 80)
    
    feature_importance = classifier.get_feature_importance(top_n=20)
    if feature_importance is not None:
        logger.info("\n" + feature_importance.to_string(index=False))
    
    # Save model
    logger.info("\n" + "=" * 80)
    logger.info("SAVING MODEL")
    logger.info("=" * 80)
    
    classifier.save(args.models_dir)
    
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"\nModel Type: {model_type}")
    logger.info(f"Test Accuracy: {history['test_accuracy']:.4f} ({history['test_accuracy']*100:.2f}%)")
    logger.info(f"Models saved to: {args.models_dir}")
    logger.info("=" * 80)
    
    return history

def compare_models(args):
    """Train and compare all model types"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("COMPARING ALL MODEL TYPES")
    logger.info("=" * 80)
    
    model_types = ['logistic', 'random_forest', 'xgboost', 'lightgbm']
    results = {}
    
    for model_type in model_types:
        try:
            history = train_single_model(args, model_type)
            results[model_type] = history
            logger.info(f"\n✓ {model_type}: {history['test_accuracy']:.4f}")
        except Exception as e:
            logger.error(f"\n✗ {model_type}: Failed - {e}")
            results[model_type] = None
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("MODEL COMPARISON SUMMARY")
    logger.info("=" * 80)
    
    comparison_df = pd.DataFrame([
        {
            'Model': model_type.title(),
            'Train Acc': f"{r['train_accuracy']:.4f}" if r else 'Failed',
            'Val Acc': f"{r['val_accuracy']:.4f}" if r else 'Failed',
            'Test Acc': f"{r['test_accuracy']:.4f}" if r else 'Failed',
            'Features': r['num_features'] if r else '-',
        }
        for model_type, r in results.items()
    ])
    
    logger.info("\n" + comparison_df.to_string(index=False))
    
    # Best model
    valid_results = {k: v for k, v in results.items() if v is not None}
    if valid_results:
        best_model = max(valid_results.items(), key=lambda x: x[1]['test_accuracy'])
        logger.info(f"\n🏆 Best Model: {best_model[0].upper()}")
        logger.info(f"   Test Accuracy: {best_model[1]['test_accuracy']:.4f} ({best_model[1]['test_accuracy']*100:.2f}%)")
    
    logger.info("\n" + "=" * 80)

def main():
    """Main training function"""
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.compare_all:
            compare_models(args)
        else:
            train_single_model(args, args.model)
        
        return 0
    
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
