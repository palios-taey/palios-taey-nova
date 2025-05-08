# Testing the Streaming Implementation

This guide provides instructions for testing the streaming implementation in the Claude DC environment.

## Prerequisites

Before testing the streaming implementation, ensure you have:

1. A valid Anthropic API key with access to Claude-3 models
2. Python 3.9 or higher installed
3. The Anthropic Python SDK (v0.5.0 or higher) installed

You can verify your setup with:

```bash
python streaming/verify_setup.py
```

## Testing Process

The testing process follows a phased approach to validate different aspects of the streaming implementation:

### Phase 1: Basic Streaming

This phase tests the basic streaming functionality without tool use:

```bash
python streaming/non_interactive_test.py
```

This script sends predefined messages to Claude and displays the streaming responses token-by-token.

### Phase 2: Tool Use During Streaming

This phase tests tool use during streaming responses:

```bash
python streaming/non_interactive_tool_test.py
```

This script sends messages that encourage Claude to use the bash tool, then executes the commands and sends the results back to Claude during streaming.

### Phase 3: Integration Testing

This phase tests the integration between the streaming implementation and the original Claude DC environment:

```bash
python streaming/integration_test.py --phase phase1
```

You can test different phases of the integration:

- `phase1`: Basic streaming with bash tool only
- `phase2`: Streaming with both bash and file tools
- `phase3`: Streaming with bash, file, and thinking capabilities

### Full Testing Suite

To run all tests in sequence:

```bash
./streaming/run_tests.sh
```

This script runs the verification, basic streaming test, tool streaming test, and integration tests in order.

## Troubleshooting

If you encounter issues during testing:

1. Check the logs in `streaming/logs/` for detailed error information
2. Verify that your API key is valid and has access to the required models
3. Check that the feature toggles are set correctly in `streaming/feature_toggles.json`
4. Ensure you have the correct version of the Anthropic SDK installed

Common issues:

- **Authentication errors**: Verify your API key is set correctly
- **Model access errors**: Ensure you have access to the Claude-3 model you're trying to use
- **Tool execution errors**: Check that the tool definitions match what Claude expects

## Next Steps

After successful testing, you can integrate the streaming implementation with the production environment by:

1. Setting the `use_unified_streaming` toggle to `true` in `streaming/feature_toggles.json`
2. Using the `streaming_integration.py` module as the entry point for Claude DC
3. Gradually enabling more features through the feature toggles