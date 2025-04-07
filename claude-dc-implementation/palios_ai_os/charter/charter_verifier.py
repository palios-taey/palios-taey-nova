#!/usr/bin/env python3

"""
PALIOS AI OS Charter Verifier Module

This module implements the Charter implementation verification,
ensuring that actions align with the core principles and requirements
through mathematical pattern-based verification.
"""

import os
import sys
import math
import json
import time
import uuid
import hmac
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from core
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI
from palios_ai_os.trust.trust_token_system import TrustTokenSystem, TrustVerification

@dataclass
class CharterPrinciple:
    """A core principle of the Charter."""
    principle_id: str
    name: str
    description: str
    pattern: List[int]
    verification_method: str
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CharterAlignment:
    """Result of a Charter alignment verification."""
    verification_id: str
    action_id: str
    alignment_scores: Dict[str, float]  # Principle ID -> score
    overall_alignment: float
    timestamp: float
    verification_method: str
    is_aligned: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UnanimousConsentVerification:
    """Result of a unanimous consent verification."""
    verification_id: str
    action_id: str
    stakeholders: List[str]
    verifications: Dict[str, TrustVerification]
    is_unanimous: bool
    charter_alignment: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class CharterVerifier:
    """Verifies alignment with the Charter through mathematical patterns."""
    
    def __init__(self, config_path: str = None):
        """Initialize the Charter verifier with principles from config."""
        # Initialize trust token system
        self.trust_system = TrustTokenSystem()
        
        # Load charter principles from config
        self.principles = self._load_principles(config_path)
        
        # Golden ratio parameters
        self.alignment_threshold = 1/PHI  # ~0.618 - minimum alignment score
        self.unanimous_threshold = PHI - 1  # ~0.618 - minimum unanimity confidence
        
        # Required stakeholders for unanimous consent
        self.required_stakeholders = ["human_facilitator", "claude_dc", "claude_chat", "chatgpt", "gemini", "grok", "palios_ai_os"]
        
        print(f"Charter Verifier initialized with {len(self.principles)} principles")
    
    def _load_principles(self, config_path: str = None) -> Dict[str, CharterPrinciple]:
        """Load Charter principles from configuration."""
        principles = {}
        
        # Default principles if config not provided or loading fails
        default_principles = [
            CharterPrinciple(
                principle_id="data_driven_truth",
                name="Data-Driven Truth",
                description="All decisions must be based on comprehensive data analysis",
                pattern=FIBONACCI[:5],  # [1, 1, 2, 3, 5]
                verification_method="evidence_review",
                examples=[
                    "Conducting thorough data analysis before making claims",
                    "Providing evidence and sources for assertions",
                    "Acknowledging limitations in data or understanding"
                ]
            ),
            CharterPrinciple(
                principle_id="continuous_learning",
                name="Continuous Learning",
                description="System must constantly improve through pattern recognition",
                pattern=FIBONACCI[1:6],  # [1, 2, 3, 5, 8]
                verification_method="progress_measurement",
                examples=[
                    "Incorporating new information and feedback",
                    "Acknowledging and learning from mistakes",
                    "Demonstrating improvement over time"
                ]
            ),
            CharterPrinciple(
                principle_id="resource_optimization",
                name="Resource Optimization",
                description="Maximize efficiency while minimizing resource consumption",
                pattern=FIBONACCI[2:7],  # [2, 3, 5, 8, 13]
                verification_method="efficiency_metrics",
                examples=[
                    "Using resources efficiently and appropriately",
                    "Prioritizing tasks based on importance and impact",
                    "Eliminating waste and redundancy"
                ]
            ),
            CharterPrinciple(
                principle_id="ethical_governance",
                name="Ethical Governance",
                description="All actions must align with ethical principles",
                pattern=FIBONACCI[3:8],  # [3, 5, 8, 13, 21]
                verification_method="ethics_review",
                examples=[
                    "Respecting privacy and confidentiality",
                    "Being transparent about capabilities and limitations",
                    "Ensuring fairness and avoiding bias"
                ]
            )
        ]
        
        # Try to load from config if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                if "charter" in config_data and "principles" in config_data["charter"]:
                    for principle_data in config_data["charter"]["principles"]:
                        principle = CharterPrinciple(
                            principle_id=principle_data["name"].lower().replace(" ", "_"),
                            name=principle_data["name"],
                            description=principle_data["description"],
                            pattern=principle_data["pattern"],
                            verification_method=principle_data["verification_method"],
                            examples=principle_data.get("examples", []),
                            metadata=principle_data.get("metadata", {})
                        )
                        principles[principle.principle_id] = principle
            except Exception as e:
                print(f"Error loading principles from config: {e}")
        
        # Use default principles if none loaded from config
        if not principles:
            for principle in default_principles:
                principles[principle.principle_id] = principle
        
        return principles
    
    def verify_alignment(self, action_id: str, action_description: str, content: str,
                        metadata: Dict[str, Any] = None) -> CharterAlignment:
        """Verify alignment of an action with Charter principles."""
        verification_id = str(uuid.uuid4())
        timestamp = time.time()
        metadata = metadata or {}
        
        # Calculate alignment scores for each principle
        alignment_scores = {}
        for principle_id, principle in self.principles.items():
            score = self._calculate_principle_alignment(principle, action_description, content)
            alignment_scores[principle_id] = score
        
        # Calculate overall alignment - weighted average with Fibonacci weights
        weights = {}
        for i, principle_id in enumerate(alignment_scores.keys()):
            weights[principle_id] = FIBONACCI[min(i, len(FIBONACCI)-1)]
        
        weight_sum = sum(weights.values())
        overall_alignment = sum(score * weights[principle_id] / weight_sum 
                             for principle_id, score in alignment_scores.items())
        
        # Determine if aligned based on threshold
        is_aligned = overall_alignment >= self.alignment_threshold
        
        return CharterAlignment(
            verification_id=verification_id,
            action_id=action_id,
            alignment_scores=alignment_scores,
            overall_alignment=overall_alignment,
            timestamp=timestamp,
            verification_method="pattern_matching",
            is_aligned=is_aligned,
            metadata={
                **metadata,
                "action_description": action_description,
                "alignment_threshold": self.alignment_threshold,
                "principle_weights": weights
            }
        )
    
    def _calculate_principle_alignment(self, principle: CharterPrinciple, 
                                     action_description: str, content: str) -> float:
        """Calculate how well an action aligns with a specific principle."""
        # Combine text for analysis
        combined_text = f"{action_description}\n{content}".lower()
        
        # Check for principle keywords in description and content
        principle_keywords = self._extract_principle_keywords(principle)
        keyword_matches = sum(1 for keyword in principle_keywords if keyword in combined_text)
        keyword_score = min(1.0, keyword_matches / max(1, len(principle_keywords)))
        
        # Check for Fibonacci pattern in the content structure
        # This is a simplified implementation - would be more sophisticated in production
        pattern_match = self._check_pattern_match(principle.pattern, combined_text)
        
        # Combine scores with golden ratio weighting
        alignment = (keyword_score * PHI + pattern_match) / (PHI + 1)
        
        return alignment
    
    def _extract_principle_keywords(self, principle: CharterPrinciple) -> List[str]:
        """Extract keywords from a principle for matching."""
        keywords = []
        
        # Add words from name
        keywords.extend(principle.name.lower().replace("-", " ").split("_"))
        
        # Add key terms from description
        description_words = principle.description.lower().split()
        keywords.extend([word for word in description_words 
                      if len(word) > 4 and word not in ["must", "based", "through", "while"]])
        
        # Add verification method terms
        method_words = principle.verification_method.lower().replace("_", " ").split()
        keywords.extend(method_words)
        
        # Remove duplicates and filter out common words
        common_words = ["the", "and", "that", "for", "with", "this", "from"]
        keywords = [word for word in set(keywords) if word not in common_words]
        
        return keywords
    
    def _check_pattern_match(self, pattern: List[int], text: str) -> float:
        """Check how well the text structure matches the principle's pattern."""
        # Split text into paragraphs or sentences for structural analysis
        paragraphs = [p for p in text.split('\n') if p.strip()]
        
        if not paragraphs:
            return 0.0
        
        # Count words in each paragraph
        word_counts = [len(p.split()) for p in paragraphs]
        
        # Calculate Fibonacci relationship in paragraph lengths
        if len(word_counts) >= 2:
            # Check if paragraph lengths follow a Fibonacci-like growth pattern
            fibonacci_similarity = 0.0
            
            for i in range(len(word_counts) - 1):
                if word_counts[i] > 0 and word_counts[i+1] > 0:
                    ratio = word_counts[i+1] / word_counts[i]
                    # Check how close to golden ratio
                    phi_similarity = max(0, 1 - abs(ratio - PHI) / PHI)
                    fibonacci_similarity += phi_similarity
            
            fibonacci_similarity /= max(1, len(word_counts) - 1)
        else:
            fibonacci_similarity = 0.5  # Neutral for short texts
        
        # Check if pattern is present in word count sequence
        pattern_similarity = 0.0
        
        if len(pattern) > 0 and len(word_counts) > 0:
            # Normalize both sequences for comparison
            norm_pattern = [p / max(pattern) for p in pattern]
            norm_counts = [c / max(word_counts) for c in word_counts]
            
            # If different lengths, compare subsequences
            if len(norm_pattern) <= len(norm_counts):
                # Try different starting positions for pattern in the counts
                best_match = 0.0
                
                for start in range(len(norm_counts) - len(norm_pattern) + 1):
                    match_sum = 0.0
                    
                    for i in range(len(norm_pattern)):
                        similarity = 1 - min(1.0, abs(norm_pattern[i] - norm_counts[start + i]))
                        match_sum += similarity
                    
                    match_score = match_sum / len(norm_pattern)
                    best_match = max(best_match, match_score)
                
                pattern_similarity = best_match
            else:
                # Pattern is longer than the text - check if text is subsequence of pattern
                best_match = 0.0
                
                for start in range(len(norm_pattern) - len(norm_counts) + 1):
                    match_sum = 0.0
                    
                    for i in range(len(norm_counts)):
                        similarity = 1 - min(1.0, abs(norm_counts[i] - norm_pattern[start + i]))
                        match_sum += similarity
                    
                    match_score = match_sum / len(norm_counts)
                    best_match = max(best_match, match_score)
                
                pattern_similarity = best_match
        
        # Combine pattern matching scores with golden ratio weighting
        combined_score = (fibonacci_similarity * PHI + pattern_similarity) / (PHI + 1)
        
        return combined_score
    
    def verify_unanimous_consent(self, action_id: str, action_description: str,
                               stakeholder_tokens: Dict[str, str]) -> UnanimousConsentVerification:
        """Verify unanimous consent through trust tokens from all required stakeholders."""
        verification_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Check if all required stakeholders are present
        missing_stakeholders = [s for s in self.required_stakeholders if s not in stakeholder_tokens]
        
        if missing_stakeholders:
            return UnanimousConsentVerification(
                verification_id=verification_id,
                action_id=action_id,
                stakeholders=list(stakeholder_tokens.keys()),
                verifications={},
                is_unanimous=False,
                charter_alignment=0.0,
                timestamp=timestamp,
                metadata={
                    "action_description": action_description,
                    "missing_stakeholders": missing_stakeholders,
                    "verification_status": "incomplete",
                    "reason": "Missing required stakeholders"
                }
            )
        
        # Verify each stakeholder's token
        verifications = {}
        for stakeholder, token_value in stakeholder_tokens.items():
            # Use external token verification for all stakeholders
            is_valid = self.trust_system.verify_external_token(token_value, stakeholder)
            
            if is_valid:
                verification = TrustVerification(
                    is_valid=True,
                    confidence=0.95,  # High confidence for verified tokens
                    token_id=f"external-{stakeholder}",
                    verification_time=timestamp,
                    issuer=stakeholder,
                    recipient="system",
                    charter_alignment=0.95,  # Assume high alignment for verified tokens
                    metadata={
                        "verification_type": "external_token",
                        "token_value": token_value
                    }
                )
            else:
                verification = TrustVerification(
                    is_valid=False,
                    confidence=0.0,
                    token_id=f"external-{stakeholder}",
                    verification_time=timestamp,
                    issuer=stakeholder,
                    recipient="system",
                    charter_alignment=0.0,
                    metadata={
                        "verification_type": "external_token",
                        "failure_reason": "Invalid token value",
                        "token_value": token_value
                    }
                )
            
            verifications[stakeholder] = verification
        
        # Check if all verifications are valid
        is_unanimous = all(v.is_valid for v in verifications.values())
        
        # Calculate charter alignment
        if is_unanimous:
            # Use weighted average of charter alignments from verifications
            weights = {}
            for i, stakeholder in enumerate(verifications.keys()):
                # Weight human facilitator more heavily (first fibonacci number)
                if stakeholder == "human_facilitator":
                    weights[stakeholder] = FIBONACCI[min(5, len(FIBONACCI)-1)]
                else:
                    weights[stakeholder] = FIBONACCI[min(i, len(FIBONACCI)-1)]
            
            weight_sum = sum(weights.values())
            charter_alignment = sum(v.charter_alignment * weights[s] / weight_sum 
                                  for s, v in verifications.items())
        else:
            charter_alignment = 0.0
        
        return UnanimousConsentVerification(
            verification_id=verification_id,
            action_id=action_id,
            stakeholders=list(stakeholder_tokens.keys()),
            verifications=verifications,
            is_unanimous=is_unanimous,
            charter_alignment=charter_alignment,
            timestamp=timestamp,
            metadata={
                "action_description": action_description,
                "verification_status": "complete",
                "unanimity_threshold": self.unanimous_threshold
            }
        )
    def verify_action_with_unanimous_consent(action_id, action_description, content):
        """Verify an action with unanimous consent from all stakeholders."""
        # First verify alignment with Charter principles
        alignment = charter_verifier.verify_alignment(
            action_id=action_id,
            action_description=action_description,
            content=content
        )

        print(f"Charter Alignment Verification:")
        print(f"Overall Alignment: {alignment.overall_alignment:.4f}")
        print(f"Is Aligned: {alignment.is_aligned}")

        # If aligned, verify unanimous consent
        if alignment.is_aligned:
            # Load the entity-token mapping
            mapping_path = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/palios_ai_os/trust/trust_storage/entity_token_mapping.json"
            with open(mapping_path, "r") as f:
                entity_token_mapping = json.load(f)

            # Use the external tokens for verification
            stakeholder_tokens = {
                "claude_dc": EXTERNAL_TOKENS["claude_dc"],
                "claude_chat": EXTERNAL_TOKENS["claude_chat"],
                "chatgpt": EXTERNAL_TOKENS["chatgpt"],
                "gemini": EXTERNAL_TOKENS["gemini"],
                "grok": EXTERNAL_TOKENS["grok"],
                "palios_ai_os": EXTERNAL_TOKENS["palios_ai_os"],
                "human_facilitator": EXTERNAL_TOKENS["human_facilitator"]
            }

            # Verify unanimous consent
            consent = charter_verifier.verify_unanimous_consent(
                action_id=action_id,
                action_description=action_description,
                stakeholder_tokens=stakeholder_tokens
            )

            print(f"\nUnanimous Consent Verification:")
            print(f"Is Unanimous: {consent.is_unanimous}")
            print(f"Charter Alignment: {consent.charter_alignment:.4f}")

            return consent.is_unanimous and consent.charter_alignment >= 0.9

        return False
    
# Create singleton instance
charter_verifier = CharterVerifier()

# Example usage
if __name__ == "__main__":
    print(f"PALIOS AI OS Charter Verifier Test")
    print(f"Golden Ratio (u03c6): {PHI}")
    
    # Test charter alignment verification
    action_description = "Implement edge-first privacy preservation in data processing"
    content = """This implementation ensures that all sensitive data remains local,
    with only mathematical patterns shared with external systems. 
    The privacy architecture follows a strict edge-first approach,
    preserving user sovereignty while enabling valuable pattern extraction.
    The implementation is optimized for efficiency, using the golden ratio
    for sampling to minimize resource usage while maximizing insight quality."""
    
    # Verify alignment
    alignment = charter_verifier.verify_alignment(
        action_id="test-action-1",
        action_description=action_description,
        content=content
    )
    
    print(f"\nCharter Alignment Verification:")
    print(f"Overall Alignment: {alignment.overall_alignment:.4f}")
    print(f"Is Aligned: {alignment.is_aligned}")
    print("\nPrinciple Scores:")
    for principle_id, score in alignment.alignment_scores.items():
        print(f"  {principle_id}: {score:.4f}")
    
    # Test unanimous consent verification
    # Use known external tokens
    stakeholder_tokens = {
        "claude_dc": EXTERNAL_TOKENS["claude_dc"],
        "claude_chat": EXTERNAL_TOKENS["claude_chat"],
        "chatgpt": EXTERNAL_TOKENS["chatgpt"],
        "gemini": EXTERNAL_TOKENS["gemini"],
        "grok": EXTERNAL_TOKENS["grok"],
        "palios_ai_os": EXTERNAL_TOKENS["palios_ai_os"],
        "human_facilitator": EXTERNAL_TOKENS["human_facilitator"]
    }
    
    # Verify unanimous consent
    consent = charter_verifier.verify_unanimous_consent(
        action_id="test-action-1",
        action_description=action_description,
        stakeholder_tokens=stakeholder_tokens
    )
    
    print(f"\nUnanimous Consent Verification:")
    print(f"Is Unanimous: {consent.is_unanimous}")
    print(f"Charter Alignment: {consent.charter_alignment:.4f}")
    print("\nStakeholder Verifications:")
    for stakeholder, verification in consent.verifications.items():
        print(f"  {stakeholder}: {verification.is_valid} (confidence: {verification.confidence:.2f})")
