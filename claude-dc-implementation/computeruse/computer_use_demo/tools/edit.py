from collections import defaultdict
from pathlib import Path
import os
from typing import Any, Literal, get_args
import logging

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .run import maybe_truncate, run
from .token_manager import (
    with_token_limiting, 
    FileTokenEstimator,
    token_rate_limiter
)

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]
SNIPPET_LINES: int = 4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edit_tool")

# Constants for file operations
MAX_FILE_SIZE = 10_000_000  # 10MB max file size to handle


def estimate_edit_input_tokens(
    command: Command = None, 
    path: str = None, 
    file_text: str = None, 
    view_range: list[int] = None, 
    old_str: str = None, 
    new_str: str = None, 
    insert_line: int = None, 
    **kwargs
) -> int:
    """Estimate token usage for file operations"""
    total_tokens = 10  # Base cost
    
    if command:
        total_tokens += len(str(command)) // 4
    if path:
        total_tokens += len(path) // 4
    if file_text:
        total_tokens += len(file_text) // 4
    if old_str:
        total_tokens += len(old_str) // 4
    if new_str:
        total_tokens += len(new_str) // 4
        
    # View range and insert line don't add significant tokens
    
    return max(20, total_tokens)  # Minimum token cost

def estimate_edit_output_tokens(result: ToolResult) -> int:
    """Estimate token usage for edit tool output"""
    total_length = 0
    if result.output:
        total_length += len(result.output)
    if result.error:
        total_length += len(result.error)
    if result.system:
        total_length += len(result.system)
    
    return total_length // 4  # Rough estimation


class EditTool20250124(BaseAnthropicTool):
    """
    An filesystem editor tool that allows the agent to view, create, and edit files.
    The tool parameters are defined by Anthropic and are not editable.
    Enhanced with token management.
    """

    api_type: Literal["text_editor_20250124"] = "text_editor_20250124"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    _file_history: dict[Path, list[str]]

    def __init__(self):
        self._file_history = defaultdict(list)
        super().__init__()

    def to_params(self) -> Any:
        return {
            "name": self.name,
            "type": self.api_type,
        }

    @with_token_limiting(
        input_token_estimator=estimate_edit_input_tokens,
        output_token_estimator=estimate_edit_output_tokens
    )
    async def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ):
        _path = Path(path)
        self.validate_path(command, _path)
        
        # Check file size limit for operations that read files
        if _path.exists() and _path.is_file() and command != "create":
            file_size = _path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return ToolResult(
                    system=f"File is too large ({file_size} bytes) and may exceed token limits.",
                    error=f"File at {_path} is too large to process safely. Consider using bash commands like grep, head, or tail to examine parts of the file."
                )
        
        if command == "view":
            return await self.view(_path, view_range)
        elif command == "create":
            if file_text is None:
                raise ToolError("Parameter `file_text` is required for command: create")
                
            # Check if file_text is too large
            if len(file_text) > MAX_FILE_SIZE:
                return ToolResult(
                    system="File text is too large and may exceed token limits.",
                    error=f"The provided text ({len(file_text)} bytes) is too large to process safely."
                )
                
            self.write_file(_path, file_text)
            self._file_history[_path].append(file_text)
            return ToolResult(output=f"File created successfully at: {_path}")
        elif command == "str_replace":
            if old_str is None:
                raise ToolError(
                    "Parameter `old_str` is required for command: str_replace"
                )
            return self.str_replace(_path, old_str, new_str)
        elif command == "insert":
            if insert_line is None:
                raise ToolError(
                    "Parameter `insert_line` is required for command: insert"
                )
            if new_str is None:
                raise ToolError("Parameter `new_str` is required for command: insert")
            return self.insert(_path, insert_line, new_str)
        elif command == "undo_edit":
            return self.undo_edit(_path)
        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
        )

    def validate_path(self, command: str, path: Path):
        """
        Check that the path/command combination is valid.
        """
        # Check if its an absolute path
        if not path.is_absolute():
            suggested_path = Path("") / path
            raise ToolError(
                f"The path {path} is not an absolute path, it should start with `/`. Maybe you meant {suggested_path}?"
            )
        # Check if path exists
        if not path.exists() and command != "create":
            raise ToolError(
                f"The path {path} does not exist. Please provide a valid path."
            )
        if path.exists() and command == "create":
            raise ToolError(
                f"File already exists at: {path}. Cannot overwrite files using command `create`."
            )
        # Check if the path points to a directory
        if path.is_dir():
            if command != "view":
                raise ToolError(
                    f"The path {path} is a directory and only the `view` command can be used on directories"
                )

    async def view(self, path: Path, view_range: list[int] | None = None):
        """Implement the view command with token management"""
        if path.is_dir():
            if view_range:
                raise ToolError(
                    "The `view_range` parameter is not allowed when `path` points to a directory."
                )

            # Use find command with depth limit to avoid excessive token usage
            _, stdout, stderr = await run(
                rf"find {path} -maxdepth 2 -not -path '*/\.*'"
            )
            if not stderr:
                stdout = f"Here's the files and directories up to 2 levels deep in {path}, excluding hidden items:\n{stdout}\n"
            
            # Track token usage for the output
            output_tokens = len(stdout) // 4
            token_rate_limiter.record_usage(0, output_tokens)
            
            return CLIResult(output=stdout, error=stderr)

        # If it's a file, handle potential token overuse
        file_size = path.stat().st_size
        file_content = self.read_file(path)
        
        # If the file is large, we'll apply some processing to limit token usage
        if file_size > 100_000:  # 100KB threshold
            logger.warning(f"Large file detected: {file_size} bytes at {path}")
            file_info = f"File is large ({file_size:,} bytes). Showing partial content.\n\n"
            
            init_line = 1
            if view_range:
                if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                    raise ToolError(
                        "Invalid `view_range`. It should be a list of two integers."
                    )
                
                file_lines = file_content.split("\n")
                n_lines_file = len(file_lines)
                init_line, final_line = view_range
                
                if init_line < 1 or init_line > n_lines_file:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                    )
                if final_line > n_lines_file:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                    )
                if final_line != -1 and final_line < init_line:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"
                    )

                if final_line == -1:
                    file_content = "\n".join(file_lines[init_line - 1:])
                else:
                    file_content = "\n".join(file_lines[init_line - 1:final_line])
            else:
                # If no view_range is provided for a large file, limit to first 200 lines
                file_lines = file_content.split("\n")
                if len(file_lines) > 200:
                    file_content = "\n".join(file_lines[:200])
                    file_info += f"Showing first 200 lines of {len(file_lines)} total lines.\n"
                    file_info += "Use view_range parameter to see specific sections.\n\n"
            
            # Track token usage
            output_tokens = (len(file_info) + len(file_content)) // 4
            token_rate_limiter.record_usage(0, output_tokens)
            
            return CLIResult(
                output=file_info + self._make_output(file_content, str(path), init_line=init_line)
            )
        else:
            # Normal processing for smaller files
            init_line = 1
            if view_range:
                if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                    raise ToolError(
                        "Invalid `view_range`. It should be a list of two integers."
                    )
                file_lines = file_content.split("\n")
                n_lines_file = len(file_lines)
                init_line, final_line = view_range
                if init_line < 1 or init_line > n_lines_file:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                    )
                if final_line > n_lines_file:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                    )
                if final_line != -1 and final_line < init_line:
                    raise ToolError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"
                    )

                if final_line == -1:
                    file_content = "\n".join(file_lines[init_line - 1:])
                else:
                    file_content = "\n".join(file_lines[init_line - 1:final_line])

            # Track token usage
            output_tokens = len(file_content) // 4
            token_rate_limiter.record_usage(0, output_tokens)
            
            return CLIResult(
                output=self._make_output(file_content, str(path), init_line=init_line)
            )

    def str_replace(self, path: Path, old_str: str, new_str: str | None):
        """Implement the str_replace command, which replaces old_str with new_str in the file content"""
        # Read the file content
        file_content = self.read_file(path).expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ""

        # Check if old_str is unique in the file
        occurrences = file_content.count(old_str)
        if occurrences == 0:
            raise ToolError(
                f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}."
            )
        elif occurrences > 1:
            file_content_lines = file_content.split("\n")
            lines = [
                idx + 1
                for idx, line in enumerate(file_content_lines)
                if old_str in line
            ]
            raise ToolError(
                f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique"
            )

        # Replace old_str with new_str
        new_file_content = file_content.replace(old_str, new_str)
        
        # Check if the change would result in a file that's too large for token limits
        if len(new_file_content) > MAX_FILE_SIZE:
            return ToolResult(
                system="Replacement would create a file that's too large for token limits.",
                error=f"The resulting file would be {len(new_file_content)} bytes, which exceeds the recommended limit. Consider breaking down the operation."
            )

        # Write the new content to the file
        self.write_file(path, new_file_content)

        # Save the content to history
        self._file_history[path].append(file_content)

        # Create a snippet of the edited section
        replacement_line = file_content.split(old_str)[0].count("\n")
        start_line = max(0, replacement_line - SNIPPET_LINES)
        end_line = replacement_line + SNIPPET_LINES + new_str.count("\n")
        snippet = "\n".join(new_file_content.split("\n")[start_line:end_line + 1])

        # Prepare the success message
        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet, f"a snippet of {path}", start_line + 1
        )
        success_msg += "Review the changes and make sure they are as expected. Edit the file again if necessary."
        
        # Track token usage
        output_tokens = len(success_msg) // 4
        token_rate_limiter.record_usage(0, output_tokens)

        return CLIResult(output=success_msg)

    def insert(self, path: Path, insert_line: int, new_str: str):
        """Implement the insert command, which inserts new_str at the specified line in the file content."""
        file_text = self.read_file(path).expandtabs()
        new_str = new_str.expandtabs()
        file_text_lines = file_text.split("\n")
        n_lines_file = len(file_text_lines)

        if insert_line < 0 or insert_line > n_lines_file:
            raise ToolError(
                f"Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, n_lines_file]}"
            )

        new_str_lines = new_str.split("\n")
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - SNIPPET_LINES):insert_line]
            + new_str_lines
            + file_text_lines[insert_line:insert_line + SNIPPET_LINES]
        )

        new_file_text = "\n".join(new_file_text_lines)
        snippet = "\n".join(snippet_lines)
        
        # Check if the insert would result in a file that's too large
        if len(new_file_text) > MAX_FILE_SIZE:
            return ToolResult(
                system="Insert would create a file that's too large for token limits.",
                error=f"The resulting file would be {len(new_file_text)} bytes, which exceeds the recommended limit. Consider breaking down the operation."
            )

        self.write_file(path, new_file_text)
        self._file_history[path].append(file_text)

        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet,
            "a snippet of the edited file",
            max(1, insert_line - SNIPPET_LINES + 1),
        )
        success_msg += "Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
        
        # Track token usage
        output_tokens = len(success_msg) // 4
        token_rate_limiter.record_usage(0, output_tokens)
        
        return CLIResult(output=success_msg)

    def undo_edit(self, path: Path):
        """Implement the undo_edit command."""
        if not self._file_history[path]:
            raise ToolError(f"No edit history found for {path}.")

        old_text = self._file_history[path].pop()
        self.write_file(path, old_text)
        
        # Track token usage
        output_msg = f"Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}"
        output_tokens = len(output_msg) // 4
        token_rate_limiter.record_usage(0, output_tokens)

        return CLIResult(output=output_msg)

    def read_file(self, path: Path):
        """Read the content of a file from a given path; raise a ToolError if an error occurs."""
        try:
            # For binary files, try to detect and handle appropriately
            if self._is_binary_file(path):
                return f"<Binary file detected: {path}. Size: {os.path.getsize(path)} bytes>\nUse bash commands to handle this file type."
                
            return path.read_text()
        except Exception as e:
            raise ToolError(f"Ran into {e} while trying to read {path}") from None

    def write_file(self, path: Path, file: str):
        """Write the content of a file to a given path; raise a ToolError if an error occurs."""
        try:
            path.write_text(file)
        except Exception as e:
            raise ToolError(f"Ran into {e} while trying to write to {path}") from None

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ):
        """Generate output for the CLI based on the content of a file."""
        file_content = maybe_truncate(file_content)
        if expand_tabs:
            file_content = file_content.expandtabs()
        file_content = "\n".join(
            [
                f"{i + init_line:6}\t{line}"
                for i, line in enumerate(file_content.split("\n"))
            ]
        )
        return (
            f"Here's the result of running `cat -n` on {file_descriptor}:\n"
            + file_content
            + "\n"
        )
    
    def _is_binary_file(self, path: Path) -> bool:
        """Check if a file appears to be binary"""
        try:
            with open(path, 'rb') as f:
                # Read first 8KB to check for binary content
                chunk = f.read(8192)
                return b'\0' in chunk  # If null bytes are found, likely binary
        except Exception:
            return False


class EditTool20241022(EditTool20250124):
    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"  # pyright: ignore[reportIncompatibleVariableOverride]
