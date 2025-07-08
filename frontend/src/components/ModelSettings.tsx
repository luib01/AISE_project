// frontend/src/components/ModelSettings.tsx
import React, { useState, useEffect } from "react";
import apiClient from "../api/apiClient.ts";
import { MODEL_INFO_ENDPOINT, CHANGE_MODEL_ENDPOINT, HEALTH_CHECK_ENDPOINT } from "../api/endpoints.ts";

interface ModelInfo {
  current_model: string;
  base_url: string;
  timeout: number;
  temperature: number;
  max_tokens: number;
  available_models: string[];
}

const ModelSettings: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [healthStatus, setHealthStatus] = useState<any>(null);

  useEffect(() => {
    loadModelInfo();
    checkHealth();
  }, []);

  const loadModelInfo = async () => {
    try {
      const response = await apiClient.get(MODEL_INFO_ENDPOINT);
      setModelInfo(response.data);
      setSelectedModel(response.data.current_model);
    } catch (err) {
      console.error("Error loading model info:", err);
      setError("Failed to load model information");
    }
  };

  const checkHealth = async () => {
    try {
      const response = await apiClient.get(HEALTH_CHECK_ENDPOINT);
      setHealthStatus(response.data);
    } catch (err) {
      console.error("Health check failed:", err);
      setHealthStatus({ status: "unhealthy", message: "Ollama connection failed" });
    }
  };

  const changeModel = async () => {
    if (!selectedModel || selectedModel === modelInfo?.current_model) {
      setError("Please select a different model");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await apiClient.post(CHANGE_MODEL_ENDPOINT, null, {
        params: { new_model: selectedModel }
      });

      setSuccess(response.data.message);
      await loadModelInfo();
      await checkHealth();
    } catch (err: any) {
      console.error("Error changing model:", err);
      setError(err.response?.data?.detail || "Failed to change model");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "text-green-600";
      case "unhealthy": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-100 text-green-800";
      case "unhealthy": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow text-gray-800 max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold mb-6">AI Model Settings</h2>
      
      {/* Health Status */}
      {healthStatus && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">System Health</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${getStatusBadge(healthStatus.status)}`}>
                {healthStatus.status.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Message:</span>
              <span className={`ml-2 text-sm ${getStatusColor(healthStatus.status)}`}>
                {healthStatus.message}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Current Model Info */}
      {modelInfo && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Current Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-gray-600">Model:</span>
              <span className="ml-2 font-medium">{modelInfo.current_model}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Base URL:</span>
              <span className="ml-2 font-medium">{modelInfo.base_url}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Timeout:</span>
              <span className="ml-2 font-medium">{modelInfo.timeout}s</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Temperature:</span>
              <span className="ml-2 font-medium">{modelInfo.temperature}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Max Tokens:</span>
              <span className="ml-2 font-medium">{modelInfo.max_tokens}</span>
            </div>
          </div>
        </div>
      )}

      {/* Model Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Change Model</h3>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select Model:
            </label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {modelInfo?.available_models.map((model) => (
                <option key={model} value={model}>
                  {model} {model === modelInfo.current_model ? "(Current)" : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={changeModel}
              disabled={loading || !selectedModel || selectedModel === modelInfo?.current_model}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Changing..." : "Change Model"}
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {success}
        </div>
      )}

      {/* Available Models Info */}
      {modelInfo && (
        <div className="p-4 bg-yellow-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Available Models</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {modelInfo.available_models.map((model) => (
              <div key={model} className="flex items-center space-x-2">
                <span className={`w-2 h-2 rounded-full ${model === modelInfo.current_model ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                <span className={`text-sm ${model === modelInfo.current_model ? 'font-medium' : ''}`}>
                  {model}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <p><strong>Note:</strong> Model changes are temporary until the application restarts.</p>
            <p>To make permanent changes, update the OLLAMA_MODEL variable in your .env file.</p>
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={() => {
            loadModelInfo();
            checkHealth();
          }}
          className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
        >
          Refresh Status
        </button>
      </div>
    </div>
  );
};

export default ModelSettings;
