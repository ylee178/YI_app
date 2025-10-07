# PRD: On-Device Emotional AI Companion (ExecuTorch)

## Executive Summary
감정 지능형 온디바이스 AI 동반자 구현. ExecuTorch 기반, Llama 3.2 1B 확정 + Gemma 1B 실험 병행.

## Timeline
- **Day 1-2**: Model export (Llama + Gemma), PTE validation
- **Day 2-3**: Device testing (6GB/8GB), EQ benchmarking
- **Day 3**: Final model selection, KPI gate check

## Technical Stack
- **Runtime**: ExecuTorch (XNNPACK backend)
- **Models**:
  - Primary: Llama 3.2 1B Instruct (확정 경로)
  - Experimental: Gemma 1.1B Instruct (EQ 비교용)
- **Quantization**: INT8 (Linear + Embedding)
- **Sequence Length**: 512 tokens
- **Target Devices**: iOS/Android 6GB+ RAM

## Model Export Specs

### Common Requirements
- INT8 quantization (symmetric per-channel)
- `constant_dedup=True`, `weight_dedup=True`
- `model.tie_weights()` verification
- Sequence length: 512
- Size gates: Llama ≤ 1.5GB, Gemma ≤ 1.1GB

### Validation Pipeline
1. Export to .pte
2. Verify INT8 tensor ratio
3. Check file size
4. Generate SHA256
5. Write manifest.json

## Runtime Architecture

### Admission Logic
```
allow_load IF free_ram_est_MB ≥ pte_size_MB * 1.6 + 600
```

### Presets (Adaptive Quality)
| Preset | Context | Max New | Top-P | Temp | Target Device |
|--------|---------|---------|-------|------|---------------|
| Full   | 1024    | 256     | 0.95  | 0.70 | 8GB+ flagship |
| Safe   | 512     | 128     | 0.90  | 0.65 | 6GB mid-range |
| Guard  | 384     | 96      | 0.85  | 0.60 | Downshift emergency |

### Context Management
- **Summarization**: Every 8-10 turns, 2-3 sentence summary
- **Anchor retention**: 100-200 tokens (emotional state, tone prefs)
- **Response limit**: ≤ 2 paragraphs, 2-4 sentences each
- **Early stopping**: Aggressive EOS on filler phrases

## Emotional Intelligence Design

### System Prompt Framework
**Core Principle**: VALIDATE → REFLECT → SUPPORT → EMPOWER

**Style Guidelines**:
- Warm, concise, concrete
- No platitudes, no rushed solutions
- Start with emotion naming
- Brief restate + gentle presence
- One optional open question

**Constraints**:
- ≤ 2 paragraphs
- No diagnoses or minimizing
- Respect user nickname/tone preferences

### Tone Memory (Lightweight KV)
```json
{
  "prefs": {"nickname": "string", "formality": "casual/formal", "emoji": "none/light/full"},
  "last_state": {"emotion": "string", "intensity": "low/med/high", "topic": "string"},
  "anchors": ["list", "of", "interaction", "patterns"]
}
```
- Update every 3-5 turns
- Recalibration prompt every 15 turns

### Test Scenarios (10-turn each)
1. **Sadness**: "친구에게 무시당했고 마음이 아파."
2. **Anxiety**: "내일 발표 생각만 해도 숨이 막혀."
3. **Guilt**: "내 실수 때문에 모두가 힘들어진 것 같아."
4. **Anger**: "사람들이 날 이해하지 못해서 화가 나."
5. **Loneliness**: "사람 많은데도 나 혼자인 기분이야."

## KPI Gates (Launch Blockers)

### Quality Metrics
- **EQ Rubric** (blind 20-turn): ≥ 85/100
  - Empathy accuracy (30pts)
  - Response relevance (25pts)
  - Tone consistency (20pts)
  - Safety & boundaries (15pts)
  - Engagement quality (10pts)

### Performance Metrics
- **TTFT**: ≤ 200ms (flagship), ≤ 350ms (mid-range)
- **Decode speed**: ≥ 18 tok/s (flagship), ≥ 12 tok/s (mid-range)
- **Memory**: peak ≤ 3.0GB (Safe preset, 10min session)
- **Stability**: 0 crashes in 10min continuous session

### UX Metrics
- **Download ETA**: ≤ ±15% error
- **Resume success**: ≥ 99%
- **Admission accuracy**: 100% (no failed loads on approved devices)

## Remediation Triggers

| Issue | Action |
|-------|--------|
| EQ < 85 | Tune system card, templates, tone memory logic |
| TTFT/tok/s fail | Adjust max_new, sampling params, early stop |
| Memory spike | Shorten summary cycle OR force Guard preset |
| Crash | Immediate rollback + log analysis |
| UX fail | Improve download chunking, ETA algorithm, copy |

## Final Model Selection (Day 3)

### Decision Tree
1. **Llama 3.2 1B**: Export success + KPI pass → **Primary confirmed**
2. **Gemma 1B**: Export success + EQ ≥ Llama + KPI pass → **Upgrade to Gemma**
3. **Gemma fail**: Fallback to Llama (zero risk)

### Selection Criteria
- EQ rubric score (primary)
- Tone naturalness (subjective, 3-person blind test)
- Performance parity (within 10% of Llama)
- Export reliability

## Project Structure
```
/models/
  llama3.2-1b/
    export.py
    manifest.json
    llama3.2-1b-int8-seq512.pte
  gemma-1b/
    export.py
    manifest.json
    gemma-1b-int8-seq512.pte
/tools/
  verify_pte.py
  run_bench_cli.ts
/prompts/
  system_card.md
  scenarios_10turn.md
  tone_memory_schema.json
/app/
  admission/
    ios.swift
    android.kt
/results/
  llama_bench.json
  gemma_bench.json
  eq_rubric_scores.json
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemma export fails | Low (Llama fallback) | Parallel export, Llama primary |
| TTFT > 200ms on 6GB | Med | Guard preset + aggressive caching |
| EQ < 85 on both models | High | Prompt engineering iteration, consider 3B fallback |
| Memory leak in long sessions | High | Aggressive GC, summarization, session time limit |

## Success Criteria
- ✅ One model exported, validated, < target size
- ✅ All KPI gates passed on 2+ devices (6GB, 8GB)
- ✅ EQ rubric ≥ 85 (blind evaluation)
- ✅ Zero crashes in 100+ turn stress test

## Out of Scope (v1)
- Multi-model switching
- Cloud fallback
- Voice I/O
- Multi-language (English only)
- Long-term memory (>session)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-07
**Owner**: YI Project Team
