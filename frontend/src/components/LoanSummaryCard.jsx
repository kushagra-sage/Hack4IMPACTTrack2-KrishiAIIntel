import React, { useState } from 'react';
import { TrendingUp, IndianRupee, Shield, Star, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LoanSummaryCard = ({ fields, decisionData, onRequestDecision, onDownloadReport, isLoading }) => {
  const [expanded, setExpanded] = useState(true);

  // If we have no data and no way to request it, don't render
  if (!fields || (!fields.asset_cost && !decisionData)) return null;

  const hasDecision = decisionData && decisionData.decision_support;
  const ds = hasDecision ? decisionData.decision_support : null;

  const formatCurrency = (val) => {
    if (val == null) return '—';
    return '₹' + Number(val).toLocaleString('en-IN');
  };

  const getEligibilityColor = (status) => {
    if (!status) return { bg: 'bg-gray-800', text: 'text-gray-400', border: 'border-gray-600', glow: '' };
    const s = status.toLowerCase();
    if (s.includes('high'))
      return { bg: 'bg-emerald-900/30', text: 'text-emerald-400', border: 'border-emerald-500/40', glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]' };
    if (s.includes('moderate'))
      return { bg: 'bg-amber-900/30', text: 'text-amber-400', border: 'border-amber-500/40', glow: 'shadow-[0_0_15px_rgba(245,158,11,0.2)]' };
    return { bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-500/40', glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)]' };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="mt-5"
    >
      <div className="bg-gradient-to-br from-dark-800/90 to-dark-900/90 rounded-2xl border border-primary-500/20 overflow-hidden backdrop-blur-md">
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-primary-900/30 to-accent-900/20 hover:from-primary-900/40 hover:to-accent-900/30 transition-all"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-500/20 rounded-xl border border-primary-500/30">
              <TrendingUp className="w-5 h-5 text-primary-400" />
            </div>
            <div className="text-left">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Loan Decision Support</h4>
              <p className="text-[11px] text-primary-300/70 mt-0.5">AI-powered financial analysis</p>
            </div>
          </div>
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-primary-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-primary-400" />
          )}
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="p-6 space-y-5">
                {/* Request button if no data yet */}
                {!hasDecision && (
                  <button
                    onClick={() => onRequestDecision && onRequestDecision(fields)}
                    disabled={isLoading || !fields.asset_cost}
                    className="w-full py-3 px-6 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white font-bold rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(14,165,233,0.3)]"
                  >
                    {isLoading ? (
                      <>
                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="w-5 h-5" />
                        Generate Loan Analysis
                      </>
                    )}
                  </button>
                )}

                {/* EMI Cards */}
                {hasDecision && (
                  <>
                    <div className="grid grid-cols-3 gap-3">
                      {Object.entries(ds.emi_options || {}).map(([key, emi]) => {
                        const isRecommended = key === ds.recommended_plan;
                        const label = key.replace('_', ' ').replace('years', 'Years');
                        return (
                          <div
                            key={key}
                            className={`relative rounded-xl p-4 text-center transition-all ${
                              isRecommended
                                ? 'bg-primary-900/40 border-2 border-primary-400/60 shadow-[0_0_25px_rgba(14,165,233,0.3)]'
                                : 'bg-dark-800/80 border border-dark-600 hover:border-primary-500/30'
                            }`}
                          >
                            {isRecommended && (
                              <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-primary-500 text-white text-[9px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-widest flex items-center gap-1 shadow-[0_0_10px_rgba(14,165,233,0.5)]">
                                <Star className="w-2.5 h-2.5" />
                                Recommended
                              </div>
                            )}
                            <div className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 mb-2 mt-1">
                              {label}
                            </div>
                            <div className={`text-xl font-bold font-mono ${isRecommended ? 'text-primary-300' : 'text-gray-200'}`}>
                              {formatCurrency(Math.round(emi))}
                            </div>
                            <div className="text-[10px] text-gray-500 mt-1">per month</div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Eligibility Badge */}
                    {ds.eligibility && (() => {
                      const colors = getEligibilityColor(ds.eligibility);
                      return (
                        <div className={`rounded-xl p-4 ${colors.bg} border ${colors.border} ${colors.glow}`}>
                          <div className="flex items-center gap-3 mb-2">
                            <Shield className={`w-5 h-5 ${colors.text}`} />
                            <span className={`text-sm font-bold ${colors.text} uppercase tracking-wider`}>
                              {ds.eligibility}
                            </span>
                          </div>
                          {ds.reason && (
                            <p className="text-xs text-gray-400 leading-relaxed pl-8">
                              {ds.reason}
                            </p>
                          )}
                        </div>
                      );
                    })()}

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-[10px] text-gray-500 px-1 font-mono">
                      <span>Rate: {ds.annual_interest_rate}% p.a.</span>
                      <span>Asset: {formatCurrency(ds.asset_cost)}</span>
                      {ds.horse_power && <span>HP: {ds.horse_power}</span>}
                    </div>

                    {/* Download Report Button */}
                    <button
                      onClick={() => onDownloadReport && onDownloadReport(fields, decisionData)}
                      className="w-full mt-2 py-2.5 px-5 bg-dark-800/80 border border-primary-500/30 hover:border-primary-400/50 text-primary-300 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 text-sm hover:bg-primary-900/30 hover:shadow-[0_0_15px_rgba(14,165,233,0.15)]"
                    >
                      <Download className="w-4 h-4" />
                      Download Report
                    </button>
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
