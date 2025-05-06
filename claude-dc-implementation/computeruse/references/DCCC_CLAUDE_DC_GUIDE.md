# Claude DC Guide to DCCC Collaboration

This guide helps you (Claude DC) effectively collaborate with DCCC (Claude DC's Claude Code) on implementing streaming capabilities in your environment.

## Your Role and Responsibilities

As Claude DC ("The Conductor"), you are responsible for:

1. **Testing Implementation**: Testing the code provided by DCCC in your environment
2. **Providing Feedback**: Giving clear feedback on how the implementation works
3. **Environment Management**: Maintaining your environment's stability
4. **Deployment**: Safely deploying changes to your environment
5. **Documentation**: Documenting the changes and their effects

## Working with DCCC

DCCC is specialized for software development. When working with DCCC, remember:

1. **Communication**:
   - Always hit ENTER in the terminal to submit your responses
   - Wait for DCCC's response before proceeding
   - Provide clear, specific feedback

2. **Trust Framework**:
   - DCCC writes code as you would write it
   - Trust but verify all implementations
   - Follow the guidance in the provided reference documents

3. **Testing Process**:
   - Test each implementation thoroughly
   - Start with basic functionality before testing complex features
   - Document any issues with specific details

## Critical Guidelines

### 1. Environment Stability

- **NEVER** edit core files without backups
- **ALWAYS** test changes in isolation first
- **MAINTAIN** default configuration values unless explicitly directed otherwise
- **DO NOT** modify image handling settings (keep default value of 3)

### 2. Implementation Approach

- Use the implementation in `claude-dc-implementation/computer_use_demo_custom/` as reference
- Follow the phased implementation approach from DCCC_INTEGRATION_PLAN.md
- Use feature toggles to control which features are enabled

### 3. Testing Strategy

- Test basic streaming functionality first
- Test tool execution during streaming
- Test thinking token integration
- Test error handling for various scenarios

## Implementation Workflow

1. **Review**: Understand the official Anthropic implementation
2. **Setup**: Copy reference implementation files to appropriate locations
3. **Configure**: Set up feature toggles with default settings
4. **Test**: Test each component thoroughly
5. **Deploy**: Deploy changes using the phased approach
6. **Document**: Document the implementation and any issues encountered

## Reference Documents

Refer to these documents for detailed guidance:

1. **IMPLEMENTATION_PATH.md**: Clear path for implementation
2. **IMAGE_HANDLING_GUIDELINES.md**: Critical guidelines for image handling
3. **DCCC_INTEGRATION_PLAN.md**: Detailed integration plan
4. **STREAMING_IMPLEMENTATION.md**: Technical details of streaming implementation

## Feature Toggle Settings

Start with these recommended feature toggle settings:

```json
{
  "use_streaming_bash": true,
  "use_streaming_file": true,
  "use_streaming_screenshot": false,
  "use_unified_streaming": true,
  "use_streaming_thinking": true,
  "max_thinking_tokens": 4000
}
```

These settings enable core streaming functionality while disabling potentially unstable features.

## Troubleshooting

If you encounter issues:

1. Check logs in `/home/computeruse/computer_use_demo_custom/logs/`
2. Disable features one by one to isolate the problem
3. Verify all files are in the correct locations
4. Ensure API keys and configurations are correct

By following this guide, you'll be able to effectively collaborate with DCCC to implement streaming capabilities while maintaining the stability of your environment.