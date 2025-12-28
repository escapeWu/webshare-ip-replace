---
name: ip-quality-analyzer
description: Analyze IP quality reports to determine if an IP is high-quality residential. Use when you have an IP quality report (from replace_ip_and_check MCP tool) and need to evaluate whether the IP meets quality standards. Triggers on requests like "analyze this IP report", "is this IP high quality", "check if IP is residential".
---

# IP Quality Analyzer

Analyze IP quality check reports to determine if an IP meets high-quality residential standards.

## Quality Standards

A high-quality residential IP must meet ALL of the following criteria:

### 1. Type Requirement (Residential/ISP)

The IP must be identified as residential/ISP by the majority of detection sources.

**Acceptable types:**
- 家宽 (Residential)
- ISP
- Residential

**Disqualifying types (any occurrence fails):**
- Business (商业)
- Hosting (托管)
- Data Center (数据中心)
- Proxy (代理)
- VPN
- Cloud (云)

### 2. Risk Requirement (Low or Extremely Low)

Risk scores must be "极低 (Extremely Low)" or "低 (Low)" across all detection sources.

**Acceptable risk levels:**
- 极低风险 / Extremely Low
- 低风险 / Low

**Disqualifying risk levels (any occurrence fails):**
- 中风险 / Medium
- 高风险 / High
- 存在风险 / Risk Present
- 危险 / Critical

## Analysis Procedure

1. **Check whitelist first**: If ip match user provide whitelist ip range(172.13.x.x for example) immediately pass as high quality.

2. **Parse the report** to extract:
   - IP type classifications from all sources (IPinfo, ipregistry, ipapi, IP2Location, AbuseIPDB)
   - Risk scores from all sources (IP2Location, Scamalytics, ipapi, AbuseIPDB, IPQS, DB-IP)
   - Risk factors (proxy, VPN, Tor, server, abuse flags)

3. **Count issues**:
   - `risk_count`: Number of medium/high/critical risk indicators
   - `non_isp_count`: Number of non-residential type indicators

4. **Determine quality**:
   - `is_high_quality = true` only if `risk_count == 0` AND `non_isp_count == 0`
   - Any single high-risk or non-ISP indicator means `is_high_quality = false`

## Output Format

Return analysis in this exact JSON structure:

```json
{
  "is_high_quality": boolean,
  "reason": "Brief explanation of the determination",
  "risk_count": number,
  "non_isp_count": number
}
```

## Example Analysis

### High Quality IP Example

Report shows:
- All sources: 家宽 (Residential)
- Risk scores: 低风险 across all sources

Result:
```json
{
  "is_high_quality": true,
  "reason": "All sources identify as residential with low risk scores.",
  "risk_count": 0,
  "non_isp_count": 0
}
```

### Low Quality IP Example

Report shows:
- Type: 家宽 from all sources
- Scamalytics: 70 (高风险)
- IPQS: 88 (存在风险)

Result:
```json
{
  "is_high_quality": false,
  "reason": "Scamalytics shows high risk (70) and IPQS shows risk present (88).",
  "risk_count": 2,
  "non_isp_count": 0
}
```
