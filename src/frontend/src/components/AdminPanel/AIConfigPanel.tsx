"use client";

import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  DollarSign, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Save,
  TestTube,
  FileText,
  BarChart3,
  Clock,
  Zap,
  Edit,
  Key,
  Brain,
  MessageSquare,
  Calculator
} from 'lucide-react';

// Interfaces
interface AIModel {
  model_name: string;
  input_price: number;
  output_price: number;
  notes?: string;
}

interface AIProvider {
  name: string;
  display_name: string;
  models: AIModel[];
}

interface AIModelConfig {
  model_name: string;
  provider: string;
  temperature: number;
  max_tokens: number;
  min_tokens: number;
  token_decrement: number;
  max_retries: number;
  timeout_seconds: number;
  max_text_length: number;
  max_tables_summary: number;
  custom_input_price?: number;
  custom_output_price?: number;
}

interface PromptTemplates {
  extraction_prompt: string;
  table_summary_template: string;
  no_tables_message: string;
  error_fallback_template: string;
}

interface UsageStats {
    total_requests: number;
    total_cost: number;
    total_input_tokens: number;
    total_output_tokens: number;
    average_processing_time: number;
    daily_cost: number;
    daily_requests: number;
    last_updated: string;
}

interface CostEstimate {
  input_cost: number;
  output_cost: number;
  total_cost: number;
  per_request_estimate: number;
}

const AIConfigPanel: React.FC = () => {
  // State management
  const [config, setConfig] = useState<AIModelConfig | null>(null);
  const [prompts, setPrompts] = useState<PromptTemplates | null>(null);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate>({
    input_cost: 0,
    output_cost: 0,
    total_cost: 0,
    per_request_estimate: 0
  });
  const [keyStatuses, setKeyStatuses] = useState<Record<string, 'set' | 'not_set' | 'valid' | 'invalid'>>({});
  const [validatingProvider, setValidatingProvider] = useState<string | null>(null);

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activePromptEditor, setActivePromptEditor] = useState<keyof PromptTemplates | null>(null);
  const [testResults, setTestResults] = useState<any>(null);
  const [isCustomModel, setIsCustomModel] = useState(false);

  // Load data on component mount
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          loadProviders(),
          loadCurrentConfig(),
          loadUsageStats(),
          loadKeyStatuses()
        ]);
      } catch (err: any) {
        setError(err.message || 'Failed to load initial data.');
        console.error('Initial data loading error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  // Real-time cost calculation
  useEffect(() => {
    if (providers.length > 0 && config) {
      calculateCostEstimate();
    }
  }, [config, providers]);

  const loadProviders = async () => {
    const response = await fetch('/api/admin/ai-config/providers');
    if (!response.ok) {
      throw new Error(`Failed to load AI providers: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    if (data && data.providers) {
      setProviders(data.providers);
    }
  };

  const loadCurrentConfig = async () => {
    const response = await fetch('/api/admin/ai-config/status');
    if (!response.ok) {
      throw new Error(`Failed to load current config: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    if (data && data.model) {
      setConfig(data.model);
    }
    if (data && data.prompt_templates) {
      setPrompts(data.prompt_templates);
    }
  };

  const loadUsageStats = async () => {
    const response = await fetch('/api/admin/ai-config/usage/stats');
    if (!response.ok) {
      throw new Error(`Failed to load usage stats: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    if (data) {
      setStats({
        total_requests: data.total_requests || 0,
        total_cost: data.total_cost_usd || 0,
        total_input_tokens: data.total_tokens || 0,
        total_output_tokens: 0,
        average_processing_time: data.average_tokens_per_request || 0,
        daily_cost: data.cost_today_usd || 0,
        daily_requests: data.requests_today || 0,
        last_updated: new Date().toISOString()
      });
    }
  };

  const loadKeyStatuses = async () => {
    try {
      const response = await fetch('/api/admin/ai-config/key-status');
      if (response.ok) {
        const statuses = await response.json();
        setKeyStatuses(statuses);
      }
    } catch (err) {
      console.error('Failed to load key statuses:', err);
    }
  };

  const calculateCostEstimate = () => {
    if (!providers.length || !config) return;

    let pricing = null;

    for (const provider of providers) {
      const model = provider.models.find(m => m.model_name === config.model_name);
      if (model) {
        pricing = {
          input_tokens_per_million: model.input_price,
          output_tokens_per_million: model.output_price
        };
        break;
      }
    }

    if (!pricing && isCustomModel && config.custom_input_price && config.custom_output_price) {
      pricing = {
        input_tokens_per_million: config.custom_input_price,
        output_tokens_per_million: config.custom_output_price
      };
    }

    if (pricing) {
      const typicalInput = 8000;
      const typicalOutput = 2000;

      const inputCost = (typicalInput / 1_000_000) * pricing.input_tokens_per_million;
      const outputCost = (typicalOutput / 1_000_000) * pricing.output_tokens_per_million;
      const totalCost = inputCost + outputCost;

      setCostEstimate({
        input_cost: inputCost,
        output_cost: outputCost,
        total_cost: totalCost,
        per_request_estimate: totalCost
      });
    }
  };


  const handleSaveConfig = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/admin/ai-config/model-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update configuration');
      }

      setSuccess('Configuration updated successfully!');
      await loadUsageStats();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrompt = async (templateName: keyof PromptTemplates) => {
    if (!prompts) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/admin/ai-config/prompt-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_name: templateName,
          template_content: prompts[templateName]
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update prompts');
      }

      setSuccess(`Prompt '${templateName}' updated successfully!`);
      setActivePromptEditor(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConfiguration = async () => {
    setLoading(true);
    setError(null);
    setTestResults(null);

    try {
      const response = await fetch('/api/admin/ai-config/test-configuration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Test failed');
      }

      const results = await response.json();
      setTestResults(results);
      setSuccess('Configuration test completed!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateKey = async (provider: string) => {
    setValidatingProvider(provider);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`/api/admin/ai-config/validate-key/${provider}`, { method: 'POST' });
      const result = await response.json();
      if (response.ok && result.success) {
        setKeyStatuses(prev => ({ ...prev, [provider]: 'valid' }));
        setSuccess(result.message);
      } else {
        setKeyStatuses(prev => ({ ...prev, [provider]: 'invalid' }));
        throw new Error(result.detail || 'Validation failed.');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setValidatingProvider(null);
    }
  };

  const PromptEditorModal: React.FC = () => {
    if (!activePromptEditor || !prompts) return null;

    const handleSave = () => {
        handleSavePrompt(activePromptEditor);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl">
          <div className="p-6 border-b">
            <h3 className="text-lg font-medium text-gray-900">Edit: {activePromptEditor}</h3>
          </div>
          <div className="p-6">
            <textarea
              aria-label={`Edit ${activePromptEditor}`}
              value={prompts[activePromptEditor]}
              onChange={(e) => setPrompts({ ...prompts, [activePromptEditor]: e.target.value })}
              className="w-full h-96 p-3 border border-neutral-300 rounded-lg font-mono text-sm resize-y focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="p-4 bg-gray-50 flex justify-end space-x-3">
            <button onClick={() => setActivePromptEditor(null)} className="px-4 py-2 text-sm text-gray-700 bg-white border rounded-md hover:bg-gray-100">
              Cancel
            </button>
            <button onClick={handleSave} disabled={loading} className="px-4 py-2 text-sm text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50">
              {loading ? 'Saving...' : 'Save Template'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderAPIKeyGuidance = () => {
    if (!config) return null;
    const provider = config.provider.toLowerCase();
    let envVar = '';

    if (provider.includes('anthropic') || provider.includes('claude')) envVar = 'ANTHROPIC_API_KEY';
    else if (provider.includes('openai') || provider.includes('gpt')) envVar = 'OPENAI_API_KEY';
    else if (provider.includes('google') || provider.includes('gemini')) envVar = 'GOOGLE_API_KEY';

    if (!envVar) return null;

    const providerStatus = keyStatuses[provider];
    const isProviderValidating = validatingProvider === provider;

    return (
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Key className="h-5 w-5 text-blue-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-blue-800">API Key Configuration</h4>
            <p className="text-sm text-blue-700">
              For security, API keys are managed on the server. To use this provider, ensure the
              <code className="mx-1 px-1.5 py-0.5 bg-blue-200 text-blue-900 rounded font-mono text-xs">
                {envVar}
              </code>
              environment variable is set in your backend's <code className="mx-1 px-1.5 py-0.5 bg-blue-200 text-blue-900 rounded font-mono text-xs">.env</code> file.
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-sm font-medium text-blue-800 mr-2">API Key Status:</span>
            {providerStatus === 'valid' && <span className="text-sm font-semibold text-green-600">✅ Validated</span>}
            {providerStatus === 'invalid' && <span className="text-sm font-semibold text-red-600">❌ Invalid Key</span>}
            {providerStatus === 'not_set' && <span className="text-sm font-semibold text-yellow-600">⚠️ Not Set in .env</span>}
            {(!providerStatus || providerStatus === 'set') && <span className="text-sm text-gray-500">Not yet validated</span>}
          </div>
          <button
            onClick={() => handleValidateKey(provider)}
            disabled={isProviderValidating}
            className="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {isProviderValidating ? (
              <>
                <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                Validating...
              </>
            ) : 'Validate Key'}
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-4 text-lg text-neutral-700">Loading Configuration...</span>
      </div>
    );
  }

  if (error) {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
              <span className="text-red-800">{error}</span>
            </div>
        </div>
    );
  }

  if (!config || !prompts) {
    return <div>No configuration data found. Please check the backend server.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-800 flex items-center">
          <Brain className="h-8 w-8 mr-3 text-primary-600" />
          🤖 AI Konfiguráció
        </h1>
        <p className="text-neutral-600 mt-2">
          AI modellek, prompt-ok és költségek valós idejű kezelése
        </p>
      </div>

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
          <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
          <span className="text-green-800">{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
            <h2 className="text-xl font-semibold text-neutral-800 mb-4 flex items-center">
              <Zap className="h-5 w-5 mr-2 text-primary-600" />
              AI Model Configuration
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Provider Selection */}
              <div>
                <label htmlFor="provider-select" className="block text-sm font-medium text-neutral-700 mb-2">
                  AI Provider
                </label>
                <select
                  id="provider-select"
                  value={config.provider}
                  onChange={(e) => {
                    const newProvider = e.target.value;
                    const isNowCustom = newProvider === 'custom';
                    const firstModel = providers.find(p => p.name === newProvider)?.models[0]?.model_name || '';
                    
                    setConfig({ 
                      ...config, 
                      provider: newProvider,
                      // Reset model name when provider changes
                      model_name: isNowCustom ? 'custom-model' : firstModel
                    });
                    setIsCustomModel(isNowCustom);
                  }}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  {providers.map(provider => (
                    <option key={provider.name} value={provider.name}>
                      {provider.display_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* DYNAMIC Model Selection */}
              <div>
                <label htmlFor="model-name-select" className="block text-sm font-medium text-neutral-700 mb-2">
                  Model Name
                </label>
                {config.provider === 'custom' ? (
                  <input
                    id="model-name-input"
                    type="text"
                    value={config.model_name}
                    onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                    placeholder="Enter custom model name"
                    className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                ) : (
                  <select
                    id="model-name-select"
                    value={config.model_name}
                    onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                    className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    {providers
                      .find(p => p.name === config.provider)
                      ?.models.map(model => (
                        <option key={model.model_name} value={model.model_name}>
                          {model.model_name} {model.notes ? `(${model.notes})` : ''}
                        </option>
                      ))}
                  </select>
                )}
              </div>

              {/* Custom Pricing (only for custom models) */}
              {config.provider === 'custom' && (
                <>
                  <div>
                    <label htmlFor="custom-input-price" className="block text-sm font-medium text-neutral-700 mb-2">
                      Input Price (per 1M tokens)
                    </label>
                    <input
                      id="custom-input-price"
                      type="number"
                      step="0.01"
                      value={config.custom_input_price || ''}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        custom_input_price: parseFloat(e.target.value) || 0 
                      })}
                      className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="custom-output-price" className="block text-sm font-medium text-neutral-700 mb-2">
                      Output Price (per 1M tokens)
                    </label>
                    <input
                      id="custom-output-price"
                      type="number"
                      step="0.01"
                      value={config.custom_output_price || ''}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        custom_output_price: parseFloat(e.target.value) || 0 
                      })}
                      className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                </>
              )}

              <div>
                <label htmlFor="temperature-range" className="block text-sm font-medium text-neutral-700 mb-2">
                  Temperature ({config.temperature})
                </label>
                <input
                  id="temperature-range"
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>

              <div>
                <label htmlFor="max-tokens-input" className="block text-sm font-medium text-neutral-700 mb-2">
                  Max Tokens
                </label>
                <input
                  id="max-tokens-input"
                  type="number"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) || 0 })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="min-tokens-input" className="block text-sm font-medium text-neutral-700 mb-2">
                  Min Tokens
                </label>
                <input
                  id="min-tokens-input"
                  type="number"
                  value={config.min_tokens}
                  onChange={(e) => setConfig({ ...config, min_tokens: parseInt(e.target.value) || 0 })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="max-retries-input" className="block text-sm font-medium text-neutral-700 mb-2">
                  Max Retries
                </label>
                <input
                  id="max-retries-input"
                  type="number"
                  value={config.max_retries}
                  onChange={(e) => setConfig({ ...config, max_retries: parseInt(e.target.value) || 0 })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="timeout-input" className="block text-sm font-medium text-neutral-700 mb-2">
                  Timeout (seconds)
                </label>
                <input
                  id="timeout-input"
                  type="number"
                  value={config.timeout_seconds}
                  onChange={(e) => setConfig({ ...config, timeout_seconds: parseInt(e.target.value) || 0 })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={handleSaveConfig}
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
              >
                <Save className="h-4 w-4 mr-2" />
                {loading ? 'Saving...' : 'Save Configuration'}
              </button>
              
              <button
                onClick={handleTestConfiguration}
                disabled={loading}
                className="px-4 py-2 bg-secondary-600 text-white rounded-lg hover:bg-secondary-700 disabled:opacity-50 flex items-center"
              >
                <TestTube className="h-4 w-4 mr-2" />
                Test Configuration
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
            <h3 className="text-lg font-semibold text-neutral-800 mb-4 flex items-center">
              <Calculator className="h-5 w-5 mr-2 text-green-600" />
              Cost Calculator
            </h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Input Cost:</span>
                <span className="text-sm font-medium">${costEstimate.input_cost.toFixed(4)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Output Cost:</span>
                <span className="text-sm font-medium">${costEstimate.output_cost.toFixed(4)}</span>
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-neutral-700">Per Request:</span>
                  <span className="text-lg font-bold text-green-600">
                    ${costEstimate.per_request_estimate > 0 ? costEstimate.per_request_estimate.toFixed(4) : 'N/A'}
                  </span>
                </div>
              </div>
              <div className="text-xs text-neutral-500 mt-2">
                * Based on 8K input + 2K output tokens
              </div>
            </div>
          </div>

          {stats && (
            <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
              <h3 className="text-lg font-semibold text-neutral-800 mb-4 flex items-center">
                <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                Usage Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Total Requests:</span>
                  <span className="text-sm font-medium">{stats.total_requests.toLocaleString() || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Total Cost:</span>
                  <span className="text-sm font-medium">${stats.total_cost.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Daily Cost:</span>
                  <span className="text-sm font-medium">${stats.daily_cost.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Avg. Processing:</span>
                  <span className="text-sm font-medium">{stats.average_processing_time > 0 ? stats.average_processing_time.toFixed(1) + 's' : 'N/A'}</span>
                </div>
                <div className="text-xs text-neutral-500 mt-2">
                  Last updated: {new Date(stats.last_updated).toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {testResults && (
            <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
              <h3 className="text-lg font-semibold text-neutral-800 mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2 text-purple-600" />
                Test Results
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Success:</span>
                  <span className={`text-sm font-medium ${testResults.success ? 'text-green-600' : 'text-red-600'}`}>
                    {testResults.success ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Processing Time:</span>
                  <span className="text-sm font-medium">{testResults.test_result?.processing_time_ms?.toFixed(0)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Extracted Product:</span>
                  <span className="text-sm font-medium">{testResults.test_result?.extracted_product_name || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Confidence:</span>
                  <span className="text-sm font-medium">{testResults.test_result?.confidence_score?.toFixed(2) || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      {renderAPIKeyGuidance()}
      <PromptEditorModal />
    </div>
  );
};

export default AIConfigPanel; 