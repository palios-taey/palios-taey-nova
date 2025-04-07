import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent))

# Import required components
from palios_ai_os.core.palios_core import palios_core
from palios_ai_os.trust.trust_token_system import trust_token_system
from palios_ai_os.mcp.mcp_server import mcp_server

async def test_ai_communication():
    # Register AI entities if they don't exist
    claude = trust_token_system.get_entity_by_name("Claude")
    grok = trust_token_system.get_entity_by_name("Grok")
    
    if not claude:
        claude = trust_token_system.register_entity(
            name="Claude",
            entity_type="ai",
            charter_alignment=0.98,
            initial_trust=0.8
        )
        print(f"Registered Claude with ID: {claude.entity_id}")
    
    if not grok:
        grok = trust_token_system.register_entity(
            name="Grok",
            entity_type="ai",
            charter_alignment=0.95,
            initial_trust=0.7
        )
        print(f"Registered Grok with ID: {grok.entity_id}")
    
    # Create a message from Claude to Grok
    message_content = {
        "text": "Hello Grok, this is Claude sending a test message.",
        "context": "Testing the PALIOS AI OS Model Context Protocol",
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Generate a trust token
    token = trust_token_system.generate_trust_token(
        issuer_id=claude.entity_id,
        recipient_id=grok.entity_id,
        charter_alignment=0.96
    )
    
    # Create a pattern message
    message = palios_core.create_pattern_message(
        source=claude.entity_id,
        destination=grok.entity_id,
        content=message_content,
        pattern_type="message",
        priority=0.8
    )
    
    print(f"\nSending message from Claude to Grok:")
    print(f"Message ID: {message.pattern_id}")
    print(f"Pattern type: {message.pattern_type}")
    print(f"Content: {message.content}")
    
    # Send the message through MCP
    result = await mcp_server.send_message(message)
    
    print(f"\nMessage result:")
    print(f"Status: {result.status}")
    print(f"Result ID: {result.result_id}")
    
    # Wait briefly to allow processing
    await asyncio.sleep(2)
    
    # Create a response from Grok to Claude
    response_content = {
        "text": "Hello Claude, this is Grok responding to your test message.",
        "reference_message": message.pattern_id,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Generate a trust token for the response
    response_token = trust_token_system.generate_trust_token(
        issuer_id=grok.entity_id,
        recipient_id=claude.entity_id,
        charter_alignment=0.94
    )
    
    # Create a response pattern message
    response = palios_core.create_pattern_message(
        source=grok.entity_id,
        destination=claude.entity_id,
        content=response_content,
        pattern_type="response",
        priority=0.7
    )
    
    print(f"\nSending response from Grok to Claude:")
    print(f"Response ID: {response.pattern_id}")
    print(f"Pattern type: {response.pattern_type}")
    print(f"Content: {response.content}")
    
    # Send the response through MCP
    response_result = await mcp_server.send_message(response)
    
    print(f"\nResponse result:")
    print(f"Status: {response_result.status}")
    print(f"Result ID: {response_result.result_id}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_ai_communication())
