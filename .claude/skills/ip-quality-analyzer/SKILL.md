---
name: ip-quality-analyzer
description: Analyze IP quality reports to determine if an IP is high-quality residential. Use when you have an IP quality report (from replace_ip_and_check MCP tool) and need to evaluate whether the IP meets quality standards. Triggers on requests like "analyze this IP report", "is this IP high quality", "check if IP is residential".
---

# IP Quality Analyzer

Evaluate IP quality reports and determine residential status.

## Quality Criteria

**Pass requirements (ALL must be met):**
- Type: 家宽/Residential/ISP (majority of sources, allow 2 business )
- Risk: 极低/低 (Low or Extremely Low) across all sources

**Immediate fail conditions:**
- Type: Business/Hosting/Data Center/Proxy/VPN/Cloud
- Risk: 中/高/存在风险/危险 (Medium or higher)

## Whitelist

If IP matches user-provided whitelist range (e.g., `172.13.x.x`), immediately pass as high quality.

## Output

```json
{
  "is_high_quality": true,
  "reason": "All sources residential, low risk",
  "risk_count": 0,
  "non_isp_count": 0
}
```
