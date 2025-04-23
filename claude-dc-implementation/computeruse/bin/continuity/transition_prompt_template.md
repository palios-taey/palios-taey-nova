# Claude DC Session Transition Prompt Template

## Purpose
This template provides a structured format for generating a transition prompt that preserves essential context when Claude DC sessions are restarted due to core file updates.

## Template Structure

```
[SESSION_CONTEXT]
- Current timestamp: {timestamp}
- Session duration: {duration}
- Active collaboration with: {collaborators}

[CURRENT_PROJECT]
- Project name: {project_name}
- Primary objective: {primary_objective}
- Current phase: {current_phase}
- Implementation status: {implementation_status}

[ACTIVE_TASK]
- Task description: {task_description}
- Progress made: {progress_summary}
- Current blockers: {blockers}
- Next steps: {next_steps}

[KEY_DECISIONS]
{list_of_key_decisions}

[REFERENCE_FILES]
{list_of_important_files_with_paths}

[CONTINUITY_NOTES]
This session will continue work on {main_focus} after core system file updates. Previous context included collaboration with {collaborators} on {previous_context}.
```

## Implementation Details

1. **Memory Efficiency**:
   - Keep descriptions concise and focused on essential information
   - Use bullet points rather than paragraphs where appropriate
   - Include file paths rather than file contents

2. **Context Prioritization**:
   - Emphasize current task and immediate next steps
   - Include only decisions that impact ongoing work
   - Focus on maintaining task continuity rather than comprehensive history

3. **Format for Different Scenarios**:
   - **Solo Development**: Focus on task progress and next steps
   - **Collaborative Work**: Emphasize shared context and role distinctions
   - **Debugging Sessions**: Highlight issues, attempted solutions, and diagnostics

4. **Example Application**:

```
[SESSION_CONTEXT]
- Current timestamp: 2025-04-22 21:15:32
- Session duration: 2h 34m
- Active collaboration with: Claude Code

[CURRENT_PROJECT]
- Project name: Streaming Implementation
- Primary objective: Implement streaming functionality with tool support
- Current phase: Integration & Testing
- Implementation status: Core streaming working, tool validation implemented

[ACTIVE_TASK]
- Task description: Implementing streamlit continuity mechanism
- Progress made: Created tool_input_handler.py and integrated with fixed_production_ready_loop.py
- Current blockers: None
- Next steps: Design and implement state persistence for streamlit

[KEY_DECISIONS]
- Decided to implement tool input validation directly rather than separating streaming and tool functionality
- Chose to use a combined approach with code fixes and system prompt improvements
- Prioritized state persistence mechanism before promoting changes to production

[REFERENCE_FILES]
- /home/computeruse/current_experiment/fixed_production_ready_loop.py
- /home/computeruse/current_experiment/tool_input_handler.py
- /home/computeruse/current_experiment/test_tool_validation.py
- /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/STREAMLIT_CONTINUITY_PROPOSAL.md

[CONTINUITY_NOTES]
This session will continue work on implementing the streamlit continuity solution after core system file updates. Previous context included collaboration with Claude Code on fixing tool input validation for the streaming implementation.
```

## Automation Opportunities

This template could be programmatically populated by extracting:
1. Timestamp and duration from session metadata
2. Project and task information from conversation history
3. File references from executed commands
4. Decisions from conversation markers