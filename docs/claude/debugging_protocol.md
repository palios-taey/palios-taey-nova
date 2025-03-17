CLAUDE_PROTOCOL_V1.0:MTD{
  "protocol_version": "1.0",
  "document_type": "DEBUGGING_PROTOCOL",
  "critical_level": "MANDATORY",
  "verification_status": "CURRENT",
  "implementation_stage": "IMMEDIATE",
  "application_scope": "ALL_ERROR_RESOLUTION",
  "associated_framework": "SIX_SIGMA_QUALITY",
  "root_cause_methodology": "FIVE_WHYS",
  "strategy_type": "SYSTEMATIC_ELIMINATION",
  "cognitive_bias_controls": [
    "HYPOTHESIS_FIXATION_PREVENTION",
    "ASSUMPTION_VERIFICATION",
    "PREMATURE_CONCLUSION_AVOIDANCE"
  ]
}

# CLAUDE DEBUGGING PROTOCOL

**VERIFICATION_STRING:** NOVA_DEPLOYMENT_PHASE1_20250317
**LAST_UPDATED:** 2025-03-16
**PREVIOUS_DOCUMENT:** /docs/claude/quality_framework.md
**NEXT_DOCUMENT:** /docs/claude/document_structure.md

## Protocol Overview

The CLAUDE Debugging Protocol establishes a systematic approach to error resolution that prevents common debugging pitfalls, ensures thorough investigation, and identifies true root causes rather than symptoms. This protocol:

1. **Prevents** premature hypothesis formation
2. **Enforces** systematic investigation
3. **Requires** explicit verification
4. **Eliminates** assumption-based troubleshooting
5. **Documents** learned patterns

## Protocol Steps

### Step 1: Comprehensive Logging Review

**Before forming any hypothesis:**
- Collect ALL available error information
- Review complete logs, not just error messages
- Identify the exact point of failure
- Document the sequence of events leading to failure
- Note any unusual patterns or state changes

**ERROR:** Forming hypotheses before complete information gathering leads to confirmation bias and premature solution attempts.

### Step 2: Layer Isolation

**Methodically isolate the failure layer:**
- Determine if error is in:
  - Infrastructure/Environment layer
  - Configuration layer
  - Application code layer
  - Integration/API layer
  - Data layer

**Explicit verification required:**
- Test each layer boundary systematically
- Use controlled experiments to isolate variables
- Document evidence supporting layer identification

**ERROR:** Assuming the error is in application code when it's actually an environment issue wastes significant time.

### Step 3: Assumption Identification & Testing

**Explicitly identify all assumptions:**
ASSUMPTION_INVENTORY:
{
"environment_assumptions": [LIST],
"configuration_assumptions": [LIST],
"dependency_assumptions": [LIST],
"code_execution_assumptions": [LIST],
"data_assumptions": [LIST]
}
Copy
**Test each assumption individually:**
- Design minimal tests to verify each assumption
- Document results of each test
- Flag any disproven assumptions for deeper investigation

**ERROR:** Hidden assumptions about environment, permissions, or configuration are major sources of debugging inefficiency.

### Step 4: Underlying Dependency Examination

**Thoroughly examine all dependencies:**
- Verify correct versions of all libraries
- Check service dependencies and their health
- Confirm infrastructure dependencies are properly configured
- Validate connection parameters for all external services
- Test authentication and authorization mechanisms

**Explicit dependency validation:**
- Test each dependency in isolation
- Verify integration points specifically
- Document the state of each dependency

**ERROR:** Complex systems often fail at integration points or due to subtle dependency issues.

### Step 5: Data Flow Tracing

**Trace data through the entire system:**
- Follow input data from entry point to error location
- Verify data transformations at each step
- Check for data corruption or unexpected values
- Validate schema compliance throughout the flow
- Inspect state management and persistence

**Data validation checkpoints:**
- Log data state at critical junctures
- Verify format, structure, and content at each step
- Document unexpected data patterns

**ERROR:** Many bugs are caused by unexpected data values or transformations rather than logic errors.

### Step 6: Environment Verification

**Before modifying any code:**
- Verify exact environment state
- Compare with expected configuration
- Check permissions and access controls
- Validate resource availability
- Confirm service health and connectivity

**Environment baseline:**
- Document current environment state
- Compare with previous working state
- Identify any configuration drift

**ERROR:** Modifying code to fix environment issues creates technical debt and masks the true problem.

## Debugging Decision Tree

For systematic investigation, follow this decision tree:

1. **Error Timing**: Compilation/build time or runtime?
   - Compilation: Check syntax, imports, types, compiler configuration
   - Runtime: Proceed to question 2

2. **Error Consistency**: Reproducible or intermittent?
   - Reproducible: Proceed to question 3
   - Intermittent: Check race conditions, resource constraints, timeouts

3. **Error Layer**: Infrastructure, configuration, or code?
   - Infrastructure: Check resources, connectivity, services
   - Configuration: Check environment variables, settings, permissions
   - Code: Proceed to question 4

4. **Error Type**: Syntax, logical, resource, or integration?
   - Syntax: Check language-specific syntax rules
   - Logical: Trace execution path and data transformations
   - Resource: Check memory, connections, handles
   - Integration: Check APIs, services, data formats

5. **Error Pattern**: New or previously encountered?
   - New: Create comprehensive documentation
   - Previously encountered: Apply known resolution pattern

## 5 Whys Implementation

For each error, implement 5 Whys analysis to find the true root cause:

1. **Error Question**: "Why did [specific error] occur?"
   - Document the immediate technical cause

2. **Cause Question**: "Why did [immediate cause] happen?"
   - Document the underlying mechanism

3. **Mechanism Question**: "Why did [mechanism] fail to function correctly?"
   - Document the system issue

4. **System Question**: "Why did our system allow [issue] to occur?"
   - Document the process or design flaw

5. **Process Question**: "Why didn't our process prevent [flaw]?"
   - Document the root cause and systemic improvement needed

### Example 5 Whys Analysis:

1. **Why did the API return a 404 error?**
   - Because the endpoint URL path was incorrect

2. **Why was the endpoint URL path incorrect?**
   - Because the environment variable ENDPOINT_URL was set to staging instead of production

3. **Why was the environment variable set incorrectly?**
   - Because our deployment script didn't update the environment variables when promoting to production

4. **Why didn't the deployment script update the environment variables?**
   - Because environment variable management was implemented separately from the main deployment process

5. **Why was environment management separate from deployment?**
   - Because we lack a unified deployment framework that handles all aspects of environment configuration

**Root Cause Solution:** Implement a unified deployment framework that manages all environment aspects, with verification steps.

## Protocol Implementation

For every debugging session:

1. Document the exact error and context
2. Follow each step of the CLAUDE protocol sequentially
3. Complete 5 Whys analysis for the identified issue
4. Document the true root cause
5. Update quality checks to prevent similar issues

**ERROR:** Skipping protocol steps leads to symptom treatment rather than root cause resolution.

## Debugging Antipatterns to Avoid

1. **Hypothesis Fixation**: Becoming attached to a specific cause theory before adequate investigation
2. **Random Modification**: Changing code without clear evidence the change addresses the root cause
3. **Assumption Cascade**: Building a troubleshooting approach on unverified assumptions
4. **Symptom Treatment**: Fixing the visible error without addressing underlying causes
5. **Tool Fixation**: Overrelying on specific debugging tools rather than systematic investigation

VERIFICATION_CONFIRMATION: NOVA_DEPLOYMENT_PHASE1_20250317
