# Model Deployment Guide - YI App Phase 1

## Overview
This guide explains how to deploy the Qwen 2.5 1.5B Q4_K_M model to iOS and Android devices for on-device inference with llama.rn.

## Model Details
- **File**: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- **Size**: ~950MB
- **Location**: `/Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf`

---

## iOS Deployment

### Option 1: Bundle with App (Recommended for Testing)

1. **Add model to Xcode project**:
   ```bash
   cd /Users/uxersean/Desktop/YI_Clean/packages/app/ios
   mkdir -p models
   cp /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf models/
   ```

2. **Open Xcode and add model**:
   - Open `YIApp.xcworkspace` (NOT .xcodeproj)
   - Right-click on `YIApp` project
   - Select "Add Files to YIApp..."
   - Navigate to `ios/models/` folder
   - Select `qwen2.5-1.5b-instruct-q4_k_m.gguf`
   - Check "Copy items if needed"
   - Add to target "YIApp"

3. **Update model path in App.tsx**:
   ```typescript
   import { Platform } from 'react-native';
   import RNFS from 'react-native-fs'; // If using Documents directory

   // For bundled model:
   const MODEL_PATH = Platform.select({
     ios: `${RNFS.MainBundlePath}/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`,
     android: 'file:///android_asset/models/qwen2.5-1.5b-instruct-q4_k_m.gguf',
   });
   ```

4. **Build for device**:
   - Connect iPhone/iPad via USB
   - Select your device in Xcode
   - Set signing team in "Signing & Capabilities"
   - Build and run (Cmd+R)

**Note**: This increases app size by ~950MB. App Store may reject apps >500MB over cellular.

### Option 2: Documents Directory (Production)

1. **Download model on first launch**:
   ```typescript
   const documentsPath = RNFS.DocumentDirectoryPath;
   const modelPath = `${documentsPath}/qwen2.5-1.5b-instruct-q4_k_m.gguf`;

   // Download from CDN on first launch
   await RNFS.downloadFile({
     fromUrl: 'https://your-cdn.com/models/qwen2.5-1.5b.gguf',
     toFile: modelPath,
   });
   ```

2. **Check if model exists**:
   ```typescript
   const modelExists = await RNFS.exists(modelPath);
   if (!modelExists) {
     // Show download UI
   }
   ```

---

## Android Deployment

### Option 1: Assets Folder (Testing)

1. **Create assets directory**:
   ```bash
   cd /Users/uxersean/Desktop/YI_Clean/packages/app/android/app/src/main
   mkdir -p assets/models
   ```

2. **Copy model** (WARNING: Large file, may cause build issues):
   ```bash
   cp /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf \
      android/app/src/main/assets/models/
   ```

3. **Update model path**:
   ```typescript
   const MODEL_PATH = 'file:///android_asset/models/qwen2.5-1.5b-instruct-q4_k_m.gguf';
   ```

**Note**: Android APK size limit is 100MB (AAB is 150MB base). Use Option 2 for production.

### Option 2: Internal Storage (Recommended)

1. **Copy model to device**:
   ```bash
   # Via ADB
   adb push /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf \
      /data/local/tmp/
   ```

2. **Or download on first launch**:
   ```typescript
   import RNFS from 'react-native-fs';

   const modelPath = `${RNFS.DocumentDirectoryPath}/qwen2.5-1.5b-instruct-q4_k_m.gguf`;

   if (!(await RNFS.exists(modelPath))) {
     await RNFS.downloadFile({
       fromUrl: 'https://your-cdn.com/models/qwen2.5-1.5b.gguf',
       toFile: modelPath,
     });
   }
   ```

3. **Update App.tsx**:
   ```typescript
   const MODEL_PATH = '/data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf';
   ```

---

## Quick Testing Setup

### iOS (Real Device Required - Metal backend)

```bash
# 1. Copy model to iOS project
cd /Users/uxersean/Desktop/YI_Clean/packages/app
mkdir -p ios/models
cp /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf ios/models/

# 2. Open Xcode
open ios/YIApp.xcworkspace

# 3. Add model file to project (see Option 1 above)

# 4. Build and run on device
```

### Android (Emulator or Device)

```bash
# 1. Push model to device/emulator
adb push /Users/uxersean/Desktop/YI_Clean/models/qwen2.5-1.5b/qwen2.5-1.5b-instruct-q4_k_m.gguf \
   /data/local/tmp/

# 2. Verify file exists
adb shell ls -lh /data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf

# 3. Build and run
cd /Users/uxersean/Desktop/YI_Clean/packages/app
npx react-native run-android
```

---

## Verifying Model Path

Update `/packages/app/App.tsx` line 24:

```typescript
// Current (for ADB-pushed Android):
const MODEL_PATH = '/data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf';

// For iOS bundled:
const MODEL_PATH = Platform.select({
  ios: 'models/qwen2.5-1.5b-instruct-q4_k_m.gguf', // Relative to bundle
  android: '/data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf',
});

// For production (Documents directory):
const MODEL_PATH = `${RNFS.DocumentDirectoryPath}/qwen2.5-1.5b-instruct-q4_k_m.gguf`;
```

---

## Troubleshooting

### iOS
- **"Model load failed"**: Check file is added to Xcode target
- **Simulator crashes**: Use real device (Metal required)
- **Slow load**: First load takes 10-30s, normal for ~1GB model

### Android
- **File not found**: Verify ADB push succeeded
- **Permission denied**: Use `/data/local/tmp/` or app's internal storage
- **OOM**: Reduce n_ctx to 256 or use smaller quantization

### Both Platforms
- **TTFT > 1000ms**: GPU layers not enabled, check Metal/GPU offload
- **Low tok/s (<10)**: Thermal throttling or insufficient RAM
- **App crash**: Insufficient memory, close other apps

---

## Performance Expectations

| Device | TTFT | Tokens/sec | Memory Peak |
|--------|------|------------|-------------|
| iPhone 13 Pro | 150-200ms | 25-30 tok/s | ~2.5GB |
| iPhone 12 | 200-300ms | 18-22 tok/s | ~2.8GB |
| Galaxy S21 | 250-400ms | 15-20 tok/s | ~2.6GB |
| Pixel 6 | 300-450ms | 12-18 tok/s | ~2.9GB |

---

## Next Steps (Phase 2)

1. Implement production model download service
2. Add memory admission logic (6GB RAM check)
3. Adaptive quality presets (512/1024 ctx switching)
4. Structured logging (JSONL metrics)
5. Integration with backend tone memory API
