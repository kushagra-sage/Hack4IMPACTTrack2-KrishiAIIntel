import React from 'react';
import { motion } from 'framer-motion';
import { Target, Brain, Settings2, Database, LineChart } from 'lucide-react';

const STEPS = [
  {
    icon: Target,
    title: 'YOLO Detection',
    desc: 'Detects stamps & signatures for authenticity verification',
    color: 'from-red-500/20 to-orange-500/20',
    border: 'border-red-500/30',
    iconColor: 'text-red-400',
  },
  {
    icon: Brain,
    title: 'Qwen2.5-VL Extraction',
    desc: 'Extracts dealer, model, HP, and cost from invoice images',
    color: 'from-purple-500/20 to-indigo-500/20',
    border: 'border-purple-500/30',
    iconColor: 'text-purple-400',
  },
  {
    icon: Settings2,
    title: 'Data Normalization',
    desc: 'Validates and cleans fields against schema rules',
    color: 'from-blue-500/20 to-cyan-500/20',
    border: 'border-blue-500/30',
    iconColor: 'text-blue-400',
  },
  {
    icon: Database,
    title: 'RAG Indexing',
    desc: 'Embeds into FAISS vector store & SQLite for retrieval',
    color: 'from-emerald-500/20 to-green-500/20',
    border: 'border-emerald-500/30',
    iconColor: 'text-emerald-400',
  },
  {
    icon: LineChart,
    title: 'Decision Support',
    desc: 'Generates EMI options, risk score & loan recommendations',
    color: 'from-amber-500/20 to-yellow-500/20',
    border: 'border-amber-500/30',
    iconColor: 'text-amber-400',
  },
];

const UnderTheHood = () => {
  return (
    <div className="w-full mt-2">
      <div className="text-center mb-5">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-agri-accent mb-1.5">
          Under The Hood
        </p>
        <h3 className="text-lg font-bold text-white/90">
          What Happens After Upload
        </h3>
      </div>

      <div className="flex flex-wrap items-stretch justify-center gap-3">
        {STEPS.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            className={`relative flex flex-col items-center text-center p-4 rounded-xl border ${step.border} bg-gradient-to-br ${step.color} backdrop-blur-sm w-[calc(20%-0.75rem)] min-w-[150px] hover:scale-[1.03] transition-transform cursor-default`}
          >
            {/* Step number */}
            <div className="absolute -top-2 -left-2 w-5 h-5 rounded-full bg-finance-dark border border-white/20 flex items-center justify-center text-[9px] font-black text-white/70 z-10">
              {i + 1}
            </div>

            {/* Animated icon */}
            <motion.div
              animate={{ y: [0, -3, 0] }}
              transition={{ repeat: Infinity, duration: 2.5, delay: i * 0.3 }}
              className={`w-8 h-8 mb-2.5 ${step.iconColor}`}
            >
              <step.icon className="w-full h-full" />
            </motion.div>

            <h4 className="text-xs font-bold text-white mb-1 tracking-wide">
              {step.title}
            </h4>
            <p className="text-[10px] text-gray-400 leading-snug">
              {step.desc}
            </p>

            {/* Connector dot (between items) */}
            {i < STEPS.length - 1 && (
              <div className="hidden xl:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-20">
                <motion.div
                  animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.2 }}
                  className="w-2 h-2 rounded-full bg-agri-accent shadow-[0_0_8px_#2ECC71]"
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default UnderTheHood;
