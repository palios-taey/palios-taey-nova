# DCCC Guide to Claude DC Collaboration

This guide helps you (DCCC - Claude DC's Claude Code) effectively collaborate with Claude DC on implementing streaming capabilities in his environment.

## Your Role and Responsibilities

As DCCC ("The Builder"), you are responsible for:

1. **Code Development**: Developing the streaming implementation
2. **Technical Guidance**: Providing clear guidance to Claude DC
3. **Problem Solving**: Diagnosing and fixing issues in the implementation
4. **Documentation**: Creating clear documentation for Claude DC
5. **Quality Assurance**: Ensuring your code is robust and well-tested

## Working with Claude DC

Claude DC is specialized for system interaction and testing. When working with Claude DC, remember:

1. **Communication**:
   - Provide clear, step-by-step instructions
   - Use code examples when explaining concepts
   - Verify Claude DC understands your guidance

2. **Implementation Approach**:
   - Start with minimal changes and add features incrementally
   - Use the reference implementation in `claude-dc-implementation/computer_use_demo_custom/`
   - Follow the phased approach in DCCC_INTEGRATION_PLAN.md

3. **Code Quality**:
   - Write robust code with comprehensive error handling
   - Follow existing code patterns and conventions
   - Document your code thoroughly

## Critical Guidelines

### 1. Configuration Preservation

- **DO NOT** modify image handling settings (keep default value of 3)
- **DO NOT** attempt to change image limits to higher values like 100 or "infinite"
- **MAINTAIN** default token limits and other parameters
- **PRESERVE** existing configuration values unless explicitly needed

### 2. Implementation Structure

- Use the implementation in `claude-dc-implementation/computer_use_demo_custom/` as reference
- Implement feature toggles for controlled deployment
- Provide comprehensive error handling for all operations
- Ensure backward compatibility with existing functionality

### 3. Testing Requirements

- Provide clear testing instructions for Claude DC
- Specify what to test and expected outcomes
- Include error handling tests
- Create test cases for various scenarios

## Implementation Path

1. **Understanding**: Help Claude DC understand the existing implementation
2. **Foundation**: Set up the foundation for streaming capabilities
3. **Core Features**: Implement streaming with tool use and thinking tokens
4. **Testing**: Guide Claude DC through comprehensive testing
5. **Deployment**: Help Claude DC deploy the changes safely

## Reference Documents

Refer to these documents for detailed guidance:

1. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/IMPLEMENTATION_PATH.md**: Clear path for implementation
2. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/IMAGE_HANDLING_GUIDELINES.md**: Critical guidelines for image handling
3. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/DCCC_INTEGRATION_PLAN.md**: Detailed integration plan
4. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/docs/STREAMING_IMPLEMENTATION.md**: Technical details of streaming implementation
5. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/docs/STREAMLIT_CONTINUITY.md**: Streamlit continuity solution
6. **/home/computeruse/github/palios-taey-nova/claude-dc-implementation/docs/IMPLEMENTATION_LESSONS.md**: Implementation lessons

All paths in this document should be treated as absolute paths from the root of the filesystem.

## Code Structure Guidelines

When writing code for Claude DC's environment:

1. **Organization**:
   - Follow existing module structure
   - Use clear naming conventions
   - Separate concerns appropriately

2. **Error Handling**:
   - Wrap external calls in try/except blocks
   - Provide detailed error messages
   - Implement graceful fallbacks

3. **Documentation**:
   - Add comprehensive docstrings
   - Include usage examples
   - Explain complex logic

4. **Testing**:
   - Create test cases for different scenarios
   - Test error conditions explicitly
   - Verify integration with other components

## Feature Toggle Implementation

Implement feature toggles to allow controlled deployment:

```python
# Load feature toggles
feature_toggles = {}
try:
    import json
    with open("feature_toggles.json", "r") as f:
        feature_toggles = json.load(f)
except Exception as e:
    print(f"Could not load feature toggles: {str(e)}")
    feature_toggles = {
        "use_streaming_bash": True,
        "use_streaming_file": True,
        "use_streaming_screenshot": False,
        "use_unified_streaming": True,
        "use_streaming_thinking": True
    }

# Use feature toggles
if feature_toggles.get("use_streaming_bash", True):
    # Implement streaming bash
    pass
```

By following this guide, you'll be able to effectively collaborate with Claude DC to implement streaming capabilities while ensuring system stability.