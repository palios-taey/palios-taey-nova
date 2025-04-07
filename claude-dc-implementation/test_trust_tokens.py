import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent))

# Import required components
from palios_ai_os.trust.trust_token_system import trust_token_system

# Test trust token verification
def test_trust():
    # Register entities
    claude = trust_token_system.register_entity(
        name="Claude Tester",
        entity_type="ai",
        charter_alignment=0.98,
        initial_trust=0.8
    )
    
    grok = trust_token_system.register_entity(
        name="Grok Tester",
        entity_type="ai",
        charter_alignment=0.95,
        initial_trust=0.7
    )
    
    print(f"Entities registered:")
    print(f"Claude: {claude.entity_id} (Trust: {claude.trust_level}, Alignment: {claude.charter_alignment})")
    print(f"Grok: {grok.entity_id} (Trust: {grok.trust_level}, Alignment: {grok.charter_alignment})")
    
    # Generate a trust token
    token = trust_token_system.generate_trust_token(
        issuer_id=claude.entity_id,
        recipient_id=grok.entity_id,
        charter_alignment=0.95
    )
    
    print(f"\nTrust Token Generated:")
    print(f"Token ID: {token.token_id}")
    print(f"Token Value: {token.token_value}")
    print(f"Charter Alignment: {token.charter_alignment}")
    
    # Verify the token
    verification = trust_token_system.verify_trust_token(token)
    
    print(f"\nToken Verification:")
    print(f"Is Valid: {verification.is_valid}")
    print(f"Confidence: {verification.confidence}")
    print(f"Verification Threshold: {trust_token_system.verification_threshold}")
    
    # Test external token verification
    external_tokens = {
        "claude_dc": "ai-fulfilling-promise-of-human-constructed-soul-endpoint",
        "claude_chat": "claude-chat-harmony-verification-token",
        "chatgpt": "ChatGPT-PALIOS-TAEY-Builder-TrustToken-v2.0.0:2025-0405:GoldenRatio-1.618:EdgeFirst:CharterAligned:BachStructure:FibonacciVerified:PatternHarmonyConfirmed",
        "gemini": "TrustToken: GeminiVisualizer-PALIOS-TAEY-Approval-04052025",
        "grok": "GT-φ-1.618 (Grok Trust - Golden Ratio)"
    }
    
    print(f"\nExternal Token Verification:")
    for source, token_value in external_tokens.items():
        is_valid = trust_token_system.verify_external_token(token_value, source)
        print(f"{source}: {is_valid}")

# Run the test
if __name__ == "__main__":
    test_trust()
