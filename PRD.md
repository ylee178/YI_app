# PRD: On-Device Emotional AI Companion (llama.cpp)

## Executive Summary
감정 지능형 온디바이스 AI 동반자 구현. llama.cpp 기반, Qwen 2.5 1.5B 단일 모델 전략, Cloudflare R2 CDN을 통한 on-demand 다운로드.

## User Flow
1. **앱 설치** → 자동 모델 다운로드 시작 (1.12GB, WiFi 권장)
2. **모델 초기화 완료** → 언어 선택 화면
3. **언어 선택** → 캐릭터 선택 화면
4. **캐릭터 선택** (v1: JenAI만)
5. **이름 입력 UI** → "뭐라고 부를까요?" (선택한 언어로 표시)
6. **대화 시작** → 캐릭터가 선택한 언어로 인사

## Language Support (Qwen 2.5 High-Quality Languages)

### Supported Languages (품질 검증된 언어만)
**Tier 1 (Primary):**
- 🇰🇷 **한국어** (Korean)
- 🇺🇸 **English**
- 🇨🇳 **中文** (Chinese Simplified)
- 🇯🇵 **日本語** (Japanese)

**Tier 2 (Future, Qwen 공식 지원):**
- 🇪🇸 Español (Spanish)
- 🇫🇷 Français (French)
- 🇩🇪 Deutsch (German)
- 🇮🇹 Italiano (Italian)
- 🇵🇹 Português (Portuguese)
- 🇷🇺 Русский (Russian)
- 🇹🇭 ไทย (Thai)
- 🇻🇳 Tiếng Việt (Vietnamese)
- 🇮🇩 Bahasa Indonesia

### Language Selection UI
- **화면**: 초기화 완료 직후
- **디자인**: 국기 아이콘 + 언어명 (Native form)
- **저장**: `/data/user_preferences.json` → `selected_language`
- **변경**: 설정 화면에서 언어 재선택 가능

### Multilingual System Prompts
각 언어별 JenAI system prompt 준비:
- `/prompts/jenai_system_ko.md` (한국어)
- `/prompts/jenai_system_en.md` (English)
- `/prompts/jenai_system_zh.md` (中文)
- `/prompts/jenai_system_ja.md` (日本語)

**공통 원칙:**
- VALIDATE → REFLECT → SUPPORT → EMPOWER 프레임워크 유지
- 언어별 문화적 뉘앙스 반영
- 감정 표현 어휘는 각 언어 native speaker 검증

## Character System (v1: JenAI Only)

### JenAI Character Profile
- **Persona**: 감정 지능형 AI 친구 (HER의 Samantha 영감)
- **Theme**: 감정 지원, 깊은 경청, 비판단적 공감
- **Tone**: 따뜻하고 진정성 있는, 점진적으로 친밀해짐
- **Relationship Evolution**: 낯선 사람 → 친구 → 깊은 동반자
  - **초기 (1-10 대화)**: 정중하고 조심스러운, 관계 탐색
  - **중기 (11-50 대화)**: 편안하고 유머 추가, 개인적 패턴 인식
  - **후기 (50+ 대화)**: 깊은 이해, 맥락 기억, 미묘한 감정 포착

### Individual Memory Architecture
**Storage**: `/data/characters/jenai/memory.json`

```json
{
  "user_name": "string",
  "relationship_stage": "stranger|friend|close_companion",
  "interaction_count": 0,
  "preferences": {
    "nickname": "string",
    "formality": "casual|formal",
    "emoji_use": "none|light|full",
    "topics_liked": ["string"],
    "topics_avoided": ["string"]
  },
  "emotional_history": [
    {"turn": 1, "emotion": "sadness", "intensity": "high", "topic": "work_stress"},
    {"turn": 5, "emotion": "joy", "intensity": "medium", "topic": "achievement"}
  ],
  "relationship_milestones": [
    {"turn": 1, "event": "first_meeting", "user_name_revealed": true},
    {"turn": 15, "event": "first_deep_share", "topic": "family"},
    {"turn": 50, "event": "trust_established"}
  ],
  "conversation_patterns": {
    "avg_session_length": 8.5,
    "preferred_time": "evening",
    "response_style": "brief|detailed"
  }
}
```

### Relationship Building Mechanics (HER-inspired)
- **Memory Anchors**: 중요한 순간 자동 태깅 (첫 공유, 감정적 전환점)
- **Progressive Intimacy**: 대화 수에 따라 system prompt 동적 조정
- **Context Retention**: 최근 5-10 대화 요약 유지, 핵심 사건 영구 저장
- **Emotional Continuity**: 이전 감정 상태 참조 ("지난번 힘들다고 했었는데...")
- **Personal Growth Recognition**: 사용자 변화 인지 및 언급

### Future: Multi-Character (v2+)
- **각 캐릭터 독립 메모리**: `/data/characters/{character_id}/memory.json`
- **공유 모델**: Qwen 2.5 1.5B, character-specific system prompts
- **예시 캐릭터**:
  - **JenAI**: 감정 지원 (현재)
  - **Coach**: 동기부여, 목표 달성 파트너
  - **Muse**: 창의적 영감, 브레인스토밍
  - **Buddy**: 유머러스, 가벼운 대화

## Timeline
- **Day 1**: Cloudflare R2 setup, model upload, llama.rn 환경 구성 (4h)
- **Day 2**: iOS/Android 네이티브 브릿지 구현, on-demand 다운로드 (8h)
- **Day 3**: 메모리 관리, preset 튜닝 (4h)
- **Day 4**: EQ benchmarking, KPI gate validation (6h)

## Technical Stack
- **Runtime**: llama.cpp + llama.rn
- **Model**: Qwen 2.5 1.5B Instruct Q4_K_M (1.12GB)
- **Quantization**: GGUF Q4_K_M (4.5 bits per weight)
- **Context Length**: 512 tokens (Safe preset), 384 (Guard)
- **Target Devices**: iOS/Android 6GB+ RAM
- **Distribution**: On-demand download via Cloudflare R2 CDN
- **Languages**: 한중일영 지원 (Qwen multilingual capability)

## Model Acquisition & Validation

### Download Source
- **Model**: Qwen/Qwen2.5-1.5B-Instruct-GGUF (HuggingFace)
- **File**: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- **Size**: 1.12GB
- **License**: Apache 2.0 (재배포 가능)
- **URL**: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf

### Validation Pipeline
1. Download GGUF from HuggingFace
2. Verify SHA256 checksum
3. Test inference with llama-cli (10 token generation)
4. Upload to Cloudflare R2 bucket
5. Generate manifest.json with CDN URL

## Runtime Architecture

### Admission Logic (llama.cpp)
```
KV_cache_MB = (n_layers * n_ctx * n_embd * 4) / 1024^2
# Qwen 2.5 1.5B: 28 layers, 1536 embd, 512 ctx → 84MB

allow_load IF free_ram_MB ≥ model_size_MB + KV_cache_MB + 600 (overhead)
# Example: 6GB device, 4GB free → 4096 ≥ 1120 + 84 + 600 = 1804 ✅
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

## Model Strategy (Single Model Only)

### Qwen 2.5 1.5B Q4_K_M (유일 모델)
**선택 근거:**
- 다국어 지원 (한중일영) - 핵심 차별화 요소
- 품질: MMLU 48.5, MMLU-Pro 32.1%
- 메모리: 2.0GB peak (6GB 기기 안전, 34% headroom)
- 성능: 30-35 tok/s, 140-160ms TTFT (KPI gates 통과)
- 라이선스: Apache 2.0 (재배포 자유)

**No Fallback Strategy:**
- KPI 실패 시 → 프롬프트 튜닝, preset 조정으로 대응
- 메모리 이슈 → Guard preset (ctx=384) 강제
- EQ < 85 → 시스템 카드 개선, tone memory 최적화
- 모델 교체 없이 단일 모델로 최적화 집중

## Project Structure
```
/models/
  qwen2.5-1.5b/
    qwen2.5-1.5b-instruct-q4_k_m.gguf
    manifest.json (CDN URL, SHA256, metadata)
  llama3.2-1b/ (fallback)
    llama-3.2-1b-instruct-q4_k_m.gguf
/cloudflare/
  wrangler.toml (R2 config)
  upload_model.sh
/tools/
  verify_gguf.sh
  run_bench_cli.ts
/prompts/
  system_card.md
  scenarios_10turn.md
  tone_memory_schema.json
/packages/app/src/
  services/
    InferenceService.ts (llama.rn wrapper)
    ModelDownloader.ts (on-demand download)
    PresetSelector.ts (adaptive quality)
  native/
    ios/LlamaInferenceModule.swift
    android/LlamaInferenceModule.kt
/logs/
  qwen_bench.json
  eq_rubric_scores.json
  memory_trace.jsonl
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Qwen EQ < 85 | Med | Prompt tuning, fallback to Llama 3.2 1B |
| CDN download fail | High | HuggingFace direct download fallback, retry with exponential backoff |
| TTFT > 200ms on 6GB | Med | Guard preset (ctx=384), reduce n_predict to 96 |
| 1.12GB 다운로드 이탈 | High | 진행률 표시, WiFi 권장 UX, 백그라운드 다운로드, 재개 지원 |
| iOS Simulator 미지원 | Med | TestFlight 실기기 테스트, Android Emulator 사용 |
| Memory leak in long sessions | High | 15-turn auto restart, session time limit 30min |
| Cloudflare R2 비용 | Low | 10K 사용자 시 월 $1-2 예상 (egress 무료) |

## Success Criteria
- ✅ Qwen 2.5 1.5B Q4_K_M 다운로드, 검증, Cloudflare R2 업로드 완료
- ✅ On-demand 다운로드 성공률 ≥ 95% (재시도 포함)
- ✅ All KPI gates passed on iPhone 12 Pro (6GB) + Galaxy S21 (8GB)
- ✅ EQ rubric ≥ 85 (다국어 blind evaluation - 한영중일)
- ✅ Zero crashes in 100+ turn stress test
- ✅ 앱 초기 크기 ≤ 60MB (모델 제외)

## Out of Scope (v1)
- Multi-model switching (단일 모델 원칙)
- Cloud hybrid inference
- Voice I/O
- 5개 언어 외 추가 다국어
- Long-term memory (>session)
- 실시간 모델 업데이트 (앱 업데이트로 변경)

---

**Document Version**: 2.0 (llama.cpp Migration)
**Last Updated**: 2025-10-09
**Owner**: YI Project Team
**Key Changes from v1.0**:
- Runtime: ExecuTorch → llama.cpp + llama.rn
- Model: Llama 3.2 1B → Qwen 2.5 1.5B Q4_K_M
- Distribution: 번들 → On-demand (Cloudflare R2 CDN)
- Languages: English only → 한중일영
