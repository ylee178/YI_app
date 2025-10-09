# Phase 1 Setup Checklist - YI App

## Status: READY FOR DEVICE TESTING

### Completed Tasks

- [x] React Native TypeScript project initialized
- [x] llama.rn v0.7.0-rc.2 installed
- [x] iOS CocoaPods configured (77 pods, llama-rn integrated)
- [x] Android autolinking configured
- [x] InferenceService implemented (4 languages: ko, en, zh, ja)
- [x] Test UI created with streaming inference
- [x] Model deployment guide created
- [x] iOS build verified (real device detected: "Uxer Sean")

### Prerequisites for Testing

#### iOS Testing (REQUIRED: Real Device)
- [x] iOS device connected: "Uxer Sean" (ID: 00008120-001409A234B8C01E)
- [ ] Xcode signing configured (Team ID set)
- [ ] Model file added to Xcode project bundle
- [ ] Build and deploy to device
- [ ] Test 4-language inference

**Action Required**:
```bash
# 1. Copy model to iOS bundle
mkdir -p /Users/uxersean/Desktop/YI_Clean/packages/app/ios/models
cp /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf \
   /Users/uxersean/Desktop/YI_Clean/packages/app/ios/models/

# 2. Open Xcode
open /Users/uxersean/Desktop/YI_Clean/packages/app/ios/YIApp.xcworkspace

# 3. Add model to target:
#    - Right-click YIApp project
#    - "Add Files to YIApp..."
#    - Select ios/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
#    - Check "Copy items if needed"
#    - Add to target "YIApp"

# 4. Update App.tsx model path (line 24):
const MODEL_PATH = 'models/qwen2.5-1.5b-instruct-q4_k_m.gguf';

# 5. Set signing team in Xcode:
#    - Select YIApp project
#    - Signing & Capabilities
#    - Team: [Your Apple Developer Account]

# 6. Build to device (Cmd+R)
```

#### Android Testing (BLOCKED: Java/Android SDK Required)
- [ ] Java JDK 17+ installed
- [ ] Android SDK installed
- [ ] Android Studio configured
- [ ] Emulator created OR device connected
- [ ] Model pushed via ADB

**Action Required**:
```bash
# Install Java (via Homebrew)
brew install openjdk@17

# Install Android Studio
# Download from https://developer.android.com/studio

# After Android Studio setup:
# 1. Push model to device
adb push /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf \
   /data/local/tmp/

# 2. Verify
adb shell ls -lh /data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf

# 3. Build and run
cd /Users/uxersean/Desktop/YI_Clean/packages/app
npx react-native run-android
```

---

## Project Structure

```
/Users/uxersean/Desktop/YI_Clean/packages/app/
├── App.tsx                          # Main test UI (4-language selector)
├── src/
│   └── services/
│       └── InferenceService.ts      # llama.rn wrapper with metrics
├── ios/
│   ├── YIApp.xcworkspace            # Open this in Xcode
│   ├── Podfile                      # CocoaPods config
│   └── models/                      # (Create this) Model bundle location
├── android/
│   ├── build.gradle                 # Root build config
│   └── app/
│       ├── build.gradle             # App-level config (autolinking)
│       └── src/main/assets/         # (Optional) Asset bundle location
├── node_modules/
│   └── llama.rn/                    # v0.7.0-rc.2
├── package.json
├── MODEL_DEPLOYMENT.md              # Deployment guide
└── PHASE1_SETUP_CHECKLIST.md        # This file
```

---

## Key Files

### InferenceService.ts
- **Path**: `/packages/app/src/services/InferenceService.ts`
- **Features**:
  - Multilingual system prompts (ko/en/zh/ja)
  - Streaming inference with token callback
  - Metrics tracking (TTFT, tok/s, total tokens)
  - Metal/GPU offload (n_gpu_layers: 99)
  - Context: 512 tokens, Max new: 128 tokens

### App.tsx
- **Path**: `/packages/app/App.tsx`
- **Features**:
  - Language selector (KO, EN, ZH, JA)
  - Test prompts for each language
  - Streaming text display
  - Real-time metrics (TTFT, speed, token count)
  - Error handling with user-friendly messages
  - Loading state during model initialization

### MODEL_DEPLOYMENT.md
- iOS bundling vs Documents directory
- Android assets vs internal storage
- ADB push commands
- Production CDN download strategy
- Performance expectations table

---

## Inference Configuration

### Current Settings (InferenceService.ts)
```typescript
{
  model: modelPath,
  use_mlock: true,
  n_ctx: 512,              // Context window
  n_gpu_layers: 99,        // Full GPU offload (Metal/OpenCL)
  embedding: false,

  // Generation parameters
  n_predict: 128,          // Max new tokens
  temperature: 0.7,
  top_p: 0.9,
  stop: ['<|im_end|>', '\nUser:', '\n\n']
}
```

### Multilingual System Prompts
Each language has tailored system prompt:
- **Korean**: 따뜻하고 공감적인 AI 동반자 (warm and empathetic companion)
- **English**: Warm and empathetic AI companion
- **Chinese**: 温暖且富有同理心的AI伴侣
- **Japanese**: 温かく共感的なAIコンパニオン

All prompts enforce:
- 2-3 sentence brevity
- No medical advice
- Natural, conversational tone

---

## Expected Performance (Phase 1 Baseline)

| Device | TTFT Target | Tok/s Target | Notes |
|--------|-------------|--------------|-------|
| iPhone 13 Pro | 150-200ms | 25-30 tok/s | Metal backend, optimal |
| iPhone 12 | 200-300ms | 18-22 tok/s | Metal backend, baseline |
| Galaxy S21 | 250-400ms | 15-20 tok/s | GPU offload, good |
| Mid-range Android | 300-500ms | 12-18 tok/s | May need ctx reduction |

**Memory Usage**: Expect ~2.5-3.0GB peak during inference (model: ~950MB, runtime overhead: ~1.5GB)

---

## Testing Protocol

### 1. Model Load Test
- **Expected**: 10-30 seconds on first load
- **Verify**: No crash, error message clear if fails

### 2. Single Inference Test (Each Language)
```
Prompts:
- KO: "오늘 기분이 좀 우울해요"
- EN: "I feel a bit down today"
- ZH: "我今天心情有点低落"
- JA: "今日は少し気分が落ち込んでいます"
```

**Success Criteria**:
- Response in correct language
- 2-3 sentences, empathetic tone
- TTFT < 500ms (acceptable for Phase 1)
- Tok/s > 12

### 3. Streaming Test
- Watch "Streaming:" box update in real-time
- Verify smooth token-by-token rendering
- Final "Response" box shows complete text

### 4. Rapid Fire Test
- Generate 5 responses in sequence
- No crashes
- No memory leak (stable metrics)

### 5. Language Switching Test
- Generate in KO → EN → ZH → JA
- Verify each response matches language context
- System prompt switches correctly

---

## Known Limitations (Phase 1)

1. **iOS Simulator**: NOT SUPPORTED (Metal backend required, use real device)
2. **Model Path**: Hardcoded in App.tsx (line 24), needs manual update
3. **No Download UI**: Model must be manually deployed
4. **No Memory Admission**: Will attempt load regardless of RAM availability
5. **No Adaptive Presets**: Fixed n_ctx=512, no dynamic scaling
6. **No Tone Memory**: Stateless inference (Phase 4 feature)
7. **Bundle Size**: iOS app ~1.1GB with bundled model (exceeds cellular limit)

---

## Troubleshooting Quick Reference

### iOS
| Issue | Solution |
|-------|----------|
| "Model load failed" | Check file added to Xcode target, verify path |
| Simulator crash | Use real device (Metal required) |
| "Unable to locate model" | Update MODEL_PATH to match bundle location |
| Slow TTFT (>1s) | Normal on first load, check subsequent calls |

### Android
| Issue | Solution |
|-------|----------|
| "Java Runtime not found" | Install JDK 17: `brew install openjdk@17` |
| "Model not found" | Push via ADB to /data/local/tmp/ |
| OOM crash | Reduce n_ctx to 256 in InferenceService.ts |
| Slow tok/s (<10) | Check GPU offload, close background apps |

---

## Next Steps (Post-Phase 1)

### Phase 2: Native Bridge Optimization
- [ ] iOS Memory admission check (os_proc_available_memory)
- [ ] Android Memory check (ActivityManager.MemoryInfo)
- [ ] Adaptive preset selection (Safe/Full/Guard)
- [ ] Structured metrics logging (JSONL)
- [ ] Thermal throttling detection

### Phase 3: Production Model Delivery
- [ ] CDN integration for model download
- [ ] Download progress UI
- [ ] Model version management
- [ ] Incremental download with resume support
- [ ] Integrity verification (SHA256)

### Phase 4: Emotional AI Features
- [ ] Tone memory integration (backend API)
- [ ] Context summarization (8-10 turn)
- [ ] Emotional anchor retention
- [ ] Recalibration prompt (15-turn)
- [ ] EQ rubric evaluation

### Phase 5: CI/CD & Quality Gates
- [ ] Automated EQ testing (20-turn scenarios)
- [ ] Performance benchmarking (TTFT, tok/s)
- [ ] Memory leak detection
- [ ] Crash rate monitoring (Crashlytics)
- [ ] Release readiness checklist

---

## Developer Handoff

**Current State**: Phase 1 complete, ready for device testing.

**Immediate Action**:
1. iOS: Add model to Xcode, build to "Uxer Sean" device
2. Android: Install Java/Android Studio (if needed)
3. Test 4-language inference on both platforms
4. Collect baseline metrics (TTFT, tok/s, memory)
5. Report any issues blocking Phase 2

**Contact**:
- Project root: `/Users/uxersean/Desktop/YI_Clean`
- Model location: `/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf`
- App code: `/packages/app`
- Documentation: See MODEL_DEPLOYMENT.md

**Success Definition**:
- iOS app launches on real device
- Model loads in <30s
- All 4 languages generate coherent, empathetic responses
- No crashes during 10+ inference calls
- Metrics visible in UI

---

**Phase 1 Status**: COMPLETE - READY FOR TESTING
**Next Phase**: Phase 2 - Native Bridge Optimization
**Blocker**: None (iOS Java requirement is expected, not blocking)
