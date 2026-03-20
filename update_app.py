import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace Imports
imports_old = "import { FileText, AlertCircle, Cpu, BarChart3, Brain } from 'lucide-react';"
imports_new = "import { FileText, AlertCircle, Cpu, BarChart3, Brain, UploadCloud, Layers, Briefcase, ChevronRight, Activity, Zap } from 'lucide-react';"
code = code.replace(imports_old, imports_new)

if 'import Scene3D' in code:
    code = re.sub(r'import Scene3D from \'\./components/Scene3D\';\n', '', code)

# Replace Tabs and activeTab
tabs_old = """const TABS = [
  { id: 'invoice', label: 'Invoice Analysis', icon: FileText },
  { id: 'portfolio', label: 'Portfolio Intelligence', icon: Brain },
];

function App() {
  const [activeTab, setActiveTab] = useState('invoice');"""

tabs_new = """const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity },
  { id: 'upload', label: 'Invoice Upload', icon: UploadCloud },
  { id: 'batch', label: 'Batch Processing', icon: Layers },
  { id: 'analytics', label: 'Decision Support', icon: BarChart3 },
  { id: 'portfolio', label: 'Portfolio Insights', icon: Briefcase },
];

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');"""

code = code.replace(tabs_old, tabs_new)

# Replace Return block
return_start = code.find("  return (\n    <>")
if return_start == -1:
    print("Return block not found!")
    exit(1)

new_return = """  return (
    <>
      {/* 2. NAVBAR */}
      <nav className="sticky top-0 z-50 w-full glass-morphism border-b border-white/10 shadow-lg px-6 py-4 flex justify-between items-center mb-8">
        <div className="flex items-center gap-4 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <img src="/img/logo.png" alt="KrishiIntel AI" className="h-10 object-contain drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]" />
          <span className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-agri-accent to-white tracking-wide hidden sm:block">KrishiIntel AI</span>
        </div>
        <div className="hidden md:flex gap-2">
          {TABS.map((tab) => {
            if (tab.id === 'dashboard') return null; // hide dashboard from right tabs
            return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-agri-accent/20 text-agri-accent border border-agri-accent/50 shadow-[0_0_15px_rgba(46,204,113,0.3)]'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          )})}
        </div>
      </nav>

      <div className="min-h-screen px-4 sm:px-6 lg:px-8 relative z-10 font-sans text-gray-200 pb-20">
        <div className="max-w-7xl mx-auto">
          
          <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-16 mt-4"
              >
                {/* 3. HERO SECTION */}
                <div className="text-center py-16 px-4">
                  <h1 className="text-4xl md:text-6xl font-extrabold text-white mb-6 tracking-tight drop-shadow-md leading-tight">
                    AI-Powered Agricultural<br/><span className="text-agri-accent drop-shadow-[0_0_15px_rgba(46,204,113,0.4)]">Invoice Intelligence</span>
                  </h1>
                  <p className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto mb-10 font-medium">
                    Automating loan verification, asset validation, and portfolio analytics for modern agri-finance.
                  </p>
                  <button 
                    onClick={() => setActiveTab('upload')}
                    className="bg-gradient-to-r from-agri-accent to-green-500 hover:from-green-500 hover:to-green-400 text-finance-dark font-bold py-4 px-10 rounded-full text-lg shadow-[0_0_20px_rgba(46,204,113,0.5)] hover:shadow-[0_0_30px_rgba(46,204,113,0.8)] transition-all transform hover:scale-105 flex items-center gap-3 mx-auto"
                  >
                    Start Analysis <ChevronRight className="w-5 h-5 text-finance-dark font-bold" />
                  </button>
                </div>

                {/* 4. MAIN DASHBOARD */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {[
                    { id: 'upload', title: 'Invoice Upload', desc: 'Process single tractor invoices with AI validation', icon: UploadCloud, color: 'text-blue-400' },
                    { id: 'batch', title: 'Batch Processing', desc: 'Process multiple invoices simultaneously', icon: Layers, color: 'text-yellow-400' },
                    { id: 'analytics', title: 'Decision Support', desc: 'Smart AI EMI & Loan recommendation engine', icon: BarChart3, color: 'text-agri-accent' },
                    { id: 'portfolio', title: 'Portfolio Insights', desc: 'Aggregate stats & NLP database chat', icon: Briefcase, color: 'text-purple-400' }
                  ].map((card) => (
                    <div 
                      key={card.id}
                      onClick={() => setActiveTab(card.id)}
                      className="glass-morphism-card p-8 cursor-pointer hover:scale-105 transition-all duration-300 group hover:border-agri-accent/40 hover:shadow-[0_0_25px_rgba(46,204,113,0.15)] bg-finance-dark/50"
                    >
                      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 bg-white/5 border border-white/10 group-hover:border-[currentColor] transition-colors ${card.color}`}>
                        <card.icon className={`w-7 h-7 ${card.color} group-hover:animate-pulse`} />
                      </div>
                      <h3 className="text-xl font-bold text-white mb-3">{card.title}</h3>
                      <p className="text-sm text-gray-400 leading-relaxed font-medium">{card.desc}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {(activeTab === 'upload' || activeTab === 'batch') && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
                className="space-y-8"
              >
                <div className="border border-agri-accent/20 shadow-[0_0_40px_rgba(0,0,0,0.5)] rounded-2xl overflow-hidden glass-morphism-card bg-finance-dark/60">
                  <FileUpload onFilesSelected={handleFilesSelected} disabled={processing} />
                </div>

                {/* Image Previews with Resolution Sliders */}
                {previewImages.length > 0 && !processing && results.length === 0 && (
                  <div className="space-y-5">
                    <div className="flex items-center justify-between glass-morphism-card px-6 py-5 border-l-4 border-l-agri-accent">
                      <h2 className="text-xl font-bold text-white flex items-center gap-3">
                        <ZoomIn className="w-5 h-5 text-agri-accent" />
                        Preview &amp; Process {activeTab === 'batch' ? 'Batch' : 'Invoice'}
                      </h2>
                      <span className="text-sm font-bold text-agri-accent bg-agri-accent/10 px-4 py-1.5 rounded-full">
                        {previewImages.length} {previewImages.length === 1 ? 'File' : 'Files'} Ready
                      </span>
                    </div>

                    <div
                      className={`grid gap-6 ${
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
                      className="w-full bg-gradient-to-r from-agri-dark to-finance-dark border border-agri-accent/50 hover:from-agri-accent hover:to-green-500 text-white font-bold py-5 px-8 rounded-2xl transition-all shadow-[0_0_30px_rgba(46,204,113,0.2)] hover:shadow-[0_0_40px_rgba(46,204,113,0.4)] hover:text-finance-dark flex items-center justify-center gap-3 text-lg tracking-wide uppercase"
                    >
                      <Zap className="w-6 h-6" />
                      <span>Start Intelligence Extraction</span>
                    </button>
                  </div>
                )}

                {error && (
                  <div className="bg-red-900/30 border border-red-500/50 rounded-2xl p-6 flex items-start gap-4 backdrop-blur-md">
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
                      <div className="glass-morphism overflow-hidden border border-agri-accent/30">
                        <div className="bg-finance-dark/90 border-b border-agri-accent/20 px-6 py-4">
                           <h3 className="text-lg font-bold text-white flex items-center gap-3">
                            <Activity className="w-5 h-5 text-agri-accent animate-pulse" />
                            <span className="text-agri-accent text-sm font-mono mr-2">[EXTRACTING]</span>
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

                {results.length > 0 && (
                  <div className="space-y-8 mt-10">
                    <div className="flex items-center justify-between glass-morphism-card px-6 py-5 border-l-4 border-l-agri-accent">
                      <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <FileText className="w-6 h-6 text-agri-accent" />
                        Intelligence Report
                      </h2>
                      <span className="text-sm font-bold text-agri-accent bg-agri-accent/10 border border-agri-accent/30 px-4 py-2 rounded-full shadow-[0_0_10px_rgba(46,204,113,0.2)]">
                        {results.length} {results.length === 1 ? 'Record' : 'Records'} Processed
                      </span>
                    </div>

                    {results.map((result, index) => {
                      const imageKey = result.key || `${result.originalFile}_${index}`;
                      const originalImage = imageDataMap[imageKey] || imageDataMap[Object.keys(imageDataMap)[index]];
                      const processedImage = result.processedImageData || originalImage;
                      return (
                        <div key={index} className="space-y-6">
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
                              onDownloadReport={handleDownloadReport}
                              isLoading={decisionLoadingMap[result.key]}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'analytics' && (
               <motion.div
                key="analytics"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-20"
               >
                 <BarChart3 className="w-20 h-20 text-gray-500 mx-auto mb-6 opacity-30" />
                 <h2 className="text-2xl font-bold text-gray-300 mb-4">No Data for Decision Support</h2>
                 <p className="text-gray-500">Please process an invoice first to view Decision Support analytics.</p>
                 <button onClick={() => setActiveTab('upload')} className="mt-8 px-8 py-3 bg-finance-dark border border-gray-600 rounded-xl hover:bg-gray-800 transition-colors text-white font-bold tracking-wide shadow-lg">Go to Upload</button>
               </motion.div>
            )}

            {activeTab === 'portfolio' && (
              <motion.div
                key="portfolio"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-8 mt-4"
              >
                <PortfolioStats stats={portfolioStats} isLoading={portfolioLoading} />
                <PortfolioChat onSendQuery={handleChatQuery} />
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </div>
{/* Removed footer standardizing with the design system */}
    </>
  );
}

export default App;
"""

code = code[:return_start] + new_return
with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated App.jsx successfully")
