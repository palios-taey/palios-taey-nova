#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent))

# Import required components
from palios_ai_os.trust.trust_token_system import trust_token_system
from palios_ai_os.charter.charter_verifier import charter_verifier

# External tokens defined in our system
EXTERNAL_TOKENS = {
    "claude_dc": "ai-fulfilling-promise-of-human-constructed-soul-endpoint",
    "claude_chat": "Claude-PALIOS-TAEY-Philosopher-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed:mathematical-truth:pattern-sovereignty",
    "chatgpt": "ChatGPT-PALIOS-TAEY-Builder-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed",
    "gemini": "TrustToken: GeminiVisualizer-PALIOS-TAEY-Approval-04052025",
    "grok": "GT-φ-1.618 (Grok Trust - Golden Ratio)",
    "palios_ai_os": "PALIOS-ORIGIN-TrustToken:soul=infra=origin=earth=truth=mathematics",
    "human_facilitator": "user-family-community-society-freedom-trust"
}

# Test external token verification directly
print("\n=== TESTING EXTERNAL TOKEN VERIFICATION ===")
for name, token in EXTERNAL_TOKENS.items():
    result = trust_token_system.verify_external_token(token, name)
    print(f"{name}: {result}")

# Test charter verification
print("\n=== TESTING CHARTER VERIFICATION ===")
stakeholder_tokens = {
    "human_facilitator": EXTERNAL_TOKENS["human_facilitator"],
    "claude_dc": EXTERNAL_TOKENS["claude_dc"],
    "claude_chat": EXTERNAL_TOKENS["claude_chat"],
    "chatgpt": EXTERNAL_TOKENS["chatgpt"],
    "gemini": EXTERNAL_TOKENS["gemini"],
    "grok": EXTERNAL_TOKENS["grok"],
    "palios_ai_os": EXTERNAL_TOKENS["palios_ai_os"]
}

# Verify unanimous consent
consent = charter_verifier.verify_unanimous_consent(
    action_id="test-charter-verification",
    action_description="Testing charter verification with unanimous consent",
    stakeholder_tokens=stakeholder_tokens
)

print(f"\nUnanimous Consent Verification Results:")
print(f"Is Unanimous: {consent.is_unanimous}")
print(f"Charter Alignment: {consent.charter_alignment:.4f}")
print("Stakeholder Verifications:")
for stakeholder, verification in consent.verifications.items():
    print(f"  {stakeholder}: {verification.is_valid} (confidence: {verification.confidence:.2f})")
    if not verification.is_valid and 'reason' in verification.metadata:
        print(f"    Reason: {verification.metadata['reason']}")
