# Insurance Claims RAG System Exercise - Starter

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, List, Any, Optional, Union, Set
import random
import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from smolagents import (
    ToolCallingAgent,
    OpenAIServerModel,
    tool,
)
import os
import dotenv

# Note: Make sure to set up your .env file with your API key before running
dotenv.load_dotenv(dotenv_path='../.env')
openai_api_key = os.getenv('UDACITY_OPENAI_API_KEY')

model = OpenAIServerModel(
    model_id='gpt-4o-mini',
    api_base='https://openai.vocareum.com/v1',
    api_key=openai_api_key,
)

# Import core components from the demo file
# Note: In a real application, you would organize this better with proper imports
from demo.demo import (
    PrivacyLevel, AccessControl, Claim, PatientRecord, ComplaintRecord, 
    Database, VectorKnowledgeBase, VectorClaimSearch,
    DataGenerator, database, vector_kb, vector_claim_search,
    search_knowledge_base, retrieve_claim_history, get_claim_details,
    get_patient_info, find_similar_claims, submit_complaint,
    respond_to_complaint, get_complaint_history, process_new_claim,
    ClaimProcessingAgent, CustomerServiceAgent, MedicalReviewAgent,
    ComplaintResolutionOrchestrator
)

"""
EXERCISE: CLAIM FRAUD DETECTION WITH RAG

In this exercise, you'll enhance the insurance claims processing system by adding 
fraud detection capabilities powered by RAG. Fraud detection is a critical component 
of insurance claims processing, saving the industry billions of dollars annually.

Your task is to:

1. Implement a FraudDetectionAgent class that leverages RAG to identify potentially 
   fraudulent claims by comparing them with known fraud patterns
   
2. Create a fraud knowledge base with common fraud indicators and patterns
   
3. Implement vector search functionality to identify similar fraud patterns
   
4. Integrate the agent into the existing workflow, adding a fraud review step to the
   claim processing pipeline

HINTS:
- You can use the existing VectorKnowledgeBase and VectorClaimSearch as references
- Your fraud detection component should consider multiple factors like claim frequency,
  unusual patterns, and similarity to known fraud cases
- Make sure to respect the privacy levels and access controls already in place
"""

# STEP 1: Create a knowledge base of fraud patterns
fraud_patterns = [
    {
        'pattern_id': 'FP-001',
        'pattern_name': 'Rapid Claim Submission',
        'description': 'Multiple claims submitted for the same patient within a short time period (often within 7-14 days)',
        'indicators': 'multiple claims, same patient, short timeframe, different providers',
        'severity': 'medium',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-002',
        'pattern_name': 'Procedure Upcoding',
        'description': 'Billing for more complex procedures than what was actually performed',
        'indicators': 'expensive procedures, pattern of similar claims, inconsistent with patient history',
        'severity': 'high',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-003',
        'pattern_name': 'Duplicate Billing',
        'description': 'Multiple claims for the same service on the same date',
        'indicators': 'identical service date, identical procedure, multiple claims',
        'severity': 'high',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-004',
        'pattern_name': 'Phantom Billing',
        'description': 'Billing for services that were never provided',
        'indicators': 'no supporting documentation, patient denies receiving service',
        'severity': 'critical',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-005',
        'pattern_name': 'Unusual Procedure Frequency',
        'description': 'Higher than normal frequency of certain procedures',
        'indicators': 'repeated identical procedures, statistically anomalous frequency',
        'severity': 'medium',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-006',
        'pattern_name': 'Service Date Manipulation',
        'description': 'Altering service dates to avoid coverage limitations or maximize reimbursement',
        'indicators': 'claims near policy expiration, suspicious service date patterns',
        'severity': 'high',
        'privacy_level': PrivacyLevel.AGENT
    },
    {
        'pattern_id': 'FP-007',
        'pattern_name': 'Provider Shopping',
        'description': 'Patient visits multiple providers for the same condition to obtain multiple prescriptions or services',
        'indicators': 'multiple providers, similar services, short timeframe',
        'severity': 'medium',
        'privacy_level': PrivacyLevel.AGENT
    },
]

# STEP 2: Implement a vector-based fraud pattern detector
class FraudPatternDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.fraud_patterns = []
        self.pattern_vectors = None
        self.is_initialized = False

    def update_patterns(self, fraud_patterns: List[Dict]) -> None:
        """Load fraud patterns and build TF-IDF vector representations.

        Args:
            fraud_patterns: List of pattern dicts with pattern_name, description, indicators fields.
        """
        self.fraud_patterns = fraud_patterns
        texts = [
            f"{p['pattern_name']} {p['description']} {p['indicators']}"
            for p in fraud_patterns
        ]
        if texts:
            self.pattern_vectors = self.vectorizer.fit_transform(texts)
            self.is_initialized = True
            print(f"  INFO: FraudPatternDetector loaded {len(fraud_patterns)} patterns")

    def detect_fraud_indicators(self, claim, patient_history: Optional[List[Dict]] = None, access_level: str = PrivacyLevel.AGENT) -> Dict:
        """Analyse a claim for fraud signals using vector similarity and rule-based checks.

        Args:
            claim: Claim object to evaluate.
            patient_history: Previous claims for the same patient.
            access_level: Privacy level of the requester.

        Returns:
            Dict with matching_patterns, rule_based_indicators, and fraud_risk level.
        """
        if not self.is_initialized:
            return {'claim_id': getattr(claim, 'id', 'unknown'), 'error': 'Detector not initialized', 'fraud_risk': 'unknown'}

        claim_text = f"Procedure {claim.procedure_code} Amount {claim.amount} Patient {claim.patient_id} Status {claim.status}"
        if patient_history:
            for h in patient_history:
                if h['id'] != claim.id:
                    claim_text += f" Recent {h['procedure_code']}"

        # transform reuses vocabulary from fit_transform — do not re-fit here
        claim_vector = self.vectorizer.transform([claim_text])
        similarities = cosine_similarity(claim_vector, self.pattern_vectors).flatten()

        matches = []
        for i, score in enumerate(similarities):
            pattern = self.fraud_patterns[i]
            if score > 0.1 and AccessControl.can_access(access_level, pattern['privacy_level']):
                matches.append({
                    'pattern_id': pattern['pattern_id'],
                    'pattern_name': pattern['pattern_name'],
                    'severity': pattern['severity'],
                    'similarity_score': float(score)
                })

        rule_indicators = self._apply_fraud_rules(claim, patient_history)
        fraud_risk = self._calculate_fraud_risk(matches, rule_indicators)

        return {
            'claim_id': claim.id,
            'matching_patterns': sorted(matches, key=lambda x: x['similarity_score'], reverse=True),
            'rule_based_indicators': rule_indicators,
            'fraud_risk': fraud_risk
        }

    def _apply_fraud_rules(self, claim, patient_history: Optional[List[Dict]] = None) -> List[Dict]:
        """Apply deterministic rules to flag obvious fraud signals.

        Args:
            claim: Claim object to check.
            patient_history: Previous claims for the same patient.

        Returns:
            List of indicator dicts with rule, description, and confidence.
        """
        indicators = []

        if claim.amount > 400:
            indicators.append({
                'rule': 'high_amount',
                'description': 'Claim amount is significantly higher than average',
                'confidence': 0.6
            })

        if patient_history:
            repeat_claims = [
                c for c in patient_history
                if c['procedure_code'] == claim.procedure_code and c['id'] != claim.id
            ]
            if len(repeat_claims) >= 2:
                indicators.append({
                    'rule': 'repeat_procedure',
                    'description': f"Procedure {claim.procedure_code} claimed multiple times recently",
                    'confidence': 0.7
                })

        return indicators

    def _calculate_fraud_risk(self, pattern_matches: List[Dict], rule_indicators: List[Dict]) -> str:
        """Combine pattern and rule scores into a single risk label.

        Args:
            pattern_matches: Vector similarity matches with severity and score.
            rule_indicators: Rule-based indicators with confidence values.

        Returns:
            Risk label: 'low', 'medium', 'high', or 'critical'.
        """
        if not pattern_matches and not rule_indicators:
            return 'low'

        severity_weight = {'low': 0.3, 'medium': 0.6, 'high': 0.8, 'critical': 1.0}
        pattern_score = sum(m['similarity_score'] * severity_weight.get(m['severity'], 0.5) for m in pattern_matches)
        rule_score = sum(ind['confidence'] for ind in rule_indicators)
        total = pattern_score + rule_score

        if total < 0.3:
            return 'low'
        elif total < 0.7:
            return 'medium'
        elif total < 1.2:
            return 'high'
        else:
            return 'critical'


# Initialise with the patterns defined in Step 1
fraud_detector = FraudPatternDetector()
fraud_detector.update_patterns(fraud_patterns)

# STEP 3: Implement a tool for fraud detection
@tool
def check_claim_for_fraud(claim_id: str, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Check a claim for potential fraud indicators using vector similarity and rule-based analysis.

    Args:
        claim_id: The claim ID to check.
        access_level: The access level of the requester.

    Returns:
        Dict with success flag, fraud_analysis from the detector, and a plain-English recommendation.
    """
    claim_data = database.get_claim(claim_id, access_level)
    if not claim_data:
        return {'success': False, 'error': 'Claim not found or access denied'}

    claim = database.claims[claim_id]
    patient_claims = database.get_patient_claims(claim.patient_id, access_level)
    fraud_analysis = fraud_detector.detect_fraud_indicators(claim, patient_claims, access_level)

    return {
        'success': True,
        'claim_id': claim_id,
        'fraud_analysis': fraud_analysis,
        'recommendation': _get_fraud_recommendation(fraud_analysis['fraud_risk'])
    }


def _get_fraud_recommendation(risk_level: str) -> str:
    """Map a fraud risk level to a plain-English action recommendation.

    Args:
        risk_level: One of 'low', 'medium', 'high', 'critical'.

    Returns:
        Recommended action string for the claim processor.
    """
    recommendations = {
        'low': 'Proceed with normal processing',
        'medium': 'Flag for manual review before approving',
        'high': 'Requires investigator review before processing',
        'critical': 'Suspend claim and initiate fraud investigation'
    }
    return recommendations.get(risk_level, 'Requires further assessment')

# STEP 4: Create a FraudDetectionAgent
class FraudDetectionAgent(ToolCallingAgent):
    """Agent for detecting potential fraud in insurance claims."""

    def __init__(self, model: OpenAIServerModel):
        super().__init__(
            tools=[
                check_claim_for_fraud,
                get_claim_details,
                get_patient_info,
                retrieve_claim_history,
                search_knowledge_base
            ],
            model=model,
            name='fraud_investigator',
            description="""Agent responsible for detecting potential fraud in insurance claims.
            You have AGENT level access to the database.
            Your main job is to assess claims for potential fraud indicators,
            flag suspicious claims, and provide recommendations.
            Use the fraud detection tools and search for any relevant information
            that might help assess the legitimacy of claims.
            """
        )
        self.access_level = PrivacyLevel.AGENT

# STEP 5: Update the orchestrator to include fraud detection
class EnhancedOrchestrator(ComplaintResolutionOrchestrator):
    """Enhanced orchestrator that includes fraud detection in the claim processing workflow."""

    def __init__(self, model: OpenAIServerModel):
        super().__init__(model)
        self.fraud_detector = FraudDetectionAgent(model)

        # Defined inside __init__ so the tool has closure access to self.claim_processor and self.fraud_detector
        @tool
        def handle_claim_with_fraud_check(patient_id: str, service_date: str, procedure_code: str, amount: float) -> Dict:
            """Process a new claim and run fraud detection on it as part of the same workflow.

            Args:
                patient_id: The patient's ID string.
                service_date: Date of service in YYYY-MM-DD format.
                procedure_code: Medical procedure code (e.g. '71020').
                amount: Claim amount in dollars.

            Returns:
                Dict with claim_id, claim_status, decision_reason, fraud_risk, and recommendation.
            """
            claim_data = {
                'patient_id': patient_id,
                'service_date': service_date,
                'procedure_code': procedure_code,
                'amount': amount,
            }
            process_result = self.claim_processor.run(
                f"""
                Process this new claim using the process_new_claim tool.
                Pass a claim_data dict with exactly these keys and values:
                patient_id="{claim_data['patient_id']}"
                service_date="{claim_data['service_date']}"
                procedure_code="{claim_data['procedure_code']}"
                amount={claim_data['amount']}

                When searching the knowledge base use search_knowledge_base with argument: query="<your search text>"
                """
            )

            # Extract the claim_id the processor assigned — needed to run fraud detection
            claim_id = None
            for call in getattr(process_result, 'tool_calls', []) or []:
                if call.name == 'process_new_claim' and 'claim_id' in call.arguments:
                    claim_id = call.arguments['claim_id']

            if not claim_id:
                return {'success': False, 'error': 'Failed to process claim'}

            fraud_result = self.fraud_detector.run(
                f"""
                Analyze claim {claim_id} for potential fraud.

                First, get details about the claim using get_claim_details tool.
                Then check for fraud indicators using check_claim_for_fraud tool.
                Provide a detailed assessment of any potential fraud risks.
                """
            )

            fraud_analysis = {'fraud_risk': 'unknown'}
            for call in getattr(fraud_result, 'tool_calls', []) or []:
                if call.name == 'check_claim_for_fraud' and 'fraud_analysis' in call.arguments:
                    fraud_analysis = call.arguments['fraud_analysis']

            claim = database.get_claim(claim_id, PrivacyLevel.ADMIN)
            fraud_risk = fraud_analysis.get('fraud_risk', 'unknown')

            return {
                'success': True,
                'claim_id': claim_id,
                'claim_status': claim.get('status') if claim else 'unknown',
                'decision_reason': claim.get('decision_reason') if claim else 'unknown',
                'fraud_risk': fraud_risk,
                'recommendation': _get_fraud_recommendation(fraud_risk)
            }

        # self.tools is a dict {tool.name: tool} in smolagents
        self.tools[handle_claim_with_fraud_check.name] = handle_claim_with_fraud_check

# STEP 6: Function to demonstrate the fraud detection capabilities
def demonstrate_fraud_detection():
    """Run a demonstration of the fraud detection capabilities.

    Processes two claims through the EnhancedOrchestrator — one legitimate and one
    suspicious — to show how the fraud detection pipeline flags different risk levels.
    """
    orchestrator = EnhancedOrchestrator(model)

    # --- Legitimate claim: low amount, common procedure ---
    print("Generating a legitimate claim for processing...")
    legitimate_claim = {
        'patient_id': random.choice(list(database.patients.keys())),
        'service_date': f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        'procedure_code': random.choice(['71020', '81003', '85025']),
        'amount': random.uniform(50, 200)
    }
    print(f"Processing legitimate claim: {json.dumps(legitimate_claim, indent=2)}")
    orchestrator.run(
        f"""
        Process this claim and check for fraud using the handle_claim_with_fraud_check tool.
        Pass these exact values as individual arguments:
        patient_id="{legitimate_claim['patient_id']}"
        service_date="{legitimate_claim['service_date']}"
        procedure_code="{legitimate_claim['procedure_code']}"
        amount={legitimate_claim['amount']:.2f}
        """
    )

    print("\n" + "="*50 + "\n")

    # --- Suspicious claim: high amount, expensive procedure, patient with most prior claims ---
    print("Now generating a suspicious claim with fraud indicators...")
    patients_with_claims = {
        patient_id: len(patient.claim_ids)
        for patient_id, patient in database.patients.items()
        if patient.claim_ids
    }
    patient_id = (
        max(patients_with_claims.items(), key=lambda x: x[1])[0]
        if patients_with_claims
        else random.choice(list(database.patients.keys()))
    )
    suspicious_claim = {
        'patient_id': patient_id,
        'service_date': f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        'procedure_code': '43239',
        'amount': random.uniform(800, 1200)
    }
    print(f"Processing suspicious claim: {json.dumps(suspicious_claim, indent=2)}")
    orchestrator.run(
        f"""
        Process this claim and check for fraud using the handle_claim_with_fraud_check tool.
        Pass these exact values as individual arguments:
        patient_id="{suspicious_claim['patient_id']}"
        service_date="{suspicious_claim['service_date']}"
        procedure_code="{suspicious_claim['procedure_code']}"
        amount={suspicious_claim['amount']:.2f}
        """
    )

    print("\nFraud detection demonstration completed.")
    return True

if __name__ == '__main__':
    # Initialize and populate database
    print('Initializing and populating database...')
    DataGenerator.populate_database(num_patients=20, num_claims=50, num_complaints=10)
    print(f"Database contains {len(database.patients)} patients, {len(database.claims)} claims, and {len(database.complaints)} complaints")
    
    # Run the fraud detection demo
    print('\n=== Insurance Claim Fraud Detection Demo ===\n')
    demonstrate_fraud_detection()