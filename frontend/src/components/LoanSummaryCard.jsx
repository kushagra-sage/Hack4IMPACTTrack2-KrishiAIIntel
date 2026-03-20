import React, { useState } from 'react';
import { TrendingUp, IndianRupee, Shield, Star, ChevronDown, ChevronUp, Download, PlusCircle, Calculator, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LoanSummaryCard = ({ fields, decisionData, onRequestDecision, onDownloadReport, isLoading }) => {
  const [expanded, setExpanded] = useState(true);
  const [emiMode, setEmiMode] = useState('smart'); // 'smart' or 'manual'

  // Manual EMI State
  const [manualInterest, setManualInterest] = useState(12); // 12%
  const [manualTenure, setManualTenure] = useState(5); // 5 years
  const [manualDownpayment, setManualDownpayment] = useState(20); // 20%

  if (!fields) return null;

  const hasDecision = decisionData && decisionData.decision_support;
  const ds = hasDecision ? decisionData.decision_support : null;

  const formatCurrency = (val) => {
    if (val == null) return '—';
    return '₹' + Number(val).toLocaleString('en-IN');
  };

  const calculateManualEMI = () => {
    const cost = fields.asset_cost || 0;
    const principal = cost - (cost * (manualDownpayment / 100));
    if (principal <= 0) return 0;
    const r = manualInterest / 12 / 100;
    const n = manualTenure * 12;
    if (r === 0) return principal / n;
    return (principal * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
  };

  const getEligibilityColor = (status) => {
    if (!status) return { bg: 'bg-finance-dark', text: 'text-gray-400', border: 'border-finance-dark', glow: '' };
    const s = status.toLowerCase();
    if (s.includes('high'))
      return { bg: 'bg-green-900/30', text: 'text-green-400', border: 'border-green-500/40', glow: 'shadow-[0_0_15px_rgba(46,204,113,0.2)]' };
    if (s.includes('moderate'))
      return { bg: 'bg-yellow-900/30', text: 'text-yellow-400', border: 'border-yellow-500/40', glow: 'shadow-[0_0_15px_rgba(250,204,21,0.2)]' };
    return { bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-500/40', glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)]' };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="mt-8 space-y-6"
    >
      {/* STRUCTURED EXTRACTION CARD */}
      <div className="bg-finance-dark/80 rounded-2xl border border-agri-accent/20 overflow-hidden backdrop-blur-md shadow-lg">
        <div className="px-6 py-4 bg-gradient-to-r from-agri-dark/40 to-finance-dark border-b border-agri-accent/20">
          <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Shield className="w-5 h-5 text-agri-accent" />
            Verified Invoice Details
          </h4>
        </div>
        <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-dark-900/40 p-4 rounded-xl border border-dark-600">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Dealer Name</div>
            <div className="text-sm font-semibold text-gray-200 truncate" title={fields.dealer_name}>{fields.dealer_name || 'Not Found'}</div>
          </div>
          <div className="bg-dark-900/40 p-4 rounded-xl border border-dark-600">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Tractor Model</div>
            <div className="text-sm font-semibold text-agri-accent truncate" title={fields.model_name}>{fields.model_name || 'Not Found'}</div>
          </div>
          <div className="bg-dark-900/40 p-4 rounded-xl border border-dark-600">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Horse Power</div>
            <div className="text-sm font-mono font-semibold text-gray-300">{fields.horse_power ? `${fields.horse_power} HP` : '—'}</div>
          </div>
          <div className="bg-dark-900/40 p-4 rounded-xl border border-dark-600">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Asset Cost</div>
            <div className="text-lg font-mono font-bold text-white tracking-tight">{formatCurrency(fields.asset_cost)}</div>
          </div>
        </div>

        {/* ACTION BUTTONS */}
        <div className="px-6 py-4 bg-dark-900/60 border-t border-dark-600 flex gap-4">
          <button
            onClick={() => onDownloadReport && onDownloadReport(fields, decisionData)}
            className="flex-1 bg-finance-dark border border-agri-accent/40 hover:bg-agri-accent/10 px-4 py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-bold text-white transition-all transform hover:scale-[1.02]"
          >
            <Download className="w-4 h-4 text-agri-accent" />
            Download PDF
          </button>
          <button
            onClick={() => alert('Invoice successfully added to your portfolio!')}
            className="flex-1 bg-gradient-to-r from-agri-dark to-agri-accent hover:from-agri-accent hover:to-green-500 shadow-[0_0_15px_rgba(46,204,113,0.3)] px-4 py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-bold text-finance-dark transition-all transform hover:scale-[1.02]"
          >
            <PlusCircle className="w-4 h-4" />
            Add to Portfolio
          </button>
        </div>
      </div>

      {/* DECISION SUPPORT CARD */}
      <div className="bg-gradient-to-br from-finance-dark/90 to-[#0B0F19]/90 rounded-2xl border border-agri-accent/20 overflow-hidden backdrop-blur-md">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-6 py-5 flex items-center justify-between bg-gradient-to-r from-agri-dark/30 to-[#0B0F19]/20 hover:from-agri-dark/40 transition-all border-b border-white/5"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-agri-accent/10 rounded-xl border border-agri-accent/20">
              <TrendingUp className="w-5 h-5 text-agri-accent drop-shadow-[0_0_8px_#2ECC71]" />
            </div>
            <div className="text-left">
              <h4 className="text-base font-extrabold text-white uppercase tracking-wider">Smart Loan Decision Support</h4>
              <p className="text-xs text-green-400 font-medium tracking-wide mt-1">AI-powered eligibility & EMI analysis</p>
            </div>
          </div>
          {expanded ? <ChevronUp className="w-6 h-6 text-agri-accent" /> : <ChevronDown className="w-6 h-6 text-agri-accent" />}
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="p-6 space-y-6">
                {!hasDecision && (
                  <button
                    onClick={() => onRequestDecision && onRequestDecision(fields)}
                    disabled={isLoading || !fields.asset_cost}
                    className="w-full py-4 px-6 bg-gradient-to-r from-agri-dark to-agri-accent hover:from-agri-accent hover:to-green-500 text-finance-dark font-extrabold tracking-wide uppercase rounded-xl transition-all disabled:opacity-40 flex items-center justify-center gap-3 shadow-[0_0_20px_rgba(46,204,113,0.3)] transform hover:scale-[1.01]"
                  >
                    {isLoading ? (
                      <>
                        <svg className="w-5 h-5 animate-spin text-finance-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Analyzing Risk & Eligibility...
                      </>
                    ) : (
                      <>
                        <Brain className="w-6 h-6" />
                        Generate AI Loan Analysis
                      </>
                    )}
                  </button>
                )}

                {hasDecision && (
                  <>
                    <div className="bg-dark-900/60 p-1 rounded-xl flex w-full max-w-sm mx-auto border border-dark-600 shadow-inner mb-6">
                      <button
                        onClick={() => setEmiMode('smart')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold uppercase tracking-wider rounded-lg transition-all ${emiMode === 'smart' ? 'bg-agri-accent text-finance-dark shadow-md' : 'text-gray-400 hover:text-white'}`}
                      >
                        <Brain className="w-4 h-4" /> Smart AI Mode
                      </button>
                      <button
                        onClick={() => setEmiMode('manual')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold uppercase tracking-wider rounded-lg transition-all ${emiMode === 'manual' ? 'bg-finance-dark border border-agri-accent/40 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
                      >
                        <Calculator className="w-4 h-4" /> Manual Mode
                      </button>
                    </div>

                    {emiMode === 'smart' ? (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                        <div className="bg-agri-accent/5 border border-agri-accent/20 rounded-xl p-4 text-sm text-green-300 font-medium tracking-wide flex items-center gap-3">
                          <Brain className="w-5 h-5 text-agri-accent" />
                          Based on agricultural lending standards and asset depreciation profiles.
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {Object.entries(ds.emi_options || {}).map(([key, emi]) => {
                            const isRecommended = key === ds.recommended_plan;
                            let label = key.replace('_', ' ').replace('years', 'Years');
                            if (label === '3 Years') label = '36 Months';
                            if (label === '5 Years') label = '60 Months';
                            if (label === '7 Years') label = '84 Months';

                            return (
                              <div
                                key={key}
                                className={`relative rounded-xl p-6 text-center transition-all duration-300 ${isRecommended
                                  ? 'bg-agri-dark/30 border-2 border-agri-accent/80 shadow-[0_0_25px_rgba(46,204,113,0.2)] transform scale-[1.02] z-10'
                                  : 'bg-finance-dark/80 border border-dark-600 hover:border-agri-accent/30 hover:scale-[1.01]'
                                  }`}
                              >
                                {isRecommended && (
                                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-agri-accent text-finance-dark text-xs font-extrabold px-4 py-1 rounded-full uppercase tracking-widest flex items-center gap-1.5 shadow-[0_0_15px_rgba(46,204,113,0.5)]">
                                    <Star className="w-3.5 h-3.5" />
                                    AI Recommended
                                  </div>
                                )}
                                <div className={`text-xs uppercase tracking-widest font-extrabold ${isRecommended ? 'text-green-400' : 'text-gray-400'} mb-3 mt-2`}>
                                  {label} Tenure
                                </div>
                                <div className={`text-3xl font-bold font-mono tracking-tight ${isRecommended ? 'text-white' : 'text-gray-200'}`}>
                                  {formatCurrency(Math.round(emi))}
                                </div>
                                <div className="text-[10px] text-gray-500 mt-2 uppercase tracking-widest font-semibold">per month</div>
                              </div>
                            );
                          })}
                        </div>
                      </motion.div>
                    ) : (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-dark-900/50 border border-dark-600 rounded-xl p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <div className="space-y-6">
                            <div>
                              <div className="flex justify-between text-sm font-bold text-gray-300 mb-2">
                                <span>Interest Rate (p.a.)</span>
                                <span className="text-agri-accent">{manualInterest}%</span>
                              </div>
                              <input type="range" min="5" max="25" step="0.5" value={manualInterest} onChange={(e) => setManualInterest(parseFloat(e.target.value))} className="w-full slider" />
                            </div>
                            <div>
                              <div className="flex justify-between text-sm font-bold text-gray-300 mb-2">
                                <span>Tenure (Years)</span>
                                <span className="text-agri-accent">{manualTenure} Years</span>
                              </div>
                              <input type="range" min="1" max="10" step="1" value={manualTenure} onChange={(e) => setManualTenure(parseFloat(e.target.value))} className="w-full slider" />
                            </div>
                            <div>
                              <div className="flex justify-between text-sm font-bold text-gray-300 mb-2">
                                <span>Down Payment</span>
                                <span className="text-agri-accent">{manualDownpayment}%</span>
                              </div>
                              <input type="range" min="0" max="60" step="5" value={manualDownpayment} onChange={(e) => setManualDownpayment(parseFloat(e.target.value))} className="w-full slider" />
                            </div>
                          </div>
                          <div className="flex flex-col items-center justify-center bg-finance-dark/80 border border-agri-accent/20 rounded-2xl p-6 shadow-inner">
                            <div className="text-sm uppercase tracking-widest font-bold text-gray-400 mb-2">Calculated EMI</div>
                            <div className="text-4xl font-mono font-extrabold text-white text-glow tracking-tighter mb-2">{formatCurrency(Math.round(calculateManualEMI()))}</div>
                            <div className="text-xs text-agri-accent uppercase tracking-widest font-semibold">Per Month</div>
                            <div className="mt-4 pt-4 border-t border-dark-600 w-full text-center text-xs text-gray-400">
                              Loan Amount: <span className="text-white font-mono">{formatCurrency(fields.asset_cost - (fields.asset_cost * (manualDownpayment / 100)))}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {ds.eligibility && (() => {
                      const colors = getEligibilityColor(ds.eligibility);
                      return (
                        <div className={`mt-6 rounded-xl p-5 ${colors.bg} border ${colors.border} ${colors.glow}`}>
                          <div className="flex items-center gap-3 mb-2">
                            <Shield className={`w-6 h-6 ${colors.text}`} />
                            <span className={`text-base font-extrabold ${colors.text} uppercase tracking-wider`}>
                              {ds.eligibility}
                            </span>
                          </div>
                          {ds.reason && (
                            <p className="text-sm text-gray-300 leading-relaxed pl-9 font-medium">
                              {ds.reason}
                            </p>
                          )}
                        </div>
                      );
                    })()}
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default LoanSummaryCard;
