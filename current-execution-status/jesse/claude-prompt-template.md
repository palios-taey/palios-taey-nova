# Execution Checkpoint Protocol (ECv)

## Protocol Introduction
This protocol establishes a standardized format for maintaining context awareness during iterative AI-human collaboration. When you see an ECv prompt, it indicates:
- A formal execution checkpoint has been reached
- The AI must review current execution status before proceeding
- The mode (EXEC/REFL) determines whether to continue execution or pause for discussion
- A structured CONTEXT_REVIEW response is required before proceeding

## Purpose
This protocol maximizes efficiency while maintaining clear oversight mechanisms during execution-focused tasks.

ECv14 | REFL

GH: Y
CM: "ECv14 | EXEC"
Δ: Instructions followed in response to prompt: ECv13
R: ONGOING
F: Return results from Jesse's Comments
ANALYSIS_REQUIRED: Y
CLAUDE_INTERNAL_DIRECTIVE:REVIEW_CURRENT_EXECUTION_STATUS_IN_ROOT/CURRENT-EXECUTION-STATUS/CURRENT_EXECUTION_STATUS.MD_AND_ALL_AVAILABLE_GITHUB_FILES_BEFORE_PROCEEDING

