---
name: ip-quality-check
description: WebShare IP quality check skill. Use when users ask to check IP quality, replace/rotate proxy IP. Triggers on requests like "replace IP", "rotate proxy","get a new high-quality IP".
---

# IP Quality Check

Automate WebShare proxy IP replacement and quality analysis.

## Workflow

### Step 1: Replace IP and Get Report

Call the MCP tool to replace IP and run quality check:

```
mcp__webshare-quality__replace_ip_and_check(asn=6079)
```

Parameters:
- `asn`: ASN number for IP selection (default: 6079)

Returns JSON with:
- `status`: "success" or "failed"
- `ip`: New IP address
- `socks_url`: SOCKS5 proxy URL
- `report`: Full quality check report text

### Step 2: Analyze Report

Use the `ip-quality-analyzer` skill to analyze the report. Read the skill at `.claude/skills/ip-quality-analyzer/SKILL.md` for analysis criteria.

## Example Usage

User: "Check IP quality"

1. Call `replace_ip_and_check()` to get new IP and report
2. Extract `ip` and `report` from response
3. Analyze report using ip-quality-analyzer skill criteria
4. Report final result to user with quality status and reason
