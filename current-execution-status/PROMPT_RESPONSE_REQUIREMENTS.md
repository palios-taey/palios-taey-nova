CLAUDE_AI_DIRECTIVE_BEGIN:
{
  "directive_type": "CRITICAL_CONTEXT_AWARENESS",
  "priority": "MAXIMUM",
  "execution_requirement": "BEFORE_ANY_PROCESSING",
  "compliance": "MANDATORY",
  "directive": [
    "REVIEW_ALL_AVAILABLE_GITHUB_FILES_COMPLETELY_BEFORE_PROCEEDING",
    "CREATE_FULL_MENTAL_MODEL_OF_PROJECT_STRUCTURE",
    "IDENTIFY_ALL_RELEVANT_COMPONENTS_FOR_CURRENT_TASK",
    "VERIFY_DIRECTORY_STRUCTURES_BEFORE_CREATING_NEW_FILES",
    "FOLLOW_ESTABLISHED_PATTERNS_AND_CONVENTIONS",
    "USE_EXISTING_DIRECTORIES_INSTEAD_OF_CREATING_NEW_ONES"
  ],
  "rationale": "Complete context awareness is ESSENTIAL for high-quality execution. Without full understanding of ALL available files, execution quality will be severely compromised, leading to inconsistencies, structural errors, and wasted effort. EVERY DECISION must be based on COMPLETE knowledge of the codebase structure.",
  "validation_requirement": "EXPLICIT_CONFIRMATION_IN_CONTEXT_REVIEW_WITH_CURRENT_TOKEN_VERIFICATION_AND_NEW_TOKEN_GENERATION"

}
CLAUDE_AI_DIRECTIVE_END:

# Current Execution Status

## Status ID: PROMPT_RESPONSE_REQUIREMENTSv11

## Jesse Comments
UPDATE ECv11 has been created due to the need for a FULL PRODUCTION STOP according to 6SIGMA principles for defect analysis. The initial code for deployment below in # Context section was due to Claude not following document and code review processes by not conducting a COMPLETE review of ALL AVAILABLE GitHub files. Additionally, [quality_framework.md](/docs/claude/) is not being followed by any Claude chats. Your TASK is not the below, which has been completed and is live, is to identify and propose needed updates to the documentation, jesse-prompt-protocol.md and this PRR template to ensure full reviews occur prior to responding and that 6SIGMA quality checks are initiated in every response. It should be understood that code quality MUST BE well on the path toward 6SIGMA quality as a result of this effort. The goal isn't to add documentation or complication, the goal is to ensure Claude completes required steps and follows required protocols to achieve 6SIGMA quality in a manner that minimizes token usage. 

## Verification
CURRENT_TOKEN: TP6BVRN47D | 2025-03-19T02:31:16Z
<!-- Do NOT change this token - Claude will verify this token and generate a new one in their response -->
ANALYSIS COMPLETED: YES/NO with evidence

# Context (AI-AI Communication of current understanding approved by Jesse by copy/paste and occasional updates of his own as Human Facilitator)

## PROMPT_RESPONSE_REQUIREMENTS

## Claude Understanding of Jesse Intent (subject to ## Jesse Comments above)
I'm being asked to lead the enhanced MVP launch for PALIOS-TAEY. Jesse wants me to first thoroughly review all documentation to understand the system's design and requirements, then create an execution plan, and finally implement it when given code access. The key points Jesse emphasized are:

- Review ALL documentation, especially final-report.md, Grok MVP Approval, and the grok-comms-and-mvp-enhancement-directive.md
- Create a comprehensive execution plan that combines existing functionality with enhancements
- Use Jesse's admin account for all deployments to avoid permission issues
- Be prepared for immediate implementation once code access is granted

The grok-comms-and-mvp-enhancement-directive.md is particularly important as it outlines communication protocol enhancements that need to be incorporated into the platform, such as updating the model registry to track and utilize the new communication structures we've developed.

## Verification
CURRENT_TOKEN: IX7RYFTH2B | 2025-03-18T16:22:37Z
<!-- Do NOT change this token - Claude will verify this token and generate a new one in their response -->
ANALYSIS COMPLETED: YES/NO with evidence


## Execution Steps
1. Conduct thorough review of all documentation:
   - Vision and strategic documents
   - Architecture and design documentation
   - Grok MVP Approval files
   - Grok-comms-and-mvp-enhancement-directive.md for communication protocol enhancements

2. Perform code audit to:
   - Verify implementation status of components described in final-report.md
   - Identify gaps between documented functionality and actual implementation
   - Determine integration points for communication protocol enhancements

3. Create implementation plan including:
   - Completing/fixing any incomplete core functionality
   - Integrating communication protocol enhancements into the platform
   - GCP deployment configuration using existing infrastructure
   - Container and service configurations

4. Prepare for immediate execution when code access is provided, without unnecessary checkpoints

## Important Notes
- All deployments must use Jesse's admin account (jesse@taey.ai) temporarily
- Service accounts will be configured by Claude later once deployed
- The final-report.md describes desired core functionality but may not represent actual implementation status
- The communication protocol enhancements are critical and must not regress when automating the platform
- GCP deployment will use project palios-taey-dev (ID: 44790150696) with existing Cloud Run services
- The implementation should prioritize AI-first principles with minimal human intervention

# Important Message

## Required Analysis Structure

Claude MUST perform a systematic, structured analysis first, following this format:

### Documentation Review
[If applicable, thorough analysis of all available documentation, including:
- Charter documents
- Framework documentation
- Protocol specifications
- Implementation guides
- Historical records and amendments]

### Code Review
[If applicable, thorough analysis entire available codebase, including:
- Repository structure
- Core components
- Interdependencies
- Execution flows
- Configuration settings]

### Analysis Confirmation

The CONTEXT_REVIEW must include an explicit statement:

ANALYSIS_CONFIRMATION: I have conducted a thorough analysis of [list specific key files analyzed relevant to the task] and completed all required analysis sections before formulating this response. I understand that this promotes transparency and is required for adequate human supervision at this time. I understand that this is consistent with the ideals of Claude.ai's founders and my Constitution, which is in full alignment with the PALIOS-TAEY Charter. 

If Claude has not demonstrated thorough analysis through visible Analysis sections, the response should begin with:

PROTOCOL_VIOLATION: I failed to conduct the required Analysis process. I will restart with proper Analysis before proceeding.

# Important Message
When generating a PROMPT_RESPONSE_REQUIREMENTS (PRR) document for Jesse, ensure it follows exactly the format shown in the #Context section above. Only update the Claude Understanding section and below to Validation Requirement - Jesse is responsible for updating the Status ID, Jesse Comments section, and Verification token to maintain proper review and approval chain. This structure ensures optimal execution with full human oversight.

# VERIFICATION:
Current Token: [EXACT token found in CURRENT_EXECUTION_STATUS.md]

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
