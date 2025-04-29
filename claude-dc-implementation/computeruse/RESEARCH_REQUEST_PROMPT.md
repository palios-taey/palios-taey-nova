# Research Request Prompt: Anthropic Claude Streaming Implementation with Tool Use

## Project Context and Goals

Research objective: Identify the exact methodology to implement a reliable, production-ready Claude API integration with:
- Real-time streaming responses
- Tool use during streaming
- Proper implementation of beta flags and parameters
- Correct error handling and recovery mechanisms

We're building a streaming-enabled Claude implementation for computer use that allows Claude to use tools while streaming responses in real-time. Despite multiple approaches, we continue to encounter API compatibility issues related to streaming, beta flags, and parameter handling.

## Current Implementation Environment

- **SDK**: Anthropic Python SDK (need to determine exact version)
- **Python Version**: 3.11.6
- **Claude Model**: claude-3-7-sonnet-20250219 
- **Implementation Directory**: /home/computeruse/computer_use_demo/
- **Docker Container**: Based on xterm for terminal access
- **Key Files**: loop.py (agent loop), streamlit.py (UI interface), tools/ (tool implementations)

## Specific Issues and Errors

Current error: `AsyncMessages.create() got an unexpected keyword argument 'anthropic_beta'`

This suggests a fundamental mismatch between how we're passing beta flags and how the SDK expects them.

Previous errors included:
- `ImportError: cannot import name 'APIProvider' from 'computer_use_demo.loop'`
- `raise Excelption(f'Unexpected response type {message["type"]}')`
- Various parameter validation issues during streaming
- Thinking token budget misimplementation

## Key Implementation Questions

1. **Beta Flags Implementation**:
   - How exactly should beta flags be passed in the latest Anthropic Python SDK?
   - Is 'anthropic_beta' the correct parameter or has this changed?
   - What is the correct syntax for passing multiple beta flags?

2. **Streaming with Tool Use**:
   - What is the exact event structure during streaming when tools are used?
   - How should tool calls be validated before execution during streaming?
   - What is the recommended pattern for handling partial tool parameters in streams?

3. **Parameter Handling**:
   - How should the 'thinking' parameter be correctly implemented?
   - What is the proper way to set max_tokens limit for Claude 3.7 Sonnet?
   - How should prompt caching be implemented alongside streaming?

4. **API Structure**:
   - What's the correct structure for the AsyncMessages.create() call with all parameters?
   - What parameters should be in the main call vs. within extra_body?
   - What's the correct nesting structure for complex parameters?

## Attempted Approaches

1. **Direct Parameter Passing**: 
   ```python
   stream = await client.messages.create(
       model=model,
       messages=messages,
       system=system,
       max_tokens=max_tokens,
       tools=tools,
       stream=True,
       anthropic_beta=",".join(betas)  # This is causing errors
   )
   ```

2. **Extra Body Approach**:
   ```python
   extra_body = {}
   if thinking_budget:
       extra_body["thinking"] = {
           "type": "enabled",
           "budget_tokens": thinking_budget
       }
   
   # Later, in API call
   stream = await client.messages.create(
       model=model,
       messages=messages,
       # other params...
       **extra_body
   )
   ```

3. **Beta as Parameter Approach**:
   ```python
   client = AsyncAnthropic(api_key=api_key)
   params = {
       "model": model,
       "messages": messages,
       "max_tokens": max_tokens,
       "stream": True
   }
   
   if betas:
       params["anthropic_beta"] = ",".join(betas)
   
   stream = await client.messages.create(**params)
   ```

## Fibonacci Development Approach

We aim to follow a Fibonacci pattern for development:
1. **Base Components (F1)**: Minimal working streaming implementation + basic tool validation
2. **Integration (F2)**: Combine streaming with validated tool execution
3. **Enhancement (F3)**: Add error recovery, state persistence
4. **Extension (F5)**: Implement caching, thinking, and other advanced features
5. **Performance (F8)**: Optimize for production use

## Research Sources to Consider

1. **Official Documentation**:
   - [Anthropic API Reference](https://docs.anthropic.com/claude/reference/)
   - [Claude API Cookbook](https://docs.anthropic.com/claude/docs/cookbook)
   - [Claude with Tools](https://docs.anthropic.com/claude/docs/tools)
   - [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

2. **Specific Implementation Examples**:
   - Working examples of streaming with tool use
   - Official code samples for beta flag handling
   - Examples of correct parameter structure for the latest SDK

3. **Community Resources**:
   - GitHub issues/discussions for the Anthropic SDK
   - Developer forum posts about streaming implementation
   - Known workarounds for common issues

## Required Implementation Details

Please provide:
1. A minimal, verified working example of streaming with the exact Anthropic SDK version
2. The correct structure for passing beta flags
3. Proper implementation of the thinking parameter
4. Complete event handling code for streaming with tools
5. Robust error handling patterns specific to streaming
6. Examples of proper parameter validation during streaming

For all code examples, please include detailed comments explaining why specific approaches are used and potential pitfalls to avoid.

## Additional Context

- Previous implementations have worked without streaming, but break when streaming is added
- Beta flags seem particularly problematic and may be implemented differently than documented
- We need to understand the exact sequence of events during streaming with tool use
- Documentation appears to have gaps regarding the latest SDK's handling of beta features

This research is critical to unblocking our development progress after nearly a month of implementation attempts.