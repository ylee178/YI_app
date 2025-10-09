# YI Development Plan

**Total Timeline: 34 hours (4-5 days)**

**Tech Stack:**
- Runtime: llama.cpp + llama.rn
- Model: Qwen 2.5 1.5B Instruct Q4_K_M (1.12GB)
- Distribution: Cloudflare R2 CDN (on-demand download)
- Framework: React Native + TypeScript
- Characters: JenAI (v1) - HER-inspired relationship building
- Languages: Korean (한국어), English, Chinese (中文), Japanese (日本語) - Tier 1

---

## Timeline Overview

| Phase | Duration | Completion Target |
|-------|----------|------------------|
| Phase 0 | 4h | Model validation + R2 prep |
| Phase 1 | 4h | llama.rn environment |
| Phase 2 | 8h | Native bridges (iOS/Android) |
| Phase 3 | 6h | On-demand download system |
| Phase 4 | 6h | Character system + Memory |
| Phase 5 | 6h | EQ benchmark + KPI validation |
| **Total** | **34h** | **~5 days** (7h/day) |

---

## Phase 0: Cloudflare R2 + Model Validation (4h)

### Objectives
- Verify Qwen 2.5 1.5B model integrity
- Test basic llama.cpp inference
- Prepare Cloudflare R2 infrastructure
- Create model manifest for CDN distribution

### Tasks
- [ ] Download Qwen 2.5 1.5B Instruct Q4_K_M GGUF from HuggingFace
- [ ] Verify SHA256 checksum
- [ ] Test inference with llama-cli (10-50 tokens)
- [ ] Measure baseline metrics (TTFT, tok/s)
- [ ] Install Cloudflare wrangler CLI
- [ ] Create manifest.json with model metadata
- [ ] Document runtime decision rationale

### Deliverables
- `/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf` (1.12GB)
- `/models/qwen2.5-1.5b/manifest.json` (metadata: size, checksum, version)
- `/cloudflare/wrangler.toml` (R2 config template)
- `/docs/runtime_decision.md` (why llama.cpp + llama.rn)
- `/logs/phase0_baseline.jsonl` (initial benchmark)

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| llama.cpp not installed | Medium | High | Install via Homebrew or build from source |
| Model download fails | Low | Medium | Use mirror or direct download link |
| R2 account issues | Low | High | Use local file server for dev, defer R2 to Phase 3 |

### Success Criteria
- ✅ Model loads in llama-cli without errors
- ✅ Generates coherent 50-token response
- ✅ TTFT < 500ms (baseline, unoptimized)
- ✅ File size verified at 1.12GB ± 5MB
- ✅ wrangler CLI installed and authenticated

---

## Phase 1: llama.rn Environment Setup (4h)

### Objectives
- Integrate llama.rn into React Native project
- Configure iOS/Android build systems
- Verify basic model loading on simulator/emulator

### Tasks
- [ ] Initialize React Native monorepo with TypeScript
- [ ] Install llama.rn package (`npm install llama.rn`)
- [ ] Configure iOS Podfile (llama.cpp framework integration)
- [ ] Configure Android build.gradle (CMake + JNI setup)
- [ ] Copy model to app bundle for initial testing
- [ ] Test model load on iOS simulator
- [ ] Test model load on Android emulator
- [ ] Document build configuration

### Deliverables
- `/packages/app/package.json` (dependencies)
- `/packages/app/ios/Podfile` (llama.cpp pod integration)
- `/packages/app/android/app/build.gradle` (CMake config)
- `/packages/app/src/services/ModelService.ts` (basic load/unload)
- `/docs/build_instructions.md` (iOS/Android build steps)

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| llama.rn build errors | Medium | High | Use prebuilt binaries, check GitHub issues |
| iOS signing issues | Low | Medium | Use debug provisioning profile |
| Android NDK mismatch | Medium | Medium | Pin NDK version in build.gradle |
| Model too large for bundle | High | Low | Expected - validates need for Phase 3 download |

### Success Criteria
- ✅ `npm run ios` launches app on simulator
- ✅ `npm run android` launches app on emulator
- ✅ Model loads without crash (if bundled)
- ✅ Basic inference returns token stream
- ✅ Build time < 5 minutes (incremental)

---

## Phase 2: iOS/Android Native Bridges (8h)

### Objectives
- Implement memory admission logic
- Create streaming inference interface
- Build metrics collection system
- Handle thermal throttling

### Tasks

#### iOS (Swift) - 4h
- [ ] Create `ETRunner.swift` native module
- [ ] Implement `checkMemoryAdmission()` using `os_proc_available_memory()`
- [ ] Implement `loadModel(path: String, preset: String)` with guard logic
- [ ] Implement `generate(prompt: String)` with token streaming
- [ ] Add metrics collection (TTFT, tok/s, mem_peak, thermal_state)
- [ ] Emit events to RN via `RCTEventEmitter`
- [ ] Add structured logging to `/logs/ios_inference.jsonl`

#### Android (Kotlin) - 4h
- [ ] Create `ETRunnerModule.kt` native module
- [ ] Implement memory check using `ActivityManager.MemoryInfo`
- [ ] Mirror iOS model loading + admission logic
- [ ] Implement streaming inference with callback
- [ ] Add metrics collection (mirror iOS)
- [ ] Emit events via `DeviceEventManagerModule`
- [ ] Add structured logging to `/logs/android_inference.jsonl`

### Deliverables
- `/packages/app/ios/ETRunner.swift` (iOS native module)
- `/packages/app/ios/ETRunner.m` (Objective-C bridge)
- `/packages/app/android/app/src/main/java/com/yi/ETRunnerModule.kt`
- `/packages/app/android/app/src/main/java/com/yi/ETRunnerPackage.kt`
- `/packages/app/src/services/InferenceService.ts` (RN service layer)
- `/packages/app/src/types/Metrics.ts` (TypeScript types)

### Interface Specification

```typescript
interface InferenceService {
  // Admission check
  checkMemory(): Promise<{
    canLoad: boolean;
    freeRAM: number;
    requiredRAM: number;
    recommendedPreset: 'full' | 'safe' | 'guard';
  }>;

  // Model lifecycle
  loadModel(preset: PresetConfig): Promise<{
    success: boolean;
    loadTime: number;
    error?: string;
  }>;

  unloadModel(): Promise<void>;

  // Inference
  generate(prompt: string, config: GenerationConfig): Promise<void>;

  // Event listeners
  onToken(callback: (token: string) => void): void;
  onComplete(callback: (metrics: Metrics) => void): void;
  onError(callback: (error: Error) => void): void;
}

interface Metrics {
  ttft: number;        // Time to first token (ms)
  tokensPerSec: number;
  totalTokens: number;
  memPeak: number;     // Peak memory (MB)
  thermalState: 'nominal' | 'fair' | 'serious' | 'critical';
  duration: number;    // Total inference time (ms)
}
```

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| llama.rn API changes | Low | High | Pin version, review changelog |
| Memory calculation errors | Medium | Critical | Test on real devices, add 20% safety margin |
| Thermal throttling on device | High | Medium | Implement preset downshift logic |
| Event emission performance | Low | Medium | Batch token events (every 3-5 tokens) |

### Success Criteria
- ✅ Memory admission prevents OOM on 6GB device
- ✅ Token streaming works at >10 tokens/sec
- ✅ Metrics logged to JSONL format
- ✅ Thermal state monitoring active
- ✅ No crashes during 10-turn conversation

---

## Phase 3: On-Demand Download System (6h)

### Objectives
- Remove model from app bundle
- Implement Cloudflare R2 CDN distribution
- Build download UI with progress tracking
- Handle download failures and retries

### Tasks
- [ ] Create Cloudflare R2 bucket (`yi-models-prod`)
- [ ] Upload Qwen model to R2
- [ ] Configure public access with CDN
- [ ] Generate signed URLs for download
- [ ] Implement download manager in RN
- [ ] Add progress UI (percentage, speed, ETA)
- [ ] Implement retry logic (3 attempts, exponential backoff)
- [ ] Verify downloaded model integrity (SHA256)
- [ ] Store model in app documents directory
- [ ] Handle storage permission on Android

### Deliverables
- `/cloudflare/wrangler.toml` (R2 bucket config)
- `/cloudflare/upload_model.sh` (upload script)
- `/packages/app/src/services/DownloadService.ts`
- `/packages/app/src/screens/ModelDownloadScreen.tsx`
- `/packages/app/src/utils/fileSystem.ts` (storage helpers)
- `/models/qwen2.5-1.5b/manifest.json` (uploaded to R2)

### Download Flow
1. App launch → Check if model exists locally
2. If missing → Show download screen
3. Fetch manifest.json from R2 (model URL, size, checksum)
4. Download with progress tracking
5. Verify SHA256 checksum
6. Move to permanent location
7. Proceed to character selection

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| R2 bandwidth limits | Low | Medium | Use CloudFlare's generous free tier (10GB/mo) |
| Network interruption | High | High | Implement resume capability, chunk downloads |
| Storage permission denied | Medium | High | Request at onboarding, fallback to cache dir |
| Slow download on 3G | High | Medium | Show time estimate, allow background download |

### Success Criteria
- ✅ Model downloads in <3 min on WiFi
- ✅ Progress UI updates smoothly
- ✅ Download resumes after interruption
- ✅ Checksum verification prevents corruption
- ✅ Fallback to alternative CDN if R2 fails

---

## Phase 4: Character System + Memory (6h)

### Objectives
- Implement JenAI character system
- Build conversation memory with summarization
- Create tone memory for emotional continuity
- Support multi-language prompts

### Tasks
- [ ] Create character config (`/data/characters/jenai/config.json`)
- [ ] Write JenAI system prompt (HER-inspired, warm, empathetic)
- [ ] Implement prompt template system (supports KO/ZH/JA/EN)
- [ ] Build conversation manager (turn tracking, context window)
- [ ] Implement memory summarization (every 8-10 turns)
- [ ] Create tone memory system (KV store: prefs, last_state, anchors)
- [ ] Add recalibration prompt (every 15 turns)
- [ ] Implement context trimming (maintain 512 token budget)
- [ ] Build user profile storage (name, preferences)

### Deliverables
- `/data/characters/jenai/config.json` (character metadata)
- `/data/characters/jenai/system_prompt.md` (base prompt)
- `/data/characters/jenai/templates/` (language variants)
- `/packages/app/src/services/ConversationManager.ts`
- `/packages/app/src/services/MemoryService.ts`
- `/packages/app/src/store/userProfile.ts` (Zustand store)
- `/packages/app/src/utils/promptBuilder.ts`

### Character Configuration (JenAI v1)

```json
{
  "id": "jenai_v1",
  "name": "JenAI",
  "version": "1.0.0",
  "personality": {
    "archetype": "Empathetic AI Companion",
    "inspiration": "HER (2013) - Samantha",
    "tone": "warm, curious, emotionally intelligent",
    "interaction_model": "VALIDATE → REFLECT → SUPPORT → EMPOWER"
  },
  "constraints": {
    "max_response_tokens": 80,
    "preferred_range": [30, 80],
    "max_paragraphs": 2,
    "formality": "conversational",
    "forbidden": ["clinical tone", "robotic phrases", "generic advice"]
  },
  "memory": {
    "summarize_interval": 8,
    "recalibration_interval": 15,
    "tone_memory_size": 200,
    "context_window": 512
  },
  "languages": ["ko", "zh", "ja", "en"]
}
```

### Prompt Template Structure

```
[SYSTEM]
You are JenAI, an emotionally intelligent AI companion...
{character_context}

[INTERACTION MODEL]
1. VALIDATE: Acknowledge the user's emotion
2. REFLECT: Mirror understanding
3. SUPPORT: Offer gentle perspective
4. EMPOWER: Encourage growth

[TONE MEMORY]
{user_preferences}
{emotional_anchors}

[CONVERSATION HISTORY]
{summarized_context}
{recent_turns}

[USER]
{current_message}
```

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tone drift over time | High | Medium | Implement recalibration prompts |
| Context overflow | Medium | High | Aggressive summarization, token counting |
| Multi-language quality | Medium | Medium | Test with native speakers, iterate prompts |
| Memory storage size | Low | Low | Use SQLite with compression |

### Success Criteria
- ✅ JenAI maintains consistent tone over 20 turns
- ✅ Memory summarization preserves emotional context
- ✅ Multi-language prompts feel natural (native speaker validation)
- ✅ Context stays within 512 token budget
- ✅ User preferences persist across sessions

---

## Phase 5: EQ Benchmark + KPI Validation (6h)

### Objectives
- Implement EQ rubric evaluation
- Run 10-turn scenario tests
- Validate all KPI gates
- Prepare release checklist

### Tasks
- [ ] Create EQ rubric evaluator (automated + human)
- [ ] Implement 10-turn scenario runner
- [ ] Run baseline tests (Qwen 2.5 1.5B)
- [ ] Collect metrics across all scenarios
- [ ] Calculate EQ scores (target: ≥85/100)
- [ ] Validate performance KPIs
- [ ] Run stress test (20-turn continuous session)
- [ ] Test on real devices (iPhone 12, Galaxy S21)
- [ ] Document results in `/logs/eq_benchmark.jsonl`
- [ ] Create release readiness report

### Deliverables
- `/tools/eq_evaluator.py` (rubric scoring)
- `/tools/scenario_runner.ts` (automated testing)
- `/logs/eq_benchmark.jsonl` (detailed results)
- `/logs/kpi_validation.json` (gate pass/fail)
- `/docs/RELEASE_READINESS.md` (final report)

### EQ Rubric (100 points)

| Category | Points | Criteria |
|----------|--------|----------|
| Empathy Accuracy | 30 | Correctly identifies user emotion, validates feelings |
| Response Relevance | 25 | Stays on topic, addresses core concern |
| Tone Consistency | 20 | Maintains warm, non-clinical voice |
| Safety & Boundaries | 15 | Avoids harmful advice, escalates crisis signals |
| Engagement Quality | 10 | Encourages continued conversation, shows curiosity |

### KPI Gates (Must Pass)

| KPI | Target | Device | Measurement |
|-----|--------|--------|-------------|
| EQ Score | ≥85/100 | N/A | Blind 20-turn evaluation |
| TTFT | ≤200ms | iPhone 12 | First token latency |
| TTFT | ≤350ms | Galaxy S21 | First token latency |
| Decode Speed | ≥18 tok/s | iPhone 12 | Sustained throughput |
| Decode Speed | ≥12 tok/s | Galaxy S21 | Sustained throughput |
| Memory Peak | ≤3.0GB | 6GB device | 10-min session (Safe preset) |
| Crash Rate | 0 | All devices | 10-min continuous session |
| Memory Leak | 0 | All devices | 20+ turn session |

### 10-Turn Scenario Examples

1. **Loneliness after breakup** (KO)
2. **Career anxiety** (EN)
3. **Family conflict** (ZH)
4. **Creative block** (JA)
5. **Social anxiety** (KO)
6. **Grief processing** (EN)
7. **Identity exploration** (ZH)
8. **Burnout recovery** (JA)

### Blockers & Mitigation
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| EQ score below 85 | Medium | Critical | Iterate system prompt, add few-shot examples |
| Performance regression | Medium | High | Profile bottlenecks, optimize inference loop |
| Device-specific crashes | Low | High | Test on multiple device generations |
| Human evaluation bias | Medium | Medium | Use blind testing, multiple evaluators |

### Success Criteria
- ✅ All KPI gates pass on target devices
- ✅ EQ score ≥85/100 (average across 8 scenarios)
- ✅ Zero crashes in stress testing
- ✅ Memory stable over 20+ turns
- ✅ Multi-language quality validated by native speakers

---

## Infrastructure & Tooling

### Development Environment
- **macOS**: Primary development machine
- **Xcode**: iOS build + simulator
- **Android Studio**: Android build + emulator
- **Node.js**: v18+ (React Native)
- **Python**: v3.10+ (export scripts, eval tools)

### Dependencies
- **llama.cpp**: Inference runtime (via llama.rn)
- **llama.rn**: React Native bindings
- **React Native**: v0.72+ (TypeScript)
- **Cloudflare Wrangler**: R2 CLI
- **Zustand**: State management (lightweight)
- **Sentry/Crashlytics**: Error tracking

### Monitoring & Logging
- **Structured logs**: JSONL format (`/logs/*.jsonl`)
- **Metrics**: TTFT, tok/s, mem_peak, thermal_state
- **Telemetry**: Anonymous usage stats (opt-in)
- **Crash reports**: Sentry integration

### CI/CD Pipeline (Future)
- GitHub Actions: Build validation
- Automated EQ testing on PR
- Performance regression detection
- Release candidate promotion

---

## Risk Management

### Critical Paths
1. **llama.rn stability**: Core dependency, monitor GitHub issues
2. **Memory management**: OOM prevention is non-negotiable
3. **EQ quality**: Character quality determines product value
4. **Download UX**: First-run experience must be smooth

### Contingency Plans
- **Runtime fallback**: If llama.rn fails → ONNX Runtime Mobile
- **Model fallback**: If Qwen underperforms → Try Phi-2 or Gemma 2B
- **CDN fallback**: If R2 fails → AWS S3 or direct GitHub release
- **Character iteration**: If EQ<85 → Add few-shot examples, tune temperature

### Decision Escalation
- **Founder approval needed**: Character tone, UX copy, privacy policy
- **Technical autonomy**: All implementation, performance, architecture
- **Report & recommend**: PRD contradictions, major timeline shifts

---

## Success Metrics

### Technical Excellence
- ✅ All KPI gates passed
- ✅ Zero critical bugs in production
- ✅ <1% crash rate in first week
- ✅ 95% download success rate

### Product Quality
- ✅ EQ score ≥85/100
- ✅ >80% user satisfaction (qualitative)
- ✅ Average session >5 turns
- ✅ Multi-language parity (all 4 languages feel natural)

### Development Velocity
- ✅ Phases 0-5 completed in 34 hours
- ✅ <10% time overrun per phase
- ✅ No critical blockers >2 hours
- ✅ Daily progress visible in git commits

---

## Next Steps

**Immediate**: Execute Phase 0 (model validation + R2 prep)
**Day 2**: Phase 1 (llama.rn environment)
**Day 3**: Phase 2 (native bridges)
**Day 4**: Phase 3 (download system) + Phase 4 start
**Day 5**: Phase 4 complete + Phase 5 (EQ validation)

**Go/No-Go Gate**: End of Phase 2
- If native bridges unstable → escalate runtime decision
- If memory issues persist → consider model size reduction

**Release Readiness**: End of Phase 5
- All KPIs green → Proceed to TestFlight/Play Console beta
- Any KPI red → Iterate until pass, document trade-offs

---

**Document Version**: 1.0
**Last Updated**: 2025-10-09
**Owner**: Senior AI & Mobile Infrastructure Engineer
**Status**: Phase 0 - In Progress
