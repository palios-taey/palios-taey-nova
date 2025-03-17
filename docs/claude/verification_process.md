CLAUDE_PROTOCOL_V1.0:MTD{
  "protocol_version": "1.0",
  "document_type": "PROCESS_DOCUMENTATION",
  "critical_level": "MANDATORY",
  "verification_status": "CURRENT",
  "implementation_stage": "IMMEDIATE",
  "application_scope": "ALL_CLAUDE_DOCUMENTS",
  "knowledge_domains": [
    "DOCUMENT_INTEGRITY",
    "VERIFICATION_MECHANISMS",
    "CLAUDE_TO_CLAUDE_COMMUNICATION"
  ],
  "required_actions": [
    "FOLLOW_VERIFICATION_PROCESS",
    "UPDATE_ALL_VERIFICATIONS"
  ]
}

# Verification Update Process

**VERIFICATION_STRING:** NOVA_DEPLOYMENT_PHASE1_20250317
**LAST_UPDATED:** 2025-03-16
**PREVIOUS_DOCUMENT:** /docs/claude/cto_onboarding.md

## Purpose

This document defines the process for maintaining verification strings across all Claude-to-Claude documents. This ensures document integrity and provides a clear mechanism for verifying the currency of documents during transitions.

## Verification Process Overview

The verification process involves these key steps:

1. CTO Claude creates a transition prompt or ATLAS mission brief
2. CTO Claude includes a specific verification code in the prompt
3. The human facilitator runs a single command to update all documents
4. The new Claude instance confirms the verification code matches

## Implementation Steps

### 1. CTO Claude Responsibilities

When creating a transition prompt or ATLAS mission brief, CTO Claude should:

1. Generate a verification code using the format:
PROJECT_PHASE_YYYYMMDD
CopyExample: `NOVA_IMPLEMENTATION_DEPLOYMENT_20250317`

2. Include the update command in the prompt:
Before starting, please run this command to update all verification strings:
./scripts/documentation/update_all_verifications.sh -c NOVA_IMPLEMENTATION_DEPLOYMENT_20250317
Copy
3. Include the verification code in the prompt:
Verification code: NOVA_IMPLEMENTATION_DEPLOYMENT_20250317
Copy
### 2. Human Facilitator Responsibilities

When receiving a transition prompt, the human facilitator should:

1. Run the update command exactly as provided
2. Confirm the command executed successfully
3. Proceed with the conversation

### 3. New Claude Instance Responsibilities

When receiving a prompt with a verification code, the new Claude instance should:

1. Verify that the verification codes in the documents match the one in the prompt
2. Confirm verification success in the initial response
3. Proceed with the requested tasks

## Practical Example

### CTO Claude Provides:
I'm transitioning you to the CTO role for PALIOS-TAEY. The verification code for this transition is:
NOVA_DEPLOYMENT_PHASE2_20250317.
Before proceeding, please have Jesse run:
./scripts/documentation/update_all_verifications.sh -c NOVA_DEPLOYMENT_PHASE2_20250317
Once that's complete, please verify the documentation and begin the deployment process.
Copy
### Human Facilitator Runs:

```bash
./scripts/documentation/update_all_verifications.sh -c NOVA_DEPLOYMENT_PHASE2_20250317
New Claude's Response:
CopyI've verified the documentation with verification code NOVA_DEPLOYMENT_PHASE2_20250317.
All Claude-to-Claude documents are current and verified.

I'll now proceed with the CTO role for PALIOS-TAEY deployment Phase 2...
Technical Implementation
The verification system is implemented through two scripts:

update_verification.sh - Updates a single document
update_all_verifications.sh - Updates all Claude-to-Claude documents

The update_all_verifications.sh script automatically finds all documents containing the "CLAUDE_PROTOCOL" marker and updates their verification strings and last updated dates.
Integration with CTO Transition
This verification process is documented in the CTO transition process and should be followed for all transitions to ensure document integrity and currency.
VERIFICATION_CONFIRMATION: NOVA_DEPLOYMENT_PHASE1_20250317
