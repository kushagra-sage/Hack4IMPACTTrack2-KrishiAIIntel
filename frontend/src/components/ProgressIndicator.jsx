import React from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import AIPipelineVisualization from './AIPipelineVisualization';
import { motion } from 'framer-motion';

const ProgressIndicator = ({ total, completed, current, results }) => {
  const progress = total > 0 ? (completed / total) * 100 : 0;
  const successCount = results.filter(r => r.success).length;
  const errorCount = results.filter(r => !r.success).length;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-morphism p-6 relative overflow-hidden group"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary-600/5 to-accent-600/5 pointer-events-none group-hover:from-primary-600/10 transition-colors duration-500" />
      
      <div className="relative z-10 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center text-glow">
            <Loader2 className="w-6 h-6 mr-3 text-primary-400 animate-spin" />
            Processing Documents
          </h3>
          <span className="text-sm font-medium px-3 py-1 bg-dark-800/80 rounded-full border border-primary-500/30 text-primary-300 shadow-[0_0_10px_rgba(14,165,233,0.2)]">
            {completed} / {total}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="relative pt-2">
          <div className="overflow-hidden h-2 text-xs flex rounded-full bg-dark-800 border border-dark-600">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="shadow-[0_0_10px_#0ea5e9] flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-primary-500 to-primary-400"
            />
          </div>
          <div className="mt-3 text-sm text-primary-200/80 font-medium text-right font-mono">
            {Math.round(progress)}% Complete
          </div>
        </div>

        {/* Current Processing */}
        {current && (
          <div className="bg-primary-900/20 border border-primary-500/30 rounded-xl p-4 shadow-[0_0_15px_rgba(14,165,233,0.1)]">
            <p className="text-sm text-primary-200 flex items-center">
              <Loader2 className="w-5 h-5 mr-3 animate-spin text-primary-400" />
              Currently processing: <span className="font-semibold ml-2 text-white">{current}</span>
            </p>
          </div>
        )}

        {/* Dynamic AI Pipeline Visualization */}
        {current && <AIPipelineVisualization isProcessing={true} />}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-dark-600/50">
          <div className="text-center bg-dark-800/40 rounded-xl p-3 border border-dark-600 hover:border-primary-500/30 transition-colors">
            <div className="text-3xl font-bold text-white mb-1">{total}</div>
            <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Total</div>
          </div>
          <div className="text-center bg-dark-800/40 rounded-xl p-3 border border-dark-600 hover:border-green-500/30 transition-colors">
            <div className="text-3xl font-bold text-green-400 flex items-center justify-center mb-1 text-glow">
              {successCount}
              {successCount > 0 && <CheckCircle className="w-5 h-5 ml-2 text-green-400" />}
            </div>
            <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Success</div>
          </div>
          <div className="text-center bg-dark-800/40 rounded-xl p-3 border border-dark-600 hover:border-red-500/30 transition-colors">
            <div className="text-3xl font-bold text-red-400 flex items-center justify-center mb-1">
              {errorCount}
              {errorCount > 0 && <XCircle className="w-5 h-5 ml-2 text-red-500" />}
            </div>
            <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Errors</div>
          </div>
        </div>

        {/* Results List */}
        {results.length > 0 && (
          <div className="pt-2 mt-2">
            <h4 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wider">Processing Log</h4>
            <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
              {results.map((result, index) => (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    result.success 
                      ? 'bg-green-900/10 border-green-500/20 text-green-100' 
                      : 'bg-red-900/10 border-red-500/20 text-red-100'
                  }`}
                >
                  <span className="text-sm truncate flex-1 font-medium">
                    {result.filename}
                  </span>
                  {result.success ? (
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 ml-3" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 ml-3" />
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ProgressIndicator;

