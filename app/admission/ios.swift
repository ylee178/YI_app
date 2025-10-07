/**
 * iOS Admission Logic & Runtime Presets
 * On-device model admission + adaptive quality presets
 */

import Foundation
import os.log

// MARK: - Model Preset Configuration

struct ModelPreset {
    let name: String
    let contextWindow: Int
    let maxNewTokens: Int
    let topP: Double
    let temperature: Double
    let targetDevice: String

    static let full = ModelPreset(
        name: "Full",
        contextWindow: 1024,
        maxNewTokens: 256,
        topP: 0.95,
        temperature: 0.70,
        targetDevice: "8GB+ flagship"
    )

    static let safe = ModelPreset(
        name: "Safe",
        contextWindow: 512,
        maxNewTokens: 128,
        topP: 0.90,
        temperature: 0.65,
        targetDevice: "6GB mid-range"
    )

    static let guard = ModelPreset(
        name: "Guard",
        contextWindow: 384,
        maxNewTokens: 96,
        topP: 0.85,
        temperature: 0.60,
        targetDevice: "Emergency downshift"
    )
}

// MARK: - Device Capabilities

struct DeviceCapabilities {
    let totalRAM: Int64        // in MB
    let availableRAM: Int64    // in MB
    let deviceModel: String
    let thermalState: ProcessInfo.ThermalState

    static func current() -> DeviceCapabilities {
        let totalRAM = ProcessInfo.processInfo.physicalMemory / (1024 * 1024)
        let availableRAM = getAvailableMemory()
        let deviceModel = getDeviceModel()
        let thermalState = ProcessInfo.processInfo.thermalState

        return DeviceCapabilities(
            totalRAM: Int64(totalRAM),
            availableRAM: availableRAM,
            deviceModel: deviceModel,
            thermalState: thermalState
        )
    }

    private static func getAvailableMemory() -> Int64 {
        var vmStats = vm_statistics64()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64>.size / MemoryLayout<integer_t>.size)

        let result = withUnsafeMutablePointer(to: &vmStats) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics64(mach_host_self(), HOST_VM_INFO64, $0, &count)
            }
        }

        guard result == KERN_SUCCESS else { return 0 }

        let free = Int64(vmStats.free_count) * Int64(vm_page_size) / (1024 * 1024)
        let inactive = Int64(vmStats.inactive_count) * Int64(vm_page_size) / (1024 * 1024)

        return free + inactive
    }

    private static func getDeviceModel() -> String {
        var systemInfo = utsname()
        uname(&systemInfo)
        let modelCode = withUnsafePointer(to: &systemInfo.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {
                String(validatingUTF8: $0)
            }
        }
        return modelCode ?? "Unknown"
    }
}

// MARK: - Admission Controller

class ModelAdmissionController {

    private let logger = Logger(subsystem: "com.yi.companion", category: "admission")

    /**
     * Admission formula:
     * allow_load IF free_ram_est_MB >= pte_size_MB * 1.6 + 600
     */
    func canLoadModel(pteSizeMB: Int) -> (canLoad: Bool, reason: String, recommendedPreset: ModelPreset?) {
        let device = DeviceCapabilities.current()

        logger.info("Device: \(device.deviceModel), Total RAM: \(device.totalRAM)MB, Available: \(device.availableRAM)MB")

        // Calculate required memory
        let requiredMemory = Int64(pteSizeMB) * 16 / 10 + 600  // 1.6x + 600MB overhead

        // Check 1: Available memory
        guard device.availableRAM >= requiredMemory else {
            let reason = "Insufficient memory: need \(requiredMemory)MB, have \(device.availableRAM)MB"
            logger.warning("\(reason)")
            return (false, reason, nil)
        }

        // Check 2: Thermal state
        if device.thermalState == .critical || device.thermalState == .serious {
            let reason = "Thermal throttling: state=\(device.thermalState.rawValue)"
            logger.warning("\(reason)")
            return (false, reason, nil)
        }

        // Select preset based on available memory
        let preset = selectPreset(totalRAM: device.totalRAM, availableRAM: device.availableRAM)

        logger.info("✅ Admission approved with preset: \(preset.name)")
        return (true, "Admission approved", preset)
    }

    private func selectPreset(totalRAM: Int64, availableRAM: Int64) -> ModelPreset {
        // 8GB+ device with plenty of free memory -> Full
        if totalRAM >= 8192 && availableRAM >= 4000 {
            return .full
        }

        // 6GB+ device or moderate free memory -> Safe
        if totalRAM >= 6144 && availableRAM >= 2500 {
            return .safe
        }

        // Low memory or older device -> Guard
        return .guard
    }
}

// MARK: - Runtime Monitor

class RuntimeMonitor {

    private let logger = Logger(subsystem: "com.yi.companion", category: "runtime")
    private var currentPreset: ModelPreset
    private var hasDownshifted = false

    // Performance thresholds
    private let ttftThresholdMs: Double = 200.0
    private let memoryPeakThresholdMB: Int64 = 3000

    init(initialPreset: ModelPreset) {
        self.currentPreset = initialPreset
    }

    /**
     * Monitor inference performance and trigger downshift if needed
     */
    func checkPerformance(ttftMs: Double, memoryUsedMB: Int64, thermalState: ProcessInfo.ThermalState) -> ModelPreset? {

        // Trigger 1: TTFT too high
        if ttftMs > ttftThresholdMs {
            logger.warning("TTFT threshold exceeded: \(ttftMs)ms > \(ttftThresholdMs)ms")
            return triggerDownshift()
        }

        // Trigger 2: Memory spike
        if memoryUsedMB > memoryPeakThresholdMB {
            logger.warning("Memory peak exceeded: \(memoryUsedMB)MB > \(memoryPeakThresholdMB)MB")
            return triggerDownshift()
        }

        // Trigger 3: Thermal throttling
        if thermalState == .serious || thermalState == .critical {
            logger.warning("Thermal throttling detected: \(thermalState.rawValue)")
            return triggerDownshift()
        }

        return nil  // No downshift needed
    }

    private func triggerDownshift() -> ModelPreset? {
        guard !hasDownshifted else {
            logger.error("Already downshifted to Guard preset, cannot downshift further")
            return nil
        }

        if currentPreset.name == "Full" {
            currentPreset = .safe
            logger.info("⬇️ Downshifted: Full -> Safe")
            return .safe
        } else if currentPreset.name == "Safe" {
            currentPreset = .guard
            hasDownshifted = true
            logger.info("⬇️ Downshifted: Safe -> Guard")
            return .guard
        }

        return nil
    }
}

// MARK: - Context Manager

class ContextManager {

    private var conversationHistory: [String] = []
    private var anchorCard: String = ""  // Emotional state + tone prefs
    private let maxTokensBeforeSummarization = 400

    func addTurn(userMessage: String, assistantMessage: String) {
        conversationHistory.append("User: \(userMessage)")
        conversationHistory.append("Assistant: \(assistantMessage)")

        // Check if summarization needed (every 8-10 turns)
        if conversationHistory.count >= 16 {  // ~8 turns
            summarizeHistory()
        }
    }

    private func summarizeHistory() {
        // Generate 2-3 sentence summary of conversation
        // TODO: Replace with actual summarization model call
        let summary = "[Summary of last 8-10 turns: emotional themes, key concerns]"

        // Keep anchor card (100-200 tokens) + summary
        conversationHistory = [summary]

        print("📝 Summarized conversation history")
    }

    func updateAnchorCard(emotion: String, intensity: String, topic: String) {
        anchorCard = """
        Last state: \(emotion) (\(intensity))
        Topic: \(topic)
        """
    }

    func getContext() -> String {
        return anchorCard + "\n\n" + conversationHistory.joined(separator: "\n")
    }
}

// MARK: - Usage Example

func example() {
    let admission = ModelAdmissionController()

    // Check if model can be loaded
    let pteSizeMB = 1200  // ~1.2GB model
    let result = admission.canLoadModel(pteSizeMB: pteSizeMB)

    if result.canLoad, let preset = result.recommendedPreset {
        print("✅ Model admission approved")
        print("Preset: \(preset.name)")
        print("Context: \(preset.contextWindow), MaxNew: \(preset.maxNewTokens)")

        // Initialize runtime monitor
        let monitor = RuntimeMonitor(initialPreset: preset)

        // Simulate inference metrics
        let ttft: Double = 180.0  // ms
        let memUsed: Int64 = 2500  // MB
        let thermal = ProcessInfo.processInfo.thermalState

        if let newPreset = monitor.checkPerformance(
            ttftMs: ttft,
            memoryUsedMB: memUsed,
            thermalState: thermal
        ) {
            print("⚠️ Performance degraded, switched to: \(newPreset.name)")
        }

    } else {
        print("❌ Model admission denied: \(result.reason)")
    }
}
