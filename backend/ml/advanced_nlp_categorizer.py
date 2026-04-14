"""
Advanced NLP Categorization using spaCy
- Named Entity Recognition (NER)
- Dependency parsing for subject-verb-object extraction
- Sentiment analysis for severity scoring
"""
import pandas as pd
import numpy as np
import spacy
from textblob import TextBlob
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedNLPCategorizer:
    """
    Advanced NLP categorization using:
    1. spaCy for NER and dependency parsing
    2. TextBlob for sentiment analysis
    3. Subject-Verb-Object extraction for better understanding
    """
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise
        
        # Problem severity mapping
        self.severity_keywords = {
            'critical': ['critical', 'severe', 'dangerous', 'unsafe', 'hazard', 'risk'],
            'high': ['major', 'significant', 'serious', 'important', 'urgent'],
            'medium': ['moderate', 'noticeable', 'intermittent', 'occasional'],
            'low': ['minor', 'cosmetic', 'trivial', 'slight']
        }
        
        # Action-object patterns for better categorization
        self.action_patterns = {
            'activation': ['activate', 'enable', 'turn on', 'start', 'initiate'],
            'deactivation': ['deactivate', 'disable', 'turn off', 'stop', 'shut down'],
            'display': ['display', 'show', 'present', 'render', 'appear'],
            'update': ['update', 'refresh', 'sync', 'synchronize'],
            'connection': ['connect', 'pair', 'link', 'establish'],
            'recognition': ['recognize', 'detect', 'identify', 'sense'],
            'response': ['respond', 'react', 'answer', 'reply']
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities using spaCy NER
        Returns entities grouped by type
        """
        if pd.isna(text) or not text:
            return {}
        
        doc = self.nlp(str(text))
        entities = {}
        
        for ent in doc.ents:
            entity_type = ent.label_
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].append(ent.text)
        
        return entities
    
    def extract_subject_verb_object(self, text: str) -> List[Dict[str, str]]:
        """
        Extract subject-verb-object triples using dependency parsing
        This helps understand what action is being performed on what object
        """
        if pd.isna(text) or not text:
            return []
        
        doc = self.nlp(str(text))
        svo_triples = []
        
        for token in doc:
            # Find verbs
            if token.pos_ == "VERB":
                # Find subject
                subject = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subject = child.text
                        break
                
                # Find object
                obj = None
                for child in token.children:
                    if child.dep_ in ("dobj", "pobj", "attr"):
                        obj = child.text
                        break
                
                # Find negation
                negation = any(child.dep_ == "neg" for child in token.children)
                
                if subject or obj:
                    svo_triples.append({
                        'subject': subject or 'unknown',
                        'verb': token.text,
                        'object': obj or 'unknown',
                        'negation': negation,
                        'full_phrase': f"{subject or ''} {token.text} {obj or ''}".strip()
                    })
        
        return svo_triples
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment to determine issue severity
        Returns polarity (-1 to 1) and subjectivity (0 to 1)
        """
        if pd.isna(text) or not text:
            return {'polarity': 0.0, 'subjectivity': 0.0, 'severity_score': 0.5}
        
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Calculate severity score (0-1, where 1 is most severe)
        # Negative polarity indicates problems
        # High subjectivity might indicate user frustration
        severity_score = (abs(polarity) * 0.7 + subjectivity * 0.3)
        
        # Boost severity if critical keywords present
        text_lower = str(text).lower()
        for severity, keywords in self.severity_keywords.items():
            if any(kw in text_lower for kw in keywords):
                if severity == 'critical':
                    severity_score = min(1.0, severity_score + 0.3)
                elif severity == 'high':
                    severity_score = min(1.0, severity_score + 0.2)
                break
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'severity_score': severity_score
        }
    
    def classify_action_type(self, svo_triples: List[Dict]) -> Optional[str]:
        """
        Classify the type of action based on SVO triples
        """
        if not svo_triples:
            return None
        
        # Get all verbs
        verbs = [triple['verb'].lower() for triple in svo_triples]
        
        # Match against action patterns
        for action_type, action_verbs in self.action_patterns.items():
            if any(verb in action_verbs for verb in verbs):
                return action_type.title()
        
        return None
    
    def determine_severity_level(self, severity_score: float) -> str:
        """
        Convert severity score to categorical level
        """
        if severity_score >= 0.8:
            return 'Critical'
        elif severity_score >= 0.6:
            return 'High'
        elif severity_score >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def generate_advanced_issue_type(self, row: pd.Series) -> Dict[str, any]:
        """
        Generate advanced issue categorization using NLP
        Returns a dictionary with multiple categorization fields
        """
        # Combine descriptions
        description = row.get('issue_description', '')
        rca_description = row.get('rca_description', '')
        combined_text = f"{description} {rca_description}"
        
        # Extract entities
        entities = self.extract_entities(combined_text)
        
        # Extract SVO triples
        svo_triples = self.extract_subject_verb_object(combined_text)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(combined_text)
        
        # Classify action type
        action_type = self.classify_action_type(svo_triples)
        
        # Determine severity
        severity_level = self.determine_severity_level(sentiment['severity_score'])
        
        # Extract key components from entities
        products = entities.get('PRODUCT', [])
        orgs = entities.get('ORG', [])
        
        # Build issue summary from SVO
        issue_summary = None
        if svo_triples:
            # Get the first meaningful triple
            for triple in svo_triples:
                if triple['negation']:
                    issue_summary = f"Cannot {triple['verb']} {triple['object']}"
                    break
                elif triple['object'] != 'unknown':
                    issue_summary = f"{triple['verb'].title()} {triple['object']} Issue"
                    break
        
        return {
            'entities': entities,
            'svo_triples': svo_triples,
            'action_type': action_type,
            'sentiment_polarity': sentiment['polarity'],
            'sentiment_subjectivity': sentiment['subjectivity'],
            'severity_score': sentiment['severity_score'],
            'severity_level': severity_level,
            'issue_summary': issue_summary,
            'products_mentioned': products[:3] if products else [],
            'organizations_mentioned': orgs[:3] if orgs else []
        }
    
    def categorize_dataframe(self, df: pd.DataFrame, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Apply advanced NLP categorization to dataframe
        
        Args:
            df: Input dataframe
            sample_size: If provided, only process this many records (for testing)
        """
        logger.info("Applying advanced NLP categorization...")
        
        df = df.copy()
        
        # For large datasets, optionally sample
        if sample_size and len(df) > sample_size:
            logger.info(f"Processing sample of {sample_size} records")
            df_to_process = df.sample(n=sample_size, random_state=42)
        else:
            df_to_process = df
        
        # Initialize result columns
        df_to_process['action_type_nlp'] = None
        df_to_process['severity_score'] = 0.5
        df_to_process['severity_level'] = 'Medium'
        df_to_process['sentiment_polarity'] = 0.0
        df_to_process['issue_summary_nlp'] = None
        
        # Process each record
        for idx, row in df_to_process.iterrows():
            try:
                result = self.generate_advanced_issue_type(row)
                
                df.at[idx, 'action_type_nlp'] = result['action_type']
                df.at[idx, 'severity_score'] = result['severity_score']
                df.at[idx, 'severity_level'] = result['severity_level']
                df.at[idx, 'sentiment_polarity'] = result['sentiment_polarity']
                df.at[idx, 'issue_summary_nlp'] = result['issue_summary']
                
            except Exception as e:
                logger.warning(f"Error processing record {idx}: {e}")
                continue
        
        logger.info(f"Advanced NLP categorization complete")
        logger.info(f"  Severity levels: {df['severity_level'].value_counts().to_dict()}")
        logger.info(f"  Action types: {df['action_type_nlp'].value_counts().head(5).to_dict()}")
        
        return df


def test_advanced_nlp():
    """Test the advanced NLP categorizer"""
    print("=" * 80)
    print("TESTING ADVANCED NLP CATEGORIZATION")
    print("=" * 80)
    
    categorizer = AdvancedNLPCategorizer()
    
    # Test cases
    test_cases = [
        {
            'issue_description': 'Customer cannot activate Voice Recognition system',
            'rca_description': 'Voice recognition module fails to respond to user commands'
        },
        {
            'issue_description': 'Critical safety issue: Emergency brake system does not engage',
            'rca_description': 'Brake sensor malfunction causing system failure'
        },
        {
            'issue_description': 'Radio display shows incorrect navigation information',
            'rca_description': 'GPS data not updating properly'
        },
        {
            'issue_description': 'Minor cosmetic issue with dashboard trim alignment',
            'rca_description': 'Trim piece slightly misaligned during assembly'
        }
    ]
    
    df_test = pd.DataFrame(test_cases)
    
    print("\n📋 Test Results:\n")
    for idx, row in df_test.iterrows():
        print(f"  Test Case {idx + 1}:")
        print(f"    Description: {row['issue_description'][:60]}...")
        
        result = categorizer.generate_advanced_issue_type(row)
        
        print(f"    → Severity: {result['severity_level']} (score: {result['severity_score']:.2f})")
        print(f"    → Action Type: {result['action_type']}")
        print(f"    → Issue Summary: {result['issue_summary']}")
        print(f"    → Sentiment: {result['sentiment_polarity']:.2f}")
        
        if result['svo_triples']:
            print(f"    → SVO Triples:")
            for triple in result['svo_triples'][:2]:
                neg = " (negated)" if triple['negation'] else ""
                print(f"      - {triple['subject']} → {triple['verb']} → {triple['object']}{neg}")
        
        if result['entities']:
            print(f"    → Entities: {result['entities']}")
        
        print()


if __name__ == '__main__':
    test_advanced_nlp()
