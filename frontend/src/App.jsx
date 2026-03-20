import React, { useState, useEffect } from 'react';
import { FileText, AlertCircle, Cpu, BarChart3, Brain } from 'lucide-react';
import FileUpload from './components/FileUpload';
import ProgressIndicator from './components/ProgressIndicator';
import ResultCard from './components/ResultCard';
import ImagePreview from './components/ImagePreview';
import Scene3D from './components/Scene3D';
import LoanSummaryCard from './components/LoanSummaryCard';
import PortfolioChat from './components/PortfolioChat';
import PortfolioStats from './components/PortfolioStats';
import { motion, AnimatePresence } from 'framer-motion';
import { convertFileToImages, dataUrlToBlob } from './utils/fileConverter';
import {
  processSingleInvoice,
  getDecisionSupport,
  chatQuery,
  getPortfolioStats as fetchPortfolioStats,
  generateReport,
} from './utils/api';

const TABS = [
  { id: 'invoice', label: 'Invoice Analysis', icon: FileText },
  { id: 'portfolio', label: 'Portfolio Intelligence', icon: Brain },
];

function App() {
  const [activeTab, setActiveTab] = useState('invoice');
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ total: 0, completed: 0, current: '' });
  const [error, setError] = useState(null);
  const [imageDataMap, setImageDataMap] = useState({});
  const [previewImages, setPreviewImages] = useState([]);
  const [processingIndex, setProcessingIndex] = useState(null);
  const [resolutionMap, setResolutionMap] = useState({});
  const [resultResolutionMap, setResultResolutionMap] = useState({});
  const [enhancedMap, setEnhancedMap] = useState({});
  const [reasoningMap, setReasoningMap] = useState({});

  // Decision support state
  const [decisionDataMap, setDecisionDataMap] = useState({});
  const [decisionLoadingMap, setDecisionLoadingMap] = useState({});

  // Portfolio state
  const [portfolioStats, setPortfolioStats] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);

  // Load portfolio stats when tab switches to portfolio
  useEffect(() => {
    if (activeTab === 'portfolio' && !portfolioStats) {
      setPortfolioLoading(true);
      fetchPortfolioStats()
        .then((data) => setPortfolioStats(data))
        .catch((err) => console.error('Portfolio stats error:', err))
        .finally(() => setPortfolioLoading(false));
    }
  }, [activeTab, portfolioStats]);

  const handleFilesSelected = async (files) => {
    setProcessing(false);
    setResults([]);
    setError(null);
    setImageDataMap({});
    setPreviewImages([]);
    setResolutionMap({});
    setEnhancedMap({});
    setReasoningMap({});
    setDecisionDataMap({});

    try {
      const allImages = [];
      const imageData = {};
      const previews = [];

      for (const file of files) {
        try {
          const images = await convertFileToImages(file);
          images.forEach((img, idx) => {
            const key = `${file.name}_${idx}`;
            allImages.push({
              key,
              dataUrl: img.dataUrl,
              filename: img.filename,
              originalFile: img.originalFile,
              pageNumber: img.pageNumber,
            });
            imageData[key] = img.dataUrl;
            previews.push({ key, dataUrl: img.dataUrl, filename: img.filename });
          });
        } catch (err) {
          console.error(`Error converting ${file.name}:`, err);
          setError(`Failed to convert ${file.name}: ${err.message}`);
        }
      }

      setImageDataMap(imageData);
      setPreviewImages(previews);

      const initialResolutions = {};
      previews.forEach((p) => {
        initialResolutions[p.key] = { dataUrl: p.dataUrl, resolution: 100 };
      });
      setResolutionMap(initialResolutions);
    } catch (err) {
      console.error('Processing error:', err);
      setError(`Processing failed: ${err.message}`);
    }
  };

  const handleProcessImages = async () => {
    setProcessing(true);
    setResults([]);
    setError(null);
    setProgress({ total: previewImages.length, completed: 0, current: '' });

    try {
      for (let i = 0; i < previewImages.length; i++) {
        const preview = previewImages[i];
        setProcessingIndex(i);
        setProgress((prev) => ({ ...prev, current: preview.filename }));

        try {
          const processData = resolutionMap[preview.key] || { dataUrl: preview.dataUrl, resolution: 100 };
          const blob = dataUrlToBlob(processData.dataUrl);
          const isEnhanced = enhancedMap[preview.key] || false;
          const reasoningMode = reasoningMap[preview.key] ? 'reason' : 'simple';

          const result = await processSingleInvoice(blob, preview.filename, isEnhanced, reasoningMode);

          const resultWithMetadata = {
            ...result,
            filename: preview.filename,
            originalFile: preview.filename,
            index: i,
            success: true,
            key: preview.key,
            processedImageData: processData.dataUrl,
            processedResolution: processData.resolution,
          };

          setResults((prev) => [...prev, resultWithMetadata]);

          // Auto-fetch decision support if we have asset_cost
          if (result.fields?.asset_cost) {
            handleRequestDecision(result.fields, preview.key);
          }
        } catch (error) {
          const errorResult = {
            filename: preview.filename,
            index: i,
            success: false,
            error: error.response?.data?.detail || error.message,
            key: preview.key,
          };
          setResults((prev) => [...prev, errorResult]);
        }

        setProgress((prev) => ({ ...prev, completed: i + 1 }));
      }
    } catch (err) {
      console.error('Processing error:', err);
      setError(`Processing failed: ${err.message}`);
    } finally {
      setProcessing(false);
      setProcessingIndex(null);
      setProgress((prev) => ({ ...prev, current: '' }));
    }
  };

  const handleReprocess = async (result, resolution, adjustedDataUrl) => {
    const index = results.findIndex((r) => r.key === result.key);
    if (index === -1) return;
    setProcessingIndex(index);

    try {
      const blob = dataUrlToBlob(adjustedDataUrl || imageDataMap[result.key]);
      const isEnhanced = enhancedMap[result.key] || false;
      const reasoningMode = reasoningMap[result.key] ? 'reason' : 'simple';

      const newResult = await processSingleInvoice(blob, result.filename, isEnhanced, reasoningMode);

      const resultWithMetadata = {
        ...newResult,
        filename: result.filename,
        originalFile: result.originalFile,
        index,
        success: true,
        key: result.key,
        processedImageData: adjustedDataUrl || imageDataMap[result.key],
        processedResolution: resolution,
      };

      setResults((prev) => {
        const newResults = [...prev];
        newResults[index] = resultWithMetadata;
        return newResults;
      });

      // Re-fetch decision support
      if (newResult.fields?.asset_cost) {
        handleRequestDecision(newResult.fields, result.key);
      }
    } catch (error) {
      setError(`Reprocessing failed: ${error.message}`);
    } finally {
      setProcessingIndex(null);
    }
  };

  const handleResolutionChange = (key, dataUrl, resolution) => {
    setResolutionMap((prev) => ({ ...prev, [key]: { dataUrl, resolution } }));
  };

  const handleEnhanceToggle = (key) => {
    setEnhancedMap((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleReasoningModeToggle = (key) => {
    setReasoningMap((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Decision support handler
  const handleRequestDecision = async (fields, resultKey) => {
    if (!fields?.asset_cost) return;
    const key = resultKey || 'default';
    setDecisionLoadingMap((prev) => ({ ...prev, [key]: true }));
    try {
      const data = await getDecisionSupport(fields.asset_cost, fields.horse_power, fields.model_name);
      setDecisionDataMap((prev) => ({ ...prev, [key]: data }));
    } catch (err) {
      console.error('Decision support error:', err);
    } finally {
      setDecisionLoadingMap((prev) => ({ ...prev, [key]: false }));
    }
  };

  // Chat handler
  const handleChatQuery = async (query) => {
    return await chatQuery(query);
  };

  // Download report handler
  const handleDownloadReport = async (fields, decisionData) => {
    try {
      const docId = fields.doc_id || fields.model_name || 'invoice';
      const data = await generateReport(fields, decisionData, docId);
      if (data.html) {
        const blob = new Blob([data.html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `KrishiIntel_Report_${docId}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Report generation error:', err);
      setError('Failed to generate report');
    }
  };

  return (
    <>
      <Scene3D />
      <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 relative z-10 font-sans text-gray-200">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center mb-6 relative">
              <div className="absolute inset-0 bg-primary-500/20 blur-[40px] rounded-full w-32 h-32 mx-auto" />
              <div className="p-4 bg-dark-800/80 backdrop-blur-xl rounded-2xl border border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.3)] relative z-10 group hover:border-primary-400 transition-colors">
                <Cpu className="w-14 h-14 text-primary-400 group-hover:text-primary-300 transition-colors drop-shadow-[0_0_10px_#0ea5e9]" />
              </div>
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary-400 via-white to-accent-400 mb-3 tracking-tight drop-shadow-[0_0_20px_rgba(14,165,233,0.4)] pb-1 pt-1">
              KrishiIntel AI
            </h1>
            <p className="text-lg md:text-xl text-primary-200/80 font-medium tracking-wide max-w-2xl mx-auto">
              AI-Powered Agricultural Finance Intelligence Platform
            </p>
            <p className="text-xs text-primary-400/50 mt-2 font-mono tracking-widest uppercase">Built by Team KrishiAIIntel</p>
          </motion.div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex bg-dark-800/80 rounded-2xl p-1.5 border border-dark-600 backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2.5 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
                      isActive
                        ? 'bg-gradient-to-r from-primary-600/80 to-primary-500/80 text-white shadow-[0_0_20px_rgba(14,165,233,0.3)] border border-primary-400/40'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700/50'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            {activeTab === 'invoice' && (
              <motion.div
                key="invoice"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
                className="space-y-8"
              >
                {/* Upload Section */}
                <div className="border border-primary-500/20 shadow-[0_0_40px_rgba(0,0,0,0.5)] rounded-2xl overflow-hidden">
                  <FileUpload onFilesSelected={handleFilesSelected} disabled={processing} />
                </div>

                {/* Image Previews with Resolution Sliders */}
                {previewImages.length > 0 && !processing && results.length === 0 && (
                  <div className="space-y-5">
                    <div className="flex items-center justify-between glass-morphism-card px-6 py-4">
                      <h2 className="text-xl font-bold text-white flex items-center gap-3">
                        <span className="w-2 h-2 rounded-full bg-primary-400 shadow-[0_0_8px_#0ea5e9]" />
                        Preview &amp; Adjust Resolution
                      </h2>
                      <span className="text-sm font-mono font-bold text-primary-400 bg-dark-800 border border-dark-600 px-3 py-1 rounded-full">
                        {previewImages.length} {previewImages.length === 1 ? 'Image' : 'Images'}
                      </span>
                    </div>

                    <div
                      className={`grid gap-5 ${
                        previewImages.length === 1
                          ? 'grid-cols-1 max-w-2xl mx-auto'
                          : previewImages.length === 2
                          ? 'grid-cols-1 md:grid-cols-2'
                          : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                      }`}
                    >
                      {previewImages.map((preview, idx) => (
                        <ImagePreview
                          key={preview.key}
                          onReasoningModeToggle={() => handleReasoningModeToggle(preview.key)}
                          useReasoning={reasoningMap[preview.key] || false}
                          imageData={preview.dataUrl}
                          fileName={preview.filename}
                          onResolutionChange={(dataUrl, resolution) =>
                            handleResolutionChange(preview.key, dataUrl, resolution)
                          }
                          onEnhanceToggle={() => handleEnhanceToggle(preview.key)}
                          isEnhanced={enhancedMap[preview.key] || false}
                        />
                      ))}
                    </div>

                    <button
                      onClick={handleProcessImages}
                      className="w-full bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-400 hover:to-accent-400 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-[0_0_30px_rgba(14,165,233,0.3)] hover:shadow-[0_0_40px_rgba(14,165,233,0.5)] flex items-center justify-center gap-3 text-lg tracking-wide"
                    >
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>
                        Process {previewImages.length} Image{previewImages.length > 1 ? 's' : ''}
                      </span>
                    </button>
                  </div>
                )}

                {/* Error Display */}
                {error && (
                  <div className="bg-red-900/20 border border-red-500/40 rounded-2xl p-5 flex items-start gap-4 backdrop-blur-md">
                    <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5 drop-shadow-[0_0_8px_#f87171]" />
                    <div>
                      <h3 className="text-red-200 font-bold mb-1">Processing Error</h3>
                      <p className="text-red-300/80 text-sm">{error}</p>
                    </div>
                  </div>
                )}

                {/* Progress Indicator */}
                {processing && (
                  <div className="space-y-5">
                    <ProgressIndicator
                      total={progress.total}
                      completed={progress.completed}
                      current={progress.current}
                      results={results}
                    />

                    {processingIndex !== null && previewImages[processingIndex] && (
                      <div className="glass-morphism overflow-hidden">
                        <div className="bg-dark-800/80 border-b border-primary-500/20 px-6 py-4">
                          <h3 className="text-lg font-bold text-white flex items-center gap-3">
                            <svg
                              className="w-5 h-5 text-primary-400 animate-spin drop-shadow-[0_0_8px_#0ea5e9]"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                              />
                            </svg>
                            <span className="text-primary-300 text-sm font-mono mr-2">[SCANNING]</span>
                            {previewImages[processingIndex].filename}
                          </h3>
                        </div>
                        <div className="relative bg-dark-900/60 p-6 flex justify-center items-center">
                          <img
                            src={previewImages[processingIndex].dataUrl}
                            alt="Processing"
                            className="max-w-full max-h-96 rounded-xl shadow-[0_0_25px_rgba(0,0,0,0.6)]"
                          />
                          <div className="absolute inset-0 flex items-center justify-center rounded-xl overflow-hidden">
                            <div className="scanning-line"></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Results Section */}
                {results.length > 0 && (
                  <div className="space-y-5">
                    <div className="flex items-center justify-between glass-morphism-card px-6 py-4">
                      <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <FileText className="w-6 h-6 text-primary-400 drop-shadow-[0_0_10px_#0ea5e9]" />
                        Processing Results
                      </h2>
                      <span className="text-sm font-mono font-bold text-primary-400 bg-dark-800 border border-primary-500/30 px-3 py-1 rounded-full shadow-[0_0_10px_rgba(14,165,233,0.2)]">
                        {results.length} {results.length === 1 ? 'Document' : 'Documents'}
                      </span>
                    </div>

                    {results.map((result, index) => {
                      const imageKey = result.key || `${result.originalFile}_${index}`;
                      const originalImage = imageDataMap[imageKey] || imageDataMap[Object.keys(imageDataMap)[index]];
                      const processedImage = result.processedImageData || originalImage;
                      return (
                        <div key={index}>
                          <ResultCard
                            result={result}
                            imageData={originalImage}
                            processedImageData={processedImage}
                            onReprocess={handleReprocess}
                            isProcessing={processingIndex === index}
                          />
                          {/* Loan Summary Card */}
                          {result.success && result.fields && (
                            <LoanSummaryCard
                              fields={result.fields}
                              decisionData={decisionDataMap[result.key]}
                              onRequestDecision={(fields) => handleRequestDecision(fields, result.key)}
                              onDownloadReport={handleDownloadReport}
                              isLoading={decisionLoadingMap[result.key]}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Info Cards */}
                {!processing && results.length === 0 && previewImages.length === 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div className="glass-morphism-card p-7 text-center hover:border-primary-500/30 transition-all group">
                      <div className="w-14 h-14 bg-primary-500/10 border border-primary-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:shadow-[0_0_20px_rgba(14,165,233,0.3)] transition-shadow">
                        <FileText className="w-7 h-7 text-primary-400" />
                      </div>
                      <h3 className="font-bold text-gray-100 mb-2 text-lg">Multiple Formats</h3>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        Upload images or PDFs. PDFs are automatically converted to images.
                      </p>
                    </div>

                    <div className="glass-morphism-card p-7 text-center hover:border-green-500/30 transition-all group">
                      <div className="w-14 h-14 bg-green-500/10 border border-green-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] transition-shadow">
                        <svg className="w-7 h-7 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                          />
                        </svg>
                      </div>
                      <h3 className="font-bold text-gray-100 mb-2 text-lg">Loan Decision Support</h3>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        Instant EMI calculations, eligibility classification, and loan recommendations.
                      </p>
                    </div>

                    <div className="glass-morphism-card p-7 text-center hover:border-accent-500/30 transition-all group">
                      <div className="w-14 h-14 bg-accent-500/10 border border-accent-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-shadow">
                        <Brain className="w-7 h-7 text-accent-400" />
                      </div>
                      <h3 className="font-bold text-gray-100 mb-2 text-lg">Portfolio Intelligence</h3>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        Ask natural language questions about your invoice portfolio powered by RAG + AI.
                      </p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'portfolio' && (
              <motion.div
                key="portfolio"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-8"
              >
                {/* Portfolio Stats */}
                <PortfolioStats stats={portfolioStats} isLoading={portfolioLoading} />

                {/* Chat Interface */}
                <PortfolioChat onSendQuery={handleChatQuery} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer */}
          <div className="mt-16 text-center text-primary-400/30 text-xs font-mono tracking-widest uppercase">
            <p>KrishiIntel AI — Agricultural Finance Intelligence Platform</p>
            <p className="mt-1">Built by Team KrishiAIIntel</p>
          </div>
        </div>
      </div>

      {/* Fixed persistent developer credit */}
      <div className="fixed bottom-4 right-4 z-50 text-[10px] font-mono text-primary-400/40 hover:text-primary-400/70 transition-colors duration-300 select-none">
        Team <span className="font-semibold text-primary-300/60">KrishiAIIntel</span>
      </div>
    </>
  );
}

export default App;
