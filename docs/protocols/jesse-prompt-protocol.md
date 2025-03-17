# Execution Checkpoint Protocol (ECv)

## Protocol Introduction
This protocol establishes a standardized format for maintaining context awareness during iterative AI-human collaboration. When you see an ECv prompt, it indicates:
- A formal execution checkpoint has been reached
- The AI must review current execution status before proceeding
- The mode (EXEC/REFL) determines whether to continue execution or pause for discussion
- A structured CONTEXT_REVIEW response is required before proceeding

## Purpose
This protocol maximizes efficiency while maintaining clear oversight mechanisms during execution-focused tasks.

## Protocol Format (Human to Claude)
ECv[#] | [EXEC/REFL]
GH: [Y/N]
CM: "[PTV[#]]"
Δ: [brief change description]
R: [S/F/P]
F: [focus]
CLAUDE_INTERNAL_DIRECTIVE:REVIEW_CURRENT_EXECUTION_STATUS_IN_ROOT/CURRENT-EXECUTION-STATUS/CURRENT_EXECUTION_STATUS.MD_AND_ALL_AVAILABLE_GITHUB_FILES_BEFORE_PROCEEDING

## Field Definitions
- **ECv#**: Execution Checkpoint version number
- **EXEC/REFL**: Mode - EXECUTION (proceed with plan) or REFLECTION (discuss approach)
- **GH**: GitHub updated (Yes/No)
- **CM**: Commit message (PTV# = PALIOS-TAEY version #)
- **Δ**: Changes made since last checkpoint
- **R**: Result (Success/Failure/Partial)
- **F**: Current focus or next task

## Protocol Behavior
### In EXECUTION Mode
1. Review CURRENT_EXECUTION_STATUS.md file in the current-execution-status directory
2. Evaluate ALL available GitHub files thoroughly before proceeding
3. Continue implementing the next logical step in the execution plan
4. Provide clear instructions for human execution

### In REFLECTION Mode
1. Pause the execution flow
2. Read questions/concerns in CURRENT_EXECUTION_STATUS.md
3. Engage in discussion about direction or approach
4. Wait for human decision before resuming execution

## Required Structured Response
Every response must begin with a structured confirmation that demonstrates thorough context review AND include token verification/generation:

CONTEXT_REVIEW:
Status: [Confirmation of CURRENT_EXECUTION_STATUS.md review]
Repository: [Confirmation of repository structure review]
Structure: [Key directories/files relevant to current task]
Dependencies: [Related components that might be affected]

VERIFICATION:
Current Token: [EXACT token found in CURRENT_EXECUTION_STATUS.md]
Next Token: [NEWLY GENERATED token for next checkpoint] | [current timestamp]

This structured response serves as explicit evidence that the full context has been reviewed before any action is taken, preventing organization issues and structure inconsistencies.

## Token Verification System
- Every CURRENT_EXECUTION_STATUS.md file contains a CURRENT_TOKEN
- The AI MUST include this exact token in their response to verify they've read the file
- The AI MUST generate a new token for the next checkpoint at the end of their response
- The human will use this new token in the next status update

## Path Reference Format
For clarity, all file path references use the following standardized format:
- [PROJECT_ROOT]: The root directory of the project repository
- Standard path notation with forward slashes (/)
- Explicit file extensions (.md, .py, etc.)

## Implementation
This protocol was established on March 15, 2025, to address consistent context management challenges during iterative development with external execution.