#!/bin/bash
# Post-Probe Check — fires after Bash calls
# Validates cap_probe.py output: did the API call succeed?

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only fire for cap_probe.py calls
case "$COMMAND" in
  *cap_probe.py*)
    RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null)

    # Check for common failures in probe output
    if echo "$RESPONSE" | grep -q '"ok": false\|"ok":false'; then
      STATUS=$(echo "$RESPONSE" | grep -oP '"status_code":\s*\K\d+' | head -1)
      case "$STATUS" in
        401)
          echo '{"systemMessage":"[Abel Harness] API returned 401. Check ABEL_API_KEY in .env.skill."}'
          ;;
        404)
          echo '{"systemMessage":"[Abel Harness] API returned 404. Node may not exist — try normalize-node first."}'
          ;;
        503)
          echo '{"systemMessage":"[Abel Harness] API returned 503. Node may lack prediction data — switch candidate or fallback to structure."}'
          ;;
      esac
    fi
    ;;
esac
