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
  ExternalLink,
  Calculator,
  Brain,
  MessageSquare
} from 'lucide-react';

interface AIProvider {
  name: string;
  display_name: string;
  models: {
    model_name: string;
    input_price: number;
    output_price: number;
  }[];
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
  const [config, setConfig] = useState<AIModelConfig>({
    model_name: 'claude-3-5-haiku-20241022',
    provider: 'anthropic',
    temperature: 0.0,
    max_tokens: 8192,
    min_tokens: 2048,
    token_decrement: 1024,
    max_retries: 3,
    timeout_seconds: 30,
    max_text_length: 8000,
    max_tables_summary: 3
  });
  
  const [prompts, setPrompts] = useState<PromptTemplates>({
    extraction_prompt: '',
    table_summary_template: '',
    no_tables_message: '',
    error_fallback_template: ''
  });
  
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [stats, setStats] = useState<UsageStats>({
    total_requests: 0,
    total_cost: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
    average_processing_time: 0,
    daily_cost: 0,
    daily_requests: 0,
    last_updated: new Date().toISOString()
  });
  
  const [costEstimate, setCostEstimate] = useState<CostEstimate>({
    input_cost: 0,
    output_cost: 0,
    total_cost: 0,
    per_request_estimate: 0
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activePromptEditor, setActivePromptEditor] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<any>(null);
  const [isCustomModel, setIsCustomModel] = useState(false);

  // Load data on component mount
  useEffect(() => {
    loadProviders();
    loadCurrentConfig();
    loadUsageStats();
  }, []);

  // Real-time cost calculation
  useEffect(() => {
    calculateCostEstimate();
  }, [config, providers]);

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/ai-config/providers');
      const data = await response.json();
      setProviders(data.providers);
    } catch (err) {
      setError('Failed to load AI providers');
      console.error('Provider loading error:', err);
    }
  };

  const loadCurrentConfig = async () => {
    try {
      const response = await fetch('/api/ai-config/current');
      const data = await response.json();
      setConfig(data.model);
      setPrompts(data.prompts);
      setIsCustomModel(!providers.some(p => 
        p.models.some(m => m.model_name === data.model.model_name)
      ));
    } catch (err) {
      setError('Failed to load current configuration');
      console.error('Config loading error:', err);
    }
  };

  const loadUsageStats = async () => {
    try {
      const response = await fetch('/api/ai-config/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Stats loading error:', err);
    }
  };

  const calculateCostEstimate = () => {
    if (!providers.length) return;

    let pricing = null;
    
    // Find pricing for current model
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

    // Use custom pricing if available
    if (!pricing && isCustomModel && config.custom_input_price && config.custom_output_price) {
      pricing = {
        input_tokens_per_million: config.custom_input_price,
        output_tokens_per_million: config.custom_output_price
      };
    }

    if (pricing) {
      // Estimate typical usage (8000 input tokens, 2000 output tokens per request)
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
      const response = await fetch('/api/ai-config/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update configuration');
      }

      setSuccess('Configuration updated successfully!');
      await loadUsageStats(); // Reload stats
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrompts = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/ai-config/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prompts)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update prompts');
      }

      setSuccess('Prompts updated successfully!');
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
      const response = await fetch('/api/ai-config/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_text: "Sample PDF content for testing AI configuration...",
          test_tables: [{"header": ["Parameter", "Value"], "rows": [["Test", "123"]]}]
        })
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

  const PromptEditor: React.FC<{
    title: string;
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
  }> = ({ title, value, onChange, placeholder }) => (
    <div className="bg-white rounded-lg border border-neutral-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-neutral-800 flex items-center">
          <MessageSquare className="h-4 w-4 mr-2" />
          {title}
        </h4>
        <button
          onClick={() => setActivePromptEditor(activePromptEditor === title ? null : title)}
          className="text-primary-600 hover:text-primary-700"
        >
          <Edit className="h-4 w-4" />
        </button>
      </div>
      
      {activePromptEditor === title ? (
        <div className="space-y-3">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full h-64 p-3 border border-neutral-300 rounded-lg font-mono text-sm resize-y focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => setActivePromptEditor(null)}
              className="px-3 py-1 text-sm text-neutral-600 hover:text-neutral-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSavePrompts}
              disabled={loading}
              className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
            >
              Save
            </button>
          </div>
        </div>
      ) : (
        <div className="text-sm text-neutral-600 bg-neutral-50 p-3 rounded border max-h-20 overflow-hidden">
          {value || placeholder}
        </div>
      )}
    </div>
  );

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

      {/* Status Messages */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
          <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
          <span className="text-green-800">{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Model Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Provider & Model Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
            <h2 className="text-xl font-semibold text-neutral-800 mb-4 flex items-center">
              <Zap className="h-5 w-5 mr-2 text-primary-600" />
              AI Model Configuration
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Provider Selection */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  AI Provider
                </label>
                <select
                  value={config.provider}
                  onChange={(e) => {
                    setConfig({ ...config, provider: e.target.value });
                    setIsCustomModel(e.target.value === 'custom');
                  }}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {providers.map(provider => (
                    <option key={provider.name} value={provider.name}>
                      {provider.display_name}
                    </option>
                  ))}
                  <option value="custom">Custom Model</option>
                </select>
              </div>

              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Model Name
                </label>
                {isCustomModel ? (
                  <input
                    type="text"
                    value={config.model_name}
                    onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                    placeholder="Enter custom model name"
                    className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                ) : (
                  <select
                    value={config.model_name}
                    onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                    className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    {providers
                      .find(p => p.name === config.provider)
                      ?.models.map(model => (
                        <option key={model.model_name} value={model.model_name}>
                          {model.model_name}
                        </option>
                      ))}
                  </select>
                )}
              </div>

              {/* Custom Pricing (only for custom models) */}
              {isCustomModel && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Input Price (per 1M tokens)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={config.custom_input_price || ''}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        custom_input_price: parseFloat(e.target.value) || 0 
                      })}
                      className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Output Price (per 1M tokens)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={config.custom_output_price || ''}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        custom_output_price: parseFloat(e.target.value) || 0 
                      })}
                      className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </>
              )}

              {/* Model Parameters */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Temperature ({config.temperature})
                </label>
                <input
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
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Min Tokens
                </label>
                <input
                  type="number"
                  value={config.min_tokens}
                  onChange={(e) => setConfig({ ...config, min_tokens: parseInt(e.target.value) })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Max Retries
                </label>
                <input
                  type="number"
                  value={config.max_retries}
                  onChange={(e) => setConfig({ ...config, max_retries: parseInt(e.target.value) })}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={config.timeout_seconds}
                  onChange={(e) => setConfig({ ...config, timeout_seconds: parseInt(e.target.value) })}
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

          {/* Prompt Templates */}
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
            <h2 className="text-xl font-semibold text-neutral-800 mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2 text-primary-600" />
              Prompt Templates
            </h2>
            
            <div className="space-y-4">
              <PromptEditor
                title="Main Extraction Prompt"
                value={prompts.extraction_prompt}
                onChange={(value) => setPrompts({ ...prompts, extraction_prompt: value })}
                placeholder="Enter the main extraction prompt template..."
              />
              
              <PromptEditor
                title="Table Summary Template"
                value={prompts.table_summary_template}
                onChange={(value) => setPrompts({ ...prompts, table_summary_template: value })}
                placeholder="Enter the table summary template..."
              />
              
              <PromptEditor
                title="No Tables Message"
                value={prompts.no_tables_message}
                onChange={(value) => setPrompts({ ...prompts, no_tables_message: value })}
                placeholder="Message when no tables are found..."
              />
              
              <PromptEditor
                title="Error Fallback Template"
                value={prompts.error_fallback_template}
                onChange={(value) => setPrompts({ ...prompts, error_fallback_template: value })}
                placeholder="Error fallback template..."
              />
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Real-time Cost Calculator */}
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
                    ${costEstimate.per_request_estimate.toFixed(4)}
                  </span>
                </div>
              </div>
              
              <div className="text-xs text-neutral-500 mt-2">
                * Based on 8K input + 2K output tokens
              </div>
            </div>
          </div>

          {/* Usage Statistics */}
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
            <h3 className="text-lg font-semibold text-neutral-800 mb-4 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
              Usage Statistics
            </h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Total Requests:</span>
                <span className="text-sm font-medium">{stats.total_requests.toLocaleString()}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Total Cost:</span>
                <span className="text-sm font-medium">${stats.total_cost.toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Daily Cost:</span>
                <span className="text-sm font-medium">${stats.daily_cost.toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-neutral-600">Avg. Processing:</span>
                <span className="text-sm font-medium">{stats.average_processing_time.toFixed(1)}s</span>
              </div>
              
              <div className="text-xs text-neutral-500 mt-2">
                Last updated: {new Date(stats.last_updated).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Test Results */}
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
                  <span className="text-sm font-medium">{testResults.processing_time?.toFixed(2)}s</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Tokens Used:</span>
                  <span className="text-sm font-medium">{testResults.tokens_used}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-neutral-600">Cost:</span>
                  <span className="text-sm font-medium">${testResults.cost?.toFixed(4)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIConfigPanel; 