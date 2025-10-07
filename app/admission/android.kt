/**
 * Android Admission Logic & Runtime Presets
 * On-device model admission + adaptive quality presets
 */

package com.yi.companion.admission

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.util.Log
import kotlin.math.roundToInt

// MARK: - Model Preset Configuration

data class ModelPreset(
    val name: String,
    val contextWindow: Int,
    val maxNewTokens: Int,
    val topP: Double,
    val temperature: Double,
    val targetDevice: String
) {
    companion object {
        val FULL = ModelPreset(
            name = "Full",
            contextWindow = 1024,
            maxNewTokens = 256,
            topP = 0.95,
            temperature = 0.70,
            targetDevice = "8GB+ flagship"
        )

        val SAFE = ModelPreset(
            name = "Safe",
            contextWindow = 512,
            maxNewTokens = 128,
            topP = 0.90,
            temperature = 0.65,
            targetDevice = "6GB mid-range"
        )

        val GUARD = ModelPreset(
            name = "Guard",
            contextWindow = 384,
            maxNewTokens = 96,
            topP = 0.85,
            temperature = 0.60,
            targetDevice = "Emergency downshift"
        )
    }
}

// MARK: - Device Capabilities

data class DeviceCapabilities(
    val totalRAM: Long,         // in MB
    val availableRAM: Long,     // in MB
    val deviceModel: String,
    val sdkVersion: Int
)

object DeviceInfo {

    private const val TAG = "DeviceInfo"

    fun getCurrent(context: Context): DeviceCapabilities {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)

        val totalRAM = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN) {
            memoryInfo.totalMem / (1024 * 1024)
        } else {
            // Fallback for older devices
            4096L  // Assume 4GB
        }

        val availableRAM = memoryInfo.availMem / (1024 * 1024)
        val deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}"
        val sdkVersion = Build.VERSION.SDK_INT

        Log.d(TAG, "Device: $deviceModel, Total RAM: ${totalRAM}MB, Available: ${availableRAM}MB")

        return DeviceCapabilities(totalRAM, availableRAM, deviceModel, sdkVersion)
    }
}

// MARK: - Admission Controller

class ModelAdmissionController(private val context: Context) {

    private val TAG = "AdmissionController"

    data class AdmissionResult(
        val canLoad: Boolean,
        val reason: String,
        val recommendedPreset: ModelPreset?
    )

    /**
     * Admission formula:
     * allow_load IF free_ram_est_MB >= pte_size_MB * 1.6 + 600
     */
    fun canLoadModel(pteSizeMB: Int): AdmissionResult {
        val device = DeviceInfo.getCurrent(context)

        // Calculate required memory
        val requiredMemory = (pteSizeMB * 1.6).roundToInt() + 600

        // Check 1: Available memory
        if (device.availableRAM < requiredMemory) {
            val reason = "Insufficient memory: need ${requiredMemory}MB, have ${device.availableRAM}MB"
            Log.w(TAG, reason)
            return AdmissionResult(false, reason, null)
        }

        // Check 2: Minimum Android version (API 26+)
        if (device.sdkVersion < Build.VERSION_CODES.O) {
            val reason = "Unsupported Android version: SDK ${device.sdkVersion} < 26"
            Log.w(TAG, reason)
            return AdmissionResult(false, reason, null)
        }

        // Check 3: Low memory state
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)

        if (memoryInfo.lowMemory) {
            val reason = "Device in low memory state"
            Log.w(TAG, reason)
            return AdmissionResult(false, reason, null)
        }

        // Select preset based on available memory
        val preset = selectPreset(device.totalRAM, device.availableRAM)

        Log.i(TAG, "✅ Admission approved with preset: ${preset.name}")
        return AdmissionResult(true, "Admission approved", preset)
    }

    private fun selectPreset(totalRAM: Long, availableRAM: Long): ModelPreset {
        return when {
            // 8GB+ device with plenty of free memory -> Full
            totalRAM >= 8192 && availableRAM >= 4000 -> ModelPreset.FULL

            // 6GB+ device or moderate free memory -> Safe
            totalRAM >= 6144 && availableRAM >= 2500 -> ModelPreset.SAFE

            // Low memory or older device -> Guard
            else -> ModelPreset.GUARD
        }
    }
}

// MARK: - Runtime Monitor

class RuntimeMonitor(private var currentPreset: ModelPreset) {

    private val TAG = "RuntimeMonitor"
    private var hasDownshifted = false

    // Performance thresholds
    private val ttftThresholdMs = 200.0
    private val memoryPeakThresholdMB = 3000L

    /**
     * Monitor inference performance and trigger downshift if needed
     */
    fun checkPerformance(
        ttftMs: Double,
        memoryUsedMB: Long,
        isThrottled: Boolean = false
    ): ModelPreset? {

        // Trigger 1: TTFT too high
        if (ttftMs > ttftThresholdMs) {
            Log.w(TAG, "TTFT threshold exceeded: ${ttftMs}ms > ${ttftThresholdMs}ms")
            return triggerDownshift()
        }

        // Trigger 2: Memory spike
        if (memoryUsedMB > memoryPeakThresholdMB) {
            Log.w(TAG, "Memory peak exceeded: ${memoryUsedMB}MB > ${memoryPeakThresholdMB}MB")
            return triggerDownshift()
        }

        // Trigger 3: Thermal throttling (if available)
        if (isThrottled) {
            Log.w(TAG, "Thermal throttling detected")
            return triggerDownshift()
        }

        return null  // No downshift needed
    }

    private fun triggerDownshift(): ModelPreset? {
        if (hasDownshifted) {
            Log.e(TAG, "Already downshifted to Guard preset, cannot downshift further")
            return null
        }

        return when (currentPreset.name) {
            "Full" -> {
                currentPreset = ModelPreset.SAFE
                Log.i(TAG, "⬇️ Downshifted: Full -> Safe")
                ModelPreset.SAFE
            }
            "Safe" -> {
                currentPreset = ModelPreset.GUARD
                hasDownshifted = true
                Log.i(TAG, "⬇️ Downshifted: Safe -> Guard")
                ModelPreset.GUARD
            }
            else -> null
        }
    }

    fun getCurrentPreset() = currentPreset
}

// MARK: - Context Manager

class ContextManager {

    private val conversationHistory = mutableListOf<String>()
    private var anchorCard: String = ""  // Emotional state + tone prefs
    private val maxTurnsBeforeSummarization = 8

    fun addTurn(userMessage: String, assistantMessage: String) {
        conversationHistory.add("User: $userMessage")
        conversationHistory.add("Assistant: $assistantMessage")

        // Check if summarization needed (every 8-10 turns)
        val turnCount = conversationHistory.size / 2
        if (turnCount >= maxTurnsBeforeSummarization) {
            summarizeHistory()
        }
    }

    private fun summarizeHistory() {
        // Generate 2-3 sentence summary of conversation
        // TODO: Replace with actual summarization model call
        val summary = "[Summary of last 8-10 turns: emotional themes, key concerns]"

        // Keep anchor card (100-200 tokens) + summary
        conversationHistory.clear()
        conversationHistory.add(summary)

        Log.d("ContextManager", "📝 Summarized conversation history")
    }

    fun updateAnchorCard(emotion: String, intensity: String, topic: String) {
        anchorCard = """
            Last state: $emotion ($intensity)
            Topic: $topic
        """.trimIndent()
    }

    fun getContext(): String {
        return "$anchorCard\n\n${conversationHistory.joinToString("\n")}"
    }

    fun getTurnCount() = conversationHistory.size / 2
}

// MARK: - Usage Example

fun exampleUsage(context: Context) {
    val admission = ModelAdmissionController(context)

    // Check if model can be loaded
    val pteSizeMB = 1200  // ~1.2GB model
    val result = admission.canLoadModel(pteSizeMB)

    if (result.canLoad && result.recommendedPreset != null) {
        val preset = result.recommendedPreset
        println("✅ Model admission approved")
        println("Preset: ${preset.name}")
        println("Context: ${preset.contextWindow}, MaxNew: ${preset.maxNewTokens}")

        // Initialize runtime monitor
        val monitor = RuntimeMonitor(preset)

        // Simulate inference metrics
        val ttft = 180.0  // ms
        val memUsed = 2500L  // MB
        val isThrottled = false

        val newPreset = monitor.checkPerformance(
            ttftMs = ttft,
            memoryUsedMB = memUsed,
            isThrottled = isThrottled
        )

        if (newPreset != null) {
            println("⚠️ Performance degraded, switched to: ${newPreset.name}")
        }

    } else {
        println("❌ Model admission denied: ${result.reason}")
    }
}
