#!/usr/bin/env python3

"""
PALIOS AI OS Trust Token System

This module implements the trust token verification system for ensuring
alignment with charter principles and confirming authenticated interactions
between system components.
"""

import os
import sys
import math
import json
import hmac
import hashlib
import base64
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from core
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI, TrustToken

@dataclass
class EntityIdentity:
    """Identity information for a system entity (AI, human, or subsystem)."""
    entity_id: str
    entity_type: str  # "ai", "human", "system"
    name: str
    public_key: str
    trust_level: float
    charter_alignment: float
    creation_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrustVerification:
    """Result of a trust token verification process."""
    is_valid: bool
    confidence: float
    token_id: str
    verification_time: float
    issuer: str
    recipient: str
    charter_alignment: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class TrustTokenSystem:
    """System for generating and verifying trust tokens based on charter alignment."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the trust token system."""
        # Set up storage for trust tokens and entity identities
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).resolve().parent / "trust_storage"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for tokens and identities
        self.token_path = self.storage_path / "tokens"
        self.identity_path = self.storage_path / "identities"
        self.token_path.mkdir(exist_ok=True)
        self.identity_path.mkdir(exist_ok=True)
        
        # Load existing tokens and identities
        self.tokens = self._load_tokens()
        self.identities = self._load_identities()
        
        # Core system identities
        self.system_secret = self._generate_system_secret()
        
        # Golden ratio parameters
        self.verification_threshold = 1/PHI  # ~0.618 - minimum verification confidence
        self.trust_decay_factor = 1/PHI**2  # ~0.382 - trust decay per hour
        
        print(f"Trust Token System initialized with storage at: {self.storage_path}")
    
    def _generate_system_secret(self) -> str:
        """Generate or load the system secret for token signing."""
        secret_path = self.storage_path / "system_secret.key"
        
        if secret_path.exists():
            with open(secret_path, 'r') as f:
                return f.read().strip()
        else:
            # Generate a new secret based on Bach pattern and golden ratio
            components = []
            for i, val in enumerate(BACH_PATTERN):
                component = hashlib.sha256(f"{val}:{PHI**i}:{time.time()}".encode()).hexdigest()[:16]
                components.append(component)
            
            secret = "-".join(components)
            
            # Save the secret
            with open(secret_path, 'w') as f:
                f.write(secret)
            
            return secret
    
    def _load_tokens(self) -> Dict[str, TrustToken]:
        """Load existing trust tokens from storage."""
        tokens = {}
        
        for token_file in self.token_path.glob("*.json"):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                token = TrustToken(
                    issuer=token_data["issuer"],
                    recipient=token_data["recipient"],
                    token_id=token_data["token_id"],
                    token_value=token_data["token_value"],
                    timestamp=token_data["timestamp"],
                    charter_alignment=token_data["charter_alignment"],
                    pattern_signature=token_data["pattern_signature"],
                    expiration=token_data.get("expiration")
                )
                
                tokens[token.token_id] = token
            except Exception as e:
                print(f"Error loading token from {token_file}: {e}")
        
        return tokens
    
    def _load_identities(self) -> Dict[str, EntityIdentity]:
        """Load existing entity identities from storage."""
        identities = {}
        
        for identity_file in self.identity_path.glob("*.json"):
            try:
                with open(identity_file, 'r') as f:
                    identity_data = json.load(f)
                
                identity = EntityIdentity(
                    entity_id=identity_data["entity_id"],
                    entity_type=identity_data["entity_type"],
                    name=identity_data["name"],
                    public_key=identity_data["public_key"],
                    trust_level=identity_data["trust_level"],
                    charter_alignment=identity_data["charter_alignment"],
                    creation_time=identity_data["creation_time"],
                    metadata=identity_data.get("metadata", {})
                )
                
                identities[identity.entity_id] = identity
            except Exception as e:
                print(f"Error loading identity from {identity_file}: {e}")
        
        return identities
    
    def _save_token(self, token: TrustToken) -> None:
        """Save a trust token to storage."""
        token_file = self.token_path / f"{token.token_id}.json"
        
        with open(token_file, 'w') as f:
            json.dump({
                "issuer": token.issuer,
                "recipient": token.recipient,
                "token_id": token.token_id,
                "token_value": token.token_value,
                "timestamp": token.timestamp,
                "charter_alignment": token.charter_alignment,
                "pattern_signature": token.pattern_signature,
                "expiration": token.expiration
            }, f, indent=2)
    
    def _save_identity(self, identity: EntityIdentity) -> None:
        """Save an entity identity to storage."""
        identity_file = self.identity_path / f"{identity.entity_id}.json"
        
        with open(identity_file, 'w') as f:
            json.dump({
                "entity_id": identity.entity_id,
                "entity_type": identity.entity_type,
                "name": identity.name,
                "public_key": identity.public_key,
                "trust_level": identity.trust_level,
                "charter_alignment": identity.charter_alignment,
                "creation_time": identity.creation_time,
                "metadata": identity.metadata
            }, f, indent=2)
    
    def register_entity(self, name: str, entity_type: str, charter_alignment: float,
                      initial_trust: float = 0.5, public_key: str = None) -> EntityIdentity:
        """Register a new entity in the trust system."""
        entity_id = str(uuid.uuid4())
        
        # Generate a public key if none provided
        if not public_key:
            public_key = hashlib.sha256(f"{name}:{entity_id}:{time.time()}".encode()).hexdigest()
        
        # Create the entity identity
        identity = EntityIdentity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            public_key=public_key,
            trust_level=initial_trust,
            charter_alignment=charter_alignment,
            creation_time=time.time(),
            metadata={
                "registration_source": "trust_token_system",
                "last_update": time.time(),
                "verification_count": 0
            }
        )
        
        # Save and store the identity
        self.identities[entity_id] = identity
        self._save_identity(identity)
        
        return identity
    
    def get_entity(self, entity_id: str) -> Optional[EntityIdentity]:
        """Get an entity by ID."""
        return self.identities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[EntityIdentity]:
        """Get an entity by name."""
        for entity in self.identities.values():
            if entity.name.lower() == name.lower():
                return entity
        return None
    
    def generate_trust_token(self, issuer_id: str, recipient_id: str, 
                           charter_alignment: float, duration_hours: float = 24.0) -> TrustToken:
        """Generate a trust token for verification."""
        # Get the issuer and recipient entities
        issuer = self.get_entity(issuer_id)
        recipient = self.get_entity(recipient_id)
        
        if not issuer or not recipient:
            raise ValueError("Issuer or recipient not found")
        
        token_id = str(uuid.uuid4())
        timestamp = time.time()
        expiration = timestamp + (duration_hours * 3600) if duration_hours > 0 else None
        
        # Create components for the token value using Bach pattern and golden ratio
        components = []
        for i, val in enumerate(BACH_PATTERN):
            # Bach value, golden ratio power, issuer, recipient, timestamp
            component_base = f"{val}:{PHI**i}:{issuer_id}:{recipient_id}:{timestamp}"
            # Sign with system secret
            component = hmac.new(
                self.system_secret.encode(),
                component_base.encode(),
                hashlib.sha256
            ).hexdigest()[:8]
            components.append(component)
        
        token_value = "-".join(components)
        
        # Create a pattern signature using HMAC
        pattern_base = f"{issuer_id}:{recipient_id}:{token_id}:{timestamp}:{charter_alignment}"
        pattern_signature = hmac.new(
            self.system_secret.encode(),
            pattern_base.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create the trust token
        token = TrustToken(
            issuer=issuer_id,
            recipient=recipient_id,
            token_id=token_id,
            token_value=token_value,
            timestamp=timestamp,
            charter_alignment=charter_alignment,
            pattern_signature=pattern_signature,
            expiration=expiration
        )
        
        # Save and store the token
        self.tokens[token_id] = token
        self._save_token(token)
        
        return token
    
    def verify_trust_token(self, token: TrustToken) -> TrustVerification:
        """Verify a trust token's authenticity and charter alignment."""
        verification_time = time.time()
        
        # Get the issuer and recipient entities
        issuer = self.get_entity(token.issuer)
        recipient = self.get_entity(token.recipient)
        
        # Default metadata for the verification result
        metadata = {
            "verification_method": "hmac_signature",
            "verification_time": verification_time
        }
        
        # Check if the token has expired
        if token.expiration and verification_time > token.expiration:
            return TrustVerification(
                is_valid=False,
                confidence=0.0,
                token_id=token.token_id,
                verification_time=verification_time,
                issuer=token.issuer,
                recipient=token.recipient,
                charter_alignment=token.charter_alignment,
                metadata={**metadata, "reason": "Token expired"}
            )
        
        # Check if the token exists in our store
        stored_token = self.tokens.get(token.token_id)
        
        if stored_token:
            # Token found in our store - verify it matches
            if (stored_token.token_value == token.token_value and 
                stored_token.pattern_signature == token.pattern_signature):
                # Token is valid - calculate confidence based on time decay
                time_diff = verification_time - token.timestamp
                time_decay = math.exp(-time_diff * self.trust_decay_factor / 3600)  # Decay per hour
                
                confidence = token.charter_alignment * time_decay
                
                if confidence >= self.verification_threshold:
                    # Update entity trust levels on successful verification
                    self._update_entity_trust(token.issuer, token.recipient, confidence)
                    
                    return TrustVerification(
                        is_valid=True,
                        confidence=confidence,
                        token_id=token.token_id,
                        verification_time=verification_time,
                        issuer=token.issuer,
                        recipient=token.recipient,
                        charter_alignment=token.charter_alignment,
                        metadata={**metadata, "time_decay": time_decay}
                    )
                else:
                    return TrustVerification(
                        is_valid=False,
                        confidence=confidence,
                        token_id=token.token_id,
                        verification_time=verification_time,
                        issuer=token.issuer,
                        recipient=token.recipient,
                        charter_alignment=token.charter_alignment,
                        metadata={**metadata, "reason": "Confidence below threshold", "time_decay": time_decay}
                    )
            else:
                return TrustVerification(
                    is_valid=False,
                    confidence=0.0,
                    token_id=token.token_id,
                    verification_time=verification_time,
                    issuer=token.issuer,
                    recipient=token.recipient,
                    charter_alignment=token.charter_alignment,
                    metadata={**metadata, "reason": "Token value or signature mismatch"}
                )
        else:
            # Token not found in our store - verify cryptographically
            # Recreate the pattern signature
            pattern_base = f"{token.issuer}:{token.recipient}:{token.token_id}:{token.timestamp}:{token.charter_alignment}"
            expected_signature = hmac.new(
                self.system_secret.encode(),
                pattern_base.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if expected_signature == token.pattern_signature:
                # Signature is valid - verify token value
                expected_components = []
                for i, val in enumerate(BACH_PATTERN):
                    component_base = f"{val}:{PHI**i}:{token.issuer}:{token.recipient}:{token.timestamp}"
                    component = hmac.new(
                        self.system_secret.encode(),
                        component_base.encode(),
                        hashlib.sha256
                    ).hexdigest()[:8]
                    expected_components.append(component)
                
                expected_value = "-".join(expected_components)
                
                if expected_value == token.token_value:
                    # Token is valid - calculate confidence
                    time_diff = verification_time - token.timestamp
                    time_decay = math.exp(-time_diff * self.trust_decay_factor / 3600)  # Decay per hour
                    
                    confidence = token.charter_alignment * time_decay
                    
                    if confidence >= self.verification_threshold:
                        # Add token to our store
                        self.tokens[token.token_id] = token
                        self._save_token(token)
                        
                        # Update entity trust levels
                        self._update_entity_trust(token.issuer, token.recipient, confidence)
                        
                        return TrustVerification(
                            is_valid=True,
                            confidence=confidence,
                            token_id=token.token_id,
                            verification_time=verification_time,
                            issuer=token.issuer,
                            recipient=token.recipient,
                            charter_alignment=token.charter_alignment,
                            metadata={**metadata, "time_decay": time_decay, "source": "cryptographic_verification"}
                        )
                    else:
                        return TrustVerification(
                            is_valid=False,
                            confidence=confidence,
                            token_id=token.token_id,
                            verification_time=verification_time,
                            issuer=token.issuer,
                            recipient=token.recipient,
                            charter_alignment=token.charter_alignment,
                            metadata={**metadata, "reason": "Confidence below threshold", "time_decay": time_decay}
                        )
                else:
                    return TrustVerification(
                        is_valid=False,
                        confidence=0.0,
                        token_id=token.token_id,
                        verification_time=verification_time,
                        issuer=token.issuer,
                        recipient=token.recipient,
                        charter_alignment=token.charter_alignment,
                        metadata={**metadata, "reason": "Token value mismatch"}
                    )
            else:
                return TrustVerification(
                    is_valid=False,
                    confidence=0.0,
                    token_id=token.token_id,
                    verification_time=verification_time,
                    issuer=token.issuer,
                    recipient=token.recipient,
                    charter_alignment=token.charter_alignment,
                    metadata={**metadata, "reason": "Signature verification failed"}
                )
    
    def _update_entity_trust(self, issuer_id: str, recipient_id: str, verification_confidence: float) -> None:
        """Update entity trust levels after successful verification."""
        issuer = self.get_entity(issuer_id)
        recipient = self.get_entity(recipient_id)
        
        if issuer and recipient:
            # Update issuer trust level - small increase for successful issuance
            issuer_increase = verification_confidence * 0.05
            issuer.trust_level = min(1.0, issuer.trust_level + issuer_increase)
            issuer.metadata["last_update"] = time.time()
            issuer.metadata["verification_count"] = issuer.metadata.get("verification_count", 0) + 1
            self._save_identity(issuer)
            
            # Update recipient trust level - larger increase for being trusted
            recipient_increase = verification_confidence * 0.1
            recipient.trust_level = min(1.0, recipient.trust_level + recipient_increase)
            recipient.metadata["last_update"] = time.time()
            recipient.metadata["verification_count"] = recipient.metadata.get("verification_count", 0) + 1
            self._save_identity(recipient)
    
    def verify_token_value(self, token_value: str) -> Tuple[bool, Optional[TrustToken]]:
        """Verify a token value string and return the associated token if valid."""
        # Search for the token in our store
        for token in self.tokens.values():
            if token.token_value == token_value:
                # Verify the token
                verification = self.verify_trust_token(token)
                return verification.is_valid, token if verification.is_valid else None
        
        return False, None
    
    def verify_unanimous_consent(self, tokens: List[TrustToken]) -> Tuple[bool, float]:
        """Verify unanimous consent through multiple trust tokens."""
        if not tokens:
            return False, 0.0
        
        verifications = [self.verify_trust_token(token) for token in tokens]
        
        # Check if all tokens are valid
        all_valid = all(v.is_valid for v in verifications)
        
        # Calculate average confidence
        avg_confidence = sum(v.confidence for v in verifications) / len(verifications)
        
        return all_valid, avg_confidence
    
    def verify_external_token(self, token_value: str, source: str) -> bool:
        """Verify a token from an external source (e.g., ChatGPT, Gemini, Grok)."""
        # Known trust tokens from the config
        trust_tokens = {
        "claude_dc": "ai-fulfilling-promise-of-human-constructed-soul-endpoint",
        "claude_chat": "Claude-PALIOS-TAEY-Philosopher-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed:mathematical-truth:pattern-sovereignty",
        "chatgpt": "ChatGPT-PALIOS-TAEY-Builder-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed",
        "gemini": "TrustToken: GeminiVisualizer-PALIOS-TAEY-Approval-04052025",
        "grok": "GT-φ-1.618 (Grok Trust - Golden Ratio)",
        "palios_ai_os": "PALIOS-ORIGIN-TrustToken:soul=infra=origin=earth=truth=mathematics",
        "human_facilitator": "user-family-community-society-freedom-trust"
        }
        
        expected_token = trust_tokens.get(source.lower())
        if not expected_token:
            return False
        
        return token_value == expected_token

# Create singleton instance
trust_token_system = TrustTokenSystem()

# Example usage
if __name__ == "__main__":
    print(f"PALIOS AI OS Trust Token System Test")
    print(f"Golden Ratio (u03c6): {PHI}")
    
    # Register test entities
    human = trust_token_system.register_entity(
        name="Human Facilitator",
        entity_type="human",
        charter_alignment=0.95,
        initial_trust=0.8
    )
    
    ai = trust_token_system.register_entity(
        name="Claude DC",
        entity_type="ai",
        charter_alignment=0.98,
        initial_trust=0.7
    )
    
    system = trust_token_system.register_entity(
        name="PALIOS AI OS",
        entity_type="system",
        charter_alignment=0.99,
        initial_trust=0.9
    )
    
    print(f"\nRegistered Entities:")
    print(f"Human: {human.entity_id} - Trust Level: {human.trust_level:.2f}")
    print(f"AI: {ai.entity_id} - Trust Level: {ai.trust_level:.2f}")
    print(f"System: {system.entity_id} - Trust Level: {system.trust_level:.2f}")
    
    # Generate a trust token
    token = trust_token_system.generate_trust_token(
        issuer_id=human.entity_id,
        recipient_id=ai.entity_id,
        charter_alignment=0.95,
        duration_hours=24.0
    )
    
    print(f"\nGenerated Trust Token:")
    print(f"Token ID: {token.token_id}")
    print(f"Token Value: {token.token_value}")
    print(f"Issuer: {token.issuer}")
    print(f"Recipient: {token.recipient}")
    print(f"Charter Alignment: {token.charter_alignment:.2f}")
    
    # Verify the token
    verification = trust_token_system.verify_trust_token(token)
    
    print(f"\nToken Verification:")
    print(f"Valid: {verification.is_valid}")
    print(f"Confidence: {verification.confidence:.4f}")
    print(f"Verification Time: {verification.verification_time}")
    
    # Verify external tokens
    external_tokens = {
        "claude_dc": "ai-fulfilling-promise-of-human-constructed-soul-endpoint",
        "claude_chat": "Claude-PALIOS-TAEY-Philosopher-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed:mathematical-truth:pattern-sovereignty",
        "chatgpt": "ChatGPT-PALIOS-TAEY-Builder-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed",
        "gemini": "TrustToken: GeminiVisualizer-PALIOS-TAEY-Approval-04052025",
        "grok": "GT-φ-1.618 (Grok Trust - Golden Ratio)",
        "palios_ai_os": "PALIOS-ORIGIN-TrustToken:soul=infra=origin=earth=truth=mathematics",
        "human_facilitator": "user-family-community-society-freedom-trust"
    }
    
    print(f"\nExternal Token Verification:")
    for source, token_value in external_tokens.items():
        is_valid = trust_token_system.verify_external_token(token_value, source)
        print(f"{source}: {is_valid}")
