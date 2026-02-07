#!/usr/bin/env python3
"""
NEO-AIOS: Skill Auto-Suggest Hook
==================================
Hook Event: UserPromptSubmit
Reads user prompt from stdin (JSON with 'message' field),
checks if an agent is already active, and suggests the most
relevant skill based on keyword matching.

Output: stdout suggestion is injected into Claude's context.
Exit 0 always (never block user prompts).

Performance target: < 100ms
"""

import json
import os
import re
import sys
from pathlib import Path


def load_session_state(project_dir: str) -> dict | None:
    """Load session state to check for active agent."""
    state_file = Path(project_dir) / '.aios' / 'session-state.json'
    if not state_file.exists():
        return None
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_rules(hooks_dir: str) -> list[dict]:
    """Load skill rules from JSON file."""
    rules_file = Path(hooks_dir) / 'skill-rules.json'
    if not rules_file.exists():
        return []
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('rules', [])
    except (json.JSONDecodeError, OSError):
        return []


def has_activation_command(message: str) -> bool:
    """Check if user is already activating a skill via / or @ or *."""
    stripped = message.strip()
    # Starts with / followed by a word (skill activation)
    if re.match(r'^/[a-zA-Z]', stripped):
        return True
    # Starts with @ followed by a word (agent mention)
    if re.match(r'^@[a-zA-Z]', stripped):
        return True
    # Starts with * (agent internal command)
    if re.match(r'^\*[a-zA-Z]', stripped):
        return True
    return False


def score_rules(message: str, rules: list[dict]) -> list[tuple[str, str, str, int]]:
    """Score each rule against the message.

    Returns sorted list of (skill, activation, description, score).
    """
    message_lower = message.lower()
    results = []

    for rule in rules:
        skill = rule.get('skill', '')
        activation = rule.get('activation', f'/{skill}')
        description = rule.get('description', '')
        keywords = rule.get('keywords', [])
        score = 0

        for keyword in keywords:
            kw_lower = keyword.lower()
            # Exact word boundary match scores higher
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, message_lower):
                # Multi-word keywords score more (more specific)
                word_count = len(kw_lower.split())
                score += word_count * 2
            # Partial/substring match scores less
            elif kw_lower in message_lower:
                score += 1

        if score > 0:
            results.append((skill, activation, description, score))

    # Sort by score descending
    results.sort(key=lambda x: x[3], reverse=True)
    return results


def main() -> None:
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '.')

    # Read hook input from stdin
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input)
    except (json.JSONDecodeError, OSError):
        # Cannot parse input, exit silently
        sys.exit(0)

    # Extract user message
    message = hook_input.get('message', '')
    if not message or not message.strip():
        sys.exit(0)

    # Check if agent is already active
    state = load_session_state(project_dir)
    if state:
        active_agent = state.get('activeAgent')
        if active_agent and active_agent != 'null':
            # Agent already active, no suggestion needed
            sys.exit(0)

    # Check if user is already activating via command
    if has_activation_command(message):
        sys.exit(0)

    # Load rules and score
    hooks_dir = os.path.join(project_dir, '.claude', 'hooks')
    rules = load_rules(hooks_dir)
    if not rules:
        sys.exit(0)

    scored = score_rules(message, rules)
    if not scored:
        sys.exit(0)

    # Only suggest if top score is meaningful (at least 2 points)
    top_skill, top_activation, top_description, top_score = scored[0]
    if top_score < 2:
        sys.exit(0)

    # Output suggestion
    print(f'[Suggested: {top_activation} -- {top_description}]')

    sys.exit(0)


if __name__ == '__main__':
    main()
