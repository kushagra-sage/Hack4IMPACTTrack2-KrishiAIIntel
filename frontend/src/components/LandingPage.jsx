import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ChevronRight, 
  Activity, 
  ShieldCheck, 
  Zap, 
  FileSearch, 
  Globe, 
  Building2, 
  Landmark, 
  Target,
  Database,
  Cpu,
  LineChart,
  Bot,
  Brain
} from 'lucide-react';

const LandingPage = ({ onStartAnalysis }) => {
  return (
    <div className="min-h-screen text-white font-sans overflow-x-hidden relative">
      {/* Decorative Background Elements */}
      <div className="absolute top-0 left-0 w-full h-[600px] bg-gradient-to-b from-agri-dark/40 to-transparent pointer-events-none z-0" />
      <div className="absolute -top-[300px] right-[10%] w-[600px] h-[600px] bg-agri-accent/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-[800px] -left-[200px] w-[500px] h-[500px] bg-finance-dark/80 rounded-full blur-[100px] pointer-events-none z-0" />

      {/* 1. HERO SECTION */}
      <section className="relative z-10 pt-20 pb-16 px-6 max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-12 min-h-[80vh] justify-center">
        <motion.div 
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="flex-1 space-y-6"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-agri-accent/10 border border-agri-accent/30 text-agri-accent text-[11px] font-black uppercase tracking-[0.2em] shadow-[0_0_15px_rgba(46,204,113,0.1)]">
            <span className="w-1.5 h-1.5 rounded-full bg-agri-accent animate-pulse" />
            Enterprise Grade AI
          </div>
          
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-black leading-[1.1] tracking-tight drop-shadow-2xl">
            AI-Powered Agricultural <br />
            <span className="relative">
              <span className="absolute -inset-2 bg-gradient-to-r from-agri-accent/30 to-green-500/0 blur-xl opacity-70" />
              <span className="relative text-transparent bg-clip-text bg-gradient-to-r from-agri-accent to-white">Invoice Intelligence</span>
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 font-medium max-w-xl leading-relaxed mt-4">
            Transforming tractor invoice processing into real-time financial intelligence for faster, smarter agricultural lending.
          </p>

          {/* Key Metrics */}
          <div className="flex flex-wrap gap-3 pt-4">
            {[
              { val: "95%", label: "Extraction Accuracy", color: "text-agri-accent" },
              { val: "4-8s", label: "Processing Time", color: "text-white" },
              { val: "500+", label: "Invoices Analyzed", color: "text-green-400" }
            ].map((m, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 backdrop-blur-xl shadow-xl hover:border-agri-accent/30 transition-all group">
                 <div className={`${m.color} font-black text-xl tracking-tighter group-hover:scale-110 transition-transform`}>{m.val}</div>
                 <div className="text-[9px] text-gray-500 uppercase font-black tracking-widest mt-0.5">{m.label}</div>
              </div>
            ))}
          </div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }} className="inline-block pt-6">
            <button 
              onClick={() => document.getElementById('architecture').scrollIntoView({ behavior: 'smooth' })}
              className="px-10 py-4.5 bg-white text-finance-dark hover:bg-agri-accent rounded-full font-black text-lg tracking-wider shadow-[0_10px_30px_rgba(255,255,255,0.1)] hover:shadow-[0_15px_40px_rgba(46,204,113,0.4)] transition-all flex items-center gap-3 group relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-agri-accent/0 via-agri-accent/20 to-agri-accent/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              Explore System <ChevronRight className="w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
            </button>
          </motion.div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="flex-1 relative w-full max-w-lg hidden md:block"
        >
           <div className="absolute inset-0 bg-gradient-to-r from-agri-accent to-green-400 rounded-3xl blur-[80px] opacity-20 animate-pulse" />
           <div className="relative bg-finance-dark/90 border border-white/10 rounded-3xl p-6 shadow-2xl backdrop-blur-xl transform -rotate-2 hover:rotate-0 transition-all duration-700">
             {/* Fake UI Preview Header */}
             <div className="flex gap-2 mb-6 border-b border-white/10 pb-4">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
             </div>
             {/* Fake Scanning Line */}
             <div className="relative bg-dark-900/50 rounded-xl border border-white/5 h-64 overflow-hidden mb-6 flex items-center justify-center">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(46,204,113,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(46,204,113,0.1)_1px,transparent_1px)] bg-[size:20px_20px] opacity-30" />
                <FileSearch className="w-20 h-20 text-agri-accent/50" />
                <motion.div 
                  initial={{ top: '-10%' }}
                  animate={{ top: '110%' }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="absolute left-0 w-full h-1 bg-agri-accent shadow-[0_0_20px_#2ECC71]"
                />
             </div>
             <div className="space-y-3">
               <div className="h-4 bg-white/10 rounded-full w-3/4" />
               <div className="h-4 bg-white/10 rounded-full w-1/2" />
               <div className="h-4 bg-white/10 rounded-full w-5/6" />
             </div>
           </div>
        </motion.div>
      </section>

      {/* 2. SYSTEM ARCHITECTURE SECTION */}
      <section id="architecture" className="relative z-10 py-16 bg-dark-900/30 border-y border-white/5">
         <div className="max-w-7xl mx-auto px-6">
           <div className="text-center mb-12">
             <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-agri-accent mb-3">Under The Hood</h2>
             <h3 className="text-2xl md:text-4xl font-extrabold text-white">System Architecture Pipeline</h3>
           </div>

            <div className="flex flex-wrap items-stretch justify-center gap-4 relative">
               {/* Architecture Nodes */}
               {[
                 { icon: Globe, title: "Invoice Image", desc: "Raw visual input capture", tooltip: "Direct document ingestion from files or mobile capture." },
                 { icon: Target, title: "YOLO Detection", desc: "Signature & Stamp isolation", tooltip: "YOLO detects signatures and stamps to verify document authenticity." },
                 { icon: Brain, title: "Qwen2.5-VL Extraction", desc: "Financial field scraping", tooltip: "Qwen extracts structured fields like Dealer, Model, HP, and Cost." },
                 { icon: ShieldCheck, title: "Normalization", desc: "Schema validation", tooltip: "Cleans data via normalization layer for strict database schema adherence." },
                 { icon: Database, title: "RAG Engine", desc: "FAISS + SQLite Database", tooltip: "Embeds history to FAISS and saves records to SQLite for fast retrieval." },
                 { icon: LineChart, title: "Decision Support", desc: "EMI & Risk Analytics", tooltip: "Real-time AI computes loan eligibility and multiple EMI options." }
               ].map((node, i) => (
                  <React.Fragment key={i}>
                    <motion.div 
                      whileHover={{ scale: 1.05, y: -4 }}
                      initial={{ opacity: 0, y: 20 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: i * 0.08 }}
                      className="relative group bg-finance-dark border border-agri-accent/30 rounded-2xl p-5 w-[calc(33.333%-1rem)] min-w-[140px] max-w-[180px] text-center shadow-[0_0_15px_rgba(0,0,0,0.5)] z-10 cursor-help"
                    >
                      <div className="absolute inset-0 bg-agri-accent/0 group-hover:bg-agri-accent/10 transition-colors rounded-2xl" />
                      <div className="absolute -top-2 -left-2 w-6 h-6 rounded-full bg-agri-dark border border-agri-accent/50 flex items-center justify-center text-[10px] font-black text-agri-accent z-20">{i + 1}</div>
                      <node.icon className="w-9 h-9 mx-auto mb-3 text-agri-accent drop-shadow-[0_0_8px_#2ECC71]" />
                      <h4 className="font-bold text-xs tracking-wide text-white mb-1.5">{node.title}</h4>
                      <p className="text-[9px] text-gray-400 uppercase tracking-widest leading-tight">{node.desc}</p>
                      
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-44 p-2.5 bg-white text-finance-dark text-[11px] font-semibold rounded-lg shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                        {node.tooltip}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 border-6 border-transparent border-t-white" />
                      </div>
                    </motion.div>
                  </React.Fragment>
               ))}
            </div>
         </div>
      </section>

      {/* 3. IMPACT SECTION */}
      <section className="relative z-10 py-16 max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-3">Why It Matters</h2>
          <h3 className="text-2xl md:text-4xl font-extrabold text-white">Transforming Agricultural Finance</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { title: "Faster Loan Approvals", icon: Zap, desc: "Cut processing time from days to seconds with instant invoice verification." },
            { title: "Reduced Manual Errors", icon: ShieldCheck, desc: "Eliminate human data-entry mistakes through precise Qwen2.5-VL extraction." },
            { title: "Financial Inclusion", icon: Globe, desc: "Enable faster capital deployment in rural and marginalized agricultural sectors." },
            { title: "Data-Driven Lending", icon: LineChart, desc: "Smart AI models calculate risk profiles based on exact tractor make and horsepower." }
          ].map((item, i) => (
             <motion.div 
               key={i}
               initial={{ opacity: 0, y: 20 }}
               whileInView={{ opacity: 1, y: 0 }}
               viewport={{ once: true }}
               transition={{ duration: 0.5, delay: i * 0.1 }}
               whileHover={{ scale: 1.03 }}
               className="bg-dark-800/50 backdrop-blur-sm border border-white/10 rounded-2xl p-8 shadow-xl hover:border-agri-accent/50 hover:shadow-[0_0_30px_rgba(46,204,113,0.1)] transition-all"
             >
                <div className="w-12 h-12 rounded-xl bg-agri-dark/40 border border-agri-accent/30 flex items-center justify-center mb-6">
                  <item.icon className="w-6 h-6 text-agri-accent" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">{item.title}</h4>
                <p className="text-sm text-gray-400 font-medium leading-relaxed">{item.desc}</p>
             </motion.div>
          ))}
        </div>
      </section>

      {/* 4. BUILT FOR (USE CASES) */}
      <section className="relative z-10 py-16 bg-gradient-to-r from-agri-dark/20 to-finance-dark/40 border-y border-white/5">
         <div className="max-w-7xl mx-auto px-6">
            <h3 className="text-center text-sm font-black uppercase tracking-[0.2em] text-white opacity-60 mb-10">Trusted By & Built For</h3>
            <div className="flex flex-wrap justify-center gap-8 md:gap-16">
              {[
                { label: "Banks", icon: Landmark },
                { label: "NBFCs", icon: Building2 },
                { label: "Rural Lending Systems", icon: Globe },
                { label: "Government Schemes", icon: ShieldCheck }
              ].map((uc, i) => (
                 <div key={i} className="flex items-center gap-3 opacity-70 hover:opacity-100 transition-opacity">
                    <uc.icon className="w-8 h-8 text-white" />
                    <span className="text-lg font-bold text-white tracking-wide">{uc.label}</span>
                 </div>
              ))}
            </div>
         </div>
      </section>

      {/* 5. FEATURES / FINAL CTA */}
      <section className="relative z-10 py-20 max-w-4xl mx-auto px-6 text-center">
         <div className="absolute inset-0 bg-agri-accent/5 rounded-[100px] blur-[100px] pointer-events-none" />
         <motion.div 
           initial={{ opacity: 0 }}
           whileInView={{ opacity: 1 }}
           viewport={{ once: true }}
           className="relative"
         >
           <h2 className="text-3xl md:text-5xl font-black text-white mb-6">Ready to modernize your portfolio?</h2>
           <p className="text-lg text-gray-400 mb-10 max-w-2xl mx-auto">
             Get access to Invoice Extraction, Signature Detection, Portfolio Analytics, and dynamic EMI Decision Support.
           </p>
           
           <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
             <motion.button 
               whileHover={{ scale: 1.05 }}
               onClick={onStartAnalysis}
               className="px-8 py-5 w-full sm:w-auto bg-gradient-to-r from-agri-dark to-agri-accent hover:from-agri-accent hover:to-green-500 text-finance-dark rounded-full font-black text-lg tracking-widest uppercase shadow-[0_0_30px_rgba(46,204,113,0.4)] transition-all flex items-center justify-center gap-3"
             >
               <Zap className="w-6 h-6" /> Start Analysis
             </motion.button>
             <motion.button 
               whileHover={{ scale: 1.05 }}
               className="px-8 py-5 w-full sm:w-auto bg-white/5 border border-white/20 hover:bg-white/10 text-white rounded-full font-black text-lg tracking-widest uppercase transition-all"
             >
               Try Live Demo
             </motion.button>
           </div>
         </motion.div>
      </section>

    </div>
  );
};

export default LandingPage;
