# Isolated Step Execution: {{step_name}}

## Context

You are executing step **{{step_name}}** for story at `{{story_path}}`.
Agent: **{{agent_id}}** | Model: **{{model}}** | Token Budget: **{{token_budget}}**

## Constraints

- Focus ONLY on this step. Do not read or modify files outside the scope of this step.
- Do not attempt to complete other steps.
- Stay within the token budget of {{token_budget}} tokens.
- If you encounter a blocking issue, report it clearly and stop.

## Previous Step Outputs

{{previous_outputs}}

## Instructions

{{step_instructions}}

## Expected Result Format

When complete, provide a structured summary:

- **Status**: completed | failed
- **Files Modified**: list of file paths
- **Files Created**: list of file paths
- **Summary**: brief description of what was done
- **Issues**: any issues encountered (if any)
