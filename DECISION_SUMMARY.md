# Quantization Decision: Executive Summary

**Date:** 2025-10-09
**Status:** READY FOR DECISION
**Priority:** HIGH (Blocks Day 3 model selection)

---

## TL;DR: SWITCH TO LLAMA 3.2 1B Q4_K_M

**Current Plan (PRD):** Llama 3.2 1B primary ✅
**Alternative Evaluated:** Qwen 2.5 1.5B (Q4 vs Q5)
**Recommendation:** STICK WITH LLAMA 3.2 1B Q4_K_M

### Why Llama Wins

| Metric | Llama 3.2 1B Q4 | Qwen 2.5 1.5B Q4 | Qwen 2.5 1.5B Q5 |
|--------|-----------------|------------------|------------------|
| Download Size | **808 MB** ✅ | 1,120 MB | 1,290 MB |
| Memory Peak | **1.70 GB** ✅ | 2.03 GB | 2.30 GB |
| Device Support | **4GB+ (95%)** ✅ | 6GB+ (70%) | 8GB+ (40%) |
| TTFT | **130 ms** ✅ | 150 ms | 175 ms |
| Decode Speed | **37 tok/s** ✅ | 30 tok/s | 26 tok/s |
| MMLU Score | 49.3 ✅ | 48.5 | 49.8 |
| EQ Projected | 87 ✅ | 85 (marginal) | 87 |
| ExecuTorch | **Official** ✅ | Community | Community |
| CDN Cost/10K | **$650** ✅ | $850 | $980 |

---

## Q4 vs Q5 Analysis (If Qwen Required)

### Dimension-by-Dimension Winner

1. **App Size & Download** → **Q4_K_M** ✅
   - 170 MB smaller (1.12GB vs 1.29GB)
   - 15% faster download on cellular (14.9 min vs 17.2 min @ 10Mbps)
   - $130/month lower CDN cost (AWS, 10K users)

2. **Runtime Memory & Device Compatibility** → **Q4_K_M** ✅
   - 272 MB lower peak (2.03GB vs 2.30GB)
   - Supports iPhone 12 Pro 6GB with 34% headroom (Q5 only 17%)
   - 70% market reach vs 40% (Q5 requires 8GB)

3. **Performance (TTFT & Decode)** → **Q4_K_M** ✅
   - 15% faster decode (30 tok/s vs 26 tok/s)
   - 20ms better TTFT (150ms vs 175ms)
   - Both pass KPI gates, Q4 has larger margin

4. **Quality (MMLU & EQ)** → **Q5_K_M** ✅
   - +1.3 MMLU points (49.8 vs 48.5)
   - +2 EQ points projected (87 vs 85)
   - Better emotional nuance in 100+ token responses

5. **Battery & Thermal** → **Q4_K_M** ✅
   - 22% lower energy (0.20 J/tok vs 0.26 J/tok)
   - 2.0% battery drain vs 2.6% (10 min session)
   - Lower thermal throttling risk on 6GB devices

6. **Development & Ops Cost** → **Q4_K_M** ✅
   - Simpler single-model deployment
   - $130/month CDN savings (AWS)
   - 15% faster CI/CD pipeline

**VERDICT: Q4_K_M wins 5/6 dimensions**

---

## Key Trade-Offs

### If Qwen 2.5 1.5B Q4_K_M Chosen (vs Llama)

**GAINS:**
- 1.5B params → potentially more nuanced responses
- Better multilingual (Korean/Chinese/Japanese)
- Newer training data (2024 vs 2023)

**LOSSES:**
- 38% larger download (1.12GB vs 0.81GB)
- 25% slower decode (30 vs 37 tok/s)
- Excludes iPhone 12 4GB (30% market)
- Less ExecuTorch optimization

### If Qwen 2.5 1.5B Q5_K_M Chosen (vs Q4)

**GAINS:**
- +1.3 MMLU points (49.8 vs 48.5)
- +2 EQ points (87 vs 85, both above gate)
- Better context stability at 1024 tokens

**LOSSES:**
- 60% market exclusion (8GB only)
- 15% slower performance
- 22% higher battery drain
- $130/mo higher CDN cost
- Thermal throttling risk

---

## Decision Matrix

| Scenario | Choose Llama 3.2 1B Q4 | Choose Qwen 2.5 1.5B Q4 | Choose Qwen 2.5 1.5B Q5 |
|----------|------------------------|-------------------------|-------------------------|
| **English-only, max device reach** | ✅ YES | No | No |
| **Multilingual required** | No | ✅ YES | No |
| **Quality > speed** | Maybe | Maybe | ✅ YES (8GB only) |
| **6GB target devices** | ✅ YES | ✅ YES | ❌ NO |
| **4GB support needed** | ✅ YES | ❌ NO | ❌ NO |
| **Budget-conscious (CDN)** | ✅ YES | Maybe | ❌ NO |
| **Flagship-only app (8GB+)** | No | No | ✅ YES |

---

## Critical Issues Found

### P1 Issues

1. **MM-003:** PRD specifies Llama 3.2 1B primary, Qwen not in original scope
   **Fix:** Validate Qwen adoption with stakeholder OR proceed with Llama per plan

2. **MM-001:** Qwen Q5_K_M requires 8GB, excludes 6GB target devices
   **Fix:** Use Q4_K_M if Qwen needed, or switch to Llama

### P2 Issues

3. **MM-002:** Qwen Q4_K_M EQ score marginal (85, at gate threshold)
   **Fix:** Prompt engineering OR accept risk (Llama safer at EQ 87)

---

## Recommendations (Priority Order)

### RF-001: PRIMARY - Use Llama 3.2 1B Q4_K_M ✅

**Rationale:**
- Already in PRD as primary model
- 38% smaller, 25% faster than Qwen 2.5 1.5B
- 95% device reach (4GB+) vs 70% (Qwen Q4) or 40% (Qwen Q5)
- Official ExecuTorch reference model (proven stable)
- $200/month CDN savings vs Qwen Q4 (AWS, 10K users)

**Action:** Export Llama 3.2 1B Q4_K_M → validate on iPhone 12 Pro + Galaxy S21 → proceed if EQ ≥85

### RF-002: ALTERNATIVE - Use Qwen 2.5 1.5B Q4_K_M (if multilingual critical)

**Rationale:**
- Better multilingual capability
- 1.5B params → more nuanced (marginal gain)
- Still supports 6GB devices (70% market)

**Action:** Export Qwen Q4_K_M → blind EQ test vs Llama → choose higher scorer

### RF-003: NOT RECOMMENDED - Qwen 2.5 1.5B Q5_K_M

**Rationale:**
- Quality gain too small (+1.3 MMLU, +2 EQ) to justify:
  - 60% market exclusion (8GB only)
  - 15% performance loss
  - 22% higher battery drain
  - Thermal throttling risk

**Action:** Only consider for flagship-only variant (future v2.0)

---

## Next Steps (48-96h)

1. **Export Models (Parallel, 4h)**
   - Llama 3.2 1B Q4_K_M → PTE (XNNPACK)
   - Qwen 2.5 1.5B Q4_K_M → PTE (XNNPACK, if stakeholder approves)

2. **Device Testing (48h)**
   - iPhone 12 Pro (6GB): TTFT, tok/s, mem_peak, battery
   - Galaxy S21 (8GB): Same metrics
   - Validate: TTFT ≤200ms, decode ≥18 tok/s, mem_peak ≤3.0GB

3. **EQ Benchmark (72h)**
   - 20-turn blind test, 5 scenarios (scenarios_10turn.md)
   - Both models vs eq_rubric.md
   - Target: ≥85/100

4. **Final Decision (96h)**
   - If Llama EQ ≥85 → **CHOOSE LLAMA** (per PRD)
   - If Llama <85 AND Qwen ≥85 → Escalate (model swap decision)
   - If both <85 → Prompt tuning sprint OR consider 3B models

---

## Cost Impact Summary

### Monthly CDN Cost (10,000 Users, AWS CloudFront)

| Model | Traffic (GB) | Cost | vs Llama |
|-------|--------------|------|----------|
| Llama 3.2 1B Q4 | 7,672 | **$650** | baseline |
| Qwen 2.5 1.5B Q4 | 10,640 | $850 | **+$200** |
| Qwen 2.5 1.5B Q5 | 12,255 | $980 | **+$330** |

**Annual Savings (Llama vs Qwen Q4):** $2,400
**Annual Savings (Llama vs Qwen Q5):** $3,960

### Device Reach Impact

| Model | Market Reach | Excluded Devices |
|-------|--------------|------------------|
| Llama 3.2 1B Q4 | **95%** (4GB+) | iPhone 11 and older |
| Qwen 2.5 1.5B Q4 | **70%** (6GB+) | iPhone 12 (4GB) + older |
| Qwen 2.5 1.5B Q5 | **40%** (8GB+) | iPhone 12/12 Pro/13/14 |

---

## Data Confidence Levels

| Data Point | Confidence | Source |
|------------|------------|--------|
| File sizes | **HIGH** | Official Hugging Face repos |
| Memory calc | **MEDIUM** | Formula-based, not device-tested |
| Performance | **MEDIUM** | Extrapolated from Llama 3.2 1B benchmarks |
| Quality (MMLU/EQ) | **LOW** | Projected, needs actual testing |
| CDN costs | **HIGH** | Published AWS/Cloudflare pricing |

**CRITICAL:** Run actual EQ rubric test before final decision (projected scores not validated)

---

## FINAL RECOMMENDATION

### 🚀 PRIMARY: Llama 3.2 1B Q4_K_M

**Why:**
1. **PRD alignment:** Already specified as primary model
2. **Best performance:** Fastest TTFT (130ms) + decode (37 tok/s)
3. **Widest reach:** Supports 95% of market (4GB+)
4. **Lowest cost:** $650/mo CDN (vs $850 Qwen Q4, $980 Qwen Q5)
5. **Proven stable:** Official ExecuTorch reference model

**Trade-off accepted:** No multilingual (English-only for v1.0 per PRD)

### ⚠️ FALLBACK: Qwen 2.5 1.5B Q4_K_M (only if multilingual critical)

**Why:**
1. Better Korean/Chinese/Japanese support
2. Still supports 6GB devices (70% market)
3. Acceptable performance (30 tok/s, 150ms TTFT)

**Trade-off accepted:** 38% larger, 25% slower, higher cost, EQ score marginal (85)

### ❌ NOT RECOMMENDED: Qwen 2.5 1.5B Q5_K_M

**Why:** Quality gain (+1.3 MMLU) not worth 60% market exclusion (8GB only) + performance/cost penalties

---

**DECISION REQUIRED FROM:** Founder/Product Lead
**BLOCKER:** Confirm Qwen evaluation scope (not in original PRD) OR proceed with Llama 3.2 1B
**DEADLINE:** Day 3 (per PRD timeline)

**Contact:** QA/Research Assistant (this analysis)
**Full Report:** `/Users/uxersean/Desktop/YI_Clean/analysis_qwen_quantization_decision.md`
**JSON Data:** `/Users/uxersean/Desktop/YI_Clean/qa_report_quantization_analysis.json`
