# YI App - On-Device Emotional AI Companion

**Phase 1 Status**: COMPLETE - Ready for Device Testing

## Quick Start

### iOS (Real Device Required - Metal Backend)

```bash
# 1. Add model to Xcode project
mkdir -p ios/models
cp ../../models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf ios/models/

# 2. Open workspace
open ios/YIApp.xcworkspace

# 3. In Xcode: Add ios/models/*.gguf to project target

# 4. Update App.tsx line 24:
#    const MODEL_PATH = 'models/qwen2.5-1.5b-instruct-q4_k_m.gguf';

# 5. Build to device (Cmd+R)
```

### Android (Requires Java/Android Studio)

```bash
# 1. Push model via ADB
adb push ../../models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf /data/local/tmp/

# 2. Build and run
npx react-native run-android
```

## Features

- 4-language support: Korean, English, Chinese, Japanese
- Streaming inference with real-time token display
- Performance metrics (TTFT, tokens/sec, token count)
- Qwen 2.5 1.5B Q4_K_M model (~950MB)
- llama.rn v0.7.0-rc.2 (Metal/GPU optimized)

## Project Structure

```
.
├── App.tsx                          # Test UI with 4-language selector
├── src/
│   └── services/
│       └── InferenceService.ts      # llama.rn wrapper
├── ios/
│   ├── YIApp.xcworkspace            # iOS workspace
│   └── models/                      # (Add model here)
├── android/
│   └── app/src/main/assets/         # (Optional: bundled model)
├── MODEL_DEPLOYMENT.md              # Deployment guide
├── PHASE1_SETUP_CHECKLIST.md        # Testing protocol
└── README.md                        # This file
```

## Documentation

- **MODEL_DEPLOYMENT.md**: iOS/Android deployment strategies
- **PHASE1_SETUP_CHECKLIST.md**: Prerequisites, testing, troubleshooting
- **/YI_Clean/PHASE1_COMPLETE.md**: Full Phase 1 summary

## Key Files

| File | Lines | Purpose |
|------|-------|---------|
| App.tsx | ~350 | Test interface with streaming UI |
| InferenceService.ts | ~170 | Service layer with 4-language prompts |
| package.json | - | llama.rn@0.7.0-rc.2 dependency |

## Performance Targets

| Device | TTFT | Tokens/sec | Memory |
|--------|------|------------|--------|
| iPhone 13 Pro | 150-200ms | 25-30 tok/s | ~2.5GB |
| iPhone 12 | 200-300ms | 18-22 tok/s | ~2.8GB |
| Galaxy S21 | 250-400ms | 15-20 tok/s | ~2.6GB |

## Testing Protocol

1. Select language (KO/EN/ZH/JA)
2. Tap Generate
3. Watch streaming response
4. Verify metrics display
5. Repeat for all 4 languages

**Test Prompts**:
- KO: "오늘 기분이 좀 우울해요"
- EN: "I feel a bit down today"
- ZH: "我今天心情有点低落"
- JA: "今日は少し気分が落ち込んでいます"

## Known Limitations (Phase 1)

- Model path hardcoded (line 24 in App.tsx)
- No download UI (manual deployment required)
- No memory admission (will attempt load on any device)
- No adaptive presets (fixed 512 ctx)
- iOS Simulator unsupported (Metal required)

**Resolution**: Phase 2-5 roadmap

## Troubleshooting

| Issue | Solution |
|-------|----------|
| iOS: Model load failed | Verify file added to Xcode target |
| iOS: Simulator crash | Use real device (Metal required) |
| Android: File not found | Check ADB push succeeded |
| Slow TTFT (>1s) | Normal on first load |

## Next Steps

**Phase 2**: Native bridge optimization
- Memory admission logic
- Adaptive presets (Safe/Full/Guard)
- Structured logging (JSONL)
- Thermal throttling detection

**Phase 3**: Production model delivery
- CDN download UI
- Integrity verification
- Version management

**Phase 4**: Emotional AI features
- Tone memory integration
- Context summarization
- EQ rubric evaluation

## Requirements

- Node.js 22.x
- React Native 0.82.0
- iOS: Xcode 15+, real device
- Android: Java 17+, Android Studio

## License

Proprietary - YI Project
