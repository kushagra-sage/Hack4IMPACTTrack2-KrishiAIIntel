import React, { useState, useEffect, useRef } from 'react';
import { SlidersHorizontal, Sparkles, Brain } from 'lucide-react';

const ImagePreview = ({ imageData, fileName, onResolutionChange, onEnhanceToggle, isEnhanced, onReasoningModeToggle, useReasoning }) => {
  const [resolution, setResolution] = useState(100);
  const canvasRef = useRef(null);
  const [originalDimensions, setOriginalDimensions] = useState({ width: 0, height: 0 });
  const [currentDimensions, setCurrentDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!imageData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      if (!originalDimensions.width) {
        setOriginalDimensions({ width: img.width, height: img.height });
      }

      // Calculate new dimensions based on resolution
      const newWidth = Math.floor(img.width * (resolution / 100));
      const newHeight = Math.floor(img.height * (resolution / 100));
      
      setCurrentDimensions({ width: newWidth, height: newHeight });

      // Set display size (max 400px width for preview)
      const displayWidth = Math.min(400, newWidth);
      const displayHeight = Math.floor(newHeight * (displayWidth / newWidth));

      canvas.width = displayWidth;
      canvas.height = displayHeight;

      // Draw scaled image
      ctx.drawImage(img, 0, 0, displayWidth, displayHeight);

      // Notify parent of resolution change
      if (onResolutionChange) {
        const resizedCanvas = document.createElement('canvas');
        resizedCanvas.width = newWidth;
        resizedCanvas.height = newHeight;
        const resizedCtx = resizedCanvas.getContext('2d');
        resizedCtx.drawImage(img, 0, 0, newWidth, newHeight);
        const resizedDataUrl = resizedCanvas.toDataURL('image/jpeg', 0.95);
        onResolutionChange(resizedDataUrl, resolution);
      }
    };

    img.src = imageData;
  }, [imageData, resolution]);

  const handleResolutionChange = (e) => {
    const newResolution = parseInt(e.target.value);
    setResolution(newResolution);
  };

  return (
    <div className="glass-morphism-card p-5 space-y-4 hover:border-primary-500/30 transition-colors duration-300">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-200 truncate pr-2">Preview: {fileName}</h4>
        <span className="text-xs font-mono text-primary-400 bg-dark-800 px-2 py-1 rounded-full border border-dark-600">
          {currentDimensions.width} × {currentDimensions.height}px
        </span>
      </div>

      <div className="bg-dark-900/50 rounded-xl p-3 flex justify-center border border-dark-600">
        <canvas ref={canvasRef} className="rounded-lg shadow-[0_0_15px_rgba(0,0,0,0.5)]" />
      </div>

      {/* Enhance Button */}
      <button
        onClick={() => onEnhanceToggle && onEnhanceToggle()}
        className={`w-full py-2.5 px-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 text-sm ${
          isEnhanced
            ? 'bg-accent-600/20 border border-accent-500 text-accent-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]'
            : 'bg-dark-800 border border-dark-600 hover:border-accent-500/50 hover:bg-dark-700 text-gray-300'
        }`}
      >
        <Sparkles className={`w-4 h-4 ${isEnhanced ? 'text-accent-400' : ''}`} />
        {isEnhanced ? 'Enhanced Mode Active' : 'Enhance Image'}
      </button>

      {isEnhanced && (
        <div className="bg-accent-900/20 border border-accent-500/30 rounded-lg p-3 text-xs text-accent-200 leading-relaxed">
          <span className="mr-1">✨</span> Image will be enhanced with OpenCV (CLAHE, denoising, sharpening) before processing
        </div>
      )}

      {/* Reasoning Mode Toggle */}
      <button
        onClick={() => onReasoningModeToggle && onReasoningModeToggle()}
        className={`w-full py-2.5 px-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 text-sm ${
          useReasoning
            ? 'bg-primary-600/20 border border-primary-500 text-primary-300 shadow-[0_0_15px_rgba(14,165,233,0.2)]'
            : 'bg-dark-800 border border-dark-600 hover:border-primary-500/50 hover:bg-dark-700 text-gray-300'
        }`}
      >
        <Brain className={`w-4 h-4 ${useReasoning ? 'text-primary-400' : ''}`} />
        {useReasoning ? 'Reasoning Analysis Active' : 'Simple Analysis Mode'}
      </button>

      {useReasoning && (
        <div className="bg-primary-900/20 border border-primary-500/30 rounded-lg p-3 text-xs text-primary-200 leading-relaxed">
          <span className="mr-1">🧠</span> VLM will use 2-step reasoning: analyze document structure, then extract fields
        </div>
      )}

      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-primary-400" />
            Processing Resolution
          </label>
          <span className="text-sm font-bold text-primary-400">{resolution}%</span>
        </div>
        
        <input
            type="range"
            min="10"
            max="100"
            value={resolution}
            onChange={handleResolutionChange}
            className="w-full h-2 rounded-lg cursor-pointer bg-dark-600 appearance-none"
            style={{ 
              background: `linear-gradient(to right, #0ea5e9 0%, #0ea5e9 ${resolution}%, #374151 ${resolution}%, #374151 100%)`
            }}
        />

        
        <div className="flex justify-between text-xs text-gray-500 font-medium">
          <span>Speed Optimized</span>
          <span>Quality Optimized</span>
        </div>

        {resolution < 100 && (
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 text-xs text-blue-300">
            <span className="mr-1">💡</span> Lower resolution = faster processing & lower API cost
          </div>
        )}
      </div>

      <div className="text-xs text-gray-400 space-y-2 pt-2 border-t border-dark-600/50">
        <div className="flex justify-between items-center">
          <span>Original Size:</span>
          <span className="font-mono bg-dark-800 px-2 py-0.5 rounded border border-dark-700 text-gray-300">
            {originalDimensions.width} × {originalDimensions.height}px
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span>Processing Size:</span>
          <span className="font-mono bg-primary-900/20 px-2 py-0.5 rounded border border-primary-500/30 text-primary-400">
            {currentDimensions.width} × {currentDimensions.height}px
          </span>
        </div>
      </div>
    </div>
  );
};

export default ImagePreview;
