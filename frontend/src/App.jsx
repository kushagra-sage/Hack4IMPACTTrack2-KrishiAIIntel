import React, { useState, useEffect, useRef } from 'react';
import {
  FileText, AlertCircle, Cpu, BarChart3, Brain, UploadCloud, Layers,
  Briefcase, ChevronRight, Activity, Zap, ZoomIn, CheckCircle2, Shield, Globe, Download
} from 'lucide-react';
import FileUpload from './components/FileUpload';
import ProgressIndicator from './components/ProgressIndicator';
import ResultCard from './components/ResultCard';
import ImagePreview from './components/ImagePreview';
import LoanSummaryCard from './components/LoanSummaryCard';
import PortfolioChat from './components/PortfolioChat';
import PortfolioStats from './components/PortfolioStats';
import LandingPage from './components/LandingPage';
import UnderTheHood from './components/UnderTheHood';
import { motion, AnimatePresence } from 'framer-motion';
import { convertFileToImages, dataUrlToBlob } from './utils/fileConverter';
import {
  processSingleInvoice,
  getDecisionSupport,
  generateReportPDF,
  generateBatchReportPDF,
  getPortfolioStats,
  chatQuery
} from './utils/api';

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewImages, setPreviewImages] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, completed: [] });
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [processingIndex, setProcessingIndex] = useState(null);
  const [imageDataMap, setImageDataMap] = useState({});
  const [decisionDataMap, setDecisionDataMap] = useState({});
  const [decisionLoadingMap, setDecisionLoadingMap] = useState({});
  const [useReasoning, setUseReasoning] = useState(false);
  const [reasoningMap, setReasoningMap] = useState({});
  const [portfolioStats, setPortfolioStats] = useState({});
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [enhancedMap, setEnhancedMap] = useState({});
  const resultsRef = useRef(null);

  useEffect(() => {
    if (activeTab === 'portfolio') {
      loadPortfolioStats();
    }
  }, [activeTab]);

  // Auto-scroll to results when they first appear
  useEffect(() => {
    if (results.length > 0 && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [results.length]);

  const loadPortfolioStats = async () => {
    setPortfolioLoading(true);
    try {
      const stats = await getPortfolioStats();
      setPortfolioStats(stats);
    } catch (err) {
      console.error('Failed to load portfolio stats:', err);
    } finally {
      setPortfolioLoading(false);
    }
  };

  const handleChatQuery = async (query) => {
    return await chatQuery(query);
  };

  const handleReasoningModeToggle = (key) => {
    setReasoningMap(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleEnhanceToggle = (key) => {
    setEnhancedMap(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleResolutionChange = (key, dataUrl, resolution) => {
    setPreviewImages(prev => prev.map(img =>
      img.key === key ? { ...img, dataUrl, resolution } : img
    ));
  };

  const handleFilesSelected = async (files) => {
    setSelectedFiles(files);
    setError(null);
    setResults([]);
    setProcessingIndex(null);
    setImageDataMap({});
    setDecisionDataMap({});

    try {
      if (files.length === 0) return;

      let allImages = [];
      for (const file of files) {
        if (file.type === 'application/pdf') {
          const pdfImages = await convertFileToImages(file);
          allImages = [...allImages, ...pdfImages.map((img, idx) => ({
            file,
            dataUrl: img.dataUrl,
            filename: `${file.name} (Page ${idx + 1})`,
            key: `${file.name}_${idx}`,
            resolution: 100,
            originalDataUrl: img.dataUrl
          }))];
        } else {
          const dataUrl = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
          });
          allImages.push({
            file,
            dataUrl,
            filename: file.name,
            key: file.name,
            resolution: 100,
            originalDataUrl: dataUrl
          });
        }
      }

      setPreviewImages(allImages);

      const newImageDataMap = {};
      allImages.forEach(img => {
        newImageDataMap[img.key] = img.originalDataUrl;
      });
      setImageDataMap(newImageDataMap);

      const newReasoningMap = {};
      allImages.forEach(img => {
        newReasoningMap[img.key] = false;
      });
      setReasoningMap(newReasoningMap);

      const newEnhancedMap = {};
      allImages.forEach(img => {
        newEnhancedMap[img.key] = false;
      });
      setEnhancedMap(newEnhancedMap);

    } catch (err) {
      console.error('File processing error:', err);
      setError('Failed to load files for preview');
    }
  };

  const processSingleImage = async (imageInfo, index) => {
    setProcessingIndex(index);
    let blob;

    if (imageInfo.originalDataUrl) {
      blob = dataUrlToBlob(imageInfo.originalDataUrl);
    } else {
      blob = new Blob([imageInfo.file], { type: imageInfo.file.type });
    }

    const file = new File([blob], imageInfo.filename, { type: 'image/jpeg' });

    try {
      let extractionFile = file;
      const shouldUseReasoning = reasoningMap[imageInfo.key] || false;
      const isEnhanced = enhancedMap[imageInfo.key] || false;

      if (imageInfo.resolution && imageInfo.resolution < 100) {
        if (imageInfo.dataUrl) {
          const adjustedBlob = dataUrlToBlob(imageInfo.dataUrl);
          extractionFile = new File([adjustedBlob], imageInfo.filename, { type: 'image/jpeg' });
        }
      }

      const responseData = await processSingleInvoice(extractionFile, imageInfo.filename, isEnhanced, shouldUseReasoning ? 'reason' : 'simple');

      let result = {
        originalFile: imageInfo.filename,
        key: imageInfo.key,
        pageNumber: imageInfo.pageNumber,
        ...responseData,
        success: true,
        processedResolution: imageInfo.resolution || 100,
        processedImageData: imageInfo.dataUrl
      };

      setProgress(prev => ({
        ...prev,
        completed: [...prev.completed, result]
      }));

      if (result.success && result.fields && result.fields.asset_cost) {
        handleRequestDecision(result.fields, imageInfo.key);
      }

      return result;
    } catch (err) {
      console.error(`Error processing ${imageInfo.filename}:`, err);
      const errResult = {
        originalFile: imageInfo.filename,
        key: imageInfo.key,
        pageNumber: imageInfo.pageNumber,
        success: false,
        error: err.message,
        processedResolution: imageInfo.resolution || 100,
        processedImageData: imageInfo.dataUrl
      };
      setProgress(prev => ({
        ...prev,
        completed: [...prev.completed, errResult]
      }));
      return errResult;
    }
  };

  const handleProcessImages = async () => {
    if (previewImages.length === 0) return;

    setProcessing(true);
    setError(null);
    setResults([]);

    setProgress({
      current: 1,
      total: previewImages.length,
      completed: []
    });

    const newResults = [];
    for (let i = 0; i < previewImages.length; i++) {
      setProgress(prev => ({ ...prev, current: i + 1 }));
      const result = await processSingleImage(previewImages[i], i);
      newResults.push({ ...result, _originalIndex: i });
      setResults([...newResults]);
    }

    setProcessingIndex(null);
    setProcessing(false);
  };

  const handleReprocess = async (resultToReprocess, newResolution, newAdjustedDataUrl) => {
    setProcessing(true);
    setError(null);

    const indexToReprocess = results.findIndex(r => r.key === resultToReprocess.key);
    if (indexToReprocess === -1) {
      setProcessing(false);
      return;
    }

    setProcessingIndex(indexToReprocess);

    const imageInfo = previewImages.find(img => img.key === resultToReprocess.key);
    if (!imageInfo) {
      setProcessing(false);
      return;
    }

    const updatedImageInfo = {
      ...imageInfo,
      resolution: newResolution,
      dataUrl: newAdjustedDataUrl || imageInfo.dataUrl
    };

    const newResult = await processSingleImage(updatedImageInfo, indexToReprocess);

    setResults(prevResults => {
      const newResults = [...prevResults];
      newResults[indexToReprocess] = newResult;
      return newResults;
    });

    setProcessingIndex(null);
    setProcessing(false);
  };

  const handleRequestDecision = async (fields, imageKey) => {
    setDecisionLoadingMap(prev => ({ ...prev, [imageKey]: true }));
    try {
      const decisionResult = await getDecisionSupport(fields.asset_cost, fields.horse_power, fields.model_name);
      setDecisionDataMap(prev => ({
        ...prev,
        [imageKey]: decisionResult
      }));
    } catch (err) {
      console.error("Decision Request Error", err);
    } finally {
      setDecisionLoadingMap(prev => ({ ...prev, [imageKey]: false }));
    }
  };

  const handleDownloadReport = async (fields, decisionData, docId) => {
    try {
      const blob = await generateReportPDF(fields, decisionData?.decision_support, docId);

      if (!(blob instanceof Blob)) {
        console.warn("Backend didn't return a Blob for the report.");
        return;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KrishiIntel_Report_${docId || 'Invoice'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Report generation error:', err);
      setError('Failed to generate PDF report');
    }
  };

  const handleDownloadBatchReport = async () => {
    try {
      // Collect results that have fields
      const validResults = results.filter(r => r.success && r.fields);
      if (validResults.length === 0) {
        setError("No processed invoices to include in batch report.");
        return;
      }

      const invoices = validResults.map(r => ({
        fields: r.fields,
        decision_support: decisionDataMap[r.key]?.decision_support,
        doc_id: r.doc_id || r.key
      }));

      const blob = await generateBatchReportPDF(invoices);

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KrishiIntel_Batch_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Batch report generation error:', err);
      setError('Failed to generate batch PDF report');
    }
  };

  // Merged tabs — no separate Upload / Batch
  const appTabs = [
    { id: 'home', label: 'Home Page', icon: null },
    { id: 'processing', label: 'Invoice Processing', icon: UploadCloud },
    { id: 'portfolio', label: 'Portfolio Insights', icon: Briefcase },
  ];

  // Determine mode label
  const isBatchMode = previewImages.length > 1;
  const modeLabel = previewImages.length === 0
    ? null
    : isBatchMode
      ? `Batch Mode — ${previewImages.length} Files`
      : 'Single Invoice';

  return (
    <>
      {/* 1. TOP NAVBAR (GLASSMORPHISM) */}
      <nav className="sticky top-0 z-50 w-full glass-morphism border-b border-white/10 shadow-xl flex flex-col pt-4 pb-3 px-6">
        <div className="flex justify-between items-center w-full">
          {/* Logo & Product Name */}
          <div className="flex items-center gap-4 cursor-pointer group" onClick={() => setActiveTab('home')}>
            <div className="h-[40px] w-[40px] md:h-[48px] md:w-[48px] rounded-full bg-white/10 p-1 flex items-center justify-center border border-white/20 transition-transform group-hover:scale-105 overflow-hidden">
              <img src="/img/logo.png" alt="KrishiIntel AI" className="h-full w-full object-cover" />
            </div>
            <span className="text-xl md:text-2xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-agri-accent to-white drop-shadow-md hidden sm:block">KrishiIntel AI</span>
          </div>

          {/* Institutional Logos (Right Aligned) */}
          <div className="flex items-center gap-6 md:gap-10 bg-white/5 px-6 py-2.5 rounded-2xl backdrop-blur-md border border-white/10 shadow-inner">
            <img src="/img/kiit_logo.png" alt="KIIT" className="h-[28px] md:h-[36px] object-contain hidden sm:block hover:scale-105 transition-all" />
            <img src="/img/logo_SDIS.png" alt="SDIS" className="h-[28px] md:h-[36px] object-contain hover:scale-105 transition-all" />
            <img src="/img/usc_kiit.png" alt="USC KIIT" className="h-[28px] md:h-[36px] object-contain hidden lg:block hover:scale-105 transition-all" />
          </div>
        </div>

        {/* Dynamic App Tab Navigation — merged tabs */}
        {activeTab !== 'home' && (
          <div className="flex items-center gap-2 overflow-x-auto custom-scrollbar pb-1 pt-1 border-t border-white/5">
            {appTabs.slice(1).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 flex-shrink-0 ${activeTab === tab.id
                    ? 'bg-agri-dark text-agri-accent border border-agri-accent/50 shadow-[0_0_15px_rgba(46,204,113,0.3)]'
                    : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </nav>

      {/* 2. MAIN ROUTING RENDER */}
      <div className="min-h-screen relative z-10 font-sans text-gray-200">

        <AnimatePresence mode="wait">
          {/* LANDING PAGE ROUTE */}
          {activeTab === 'home' && (
            <motion.div
              key="home"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.4 }}
            >
              <LandingPage onStartAnalysis={() => setActiveTab('processing')} />
            </motion.div>
          )}

          {/* UNIFIED INVOICE PROCESSING */}
          {activeTab === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="max-w-7xl mx-auto space-y-5 px-4 sm:px-6 lg:px-8 py-6 pb-20 mt-4"
            >
              {/* Upload area */}
              <div className="border border-agri-accent/20 shadow-[0_0_40px_rgba(0,0,0,0.5)] rounded-2xl overflow-hidden glass-morphism-card bg-finance-dark/60">
                <FileUpload onFilesSelected={handleFilesSelected} disabled={processing} />

                {/* Mode badge */}
                {modeLabel && !processing && results.length === 0 && (
                  <div className="flex justify-center pb-4">
                    <motion.span
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold border ${
                        isBatchMode
                          ? 'bg-purple-500/10 border-purple-500/30 text-purple-300'
                          : 'bg-agri-accent/10 border-agri-accent/30 text-agri-accent'
                      }`}
                    >
                      {isBatchMode ? <Layers className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
                      {modeLabel}
                    </motion.span>
                  </div>
                )}
              </div>

              {/* Under The Hood — shown when idle (no files, no results, not processing) */}
              {previewImages.length === 0 && !processing && results.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  <UnderTheHood />
                </motion.div>
              )}

              {/* Image Previews with Resolution Sliders */}
              {previewImages.length > 0 && !processing && results.length === 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between glass-morphism-card px-6 py-4 border-l-4 border-l-agri-accent">
                    <h2 className="text-xl font-bold text-white flex items-center gap-3">
                      <ZoomIn className="w-5 h-5 text-agri-accent" />
                      Preview & Process {isBatchMode ? 'Batch' : 'Invoice'}
                    </h2>
                    <span className="text-sm font-bold text-agri-accent bg-agri-accent/10 px-4 py-1.5 rounded-full ring-1 ring-agri-accent/30">
                      {previewImages.length} {previewImages.length === 1 ? 'File' : 'Files'} Ready
                    </span>
                  </div>

                  <div
                    className={`grid gap-5 ${previewImages.length === 1
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
                    className="w-full bg-gradient-to-r from-agri-dark to-finance-dark border border-agri-accent/50 hover:from-agri-accent hover:to-green-500 text-white font-black py-4 px-8 rounded-2xl transition-all shadow-[0_0_30px_rgba(46,204,113,0.2)] hover:shadow-[0_0_40px_rgba(46,204,113,0.4)] hover:text-finance-dark flex items-center justify-center gap-3 text-lg tracking-wide uppercase group"
                  >
                    <Zap className="w-6 h-6 group-hover:scale-110 transition-transform text-agri-accent group-hover:text-finance-dark" />
                    <span>Start Intelligence Extraction</span>
                  </button>
                </div>
              )}

              {error && (
                <div className="bg-red-900/30 border border-red-500/50 rounded-2xl p-5 flex items-start gap-4 backdrop-blur-md">
                  <AlertCircle className="w-6 h-6 text-red-400 mt-1" />
                  <div>
                    <h3 className="text-red-200 font-bold mb-2">Processing Error</h3>
                    <p className="text-red-300/80">{error}</p>
                  </div>
                </div>
              )}

              {processing && (
                <div className="space-y-5">
                  <ProgressIndicator
                    total={progress.total}
                    completed={progress.completed}
                    current={progress.current}
                    results={results}
                  />
                  {processingIndex !== null && previewImages[processingIndex] && (
                    <div className="glass-morphism overflow-hidden border border-agri-accent/30 rounded-2xl">
                      <div className="bg-finance-dark/90 border-b border-agri-accent/20 px-6 py-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-3">
                          <Activity className="w-5 h-5 text-agri-accent animate-pulse" />
                          <span className="text-agri-accent text-sm font-mono mr-2 drop-shadow-[0_0_5px_#2ECC71]">[EXTRACTING]</span>
                          {previewImages[processingIndex].filename}
                        </h3>
                      </div>
                      <div className="relative bg-[#0B0F19]/80 p-6 flex justify-center items-center">
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

              {/* Results — with auto-scroll anchor */}
              {results.length > 0 && (
                <motion.div
                  ref={resultsRef}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-6 mt-6"
                >
                  <div className="flex flex-col sm:flex-row gap-4 sm:items-center justify-between glass-morphism-card px-6 py-4 border-l-4 border-l-agri-accent bg-dark-900/80">
                    <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-wide flex-1">
                      <FileText className="w-6 h-6 text-agri-accent" />
                      {isBatchMode ? 'Batch Intelligence Report' : 'Intelligence Report'}
                    </h2>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-agri-accent bg-agri-dark/40 border border-agri-accent/30 px-4 py-2 rounded-full shadow-[0_0_15px_rgba(46,204,113,0.2)] flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-agri-accent" />
                        {results.length} {results.length === 1 ? 'Record' : 'Records'} Processed
                      </span>
                      {isBatchMode && (
                        <button 
                          onClick={handleDownloadBatchReport}
                          className="bg-white text-finance-dark hover:bg-agri-accent border border-agri-accent/50 px-4 py-2 rounded-full font-bold text-sm shadow-[0_0_15px_rgba(255,255,255,0.2)] transition-colors flex items-center gap-2"
                        >
                          <Download className="w-4 h-4" /> Download Batch PDF
                        </button>
                      )}
                    </div>
                  </div>

                  {results.map((result, index) => {
                    const imageKey = result.key || `${result.originalFile}_${index}`;
                    const originalImage = imageDataMap[imageKey] || imageDataMap[Object.keys(imageDataMap)[index]];
                    const processedImage = result.processedImageData || originalImage;
                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                        className="space-y-5"
                      >
                        <ResultCard
                          result={result}
                          imageData={originalImage}
                          processedImageData={processedImage}
                          onReprocess={handleReprocess}
                          isProcessing={processingIndex === index}
                        />
                        {result.success && result.fields && (
                          <LoanSummaryCard
                            fields={result.fields}
                            decisionData={decisionDataMap[result.key]}
                            onRequestDecision={(fields) => handleRequestDecision(fields, result.key)}
                            onDownloadReport={(fields, decision) => handleDownloadReport(fields, decision, result.doc_id || result.key)}
                            isLoading={decisionLoadingMap[result.key]}
                          />
                        )}
                      </motion.div>
                    );
                  })}
                </motion.div>
              )}
            </motion.div>
          )}


          {/* PORTFOLIO STATS & CHAT */}
          {activeTab === 'portfolio' && (
            <motion.div
              key="portfolio"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="max-w-7xl mx-auto space-y-6 px-4 sm:px-6 lg:px-8 py-6 pb-20 mt-4"
            >
              <PortfolioStats stats={portfolioStats} isLoading={portfolioLoading} />
              <div className="mt-8">
                <PortfolioChat onSendQuery={handleChatQuery} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </>
  );
}

export default App;
