"""
ML Pipeline - Local Training and Prediction
Complete pipeline for warranty issue clustering and categorization
NO Azure dependencies - all local processing
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import pickle
import logging
from typing import Tuple, Optional
from datetime import datetime
from ml.enhanced_categorization import EnhancedIssueCategorizer
from ml.advanced_nlp_categorizer import AdvancedNLPCategorizer

logger = logging.getLogger(__name__)

class WarrantyMLPipeline:
    """
    Complete ML pipeline for warranty data processing
    - Text preprocessing
    - TF-IDF vectorization
    - K-means clustering
    - Rule-based categorization
    - Model persistence
    """
    
    def __init__(self, data_path: str, models_dir: str = "data/models"):
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Models
        self.vectorizer = None
        self.scaler = None
        self.kmeans = None
        self.enhanced_categorizer = EnhancedIssueCategorizer()
        self.advanced_nlp_categorizer = AdvancedNLPCategorizer()
        
        # Configuration
        self.n_clusters = 50  # Optimal number found through elbow method
        self.random_state = 42
        self.use_advanced_nlp = True  # Enable/disable advanced NLP processing
        
    def load_data(self) -> pd.DataFrame:
        """Load raw warranty data"""
        logger.info(f"Loading data from {self.data_path}")
        
        if self.data_path.suffix == '.parquet':
            df = pd.read_parquet(self.data_path)
        elif self.data_path.suffix == '.csv':
            df = pd.read_csv(self.data_path)
        elif self.data_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        logger.info(f"Loaded {len(df)} records")
        return df
    
    def preprocess_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess text fields for clustering"""
        df = df.copy()
        
        # Map common column name variations to standard names
        column_mapping = {
            'Description': 'issue_description',
            'RCA: Description': 'rca_description',
            'ECU': 'ecu',
            'Affected Vehicle/Project: Model': 'affected_vehicleproject_model',
            'Model Year': 'model_year',
            'Issue Number': 'issue_number',
            'Issue Color Status': 'issue_color_status',
            'RCA: Solver Lead': 'rca_solver_lead',
            'Issue Status': 'issue_status',
            'Detection Date': 'detection_date',
            'PCA Identification: Description': 'pca_identification_description',
            'ICA: Description': 'ica_description'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df[new_name] = df[old_name]
        
        # Combine relevant text fields for clustering
        text_columns = ['issue_description', 'rca_description', 'pca_identification_description', 
                       'ica_description', 'ecu', 'affected_vehicleproject_model']
        
        # Create combined text field
        df['combined_text'] = ''
        for col in text_columns:
            if col in df.columns:
                df['combined_text'] += ' ' + df[col].fillna('').astype(str)
        
        # Clean text
        df['combined_text'] = df['combined_text'].str.lower()
        df['combined_text'] = df['combined_text'].str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
        df['combined_text'] = df['combined_text'].str.replace(r'\s+', ' ', regex=True)
        df['combined_text'] = df['combined_text'].str.strip()
        
        # Create assigned_flag from RCA: Solver Lead
        if 'rca_solver_lead' in df.columns:
            df['assigned_flag'] = df['rca_solver_lead'].apply(
                lambda x: 'Unassigned' if pd.isna(x) or str(x).strip() == '' else 'Assigned'
            )
        
        logger.info("Text preprocessing complete")
        return df
    
    def extract_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """Extract TF-IDF features from text"""
        logger.info("Extracting TF-IDF features...")
        
        # Initialize or use existing vectorizer
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=2,
                max_df=0.8,
                ngram_range=(1, 2),
                stop_words='english'
            )
            tfidf_matrix = self.vectorizer.fit_transform(df['combined_text'])
        else:
            tfidf_matrix = self.vectorizer.transform(df['combined_text'])
        
        # Convert to dense array
        features = tfidf_matrix.toarray()
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
            features = self.scaler.fit_transform(features)
        else:
            features = self.scaler.transform(features)
        
        logger.info(f"Extracted {features.shape[1]} features")
        return features, df
    
    def train_clustering(self, features: np.ndarray) -> np.ndarray:
        """Train K-means clustering model"""
        logger.info(f"Training K-means with {self.n_clusters} clusters...")
        
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        
        cluster_labels = self.kmeans.fit_predict(features)
        
        logger.info(f"Clustering complete. Inertia: {self.kmeans.inertia_:.2f}")
        return cluster_labels
    
    def generate_cluster_labels(self, df: pd.DataFrame, cluster_labels: np.ndarray) -> pd.DataFrame:
        """Generate human-readable cluster labels based on top keywords"""
        df = df.copy()
        df['cluster_id'] = cluster_labels
        
        cluster_names = {}
        
        for cluster_id in range(self.n_clusters):
            # Get documents in this cluster
            cluster_docs = df[df['cluster_id'] == cluster_id]['combined_text'].values
            
            if len(cluster_docs) == 0:
                cluster_names[cluster_id] = f"Cluster {cluster_id}"
                continue
            
            # Get top TF-IDF terms for this cluster
            cluster_tfidf = self.vectorizer.transform(cluster_docs)
            avg_tfidf = cluster_tfidf.mean(axis=0).A1
            top_indices = avg_tfidf.argsort()[-5:][::-1]
            top_terms = [self.vectorizer.get_feature_names_out()[i] for i in top_indices]
            
            # Create label from top terms
            label = ' '.join(top_terms[:3]).title()
            cluster_names[cluster_id] = label
        
        # Apply labels
        df['rca_cluster_label'] = df['cluster_id'].map(cluster_names)
        
        logger.info("Generated cluster labels")
        return df
    
    def apply_rule_based_categorization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply rule-based categorization using automotive keywords"""
        df = df.copy()
        
        # Define category rules (from original implementation)
        category_rules = {
            'ADAS & Safety Systems': [
                'adas', 'camera', 'radar', 'lidar', 'sensor', 'collision', 'blind spot',
                'lane', 'parking', 'cruise control', 'emergency brake', 'safety'
            ],
            'Infotainment & Connectivity': [
                'infotainment', 'display', 'screen', 'audio', 'bluetooth', 'usb',
                'navigation', 'gps', 'radio', 'speaker', 'connectivity', 'wifi',
                'uconnect', 'touchscreen', 'touch input', 'soft key', 'softkey',
                'multimedia', 'entertainment', 'carplay', 'android auto'
            ],
            'Powertrain & Engine': [
                'engine', 'transmission', 'powertrain', 'motor', 'battery', 'hybrid',
                'electric', 'fuel', 'exhaust', 'turbo', 'cylinder', 'piston'
            ],
            'Body & Exterior': [
                'door', 'window', 'mirror', 'trunk', 'hood', 'bumper', 'paint',
                'body', 'exterior', 'seal', 'weatherstrip', 'glass'
            ],
            'Interior & Comfort': [
                'seat', 'climate', 'hvac', 'air conditioning', 'heater', 'interior',
                'dashboard', 'console', 'trim', 'upholstery', 'comfort'
            ],
            'Electrical & Lighting': [
                'light', 'headlight', 'taillight', 'electrical', 'wiring', 'fuse',
                'relay', 'switch', 'bulb', 'led', 'indicator'
            ],
            'Chassis & Suspension': [
                'suspension', 'brake', 'wheel', 'tire', 'steering', 'chassis',
                'shock', 'strut', 'alignment', 'bearing'
            ],
            'BCM & Body Control': [
                'bcm', 'body control', 'module', 'control unit', 'ecu'
            ],
            'IPC & Instrument Cluster': [
                'ipc', 'instrument', 'cluster', 'gauge', 'speedometer', 'odometer',
                'warning light', 'indicator'
            ],
            'Network Management & Bus Communication': [
                'network management', 'nm', 'can bus', 'can', 'lin bus', 'lin',
                'bus communication', 'bus loading', 'bus message', 'wakeup',
                'nm_alive', 'nm alive', 'ring message', 'bus stress', 'communication stress',
                'network stress', 'bus timeout', 'message timeout', 'gateway'
            ]
        }
        
        def categorize_issue(text):
            """Categorize based on keyword matching with priority order"""
            text_lower = str(text).lower()
            
            # Priority order: Check more specific categories first
            priority_categories = [
                'Network Management & Bus Communication',  # Check network/bus first (most specific)
                'ADAS & Safety Systems',
                'Infotainment & Connectivity',
                'Powertrain & Engine',
                'IPC & Instrument Cluster',
                'BCM & Body Control',  # Check BCM after network (less specific)
                'Body & Exterior',
                'Interior & Comfort',
                'Electrical & Lighting',
                'Chassis & Suspension'
            ]
            
            # Check priority categories first
            for category in priority_categories:
                if category in category_rules:
                    for keyword in category_rules[category]:
                        if keyword in text_lower:
                            return category
            
            # Check any remaining categories
            for category, keywords in category_rules.items():
                if category not in priority_categories:
                    for keyword in keywords:
                        if keyword in text_lower:
                            return category
            
            return 'Other'
        
        # Apply categorization
        df['category_rule_based'] = df['combined_text'].apply(categorize_issue)
        
        # Create final category (prefer rule-based, fallback to cluster)
        df['rca_cluster_label_final'] = df.apply(
            lambda row: row['category_rule_based'] if row['category_rule_based'] != 'Other' 
            else row['rca_cluster_label'],
            axis=1
        )
        
        logger.info("Applied rule-based categorization")
        return df
    
    def add_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived fields for analysis"""
        df = df.copy()
        
        # Assignment status
        if 'rca_solver_lead' in df.columns:
            df['assignment_status'] = df['rca_solver_lead'].apply(
                lambda x: 'Unassigned' if pd.isna(x) or str(x).strip() == '' else 'Assigned'
            )
        elif 'assigned_flag' in df.columns:
            df['assignment_status'] = df['assigned_flag']
        
        # Resolution status (original)
        if 'issue_color_status' in df.columns:
            df['resolution_status'] = df['issue_color_status'].apply(
                lambda x: 'Resolved' if x in ['Dark Green', 'Cancelled'] else 'Unresolved'
            )
        
        # Normalized status (Open/Closed)
        if 'issue_color_status' in df.columns:
            df['normalized_status'] = df['issue_color_status'].apply(
                lambda x: 'Closed' if x in ['Dark Green', 'Cancelled'] else 'Open'
            )
        
        # Model field (standardize column name)
        if 'affected_vehicleproject_model' in df.columns:
            df['model'] = df['affected_vehicleproject_model']
        
        # Time-based features
        if 'detection_date' in df.columns:
            df['detection_date'] = pd.to_datetime(df['detection_date'], errors='coerce')
            df['detection_year'] = df['detection_date'].dt.year
            df['detection_month'] = df['detection_date'].dt.month
            df['detection_quarter'] = df['detection_date'].dt.quarter
        
        logger.info("Added derived fields")
        return df
    
    def expand_multiple_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Expand rows with multiple vehicle models or years into separate records.
        This ensures each model/year combination is counted in analytics.
        """
        df = df.copy()
        expanded_rows = []
        
        for idx, row in df.iterrows():
            models = []
            years = []
            
            # Parse vehicle models (separated by semicolons)
            if pd.notna(row.get('affected_vehicleproject_model')):
                model_str = str(row['affected_vehicleproject_model'])
                if ';' in model_str:
                    models = [m.strip() for m in model_str.split(';') if m.strip()]
                else:
                    models = [model_str.strip()]
            else:
                models = [None]
            
            # Parse model years (separated by semicolons)
            if pd.notna(row.get('model_year')):
                year_str = str(row['model_year'])
                if ';' in year_str:
                    years = [y.strip() for y in year_str.split(';') if y.strip()]
                else:
                    years = [year_str.strip()]
            else:
                years = [None]
            
            # Create a record for each model/year combination
            for model in models:
                for year in years:
                    new_row = row.copy()
                    new_row['affected_vehicleproject_model_expanded'] = model
                    new_row['model_year_expanded'] = year
                    expanded_rows.append(new_row)
        
        df_expanded = pd.DataFrame(expanded_rows)
        
        # Keep original columns and add expanded versions
        logger.info(f"Expanded {len(df)} issues into {len(df_expanded)} model/year combinations")
        
        return df_expanded
    
    def save_models(self):
        """Save trained models to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        models = {
            'vectorizer': self.vectorizer,
            'scaler': self.scaler,
            'kmeans': self.kmeans
        }
        
        for name, model in models.items():
            if model is not None:
                model_path = self.models_dir / f"{name}_{timestamp}.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                logger.info(f"Saved {name} to {model_path}")
        
        # Save metadata
        metadata = {
            'n_clusters': self.n_clusters,
            'random_state': self.random_state,
            'timestamp': timestamp,
            'n_features': self.vectorizer.max_features if self.vectorizer else None
        }
        
        metadata_path = self.models_dir / f"metadata_{timestamp}.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info("Models saved successfully")
    
    def load_models(self, timestamp: Optional[str] = None):
        """Load trained models from disk"""
        if timestamp is None:
            # Load latest models
            model_files = list(self.models_dir.glob("vectorizer_*.pkl"))
            if not model_files:
                raise FileNotFoundError("No trained models found")
            latest_file = max(model_files, key=lambda p: p.stat().st_mtime)
            timestamp = latest_file.stem.split('_', 1)[1]
        
        # Load models
        for name in ['vectorizer', 'scaler', 'kmeans']:
            model_path = self.models_dir / f"{name}_{timestamp}.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    setattr(self, name, pickle.load(f))
                logger.info(f"Loaded {name} from {model_path}")
        
        logger.info("Models loaded successfully")
    
    def run_full_pipeline(self, save_output: bool = True) -> pd.DataFrame:
        """Run the complete ML pipeline"""
        logger.info("=" * 50)
        logger.info("Starting Warranty ML Pipeline")
        logger.info("=" * 50)
        
        # 1. Load data
        df = self.load_data()
        
        # 2. Preprocess text
        df = self.preprocess_text(df)
        
        # 3. Extract features
        features, df = self.extract_features(df)
        
        # 4. Train clustering
        cluster_labels = self.train_clustering(features)
        
        # 5. Generate cluster labels
        df = self.generate_cluster_labels(df, cluster_labels)
        
        # 6. Apply rule-based categorization
        df = self.apply_rule_based_categorization(df)
        
        # 7. Apply enhanced NLP-based categorization
        df = self.enhanced_categorizer.categorize_dataframe(df)
        
        # 8. Apply advanced NLP (spaCy, sentiment analysis)
        if self.use_advanced_nlp:
            logger.info("Applying advanced NLP analysis (this may take a few minutes)...")
            df = self.advanced_nlp_categorizer.categorize_dataframe(df)
        
        # 9. Add derived fields
        df = self.add_derived_fields(df)
        
        # 10. Save models
        self.save_models()
        
        # 11. Save processed data
        if save_output:
            output_path = self.data_path.parent / 'processed' / 'warranty_with_predictions.parquet'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved processed data to {output_path}")
        
        logger.info("=" * 50)
        logger.info("Pipeline Complete!")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Clusters: {df['cluster_id'].nunique()}")
        logger.info(f"Categories: {df['category_rule_based'].nunique()}")
        logger.info("=" * 50)
        
        return df
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict clusters for new data using trained models"""
        if self.vectorizer is None or self.kmeans is None:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        # Preprocess
        df = self.preprocess_text(df)
        
        # Extract features
        features, df = self.extract_features(df)
        
        # Predict clusters
        cluster_labels = self.kmeans.predict(features)
        
        # Generate labels
        df = self.generate_cluster_labels(df, cluster_labels)
        
        # Apply categorization
        df = self.apply_rule_based_categorization(df)
        
        # Add derived fields
        df = self.add_derived_fields(df)
        
        return df


def main():
    """Main execution function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize pipeline
    data_path = "data/raw/warranty_data.parquet"  # Update with your path
    pipeline = WarrantyMLPipeline(data_path)
    
    # Run pipeline
    df_processed = pipeline.run_full_pipeline()
    
    print("\nPipeline Summary:")
    print(f"Total Issues: {len(df_processed):,}")
    print(f"Unique Clusters: {df_processed['cluster_id'].nunique()}")
    print(f"\nTop 10 Categories:")
    print(df_processed['rca_cluster_label_final'].value_counts().head(10))


if __name__ == "__main__":
    main()
