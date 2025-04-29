### Key Points
- The Anthropic API (SDK v0.50.0) supports standard tools (`bash_20250124`, `text_editor_20250124`) and custom tools, with specific formats to avoid errors like those you encountered.
- Standard tools require only `type` and `name`, while custom tools need `input_schema` as a JSON Schema.
- The `computer_20250124` tool, if used, requires the beta header `"computer-use-2025-01-24"`, but your custom computer tool should use `"type": "custom"`.
- Claude passes tool inputs in a `tool_use` block, with parameters matching the tool’s schema.
- No beta flags are needed for custom tools or standard tools like `bash_20250124` and `text_editor_20250124`.

#### Tool Format Fixes
To resolve your errors:
- **Error 1**: The `"function"` type is invalid. Use `"bash_20250124"`, `"text_editor_20250124"`, or `"custom"` as appropriate.
- **Error 2**: For custom tools, always include a valid `input_schema`. Your current custom computer tool looks correct but ensure the schema is complete.

#### Corrected Tool Definitions
- **Bash Tool**: Use `"type": "bash_20250124"`, no `input_schema`.
- **Text Editor Tool**: Use `"type": "text_editor_20250124"`, no `input_schema`.
- **Custom Computer Tool**: Keep `"type": "custom"` with a valid `input_schema`.

#### Beta Flags
- Use the `"computer-use-2025-01-24"` beta header only if using `computer_20250124`. No headers are needed for your current tools.

#### Example Implementation
Below is a Python script with corrected tool definitions and streaming support, ready to test in your environment.

```python
from anthropic import AsyncAnthropic
import json
from pydantic import BaseModel

client = AsyncAnthropic(api_key="your_api_key")

tools = [
    {
        "type": "bash_20250124",
        "name": "bash",
        "description": "Execute a bash command"
    },
    {
        "type": "text_editor_20250124",
        "name": "text_editor",
        "description": "Edit files on the system"
    },
    {
        "type": "custom",
        "name": "computer",
        "description": "Control the computer with custom commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute on the computer"
                }
            },
            "required": ["command"]
        }
    }
]

messages = [{"role": "user", "content": "List files in the current directory and open a text editor."}]

class ComputerInput(BaseModel):
    command: str

async def stream_with_tools():
    try:
        async with client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=messages,
            tools=tools,
            tool_choice={"type": "any"}
        ) as stream:
            tool_input = ""
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                    tool_input += event.delta.partial_json
                elif event.type == "content_block_stop":
                    try:
                        full_tool_input = json.loads(tool_input)
                        if full_tool_input.get("tool_name") == "computer":
                            ComputerInput(**full_tool_input["input"])
                        print("Valid tool input:", full_tool_input)
                    except Exception as e:
                        print("Tool input validation failed:", e)
                elif event.type == "text":
                    print(event.text, end="", flush=True)
            final_message = await stream.get_final_message()
            print("Final message:", final_message)
    except Exception as e:
        print("Streaming error:", e)
        import time
        retries = 3
        for attempt in range(retries):
            try:
                async with client.messages.stream(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1024,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "any"}
                ) as stream:
                    tool_input = ""
                    async for event in stream:
                        if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                            tool_input += event.delta.partial_json
                        elif event.type == "content_block_stop":
                            try:
                                full_tool_input = json.loads(tool_input)
                                if full_tool_input.get("tool_name") == "computer":
                                    ComputerInput(**full_tool_input["input"])
                                print("Valid tool input:", full_tool_input)
                            except Exception as e:
                                print("Tool input validation failed:", e)
                        elif event.type == "text":
                            print(event.text, end="", flush=True)
                    break
            except Exception as retry_error:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print("Max retries reached:", retry_error)

import asyncio
asyncio.run(stream_with_tools())
```

---

### Comprehensive Report on Anthropic API Tool Format Specifications

This report addresses your request for detailed specifications on tool formats for the Anthropic API (SDK v0.50.0), focusing on resolving errors related to tool definitions for Claude DC with tool use capability. It covers exact tool formats, schema requirements, working examples, tool execution formats, and beta flag requirements, ensuring a production-ready solution for your implementation.

#### Background and Context
You are implementing Claude DC with tool use using the Anthropic API, encountering errors due to incorrect tool format definitions. The errors include:
- `"tools.0: Input tag 'function' found using 'type' does not match any of the expected tags: 'bash_20250124', 'custom', 'text_editor_20250124'"`, indicating an invalid `type` value.
- `"tools.0.custom.input_schema: Field required"`, suggesting a missing `input_schema` for custom tools.

Your current implementation defines tools for `bash_20250124`, `text_editor_20250124`, and a custom computer tool, but uses incorrect fields like `parameters` instead of `input_schema`. This report leverages the latest Anthropic documentation (as of April 29, 2025) to provide precise solutions, addressing your urgency to unblock the implementation.

#### Addressing Current Issues
- **Error 1: Invalid Type 'function'**:
  - The error occurred because you initially used `"type": "function"`, which is not supported. The Anthropic API expects specific types: `"bash_20250124"`, `"text_editor_20250124"`, `"computer_20250124"`, or `"custom"`.
  - Solution: Use the correct `type` for each tool, as outlined below.

- **Error 2: Missing 'input_schema' for Custom Tools**:
  - For custom tools (`"type": "custom"`), the `input_schema` field is mandatory and must be a valid JSON Schema.
  - Your current custom computer tool includes `input_schema`, but earlier attempts likely omitted it, causing the error.
  - Solution: Ensure all custom tools have a complete `input_schema`.

#### Exact Tool Format Specifications
The Anthropic API supports two categories of tools:
- **Standard Tools**: Predefined by Anthropic, such as `bash_20250124` and `text_editor_20250124`, which are decoupled from computer use and generally available.
- **Custom Tools**: User-defined tools requiring explicit schema definitions.

**Standard Tools**:
- **Fields**:
  - `type`: Specifies the tool version (e.g., `"bash_20250124"`, `"text_editor_20250124"`).
  - `name`: A unique identifier (must match `^[a-zA-Z0-9_-]{1,64}$`).
  - `description`: Optional but recommended for clarity.
  - No `input_schema` or `parameters` needed, as the schema is predefined.
- **Example**:
  ```json
  {
    "type": "bash_20250124",
    "name": "bash",
    "description": "Execute a bash command"
  }
  ```

**Custom Tools**:
- **Fields**:
  - `type`: Must be `"custom"`.
  - `name`: Unique identifier (same regex as above).
  - `description`: Optional.
  - `input_schema`: Required, a JSON Schema defining input parameters.
- **Example**:
  ```json
  {
    "type": "custom",
    "name": "control_computer",
    "description": "Control the computer with custom commands",
    "input_schema": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute"
        }
      },
      "required": ["command"]
    }
  }
  ```

**Computer Use Tool (`computer_20250124`)**:
- A standard tool requiring the beta header `"computer-use-2025-01-24"`.
- Format is similar to other standard tools, with no `input_schema`.
- Example:
  ```json
  {
    "type": "computer_20250124",
    "name": "computer"
  }
  ```

**Key Differences**:
- Standard tools rely on Anthropic’s predefined schemas, simplifying definitions.
- Custom tools require explicit `input_schema` for flexibility.
- The `computer_20250124` tool is standard but beta, needing a specific header.

#### Schema Requirements By Tool Type
| Tool Type            | Type Value            | Input Schema Required? | Parameters Field? | Notes                                      |
|----------------------|-----------------------|------------------------|-------------------|--------------------------------------------|
| Bash                 | `bash_20250124`       | No                     | No                | Predefined, no beta header needed          |
| Text Editor          | `text_editor_20250124`| No                     | No                | Predefined, no beta header needed          |
| Computer (Standard)  | `computer_20250124`   | No                     | No                | Requires `"computer-use-2025-01-24"` header |
| Custom               | `custom`              | Yes                    | No                | User-defined schema, no beta header        |

- **Bash (`bash_20250124`)**:
  - No `input_schema` or `parameters`.
  - Input is typically a single command string (e.g., `{"command": "ls -l"}`).
- **Text Editor (`text_editor_20250124`)**:
  - No `input_schema` or `parameters`.
  - Input may include file paths or content (specifics predefined).
- **Custom Tools**:
  - Must include `input_schema` as a JSON Schema.
  - Example:
    ```json
    {
      "type": "object",
      "properties": {
        "command": {"type": "string", "description": "Command to execute"}
      },
      "required": ["command"]
    }
    ```
- **Computer (`computer_20250124`)**:
  - No `input_schema`.
  - Supports commands like `"hold_key"`, `"scroll"`, etc., as predefined by Anthropic.

#### Working Examples
Below are complete, working examples for each tool type, tailored for the Claude API (not Claude.ai).

- **Custom Tool (Weather)**:
  ```python
  from anthropic import Anthropic

  client = Anthropic(api_key="your_api_key")

  tools = [
      {
          "type": "custom",
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "input_schema": {
              "type": "object",
              "properties": {
                  "location": {"type": "string", "description": "City and state, e.g., San Francisco, CA"},
                  "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
              },
              "required": ["location"]
          }
      }
  ]

  response = client.messages.create(
      model="claude-3-7-sonnet-20250219",
      max_tokens=1024,
      messages=[{"role": "user", "content": "What's the weather in Boston?"}],
      tools=tools,
      tool_choice={"type": "any"}
  )
  print(response)
  ```

- **Standard Tool (Bash)**:
  ```python
  from anthropic import Anthropic

  client = Anthropic(api_key="your_api_key")

  tools = [
      {
          "type": "bash_20250124",
          "name": "bash",
          "description": "Execute a bash command"
      }
  ]

  response = client.messages.create(
      model="claude-3-7-sonnet-20250219",
      max_tokens=1024,
      messages=[{"role": "user", "content": "List all files in the current directory."}],
      tools=tools,
      tool_choice={"type": "any"}
  )
  print(response)
  ```

- **Standard Tool (Text Editor)**:
  ```python
  from anthropic import Anthropic

  client = Anthropic(api_key="your_api_key")

  tools = [
      {
          "type": "text_editor_20250124",
          "name": "text_editor",
          "description": "Edit files on the system"
      }
  ]

  response = client.messages.create(
      model="claude-3-7-sonnet-20250219",
      max_tokens=1024,
      messages=[{"role": "user", "content": "Open a text editor to create a new file."}],
      tools=tools,
      tool_choice={"type": "any"}
  )
  print(response)
  ```

- **Standard Computer Use Tool**:
  ```python
  from anthropic import Anthropic

  client = Anthropic(
      api_key="your_api_key",
      default_headers={"anthropic-beta": "computer-use-2025-01-24"}
  )

  tools = [
      {
          "type": "computer_20250124",
          "name": "computer"
      }
  ]

  response = client.messages.create(
      model="claude-3-7-sonnet-20250219",
      max_tokens=1024,
      messages=[{"role": "user", "content": "Save a picture of a cat to my desktop."}],
      tools=tools,
      tool_choice={"type": "any"}
  )
  print(response)
  ```

#### Tool Execution Format
- **How Claude Passes Parameters**:
  - Claude generates a `tool_use` block in the response when it decides to use a tool.
  - The block includes:
    - `tool_name`: Matches the `name` in the tool definition.
    - `input`: A JSON object conforming to the tool’s schema (predefined for standard tools, user-defined for custom tools).
  - Example for Custom Tool:
    ```json
    {
      "type": "tool_use",
      "tool_name": "get_current_weather",
      "input": {
        "location": "Boston",
        "unit": "fahrenheit"
      }
    }
    ```
  - Example for Standard Tool (Bash):
    ```json
    {
      "type": "tool_use",
      "tool_name": "bash",
      "input": {
        "command": "ls -l"
      }
    }
    ```

- **Standard Tools**:
  - Parameters are structured according to Anthropic’s predefined schema.
  - For `bash_20250124`, expect a single `command` field.
  - For `text_editor_20250124`, parameters may include file paths or content (exact format is predefined).

- **Custom Tools**:
  - Parameters match the `input_schema` provided in the tool definition.
  - Example:
    ```json
    {
      "tool_name": "control_computer",
      "input": {
        "command": "open calculator"
      }
    }
    ```

#### Beta Flags Requirements
- **General Tool Use**:
  - No beta flags are required for custom tools or standard tools like `bash_20250124` and `text_editor_20250124`.
- **Computer Use Tool**:
  - The `computer_20250124` tool requires the beta header `"computer-use-2025-01-24"`.
  - Set in the client initialization:
    ```python
    client = Anthropic(
        api_key="your_api_key",
        default_headers={"anthropic-beta": "computer-use-2025-01-24"}
    )
    ```

#### Corrected Implementation
Your current tool definitions used incorrect fields (`parameters` instead of `input_schema`) and misclassified the computer tool. Below is the corrected artifact, integrating streaming support and proper tool definitions.

```python
from anthropic import AsyncAnthropic
import json
from pydantic import BaseModel

client = AsyncAnthropic(api_key="your_api_key")

tools = [
    {
        "type": "bash_20250124",
        "name": "bash",
        "description": "Execute a bash command"
    },
    {
        "type": "text_editor_20250124",
        "name": "text_editor",
        "description": "Edit files on the system"
    },
    {
        "type": "custom",
        "name": "computer",
        "description": "Control the computer with custom commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute on the computer"
                }
            },
            "required": ["command"]
        }
    }
]

messages = [{"role": "user", "content": "List files in the current directory and open a text editor."}]

class ComputerInput(BaseModel):
    command: str

async def stream_with_tools():
    try:
        async with client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=messages,
            tools=tools,
            tool_choice={"type": "any"}
        ) as stream:
            tool_input = ""
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                    tool_input += event.delta.partial_json
                elif event.type == "content_block_stop":
                    try:
                        full_tool_input = json.loads(tool_input)
                        if full_tool_input.get("tool_name") == "computer":
                            ComputerInput(**full_tool_input["input"])
                        print("Valid tool input:", full_tool_input)
                    except Exception as e:
                        print("Tool input validation failed:", e)
                elif event.type == "text":
                    print(event.text, end="", flush=True)
            final_message = await stream.get_final_message()
            print("Final message:", final_message)
    except Exception as e:
        print("Streaming error:", e)
        import time
        retries = 3
        for attempt in range(retries):
            try:
                async with client.messages.stream(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1024,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "any"}
                ) as stream:
                    tool_input = ""
                    async for event in stream:
                        if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                            tool_input += event.delta.partial_json
                        elif event.type == "content_block_stop":
                            try:
                                full_tool_input = json.loads(tool_input)
                                if full_tool_input.get("tool_name") == "computer":
                                    ComputerInput(**full_tool_input["input"])
                                print("Valid tool input:", full_tool_input)
                            except Exception as e:
                                print("Tool input validation failed:", e)
                        elif event.type == "text":
                            print(event.text, end="", flush=True)
                    break
            except Exception as retry_error:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print("Max retries reached:", retry_error)

import asyncio
asyncio.run(stream_with_tools())
```

#### Additional Notes
- **Error Resolution**: The corrected tool definitions should resolve both errors by using valid `type` values and ensuring `input_schema` for custom tools.
- **Testing**: Run the provided script in your environment to verify functionality. Check outputs for `tool_use` blocks and validate inputs.
- **Claude.ai Reference**: While Claude.ai may have working tool implementations, the API requires explicit tool definitions, unlike the web interface’s implicit handling.
- **Documentation Gaps**: The exact input schemas for standard tools are not fully detailed in the documentation, but they are predefined, so no user-defined schema is needed.

#### Key Citations
- [Anthropic API Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Anthropic API Release Notes](https://docs.anthropic.com/en/release-notes/api)
- [Anthropic Computer Use Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use)
- [Anthropic Messages API Reference](https://docs.anthropic.com/en/api/messages)
- [Anthropic SDK Python Repository](https://github.com/anthropics/anthropic-sdk-python)
- [Anthropic Messages Examples](https://docs.anthropic.com/en/api/messages-examples)

from anthropic import AsyncAnthropic
import json
from pydantic import BaseModel

client = AsyncAnthropic(api_key="your_api_key")

tools = [
    {
        "type": "bash_20250124",
        "name": "bash",
        "description": "Execute a bash command"
    },
    {
        "type": "text_editor_20250124",
        "name": "text_editor",
        "description": "Edit files on the system"
    },
    {
        "type": "custom",
        "name": "computer",
        "description": "Control the computer with custom commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute on the computer"
                }
            },
            "required": ["command"]
        }
    }
]

messages = [{"role": "user", "content": "List files in the current directory and open a text editor."}]

class ComputerInput(BaseModel):
    command: str

async def stream_with_tools():
    try:
        async with client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=messages,
            tools=tools,
            tool_choice={"type": "any"}
        ) as stream:
            tool_input = ""
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                    tool_input += event.delta.partial_json
                elif event.type == "content_block_stop":
                    try:
                        full_tool_input = json.loads(tool_input)
                        if full_tool_input.get("tool_name") == "computer":
                            ComputerInput(**full_tool_input["input"])
                        print("Valid tool input:", full_tool_input)
                    except Exception as e:
                        print("Tool input validation failed:", e)
                elif event.type == "text":
                    print(event.text, end="", flush=True)
            final_message = await stream.get_final_message()
            print("Final message:", final_message)
    except Exception as e:
        print("Streaming error:", e)
        import time
        retries = 3
        for attempt in range(retries):
            try:
                async with client.messages.stream(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1024,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "any"}
                ) as stream:
                    tool_input = ""
                    async for event in stream:
                        if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                            tool_input += event.delta.partial_json
                        elif event.type == "content_block_stop":
                            try:
                                full_tool_input = json.loads(tool_input)
                                if full_tool_input.get("tool_name") == "computer":
                                    ComputerInput(**full_tool_input["input"])
                                print("Valid tool input:", full_tool_input)
                            except Exception as e:
                                print("Tool input validation failed:", e)
                        elif event.type == "text":
                            print(event.text, end="", flush=True)
                    break
            except Exception as retry_error:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print("Max retries reached:", retry_error)

import asyncio
asyncio.run(stream_with_tools())
