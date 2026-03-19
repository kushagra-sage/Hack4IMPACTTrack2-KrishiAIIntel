import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileSearch, Target, BrainCircuit, FileOutput, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';

const PIPELINE_STEPS = [
  { id: 1, label: 'Scanning Document Layout', icon: FileSearch, desc: 'Analyzing structure & OCR' },
  { id: 2, label: 'Running Object Detection', icon: Target, desc: 'Detecting Signature & Stamp (YOLO)' },
  { id: 3, label: 'Vision Language Model', icon: BrainCircuit, desc: 'Processing with Qwen2.5-VL' },
  { id: 4, label: 'Extracting Data', icon: FileOutput, desc: 'Structuring fields into JSON' }
];

const AIPipelineVisualization = ({ isProcessing }) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    let interval;
    if (isProcessing) {
      interval = setInterval(() => {
        setActiveStep((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : 0));
      }, 2500); // 2.5 seconds per step
    } else {
      setActiveStep(0);
    }
    return () => clearInterval(interval);
  }, [isProcessing]);

  if (!isProcessing) return null;

  return (
    <div className="w-full py-8 mt-4 bg-dark-800/50 rounded-2xl border border-primary-500/20 shadow-[0_0_30px_rgba(14,165,233,0.1)] relative overflow-hidden backdrop-blur-md">
      {/* Background Neural Particle Effect Base */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary-900/40 via-dark-900/10 to-transparent" />
      
      <div className="relative z-10 px-6">
        <h3 className="text-center text-lg font-medium text-primary-200 mb-8 tracking-wide uppercase text-glow">
          AI Processing Pipeline Active
        </h3>
        
        <div className="flex flex-col md:flex-row items-center justify-between max-w-4xl mx-auto relative">
          {/* Animated Connecting Line */}
          <div className="hidden md:block absolute top-[28px] left-[50px] right-[50px] h-[2px] bg-dark-700 z-0">
            <motion.div 
              className="h-full bg-gradient-to-r from-primary-600 via-primary-400 to-accent-400 shadow-[0_0_10px_#0ea5e9]"
              initial={{ width: "0%" }}
              animate={{ width: `${(activeStep / (PIPELINE_STEPS.length - 1)) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            />
          </div>

          {PIPELINE_STEPS.map((step, index) => {
            const isActive = index === activeStep;
            const isCompleted = index < activeStep;
            const Icon = isCompleted ? CheckCircle2 : step.icon;

            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center mb-6 md:mb-0 w-full md:w-1/4">
                {/* Node */}
                <motion.div
                  className={clsx(
                    "w-14 h-14 rounded-full flex items-center justify-center border-2 backdrop-blur-md transition-all duration-300",
                    isActive ? "bg-primary-500/20 border-primary-400 text-primary-300 shadow-[0_0_20px_rgba(14,165,233,0.6)]" : 
                    isCompleted ? "bg-accent-500/20 border-accent-500 text-accent-400" : "bg-dark-800 border-dark-600 text-gray-500"
                  )}
                  animate={isActive ? { scale: [1, 1.1, 1] } : { scale: 1 }}
                  transition={{ repeat: isActive ? Infinity : 0, duration: 2 }}
                >
                  <Icon className={clsx("w-6 h-6", isActive && "animate-pulse")} />
                </motion.div>
                
                {/* Labels */}
                <div className="mt-4 text-center">
                  <h4 className={clsx(
                    "text-sm font-semibold transition-colors duration-300",
                    isActive ? "text-primary-300" : isCompleted ? "text-accent-300" : "text-gray-500"
                  )}>
                    {step.label}
                  </h4>
                  <p className="text-xs text-gray-400 mt-1 max-w-[120px] mx-auto opacity-80">
                    {step.desc}
                  </p>
                </div>
                
                {isActive && (
                  <motion.div 
                    className="absolute -bottom-6 w-1 h-1 rounded-full bg-primary-400 shadow-[0_0_8px_#38bdf8]"
                    animate={{ y: [0, 5, 0], opacity: [0.5, 1, 0.5] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AIPipelineVisualization;
