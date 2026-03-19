import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Tractor, Users, MapPin, IndianRupee, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

const StatCard = ({ icon: Icon, label, value, sub, color = 'primary', delay = 0 }) => {
  const colorMap = {
    primary: { bg: 'bg-primary-900/20', border: 'border-primary-500/30', text: 'text-primary-400', glow: 'shadow-[0_0_15px_rgba(14,165,233,0.15)]' },
    green: { bg: 'bg-emerald-900/20', border: 'border-emerald-500/30', text: 'text-emerald-400', glow: 'shadow-[0_0_15px_rgba(16,185,129,0.15)]' },
    accent: { bg: 'bg-accent-900/20', border: 'border-accent-500/30', text: 'text-accent-400', glow: 'shadow-[0_0_15px_rgba(168,85,247,0.15)]' },
    amber: { bg: 'bg-amber-900/20', border: 'border-amber-500/30', text: 'text-amber-400', glow: 'shadow-[0_0_15px_rgba(245,158,11,0.15)]' },
  };
  const c = colorMap[color] || colorMap.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`${c.bg} border ${c.border} rounded-xl p-5 ${c.glow} hover:scale-[1.02] transition-transform`}
    >
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${c.bg} border ${c.border}`}>
          <Icon className={`w-4 h-4 ${c.text}`} />
        </div>
        <span className="text-[10px] uppercase tracking-widest font-semibold text-gray-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold font-mono ${c.text}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-1">{sub}</div>}
    </motion.div>
  );
};

const RankList = ({ title, items, labelKey, valueKey, icon: Icon, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 15 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4, delay }}
    className="bg-dark-800/60 border border-dark-600 rounded-xl p-5"
  >
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-primary-400" />
      <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">{title}</h4>
    </div>
    <div className="space-y-2.5">
      {items.map((item, i) => {
        const maxVal = items[0]?.[valueKey] || 1;
        const pct = (item[valueKey] / maxVal) * 100;
        return (
          <div key={i}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-300 truncate max-w-[180px]">{item[labelKey]}</span>
              <span className="text-primary-400 font-mono font-bold">{item[valueKey]}</span>
            </div>
            <div className="h-1.5 bg-dark-900 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.6, delay: delay + i * 0.1 }}
                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
              />
            </div>
          </div>
        );
      })}
    </div>
  </motion.div>
);

const PortfolioStats = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        <span className="ml-3 text-gray-400">Loading portfolio data…</span>
      </div>
    );
  }

  if (!stats || Object.keys(stats).length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>Portfolio data not available</p>
      </div>
    );
  }

  const fmt = (val) => {
    if (val == null) return '—';
    return '₹' + Number(val).toLocaleString('en-IN');
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={BarChart3}
          label="Total Invoices"
          value={stats.total_invoices?.toLocaleString() || 0}
          color="primary"
          delay={0}
        />
        <StatCard
          icon={IndianRupee}
          label="Portfolio Value"
          value={fmt(stats.total_portfolio_value)}
          color="green"
          delay={0.1}
        />
        <StatCard
          icon={TrendingUp}
          label="Avg. Asset Cost"
          value={fmt(stats.avg_asset_cost)}
          color="accent"
          delay={0.2}
        />
        <StatCard
          icon={Tractor}
          label="Avg. Horse Power"
          value={`${stats.avg_horse_power || 0} HP`}
          sub={`Range: ${fmt(stats.min_asset_cost)} – ${fmt(stats.max_asset_cost)}`}
          color="amber"
          delay={0.3}
        />
      </div>

      {/* Rankings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.top_models && stats.top_models.length > 0 && (
          <RankList
            title="Top Tractor Models"
            items={stats.top_models}
            labelKey="model"
            valueKey="count"
            icon={Tractor}
            delay={0.4}
          />
        )}
        {stats.top_dealers && stats.top_dealers.length > 0 && (
          <RankList
            title="Top Dealers"
            items={stats.top_dealers}
            labelKey="dealer"
            valueKey="count"
            icon={Users}
            delay={0.5}
          />
        )}
        {stats.region_distribution && stats.region_distribution.length > 0 && (
          <RankList
            title="Regional Distribution"
            items={stats.region_distribution.slice(0, 5)}
            labelKey="region"
            valueKey="count"
            icon={MapPin}
            delay={0.6}
          />
        )}
      </div>
    </div>
  );
};

export default PortfolioStats;
