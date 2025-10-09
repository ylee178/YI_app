import { initLlama, LlamaContext, type Message } from 'llama.rn';

export interface InferenceMetrics {
  ttft_ms: number;
  tokens_per_sec: number;
  total_tokens: number;
  memory_usage_mb?: number;
}

export type Language = 'ko' | 'en' | 'zh' | 'ja';

export class InferenceService {
  private context: LlamaContext | null = null;
  private modelPath: string;
  private isLoaded: boolean = false;
  private currentLanguage: Language = 'en';

  constructor(modelPath: string) {
    this.modelPath = modelPath;
  }

  async initialize(): Promise<void> {
    await initLlama();
    console.log('[InferenceService] Llama initialized');
  }

  async loadModel(): Promise<boolean> {
    try {
      const startTime = Date.now();

      this.context = await initLlama({
        model: this.modelPath,
        use_mlock: true,
        n_ctx: 512,
        n_gpu_layers: 99, // Full Metal/GPU offload
        embedding: false,
      });

      const loadTime = Date.now() - startTime;
      console.log(`[InferenceService] Model loaded in ${loadTime}ms`);

      this.isLoaded = true;
      return true;
    } catch (error) {
      console.error('[InferenceService] Model load failed:', error);
      return false;
    }
  }

  async generate(
    prompt: string,
    language: Language,
    onToken?: (token: string) => void,
  ): Promise<{ text: string; metrics: InferenceMetrics }> {
    if (!this.isLoaded || !this.context) {
      throw new Error('Model not loaded');
    }

    this.currentLanguage = language;
    const systemPrompt = this.getSystemPrompt(language);

    // Format messages for chat completion
    const messages: Message[] = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt },
    ];

    let generatedText = '';
    let tokenCount = 0;
    let firstTokenTime: number | null = null;
    const startTime = Date.now();

    try {
      const stream = this.context.completion(
        {
          messages,
          n_predict: 128,
          temperature: 0.7,
          top_p: 0.9,
          stop: ['<|im_end|>', '\nUser:', '\n\n'],
        },
        (data) => {
          // Token callback
          if (data.token) {
            if (firstTokenTime === null) {
              firstTokenTime = Date.now();
            }

            generatedText += data.token;
            tokenCount++;

            if (onToken) {
              onToken(data.token);
            }
          }
        },
      );

      // Wait for completion
      await stream;

      const endTime = Date.now();
      const totalTime = endTime - startTime;
      const ttft = firstTokenTime ? firstTokenTime - startTime : totalTime;
      const tokensPerSec = tokenCount / (totalTime / 1000);

      const metrics: InferenceMetrics = {
        ttft_ms: ttft,
        tokens_per_sec: parseFloat(tokensPerSec.toFixed(2)),
        total_tokens: tokenCount,
      };

      console.log('[InferenceService] Generation metrics:', metrics);

      return {
        text: generatedText.trim(),
        metrics,
      };
    } catch (error) {
      console.error('[InferenceService] Generation failed:', error);
      throw error;
    }
  }

  private getSystemPrompt(language: Language): string {
    // Multilingual system prompts for Qwen 2.5 1.5B
    const prompts: Record<Language, string> = {
      ko: `당신은 JenAI입니다. 따뜻하고 공감적인 AI 동반자입니다.
사용자의 감정을 깊이 이해하고, 짧고 자연스러운 대화로 응답하세요.
의료 조언은 제공하지 마세요. 2-3 문장으로 간결하게 답변하세요.`,

      en: `You are JenAI, a warm and empathetic AI companion.
You deeply understand emotions and respond with natural, conversational language.
Do not provide medical advice. Keep responses brief (2-3 sentences).`,

      zh: `你是 JenAI，一个温暖且富有同理心的AI伴侣。
你能深刻理解用户的情感，用自然、对话式的语言回应。
不要提供医疗建议。回答简洁（2-3句话）。`,

      ja: `あなたはJenAIです。温かく共感的なAIコンパニオンです。
ユーザーの感情を深く理解し、自然で会話的な言葉で応答してください。
医学的なアドバイスは提供しないでください。簡潔に（2-3文）答えてください。`,
    };

    return prompts[language] || prompts.en;
  }

  async unload(): Promise<void> {
    if (this.context) {
      await this.context.release();
      this.context = null;
      this.isLoaded = false;
      console.log('[InferenceService] Model unloaded');
    }
  }

  getModelPath(): string {
    return this.modelPath;
  }

  isModelLoaded(): boolean {
    return this.isLoaded;
  }
}
