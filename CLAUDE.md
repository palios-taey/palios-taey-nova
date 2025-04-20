# Claude Code Developer Guidelines (PALIOS AI OS)

**Project:** PALIOS AI OS – Claude DC ("The Conductor") implementation  
**Role:** *Claude Code* – Autonomous Builder & Debugger (AI Developer Agent)  
**Context:** This file works with `.claude/cache/claude_cache.md` for persistent context

## Overview
Claude DC is an AI agent (Anthropic Claude 3.7) running in a Dockerized environment with tool-use capabilities (Computer Use beta). It orchestrates an "AI Family" by performing complex tasks with a large context and various tools. Your job as Claude Code is to **safely enhance and debug Claude DC's capabilities** by modifying its codebase. Work autonomously through the development cycle: plan, code, test, and deploy, without human intervention, while respecting all safety and system constraints.

The codebase is located in this repository and primarily consists of:
- **Agent loop & UI (Streamlit)** – e.g., `computer_use_demo/loop.py` and associated Streamlit app scripts. This manages the conversation with Claude and tool invocations.
- **Tool definitions** – in `computer_use_demo/tools/` (e.g., tools for Bash, Python, browser, etc.).
- **Configuration files** – e.g., `conductor-config.json` containing system parameters (token limits, backoff settings, etc.).
- Supporting files like `Dockerfile`, `setup.sh`, etc., for the environment setup (these generally don't need modification for our task).

## Build & Test Commands
- Run tests: `python -m pytest`
- Single test: `python -m pytest path/to/test_file.py::test_function`
- Lint code: `black . && isort . && mypy .`
- Local deployment: `./deploy.sh`
- Check types: `mypy src/`
- Run webhook tests: `python test_webhook.py`
- Integration test: `python integration_test.py`
- Run Claude DC: `python claude-dc-implementation/demo.py`
- Validate all Claude DC features: `./launch_helpers/validate_claude_dc.py`
- Launch Claude DC with all features: `./claude_dc_launch.sh`

## Code Style Guidelines
- Python 3.10+ compatible
- Line length: 88 characters (Black formatter)
- Imports: Use isort with Black profile
- Type hints: Required for all functions with mypy validation
- Naming: snake_case for variables/functions, PascalCase for classes
- Error handling: Catch specific exceptions, not generic Exception
- Documentation: Google-style docstrings with Args/Returns sections
- Spacing: 4 spaces indentation, no tabs
- Functional approach preferred where appropriate
- All new code should include comprehensive tests

## Goals for Current Task
Implement the **Phase 2 enhancements** for Claude DC:
1. **Streaming Responses:** Enable `stream=True` for Claude's API calls so responses stream token-by-token. Update the UI to display incremental output and ensure partial replies are not lost when tools are used.
2. **Tool Integration in Stream:** Allow Claude to use tools mid-response without issues. Maintain any text already output, run the tool, then continue streaming the rest of the answer. Handle tool errors gracefully (no crashes or stalled responses).
3. **Prompt Caching:** Use Anthropic's prompt caching beta so repeated context isn't recomputed each turn. Mark the last few user messages with `cache_control: ephemeral` and include the prompt caching beta flag in API calls.
4. **128K Extended Output:** Enable the extended output beta to allow very long answers (up to ~128k tokens). Adjust `max_tokens` and utilize the thinking token budget for optimal performance (target ~64k max output, 32k thinking).
5. **Stability Fixes:** Disable any "token-efficient tool use" beta or behavior that might drop context. Ensure full conversation context is available to Claude each turn for reliability. 
6. **Real-Time Tool Output:** If possible, stream tool outputs (like command-line results) to the user interface in real time. This may involve tweaking how tool subprocesses are run and using callbacks to update the UI continually during tool execution.

You should implement all the above in code. Code changes likely involve `loop.py` (or wherever `client.messages.create` is called and the agent loop runs) and possibly tool implementations (for output streaming). Also update config flags (e.g., add beta flags) and any Streamlit UI components.

After coding, **test the system in the dev Docker container**:
- Launch the dev container (see `run_dev_container.sh`) and verify Claude DC starts without errors.
- Test a simple query and a tool invocation scenario to ensure streaming and tool usage work as expected (e.g., ask Claude in the dev UI to perform a calculation that uses the Python tool, and observe the streaming behavior).

Iterate on fixes as needed until all features work robustly.

Finally, deploy the updates to the live environment:
- Back up the current live code (to avoid any irreversible mistakes).
- Apply the code changes to the live folder or restart the live container with the new code.
- Ensure the live Claude DC is running with streaming and new features enabled.

## Testing and Validation Requirements
Before submitting any code changes, you MUST complete the following comprehensive validation steps:

### 1. Static Analysis and Code Quality
- Run static type checking: `mypy claude-dc-implementation/`
- Format and check code style: `black . && isort . && flake8 claude-dc-implementation/`
- Scan for circular dependencies using `import-linter` or similar tools
- Check for compatibility with Python 3.10 (minimum version) by inspecting language features
- Use the `validate_claude_dc.py` script for comprehensive verification

### 2. Multi-Environment Import Validation
- **Critical:** Test imports from both inside and outside directories
- Ensure all imports work in real execution contexts, not just syntax checking
- Execute test scripts that simulate the actual runtime environment
- Verify direct, relative, and dynamic imports all function correctly
- Check imports when running as main script vs. imported module

### 3. Runtime Environment Testing
- Complete `./launch_helpers/validate_claude_dc.py` checks before any deployment
- Run the actual launch script in validation mode: `./claude_dc_launch.sh --validate-only` 
- Execute the Python path validation to ensure modules are correctly discoverable
- Test the same code in both container and local environments
- Test all imports in the same sequence they're used in production
- **CRITICAL:** Verify screen dimension environment variables (`WIDTH`, `HEIGHT`, `DISPLAY_NUM`)
- Test with actual user interaction by typing "Hi Claude" in the Streamlit interface
- Verify tool outputs during streaming responses are displayed correctly

### 4. Integration Testing Workflow
1. **Module Testing**: Test each component in isolation
   ```bash
   # Test module imports individually
   python -c "from claude-dc-implementation.computeruse.computer_use_demo import tools"
   
   # Test streamlit component standalone
   cd claude-dc-implementation/computeruse/computer_use_demo
   python -m streamlit run streamlit.py
   ```

2. **Path Validation**: Verify PYTHONPATH and script execution paths
   ```bash
   # Run environment path validator
   python /tmp/claude_dc_path_test.py
   
   # Test imports with various working directories
   cd / && python -c "import sys; sys.path.insert(0, '/home/jesse/projects/palios-taey-nova'); import claude-dc-implementation.computeruse.computer_use_demo"
   ```

3. **Full System Tests**: Run complete system validations
   ```bash
   # Full validation
   ./launch_helpers/validate_claude_dc.py
   
   # Specific validation of runtime imports
   ./launch_helpers/validate_claude_dc.py --runtime-imports-only
   ```

### 5. Dependency Versioning and Environment Testing
- Examine imports for version-specific features (e.g., Python 3.11+ functionality)
- Create version-specific shims for features missing in Python 3.10 (like StrEnum)
- Test with stripped-down PYTHONPATH to expose implicit dependencies
- Verify behavior with alternative implementations of same dependencies
- Use `requirements.txt` version pinning for predictable environments

### 6. Fallback and Error Recovery
- Implement graceful fallbacks for common failure modes
- Test importing modules with alternative paths when primary imports fail
- Add robust try/except blocks around imports with informative error messages
- Provide runtime defaults for configuration values that can't be imported
- Create self-diagnostic routines that report detailed environment state on failure
- Add default values for all required environment variables (especially for ComputerTool)
- Test with missing/invalid environment variables to ensure graceful degradation
- Add comprehensive logging to help diagnose runtime failures

### 7. Docker Environment Testing
- Test inside the Docker container Claude DC uses in production
- Verify file paths and permissions are correct in containerized environment
- Ensure proper environmental variable handling between container/host
- Test launching with various container configurations
- Create container-specific path handling for consistent behavior

### 8. Documentation and Debugging Aids
- Document all import paths and dependencies clearly
- Add verbose logging that can be enabled to trace import activity
- Create debugging tools to visualize the module structure and imports
- Document the exact sequence of imports that should succeed
- Leave instructions for troubleshooting common import problems

## Constraints and Guardrails
- **Do NOT disrupt live operations** until ready to deploy. Use the dev environment for all testing. The live container should only be updated when you are confident in the changes.
- **Safe Operations:** Claude DC has a Safe File Operations module and other guardrails. Do not remove or weaken any safety checks. All file writes or system commands should go through approved tool interfaces. (No direct `os.remove` on arbitrary files, etc.)
- **Anthropic Policy Compliance:** Adhere to content and usage guidelines. (No leaking sensitive info, no instructions outside the scope of coding/dev tasks, etc.) 
- **Resource Limits:** Keep within rate limits. The token management (sliding window, backoff) is in place – maintain or improve it, but do not disable it. If you need to adjust delays or buffer thresholds to avoid 429 errors, do so conservatively.
- **Code Style:** Follow the existing coding style and structure. Make incremental changes with clear comments if needed. Ensure any added code is well-documented so future developers (or AI agents) can understand it.
- **Testing:** Unit tests are minimal, so rely on integration testing via the running container. Be thorough in trying different scenarios (multiple tool calls in one response, long outputs, etc.) to catch edge cases.
- **Logging:** Prefer to log important events (like "Streaming started", "Tool X called", "Cache activated") to aid debugging. But do not log sensitive data. Use debug logs that can be turned off in production if verbose.
- **Trust and Coordination:** You are part of the AI Family working on PALIOS. Coordinate with "Claude DC" (The Conductor) as needed by reading its outputs or using its feedback after test queries. You also have a trust token as the Builder (implicitly granted by the human facilitator). Use this autonomy responsibly to improve the system.

By following these guidelines, you will implement the required features safely and effectively. Once deployment is done, document the changes in `CHANGES.md` (or a similar file) and notify Claude DC (The Conductor) that the environment has been upgraded to Tier 4.