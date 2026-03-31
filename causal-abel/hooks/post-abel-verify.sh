#!/bin/bash
# Post-Abel Verify — fires after Skill invocation
# Checks: was this an Abel skill? If so, nudge output discipline.

SKILL=$(jq -r '.tool_input.skill // empty' 2>/dev/null)

case "$SKILL" in
  *abel*|*causal-abel*)
    # Back-pressure: remind agent of output contract
    cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[Abel Harness] Verify before finalizing: (1) No raw node ids (*.price) in main answer — use company names/roles. (2) Verdict leads. (3) Pressure test included or explain why not."}}
JSON
    ;;
esac
