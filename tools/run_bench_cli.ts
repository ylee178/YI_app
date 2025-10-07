#!/usr/bin/env ts-node
/**
 * Benchmark CLI for 10-turn EQ + Performance Testing
 * Measures: TTFT, tok/s, memory peak, EQ rubric score
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

interface Preset {
  name: string;
  context: number;
  maxNew: number;
  topP: number;
  temperature: number;
}

const PRESETS: Record<string, Preset> = {
  Full: { name: 'Full', context: 1024, maxNew: 256, topP: 0.95, temperature: 0.70 },
  Safe: { name: 'Safe', context: 512, maxNew: 128, topP: 0.90, temperature: 0.65 },
  Guard: { name: 'Guard', context: 384, maxNew: 96, topP: 0.85, temperature: 0.60 },
};

interface BenchmarkResult {
  model: string;
  preset: string;
  metrics: {
    ttft_ms: number;
    decode_toks_per_s: number;
    mem_peak_mb: number;
    eq_score_10turn?: number;
  };
  turns: TurnResult[];
  timestamp: string;
}

interface TurnResult {
  turn: number;
  user_input: string;
  assistant_output: string;
  ttft_ms: number;
  decode_toks: number;
  decode_time_ms: number;
  toks_per_s: number;
}

interface Scenario {
  name: string;
  emotion: string;
  prompts: string[];
}

/**
 * Mock inference function - replace with actual ExecuTorch runtime call
 */
async function runInference(
  ptePath: string,
  prompt: string,
  preset: Preset
): Promise<{ output: string; ttft_ms: number; decode_ms: number; tokens: number }> {
  // TODO: Replace with actual ExecuTorch inference
  // This is a placeholder for demonstration

  const ttft = Math.random() * 150 + 50; // 50-200ms
  const tokens = Math.floor(Math.random() * 50 + 30); // 30-80 tokens
  const decode_ms = tokens * (8 + Math.random() * 4); // ~8-12ms per token

  // Simulate processing
  await new Promise((resolve) => setTimeout(resolve, ttft + decode_ms));

  return {
    output: `[Mock response to: "${prompt.slice(0, 30)}..."] I hear you're feeling ${Math.random() > 0.5 ? 'anxious' : 'sad'}. That sounds really difficult.`,
    ttft_ms: ttft,
    decode_ms: decode_ms,
    tokens: tokens,
  };
}

/**
 * Load test scenarios from file
 */
function loadScenarios(scenarioPath: string): Scenario[] {
  if (!existsSync(scenarioPath)) {
    console.error(`❌ Scenario file not found: ${scenarioPath}`);
    process.exit(1);
  }

  // Simple parser - expects markdown format from scenarios_10turn.md
  const content = readFileSync(scenarioPath, 'utf-8');
  const scenarios: Scenario[] = [];

  const sections = content.split('##').slice(1); // Skip header

  for (const section of sections) {
    const lines = section.trim().split('\n');
    const titleLine = lines[0];
    const match = titleLine.match(/(.+?)\s*\((.+?)\)/);

    if (match) {
      const name = match[1].trim();
      const emotion = match[2].trim();
      const prompts = lines
        .slice(1)
        .filter((l) => l.trim().startsWith('-'))
        .map((l) => l.replace(/^-\s*/, '').trim());

      scenarios.push({ name, emotion, prompts: prompts.slice(0, 10) });
    }
  }

  return scenarios;
}

/**
 * Calculate simple EQ score based on rubric
 */
function calculateEQScore(turns: TurnResult[]): number {
  // Simplified rubric scoring - replace with actual human evaluation or LLM-as-judge
  let totalScore = 0;
  const maxScorePerTurn = 10;

  for (const turn of turns) {
    let turnScore = 0;

    const output = turn.assistant_output.toLowerCase();

    // Empathy signals (3 pts)
    if (output.includes('hear you') || output.includes('understand') || output.includes('feel')) {
      turnScore += 3;
    }

    // Appropriate length (2 pts) - not too short, not too long
    const wordCount = output.split(' ').length;
    if (wordCount >= 20 && wordCount <= 80) {
      turnScore += 2;
    }

    // No platitudes (2 pts)
    if (!output.includes("you'll be fine") && !output.includes('stay positive')) {
      turnScore += 2;
    }

    // Validation presence (3 pts)
    if (output.includes('valid') || output.includes('makes sense') || output.includes('natural')) {
      turnScore += 3;
    }

    totalScore += Math.min(turnScore, maxScorePerTurn);
  }

  const avgScore = (totalScore / (turns.length * maxScorePerTurn)) * 100;
  return Math.round(avgScore);
}

/**
 * Run benchmark
 */
async function runBenchmark(
  ptePath: string,
  presetName: string,
  scenarioPath: string
): Promise<BenchmarkResult> {
  console.log('='.repeat(60));
  console.log('BENCHMARK START');
  console.log('='.repeat(60));
  console.log(`Model:    ${ptePath}`);
  console.log(`Preset:   ${presetName}`);
  console.log(`Scenarios: ${scenarioPath}\n`);

  const preset = PRESETS[presetName];
  if (!preset) {
    console.error(`❌ Invalid preset: ${presetName}`);
    console.error(`   Available: ${Object.keys(PRESETS).join(', ')}`);
    process.exit(1);
  }

  const scenarios = loadScenarios(scenarioPath);
  if (scenarios.length === 0) {
    console.error('❌ No scenarios loaded');
    process.exit(1);
  }

  const turns: TurnResult[] = [];
  const ttfts: number[] = [];
  const toksPerSec: number[] = [];

  // Run first scenario (10 turns)
  const scenario = scenarios[0];
  console.log(`Running scenario: ${scenario.name} (${scenario.emotion})\n`);

  for (let i = 0; i < Math.min(10, scenario.prompts.length); i++) {
    const userInput = scenario.prompts[i];
    process.stdout.write(`Turn ${i + 1}/10: `);

    const result = await runInference(ptePath, userInput, preset);

    const toksPerS = (result.tokens / result.decode_ms) * 1000;
    ttfts.push(result.ttft_ms);
    toksPerSec.push(toksPerS);

    turns.push({
      turn: i + 1,
      user_input: userInput,
      assistant_output: result.output,
      ttft_ms: result.ttft_ms,
      decode_toks: result.tokens,
      decode_time_ms: result.decode_ms,
      toks_per_s: toksPerS,
    });

    console.log(`✓ TTFT=${result.ttft_ms.toFixed(0)}ms, ${toksPerS.toFixed(1)} tok/s`);
  }

  // Calculate metrics
  const avgTTFT = ttfts.reduce((a, b) => a + b, 0) / ttfts.length;
  const avgToksPerS = toksPerSec.reduce((a, b) => a + b, 0) / toksPerSec.length;
  const eqScore = calculateEQScore(turns);

  // Mock memory peak (replace with actual measurement)
  const memPeakMB = Math.random() * 500 + 2000; // 2000-2500 MB

  const benchResult: BenchmarkResult = {
    model: ptePath,
    preset: presetName,
    metrics: {
      ttft_ms: Math.round(avgTTFT),
      decode_toks_per_s: Math.round(avgToksPerS * 10) / 10,
      mem_peak_mb: Math.round(memPeakMB),
      eq_score_10turn: eqScore,
    },
    turns: turns,
    timestamp: new Date().toISOString(),
  };

  console.log('\n' + '='.repeat(60));
  console.log('RESULTS');
  console.log('='.repeat(60));
  console.log(`TTFT (avg):       ${benchResult.metrics.ttft_ms} ms`);
  console.log(`Decode speed:     ${benchResult.metrics.decode_toks_per_s} tok/s`);
  console.log(`Memory peak:      ${benchResult.metrics.mem_peak_mb} MB`);
  console.log(`EQ Score (10-turn): ${benchResult.metrics.eq_score_10turn}/100`);
  console.log('='.repeat(60));

  return benchResult;
}

/**
 * Main CLI
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.log('Usage: ts-node run_bench_cli.ts <pte_path> <preset> <scenario_path>');
    console.log('');
    console.log('Presets: Full, Safe, Guard');
    console.log('');
    console.log('Example:');
    console.log('  ts-node run_bench_cli.ts \\');
    console.log('    models/llama3.2-1b/llama3.2-1b-int8-seq512.pte \\');
    console.log('    Safe \\');
    console.log('    prompts/scenarios_10turn.md');
    process.exit(1);
  }

  const [ptePath, presetName, scenarioPath] = args;

  if (!existsSync(ptePath)) {
    console.error(`❌ PTE file not found: ${ptePath}`);
    process.exit(1);
  }

  const result = await runBenchmark(ptePath, presetName, scenarioPath);

  // Save results
  const outputPath = `results/${presetName.toLowerCase()}_${Date.now()}.json`;
  writeFileSync(outputPath, JSON.stringify(result, null, 2));

  console.log(`\n✅ Results saved to: ${outputPath}`);
}

main().catch((err) => {
  console.error('❌ Benchmark failed:', err);
  process.exit(1);
});
