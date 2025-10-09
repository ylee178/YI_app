/**
 * YI App - Phase 1 Test Interface
 * llama.rn integration with Qwen 2.5 1.5B Q4_K_M
 */

import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
  useColorScheme,
} from 'react-native';
import { InferenceService, type Language } from './src/services/InferenceService';

// IMPORTANT: Update this path to point to your model file
// For iOS: Copy model to app bundle or use Documents directory
// For Android: Copy to assets or use internal storage
const MODEL_PATH = '/data/local/tmp/qwen2.5-1.5b-instruct-q4_k_m.gguf';

function App(): React.JSX.Element {
  const isDarkMode = useColorScheme() === 'dark';
  const [service] = useState(() => new InferenceService(MODEL_PATH));
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [streamingText, setStreamingText] = useState('');
  const [language, setLanguage] = useState<Language>('en');
  const [metrics, setMetrics] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function init() {
      try {
        setError('Initializing llama.rn...');
        await service.initialize();

        setError('Loading model (this may take 10-30 seconds)...');
        const loaded = await service.loadModel();

        if (loaded) {
          setError('');
          setIsLoading(false);
        } else {
          setError('Failed to load model. Check model path and permissions.');
        }
      } catch (err) {
        setError(`Initialization error: ${err}`);
        setIsLoading(false);
      }
    }
    init();

    return () => {
      service.unload();
    };
  }, [service]);

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return;

    setIsGenerating(true);
    setResponse('');
    setStreamingText('');
    setMetrics('');
    setError('');

    try {
      const result = await service.generate(
        prompt,
        language,
        (token) => {
          // Streaming callback
          setStreamingText(prev => prev + token);
        },
      );

      setResponse(result.text);
      setMetrics(
        `TTFT: ${result.metrics.ttft_ms}ms | ` +
        `Speed: ${result.metrics.tokens_per_sec.toFixed(1)} tok/s | ` +
        `Tokens: ${result.metrics.total_tokens}`
      );
    } catch (err) {
      setError(`Generation error: ${err}`);
    } finally {
      setIsGenerating(false);
      setStreamingText('');
    }
  };

  const testPrompts = {
    ko: '오늘 기분이 좀 우울해요',
    en: 'I feel a bit down today',
    zh: '我今天心情有点低落',
    ja: '今日は少し気分が落ち込んでいます',
  };

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, styles.centerContent]}>
        <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>
          {error || 'Loading model...'}
        </Text>
        <Text style={styles.pathText}>{service.getModelPath()}</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />

      <View style={styles.header}>
        <Text style={styles.title}>YI - Phase 1 Test</Text>
        <Text style={styles.subtitle}>llama.rn + Qwen 2.5 1.5B</Text>
      </View>

      <View style={styles.languageBar}>
        {(['ko', 'en', 'zh', 'ja'] as Language[]).map((lang) => (
          <TouchableOpacity
            key={lang}
            style={[
              styles.langButton,
              language === lang && styles.langButtonActive,
            ]}
            onPress={() => {
              setLanguage(lang);
              setPrompt(testPrompts[lang]);
            }}
          >
            <Text
              style={[
                styles.langText,
                language === lang && styles.langTextActive,
              ]}
            >
              {lang.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder={`Enter prompt (${language})...`}
          placeholderTextColor="#999"
          value={prompt}
          onChangeText={setPrompt}
          multiline
          editable={!isGenerating}
        />
        <TouchableOpacity
          style={[styles.button, isGenerating && styles.buttonDisabled]}
          onPress={handleGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.buttonText}>Generate</Text>
          )}
        </TouchableOpacity>
      </View>

      {metrics && (
        <View style={styles.metricsBar}>
          <Text style={styles.metricsText}>{metrics}</Text>
        </View>
      )}

      <ScrollView style={styles.responseContainer}>
        {error ? (
          <Text style={styles.errorText}>{error}</Text>
        ) : (
          <>
            {streamingText && (
              <View style={styles.streamingBox}>
                <Text style={styles.streamingLabel}>Streaming:</Text>
                <Text style={styles.responseText}>{streamingText}</Text>
              </View>
            )}
            {response && !streamingText && (
              <View style={styles.responseBox}>
                <Text style={styles.responseLabel}>Response ({language}):</Text>
                <Text style={styles.responseText}>{response}</Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#E0E0E0',
    marginTop: 4,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#333',
  },
  pathText: {
    marginTop: 8,
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  languageBar: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#FFF',
    justifyContent: 'space-around',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  langButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F0F0F0',
  },
  langButtonActive: {
    backgroundColor: '#007AFF',
  },
  langText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  langTextActive: {
    color: '#FFF',
  },
  inputContainer: {
    padding: 16,
    backgroundColor: '#FFF',
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 80,
    marginBottom: 12,
    backgroundColor: '#FAFAFA',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#999',
  },
  buttonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  metricsBar: {
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#C8E6C9',
  },
  metricsText: {
    fontSize: 12,
    color: '#2E7D32',
    fontFamily: 'Courier',
  },
  responseContainer: {
    flex: 1,
    padding: 16,
  },
  streamingBox: {
    backgroundColor: '#FFF9C4',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFF176',
  },
  responseBox: {
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  streamingLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F57F17',
    marginBottom: 8,
  },
  responseLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 8,
  },
  responseText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  errorText: {
    fontSize: 14,
    color: '#D32F2F',
    backgroundColor: '#FFEBEE',
    padding: 16,
    borderRadius: 8,
  },
});

export default App;
