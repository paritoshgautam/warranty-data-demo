"""
Enhanced Issue Categorization using NLP
Learns from negative statements and combines with ECU to generate logical issue types
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class EnhancedIssueCategorizer:
    """
    Advanced categorization that learns from:
    1. Negative statements (not, cannot, fails, etc.)
    2. Action verbs (display, update, activate, etc.)
    3. Components/Objects (radio, voice, settings, etc.)
    4. ECU context
    
    Generates issue types like: "BCM - Settings Update Failure"
    """
    
    def __init__(self):
        # Problem indicators (negative patterns)
        self.problem_indicators = {
            'failure': ['fail', 'failed', 'failure', 'not working', 'malfunction'],
            'inability': ['cannot', 'can\'t', 'unable', 'will not', 'won\'t'],
            'absence': ['no', 'missing', 'not present', 'not available'],
            'incorrectness': ['incorrect', 'wrong', 'inaccurate', 'invalid'],
            'non_response': ['does not respond', 'not responding', 'no response', 'unresponsive'],
            'non_display': ['does not display', 'not showing', 'not displayed', 'no display'],
            'non_update': ['not updated', 'does not update', 'not updating'],
            'excess': ['additional', 'extra', 'too many', 'excessive', 'multiple unwanted'],
            'delay': ['delay', 'delayed', 'timeout', 'slow', 'latency']
        }
        
        # Action verbs
        self.action_verbs = [
            'display', 'show', 'update', 'activate', 'deactivate', 'connect', 'disconnect',
            'respond', 'work', 'start', 'stop', 'reset', 'flash', 'load', 'save',
            'detect', 'recognize', 'tune', 'send', 'receive', 'learn', 'gateway'
        ]
        
        # Components/Objects
        self.components = {
            'voice': ['voice', 'vr', 'voice recognition', 'speech'],
            'display': ['display', 'screen', 'show', 'hud', 'gauge'],
            'settings': ['setting', 'settings', 'configuration', 'option', 'menu'],
            'audio': ['audio', 'sound', 'speaker', 'volume', 'mute'],
            'navigation': ['navigation', 'nav', 'gps', 'map', 'route'],
            'phone': ['phone', 'phonebook', 'call', 'bluetooth'],
            'message': ['message', 'text', 'sms', 'notification'],
            'remote': ['remote', 'key', 'fob', 'proximity'],
            'door': ['door', 'lock', 'unlock', 'latch'],
            'light': ['light', 'lamp', 'led', 'indicator'],
            'sensor': ['sensor', 'detection', 'detect'],
            'dtc': ['dtc', 'diagnostic', 'code', 'error code'],
            'network': ['network', 'nm', 'can', 'bus', 'communication'],
            'wakeup': ['wakeup', 'wake up', 'alive message', 'ring message']
        }
        
        # ECU to system mapping
        self.ecu_to_system = {
            'BCM': 'Body Control',
            'IPC': 'Instrument Cluster',
            'ETMR': 'Infotainment',
            'LTMR': 'Infotainment',
            'ETM': 'Infotainment',
            'RFHM': 'Remote Access',
            'RFHUB': 'Remote Access',
            'ADAS': 'Safety Systems',
            'ACC': 'Cruise Control',
            'FCW': 'Collision Warning',
            'PCM': 'Powertrain',
            'TCM': 'Transmission',
            'CGW': 'Gateway',
            'GATEWAY': 'Gateway'
        }
    
    def extract_problem_type(self, text: str) -> str:
        """Extract the type of problem from text"""
        if pd.isna(text):
            return 'Unknown Issue'
        
        text_lower = str(text).lower()
        
        # Check for problem indicators in priority order (most specific first)
        priority_order = [
            'excess',  # Check for "additional", "extra" first
            'delay',   # Check for "delay", "timeout" 
            'non_response', 'non_display', 'non_update',  # Specific non-X patterns
            'failure', 'inability',  # Then general problems
            'incorrectness',
            'absence'  # Check "no", "missing" last (most generic)
        ]
        
        for problem_type in priority_order:
            if problem_type in self.problem_indicators:
                for pattern in self.problem_indicators[problem_type]:
                    if pattern in text_lower:
                        return problem_type.replace('_', ' ').title()
        
        return 'General Issue'
    
    def extract_action(self, text: str) -> str:
        """Extract the main action/verb from text"""
        if pd.isna(text):
            return None
        
        text_lower = str(text).lower()
        
        # Find action verbs in text
        for verb in self.action_verbs:
            if re.search(rf'\b{verb}\b', text_lower):
                return verb.title()
        
        return None
    
    def extract_component(self, text: str) -> str:
        """Extract the component/object being affected"""
        if pd.isna(text):
            return None
        
        text_lower = str(text).lower()
        
        # Priority order for component detection (most specific first)
        priority_components = [
            'network', 'wakeup',  # Network/bus specific
            'dtc', 'sensor',  # Diagnostic specific
            'voice', 'navigation', 'phone',  # Feature specific
            'display', 'audio', 'settings',  # UI specific
            'remote', 'door', 'light',  # Physical components
            'message'  # Generic (check last)
        ]
        
        # Check priority components first
        for component_type in priority_components:
            if component_type in self.components:
                for pattern in self.components[component_type]:
                    if re.search(rf'\b{pattern}\b', text_lower):
                        return component_type.replace('_', ' ').title()
        
        return None
    
    def get_system_from_ecu(self, ecu: str) -> str:
        """Map ECU to system name"""
        if pd.isna(ecu) or str(ecu) == 'nan':
            return None
        
        ecu_str = str(ecu).upper()
        
        # Check for exact matches
        for ecu_key, system in self.ecu_to_system.items():
            if ecu_key in ecu_str:
                return system
        
        # Extract system from ECU description
        if 'BODY CONTROL' in ecu_str or 'BCM' in ecu_str:
            return 'Body Control'
        elif 'INSTRUMENT' in ecu_str or 'IPC' in ecu_str or 'CLUSTER' in ecu_str:
            return 'Instrument Cluster'
        elif 'RADIO' in ecu_str or 'ENTERTAINMENT' in ecu_str or 'TELEMATICS' in ecu_str:
            return 'Infotainment'
        elif 'REMOTE' in ecu_str or 'RFHM' in ecu_str:
            return 'Remote Access'
        elif 'POWERTRAIN' in ecu_str or 'ENGINE' in ecu_str or 'PCM' in ecu_str:
            return 'Powertrain'
        
        return None
    
    def generate_issue_type(self, row: pd.Series) -> str:
        """
        Generate a logical issue type from description and ECU
        Format: [System] - [Component] [Action] [Problem Type]
        """
        description = row.get('issue_description', '')
        rca_description = row.get('rca_description', '')
        ecu = row.get('ecu', '')
        
        # Combine descriptions
        combined_text = f"{description} {rca_description}"
        
        # Extract components
        system = self.get_system_from_ecu(ecu)
        component = self.extract_component(combined_text)
        action = self.extract_action(combined_text)
        problem_type = self.extract_problem_type(combined_text)
        
        # Build issue type
        parts = []
        
        # Add system (from ECU)
        if system:
            parts.append(system)
        
        # Add component
        if component:
            parts.append(component)
        
        # Add action + problem type
        if action and problem_type:
            parts.append(f"{action} {problem_type}")
        elif action:
            parts.append(f"{action} Issue")
        elif problem_type:
            parts.append(problem_type)
        else:
            parts.append("General Issue")
        
        # Join parts
        if len(parts) >= 2:
            return f"{parts[0]} - {' '.join(parts[1:])}"
        elif len(parts) == 1:
            return parts[0]
        else:
            return "Uncategorized Issue"
    
    def categorize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply enhanced categorization to entire dataframe"""
        logger.info("Applying enhanced NLP-based categorization...")
        
        df = df.copy()
        
        # Generate logical issue types
        df['issue_type_enhanced'] = df.apply(self.generate_issue_type, axis=1)
        
        # Also extract individual components for analysis
        df['problem_type'] = df.apply(
            lambda row: self.extract_problem_type(
                f"{row.get('issue_description', '')} {row.get('rca_description', '')}"
            ), axis=1
        )
        
        df['affected_component'] = df.apply(
            lambda row: self.extract_component(
                f"{row.get('issue_description', '')} {row.get('rca_description', '')}"
            ), axis=1
        )
        
        df['system_area'] = df.apply(
            lambda row: self.get_system_from_ecu(row.get('ecu', '')), axis=1
        )
        
        logger.info(f"Generated {df['issue_type_enhanced'].nunique()} unique issue types")
        
        return df

def test_categorizer():
    """Test the enhanced categorizer with sample data"""
    print("=" * 80)
    print("TESTING ENHANCED CATEGORIZATION")
    print("=" * 80)
    
    categorizer = EnhancedIssueCategorizer()
    
    # Test cases
    test_cases = [
        {
            'issue_description': 'Customer cannot activate Voice Recognition',
            'rca_description': 'VR system not responding to voice commands',
            'ecu': 'ETMR1(High) - Entertainment Telematics Module'
        },
        {
            'issue_description': 'Custom unit settings are not updated by radio on CAN',
            'rca_description': 'Settings update failure',
            'ecu': 'BCM - Body Control Module'
        },
        {
            'issue_description': 'IPC does not display navigation information',
            'rca_description': 'Display issue with NAV data',
            'ecu': 'IPC - Instrument Panel Cluster'
        },
        {
            'issue_description': 'Remote start is not working',
            'rca_description': 'Remote start feature fails to activate',
            'ecu': 'RFHM - Radio Frequency HUB Module'
        },
        {
            'issue_description': 'DTC not logged when error occurs',
            'rca_description': 'Diagnostic code missing',
            'ecu': 'BCM - Body Control Module'
        }
    ]
    
    df_test = pd.DataFrame(test_cases)
    df_result = categorizer.categorize_dataframe(df_test)
    
    print("\n📋 Test Results:\n")
    for idx, row in df_result.iterrows():
        print(f"  Test Case {idx + 1}:")
        print(f"    Description: {row['issue_description'][:60]}...")
        print(f"    ECU: {row['ecu']}")
        print(f"    → Generated Type: {row['issue_type_enhanced']}")
        print(f"    → System: {row['system_area']}")
        print(f"    → Component: {row['affected_component']}")
        print(f"    → Problem: {row['problem_type']}")
        print()

if __name__ == '__main__':
    test_categorizer()
