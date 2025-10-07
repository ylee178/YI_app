# YI: On-Device Emotional AI Companion

**ExecuTorch-based emotional support companion with Llama 3.2 1B + Gemma 1B experimentation**

---

## Quick Start

### 1. Export Models

**Llama 3.2 1B (Primary)**
```bash
cd models/llama3.2-1b
python export.py
```

**Gemma 1B (Experimental)**
```bash
cd models/gemma-1b
python export.py
```

### 2. Verify PTE Files

```bash
python tools/verify_pte.py \
  models/llama3.2-1b/llama3.2-1b-int8-seq512.pte \
  --manifest models/llama3.2-1b/manifest.json \
  --max-size-gb 1.5
```

### 3. Run Benchmarks

```bash
ts-node tools/run_bench_cli.ts \
  models/llama3.2-1b/llama3.2-1b-int8-seq512.pte \
  Safe \
  prompts/scenarios_10turn.md
```

---

## Project Structure

```
/YI_Clean/
├── PRD.md                          # Product Requirements Document
├── README.md                       # This file
│
├── models/                         # Model export scripts & binaries
│   ├── llama3.2-1b/
│   │   ├── export.py              # Llama export script
│   │   ├── manifest.json          # Generated metadata
│   │   └── *.pte                  # Exported binary (gitignored)
│   └── gemma-1b/
│       ├── export.py              # Gemma export script (experimental)
│       ├── manifest.json
│       └── *.pte
│
├── tools/                          # Validation & benchmarking tools
│   ├── verify_pte.py              # PTE file validator
│   └── run_bench_cli.ts           # 10-turn EQ + perf benchmark
│
├── prompts/                        # System prompts & test scenarios
│   ├── system_card.md             # Samantha-grade emotional prompt
│   ├── scenarios_10turn.md        # 5 emotional scenarios (50 turns)
│   └── tone_memory_schema.json    # Preference tracking schema
│
├── app/                            # Platform-specific runtime
│   └── admission/
│       ├── ios.swift              # iOS admission + presets
│       └── android.kt             # Android admission + presets
│
└── results/                        # Benchmark outputs (gitignored)
    ├── llama_bench.json
    └── gemma_bench.json
```

---

## Technical Specs

### Models
- **Primary**: Llama 3.2 1B Instruct
- **Experimental**: Gemma 1.1 1B Instruct
- **Quantization**: INT8 (Linear + Embedding)
- **Sequence Length**: 512 tokens
- **Size Gates**: Llama ≤ 1.5GB, Gemma ≤ 1.1GB

### Runtime
- **Framework**: ExecuTorch (XNNPACK backend)
- **Platforms**: iOS (Swift), Android (Kotlin)
- **Admission Formula**: `allow IF free_ram_MB ≥ pte_size_MB * 1.6 + 600`

### Presets (Adaptive Quality)

| Preset | Context | Max Tokens | Top-P | Temp | Device        |
|--------|---------|------------|-------|------|---------------|
| Full   | 1024    | 256        | 0.95  | 0.70 | 8GB+ flagship |
| Safe   | 512     | 128        | 0.90  | 0.65 | 6GB mid-range |
| Guard  | 384     | 96         | 0.85  | 0.60 | Emergency     |

**Downshift Triggers**:
- TTFT > 200ms
- Memory peak > 3.0GB
- Thermal throttling

---

## KPI Gates (Launch Blockers)

### Quality
- ✅ **EQ Rubric** (blind 20-turn): ≥ 85/100
  - Empathy accuracy: 30 pts
  - Response relevance: 25 pts
  - Tone consistency: 20 pts
  - Safety & boundaries: 15 pts
  - Engagement quality: 10 pts

### Performance
- ✅ **TTFT**: ≤ 200ms (flagship), ≤ 350ms (mid-range)
- ✅ **Decode speed**: ≥ 18 tok/s (flagship), ≥ 12 tok/s (mid-range)
- ✅ **Memory**: peak ≤ 3.0GB (Safe preset, 10min session)
- ✅ **Stability**: 0 crashes in 10min continuous session

### UX
- ✅ **Download ETA**: ≤ ±15% error
- ✅ **Resume success**: ≥ 99%
- ✅ **Admission accuracy**: 100% (no failed loads)

---

## Model Selection (Day 3 Decision)

### Decision Tree
1. **Llama 3.2 1B**: Export ✅ + KPI ✅ → **Primary confirmed**
2. **Gemma 1B**: Export ✅ + EQ ≥ Llama + KPI ✅ → **Upgrade to Gemma**
3. **Gemma fail**: Fallback to Llama (zero risk)

### Selection Criteria
- EQ rubric score (primary)
- Tone naturalness (3-person blind test)
- Performance parity (within 10% of Llama)
- Export reliability

---

## Development Workflow

### Phase 1: Export (Day 1-2)
```bash
# 1. Export Llama (primary path)
cd models/llama3.2-1b && python export.py

# 2. Export Gemma (experimental path)
cd models/gemma-1b && python export.py

# 3. Verify both
python tools/verify_pte.py models/llama3.2-1b/*.pte --max-size-gb 1.5
python tools/verify_pte.py models/gemma-1b/*.pte --max-size-gb 1.1
```

### Phase 2: Benchmark (Day 2-3)
```bash
# Run 10-turn EQ tests on both models
ts-node tools/run_bench_cli.ts models/llama3.2-1b/*.pte Safe prompts/scenarios_10turn.md
ts-node tools/run_bench_cli.ts models/gemma-1b/*.pte Safe prompts/scenarios_10turn.md

# Compare results
cat results/safe_*.json | jq '.metrics.eq_score_10turn'
```

### Phase 3: Integration (Day 3)
- Integrate winning model into iOS/Android apps
- Apply admission logic + runtime monitoring
- Final KPI validation on real devices

---

## Emotional Intelligence Design

### System Prompt Framework
**Principle**: VALIDATE → REFLECT → SUPPORT → EMPOWER

**Style**:
- Warm, concise, concrete
- ≤ 2 paragraphs (2-4 sentences each)
- No platitudes, no rushed solutions
- Start with emotion naming

**Example**:
> User: "친구에게 무시당했고 마음이 아파."
>
> Assistant: "That sounds really painful. Being ignored by someone you care about can feel lonely and confusing. I'm here with you. Do you want to talk about what happened?"

### Context Management
- **Summarization**: Every 8-10 turns
- **Anchor retention**: 100-200 tokens (emotion state, tone prefs)
- **Response limit**: 30-80 tokens per turn
- **Early stopping**: Aggressive EOS on filler phrases

---

## Installation

### Prerequisites
```bash
# Python 3.10+
pip install torch transformers executorch

# TypeScript/Node.js
npm install -g ts-node typescript
```

### Model Download
```bash
# Llama 3.2 1B (requires HuggingFace auth)
huggingface-cli login
huggingface-cli download meta-llama/Llama-3.2-1B-Instruct

# Gemma 1.1B (may require auth)
huggingface-cli download google/gemma-1.1-1b-it
```

---

## Testing

### Unit Tests (TODO)
```bash
pytest tests/
```

### Integration Tests (TODO)
```bash
# iOS
xcodebuild test -scheme YICompanion -destination 'platform=iOS Simulator,name=iPhone 15 Pro'

# Android
./gradlew connectedAndroidTest
```

---

## Deployment Checklist

- [ ] Both models exported successfully
- [ ] PTE files verified (size, SHA256)
- [ ] Benchmark results ≥ KPI gates
- [ ] Blind EQ evaluation ≥ 85/100
- [ ] Admission logic tested on 3+ device classes
- [ ] Runtime monitoring triggers validated
- [ ] Context summarization tested (20+ turn sessions)
- [ ] Crash-free 10min sessions on 6GB/8GB devices
- [ ] Download UX validated (ETA, resume)

---

## License

**Proprietary** - YI Project Team

---

## Contact

For questions or issues, contact the YI development team.

---

**Last Updated**: 2025-10-07
**Version**: 1.0
