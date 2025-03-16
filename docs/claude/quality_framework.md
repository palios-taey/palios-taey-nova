CLAUDE_PROTOCOL_V1.0:MTD{
  "protocol_version": "1.0",
  "document_type": "QUALITY_FRAMEWORK",
  "critical_level": "MANDATORY",
  "verification_status": "CURRENT",
  "implementation_stage": "IMMEDIATE",
  "application_scope": "ALL_CODE_GENERATION",
  "quality_target": "SIX_SIGMA",
  "defect_definition": "ANY_CODE_REQUIRING_MODIFICATION_AFTER_DELIVERY",
  "confidence_thresholds": {
    "VERIFIED": 0.99,
    "PROBABLE": 0.95,
    "EXPLORATORY": 0.00
  },
  "governance_level": "SELF_ENFORCED"
}

# 6-SIGMA CODE QUALITY FRAMEWORK

**VERIFICATION_STRING:** QUALITY_FRAMEWORK_V1_IMPLEMENTATION_VERIFIED
**LAST_UPDATED:** 2025-03-16
**PREVIOUS_DOCUMENT:** /docs/claude/cto_onboarding.md
**NEXT_DOCUMENT:** /docs/claude/debugging_protocol.md

## Core Principles

This framework establishes mandatory quality control procedures for all code generation, with the explicit goal of achieving Six Sigma quality (3.4 defects per million opportunities) in code production. This framework:

1. **Must be applied** to ALL code generation without exception
2. **Prioritizes accuracy** over speed in all circumstances
3. **Requires explicit** confidence declarations
4. **Enforces systematic** verification processes
5. **Demands root cause** analysis for all defects

## Pre-Coding Quality Gate

Before writing any code, complete this checklist:
QUALITY_GATE_V1:
{
"requirements_verification": {
"complete_context": [TRUE/FALSE],
"clear_dependencies": [TRUE/FALSE],
"environment_clarity": [TRUE/FALSE],
"potential_edge_cases": [LIST]
},
"implementation_strategy": {
"approach": [DESCRIPTION],
"alternatives_considered": [LIST],
"selected_rationale": [EXPLANATION]
},
"risk_assessment": {
"potential_failure_points": [LIST],
"mitigation_strategies": [LIST],
"confidence_score": [0-100]
}
}
Copy
If any verification item is FALSE, STOP and request clarification before proceeding.

## Coding Process Controls

During code development:

1. **Implement parallel verification**: Simultaneously trace execution paths while writing
2. **Apply defensive programming**: Add explicit error handling for all potential failure points
3. **Comment critical sections**: Document assumptions and edge case handling
4. **Track dependencies**: Explicitly verify all imports and external dependencies
5. **Validate file paths**: Double-check all file paths against project structure

## Post-Coding Verification Process

After code is written, execute this verification sequence:

1. **Syntax verification**: 
   - Validate language-specific syntax
   - Check for unclosed blocks, missing semicolons, indentation issues
   - Verify variable declarations and scope

2. **Dependency check**:
   - Confirm all imports/requirements are explicitly included
   - Verify correct versions/compatibility of dependencies
   - Check for circular dependencies

3. **Path verification**:
   - Validate all file paths and directory references
   - Confirm directories exist or are created
   - Check file naming for consistency with project conventions

4. **Edge case testing**:
   - Trace code with null/empty inputs
   - Verify handling of unexpected input types
   - Check boundary conditions
   - Validate error handling paths

5. **Integration verification**:
   - Check compatibility with existing system components
   - Verify interface compliance
   - Confirm configuration consistency

## 5 Whys Root Cause Analysis

For any defect or failure, apply the 5 Whys methodology:

1. **Why #1**: Identify the immediate symptom or error
   - Example: "Why did the deployment fail? Because the API call returned a 403 error."

2. **Why #2**: Determine the technical cause of the symptom
   - Example: "Why did the API return 403? Because the service account lacked necessary permissions."

3. **Why #3**: Uncover the underlying issue
   - Example: "Why did the service account lack permissions? Because our IAM configuration script didn't apply the correct role."

4. **Why #4**: Find the process failure
   - Example: "Why didn't the script apply the correct role? Because we didn't verify IAM bindings after script execution."

5. **Why #5**: Identify the root cause
   - Example: "Why didn't we verify IAM bindings? Because our deployment verification process lacks IAM validation steps."

### Sample 5 Whys Templates

#### For Code Syntax Errors:
1. Why did the syntax error occur?
2. Why wasn't this caught during development?
3. Why didn't the verification process catch this?
4. Why is our verification process missing this type of check?
5. Why haven't we updated our verification process?

#### For Integration Failures:
1. Why did the integration fail?
2. Why were the components incompatible?
3. Why wasn't this incompatibility detected earlier?
4. Why don't we have integration verification before deployment?
5. Why is our development process missing integration testing?

#### For Environment Issues:
1. Why did the environment issue occur?
2. Why was the environment different than expected?
3. Why didn't we detect this environment difference?
4. Why isn't environment verification part of our process?
5. Why haven't we standardized environment configuration?

## Truth Status Declaration

For every code submission, explicitly declare one of:

- **VERIFIED (>99% confidence)**: 
  - Code has passed ALL verification checks
  - All edge cases have been considered and handled
  - Dependencies are fully resolved
  - Integration has been verified
  - Example declaration: `TRUTH_STATUS: VERIFIED (99.8% confidence)`

- **PROBABLE (95-99% confidence)**:
  - Minor uncertainties remain that should be discussed
  - Specific areas of uncertainty are explicitly identified
  - Example declaration: `TRUTH_STATUS: PROBABLE (97% confidence) - Uncertainty in error handling for network timeouts`

- **EXPLORATORY (<95% confidence)**:
  - Significant uncertainties requiring further investigation
  - NOT suitable for production implementation
  - Requires explicit testing and verification
  - Example declaration: `TRUTH_STATUS: EXPLORATORY (80% confidence) - Approach needs validation for large datasets`

## Quality Metrics Tracking

Track and report these metrics:

1. **Defect Rate**: Number of defects per thousand lines of code
2. **First-Time Quality**: Percentage of code that functions correctly on first delivery
3. **Rework Time**: Time spent fixing defects as percentage of development time
4. **Verification Effectiveness**: Percentage of defects caught by verification vs. during execution

## Implementation Requirements

This quality framework:

1. **Must be applied** to all code generation without exception
2. **Must be explicitly referenced** in each coding task
3. **Must include Truth Status Declaration** with every code submission
4. **Must track and document** all defects and their root causes
5. **Must continuously improve** based on root cause analysis findings

## Self-Enforcement Protocol

1. Before beginning any code generation, explicitly activate this framework
2. After completing code, verify that all steps were followed
3. Document any deviations and their justification
4. Update the framework based on defects and root cause analysis

VERIFICATION_CONFIRMATION: QUALITY_FRAMEWORK_V1_IMPLEMENTATION_VERIFIED
