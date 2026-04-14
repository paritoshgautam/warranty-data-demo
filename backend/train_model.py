"""
Training Script - Run ML Pipeline Locally
Execute this script to train the warranty clustering model
NO Azure dependencies - all local
"""
import argparse
import logging
from pathlib import Path
from ml.pipeline import WarrantyMLPipeline

def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('training.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Train Warranty ML Model Locally')
    parser.add_argument(
        '--data',
        type=str,
        default='data/raw/warranty_data.parquet',
        help='Path to input data file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/warranty_with_predictions.parquet',
        help='Path to output file'
    )
    parser.add_argument(
        '--models-dir',
        type=str,
        default='data/models',
        help='Directory to save trained models'
    )
    parser.add_argument(
        '--n-clusters',
        type=int,
        default=50,
        help='Number of clusters for K-means'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--advanced-nlp',
        action='store_true',
        default=True,
        help='Enable advanced NLP (spaCy, sentiment analysis)'
    )
    parser.add_argument(
        '--no-advanced-nlp',
        dest='advanced_nlp',
        action='store_false',
        help='Disable advanced NLP processing'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("WARRANTY ML TRAINING - LOCAL EXECUTION")
    logger.info("=" * 60)
    logger.info(f"Input Data: {args.data}")
    logger.info(f"Output Data: {args.output}")
    logger.info(f"Models Directory: {args.models_dir}")
    logger.info(f"Number of Clusters: {args.n_clusters}")
    logger.info("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = WarrantyMLPipeline(
            data_path=args.data,
            models_dir=args.models_dir
        )
        pipeline.n_clusters = args.n_clusters
        pipeline.use_advanced_nlp = args.advanced_nlp
        
        if args.advanced_nlp:
            logger.info("[OK] Advanced NLP enabled (spaCy, sentiment analysis)")
        else:
            logger.info("[SKIP] Advanced NLP disabled")
        
        # Run training
        logger.info("Starting training pipeline...")
        df_processed = pipeline.run_full_pipeline(save_output=True)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Total Records Processed: {len(df_processed):,}")
        logger.info(f"Clusters Created: {df_processed['cluster_id'].nunique()}")
        logger.info(f"Unique Categories: {df_processed['category_rule_based'].nunique()}")
        
        logger.info("\nTop 10 Issue Categories:")
        for i, (category, count) in enumerate(df_processed['rca_cluster_label_final'].value_counts().head(10).items(), 1):
            logger.info(f"  {i}. {category}: {count:,} issues")
        
        logger.info("\nAssignment Status:")
        for status, count in df_processed['assignment_status'].value_counts().items():
            logger.info(f"  {status}: {count:,} ({count/len(df_processed)*100:.1f}%)")
        
        logger.info("\nResolution Status:")
        for status, count in df_processed['resolution_status'].value_counts().items():
            logger.info(f"  {status}: {count:,} ({count/len(df_processed)*100:.1f}%)")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"[SUCCESS] Processed data saved to: {args.output}")
        logger.info(f"[SUCCESS] Models saved to: {args.models_dir}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
