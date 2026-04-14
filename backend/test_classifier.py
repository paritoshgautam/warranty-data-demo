"""
Test Script for Issue Type Classifier
Test predictions on new issues
"""
import pandas as pd
from ml.issue_classifier import IssueTypeClassifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_classifier():
    """Test the trained classifier"""
    
    logger.info("=" * 80)
    logger.info("TESTING ISSUE TYPE CLASSIFIER")
    logger.info("=" * 80)
    
    # Load trained model
    logger.info("\nLoading trained model...")
    classifier = IssueTypeClassifier.load()
    logger.info("✓ Model loaded successfully")
    
    # Test cases
    test_issues = [
        {
            'description': 'Customer cannot activate Voice Recognition feature in the infotainment system',
            'expected': 'Infotainment & Connectivity'
        },
        {
            'description': 'ETM sending additional NM_ALIVE messages during network management stress test causing delays',
            'expected': 'Network Management & Bus Communication'
        },
        {
            'description': 'Adaptive cruise control not maintaining safe distance from vehicle ahead',
            'expected': 'ADAS & Safety Systems'
        },
        {
            'description': 'Engine misfiring at high RPM with DTC P0300 stored',
            'expected': 'Powertrain & Engine'
        },
        {
            'description': 'Driver door lock not responding to key fob unlock command',
            'expected': 'Body & Exterior'
        },
        {
            'description': 'Speedometer showing incorrect speed reading',
            'expected': 'IPC & Instrument Cluster'
        },
        {
            'description': 'Headlight not turning on when switch activated',
            'expected': 'Electrical & Lighting'
        },
        {
            'description': 'Brake pedal feels spongy and requires more pressure',
            'expected': 'Chassis & Suspension'
        },
        {
            'description': 'Climate control not maintaining set temperature',
            'expected': 'Interior & Comfort'
        },
        {
            'description': 'BCM not responding to configuration changes',
            'expected': 'BCM & Body Control'
        }
    ]
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST PREDICTIONS")
    logger.info("=" * 80)
    
    correct = 0
    total = len(test_issues)
    
    for i, test in enumerate(test_issues, 1):
        description = test['description']
        expected = test['expected']
        
        # Predict
        predicted, confidence = classifier.predict_proba([description])
        predicted_category = predicted[0]
        confidence_score = confidence[0]
        
        is_correct = predicted_category == expected
        if is_correct:
            correct += 1
            status = "✓"
        else:
            status = "✗"
        
        logger.info(f"\n{status} Test {i}:")
        logger.info(f"  Description: {description[:80]}...")
        logger.info(f"  Expected: {expected}")
        logger.info(f"  Predicted: {predicted_category}")
        logger.info(f"  Confidence: {confidence_score:.2%}")
        logger.info(f"  Result: {'CORRECT' if is_correct else 'WRONG'}")
    
    accuracy = correct / total
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS")
    logger.info("=" * 80)
    logger.info(f"Correct: {correct}/{total}")
    logger.info(f"Accuracy: {accuracy:.2%}")
    logger.info("=" * 80)
    
    # Test on actual data
    logger.info("\n" + "=" * 80)
    logger.info("TESTING ON ACTUAL ISSUES")
    logger.info("=" * 80)
    
    df = pd.read_parquet('../data/processed/warranty_with_predictions.parquet')
    
    # Sample 10 random issues
    sample = df.sample(10, random_state=42)
    
    for idx, row in sample.iterrows():
        description = row['combined_text']
        actual_category = row['category_rule_based']
        
        predicted, confidence = classifier.predict_proba([description])
        predicted_category = predicted[0]
        confidence_score = confidence[0]
        
        is_correct = predicted_category == actual_category
        status = "✓" if is_correct else "✗"
        
        logger.info(f"\n{status} Issue: {row['issue_number']}")
        logger.info(f"  Description: {row['issue_description'][:80]}...")
        logger.info(f"  Actual: {actual_category}")
        logger.info(f"  Predicted: {predicted_category}")
        logger.info(f"  Confidence: {confidence_score:.2%}")
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING COMPLETE!")
    logger.info("=" * 80)

if __name__ == "__main__":
    test_classifier()
