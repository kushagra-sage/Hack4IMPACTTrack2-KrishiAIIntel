import React, { useRef, useEffect, useState } from 'react';
import { SlidersHorizontal, ChevronDown, ChevronUp, Brain, FileOutput, CheckCircle2 } from 'lucide-react';

const ResultCard = ({ result, imageData, processedImageData, onReprocess, isProcessing }) => {
  const canvasRef = useRef(null);
  const previewCanvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [signatureCrop, setSignatureCrop] = useState(null);
  const [stampCrop, setStampCrop] = useState(null);
  const [resolution, setResolution] = useState(result.processedResolution || 100);
  const [adjustedDataUrl, setAdjustedDataUrl] = useState(null);
  const [previewDimensions, setPreviewDimensions] = useState({ width: 0, height: 0 });
  const [currentImageData, setCurrentImageData] = useState(processedImageData || imageData);
  const [showReasoning, setShowReasoning] = useState(false);

  // Function to crop image regions
  const cropRegion = (img, coords, scaleX, scaleY) => {
    if (!coords || coords.length === 0) return null;

    const [x1, y1, x2, y2] = coords[0];
    const width = (x2 - x1) * scaleX;
    const height = (y2 - y1) * scaleY;

    const cropCanvas = document.createElement('canvas');
    cropCanvas.width = width;
    cropCanvas.height = height;
    const cropCtx = cropCanvas.getContext('2d');

    // Draw the cropped region
    cropCtx.drawImage(
      img,
      x1, y1, x2 - x1, y2 - y1,
      0, 0, width, height
    );

    return cropCanvas.toDataURL();
  };

  // Initialize currentImageData with processedImageData when available
  useEffect(() => {
    if (processedImageData) {
      setCurrentImageData(processedImageData);
    }
  }, [processedImageData]);

  // Main effect to draw image with bounding boxes using currentImageData
  useEffect(() => {
    if (!currentImageData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      // Set canvas size to match container while maintaining aspect ratio
      const maxWidth = 800;
      const maxHeight = 600;
      let width = img.width;
      let height = img.height;

      if (width > maxWidth) {
        height = (height * maxWidth) / width;
        width = maxWidth;
      }
      if (height > maxHeight) {
        width = (width * maxHeight) / height;
        height = maxHeight;
      }

      canvas.width = width;
      canvas.height = height;
      setDimensions({ width, height });

      // Draw image
      ctx.drawImage(img, 0, 0, width, height);

      // Calculate scale factors
      const scaleX = width / img.width;
      const scaleY = height / img.height;

      // Create cropped images for signature and stamp from the CURRENT (processed) image
      // This ensures crops match the resolution that was sent to the API
      if (result.signature_coords && result.signature_coords.length > 0) {
        const sigCrop = cropRegion(img, result.signature_coords, 1, 1);
        setSignatureCrop(sigCrop);
      }
      if (result.stamp_coords && result.stamp_coords.length > 0) {
        const stCrop = cropRegion(img, result.stamp_coords, 1, 1);
        setStampCrop(stCrop);
      }

      // Draw bounding boxes for signature
      if (result.signature_coords && result.signature_coords.length > 0) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);

        result.signature_coords.forEach(coords => {
          const [x1, y1, x2, y2] = coords;
          ctx.strokeRect(
            x1 * scaleX,
            y1 * scaleY,
            (x2 - x1) * scaleX,
            (y2 - y1) * scaleY
          );
        });

        // Add label
        ctx.fillStyle = '#ef4444';
        ctx.font = 'bold 14px Arial';
        ctx.fillText('Signature', result.signature_coords[0][0] * scaleX, result.signature_coords[0][1] * scaleY - 5);
      }

      // Draw bounding boxes for stamp
      if (result.stamp_coords && result.stamp_coords.length > 0) {
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);

        result.stamp_coords.forEach(coords => {
          const [x1, y1, x2, y2] = coords;
          ctx.strokeRect(
            x1 * scaleX,
            y1 * scaleY,
            (x2 - x1) * scaleX,
            (y2 - y1) * scaleY
          );
        });

        // Add label
        ctx.fillStyle = '#3b82f6';
        ctx.font = 'bold 14px Arial';
        ctx.fillText('Stamp', result.stamp_coords[0][0] * scaleX, result.stamp_coords[0][1] * scaleY - 5);
      }
    };

    img.src = currentImageData;
  }, [currentImageData, imageData, result]);

  // Handle resolution adjustment for preview and update currentImageData
  useEffect(() => {
    if (!imageData || !previewCanvasRef.current) return;

    const canvas = previewCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      const scale = resolution / 100;
      const newWidth = Math.floor(img.width * scale);
      const newHeight = Math.floor(img.height * scale);

      canvas.width = newWidth;
      canvas.height = newHeight;
      setPreviewDimensions({ width: newWidth, height: newHeight });

      ctx.drawImage(img, 0, 0, newWidth, newHeight);

      // Generate adjusted data URL
      const adjustedUrl = canvas.toDataURL('image/jpeg', 0.95);
      setAdjustedDataUrl(adjustedUrl);

      // Update the current image data to reflect resolution change
      setCurrentImageData(adjustedUrl);
    };

    img.src = imageData;
  }, [imageData, resolution]);

  if (!result.success) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-2xl p-6 mb-4 backdrop-blur-md">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-200">Processing Error</h3>
            <div className="mt-2 text-sm text-red-300">
              <p><strong className="text-red-100">File:</strong> {result.originalFile || result.filename}</p>
              <p><strong className="text-red-100">Error:</strong> {result.error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-morphism overflow-hidden mb-8 group">
      {/* Header */}
      <div className="bg-finance-dark/80 border-b border-green-500/20 px-6 py-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-green-400/10 to-green-600/10 pointer-events-none" />
        <div className="flex items-center justify-between relative z-10">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center text-glow">
              <svg className="w-5 h-5 mr-3 text-agri-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {result.originalFile || result.filename}
            </h3>
            {result.pageNumber && (
              <p className="text-green-400 text-sm mt-1 flex items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-green-300 mr-2 shadow-[0_0_5px_#a855f7]" />
                Page {result.pageNumber}
              </p>
            )}
          </div>
          {onReprocess && (
            <button
              onClick={() => onReprocess(result, resolution, adjustedDataUrl)}
              disabled={isProcessing}
              className="bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-[0_0_15px_rgba(14,165,233,0.15)] hover:shadow-[0_0_20px_rgba(14,165,233,0.25)]"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reprocess
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8 relative">
        {/* Decorative Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(14,165,233,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.03)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

        {/* Image with bounding boxes */}
        <div className="space-y-5 relative z-10">
          <h4 className="text-lg font-bold text-gray-200 flex items-center tracking-wide">
            <svg className="w-5 h-5 mr-3 text-agri-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Document Preview
          </h4>

          {/* Resolution Slider */}
          <div className="bg-finance-dark/80 rounded-xl p-5 border border-finance-dark shadow-inner">
            <div className="flex items-center justify-between mb-4">
              <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-agri-accent" />
                Adjust Resolution
              </label>
              <span className="text-sm font-bold text-agri-accent bg-green-400/40 px-2 py-1 rounded border border-green-500/20">{resolution}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={resolution}
              onChange={(e) => setResolution(parseInt(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-finance-dark"
              style={{ background: `linear-gradient(to right, #0ea5e9 0%, #0ea5e9 ${resolution}%, #374151 ${resolution}%, #374151 100%)` }}
              disabled={isProcessing}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-3 font-medium">
              <span>Fast Analysis</span>
              <span className="text-gray-400 font-mono text-[10px] uppercase border border-finance-dark px-1 rounded">{previewDimensions.width} × {previewDimensions.height}px</span>
              <span>High Precision</span>
            </div>
          </div>

          <div className="relative bg-finance-dark/60 rounded-xl p-4 flex justify-center items-center border border-finance-dark/50 shadow-[0_0_20px_rgba(0,0,0,0.5)_inset]">
            <canvas ref={canvasRef} className="max-w-full h-auto rounded-lg shadow-lg" />
            {isProcessing && (
              <div className="absolute inset-0 flex items-center justify-center bg-finance-dark/50 backdrop-blur-[2px] rounded-xl">
                <div className="scanning-line"></div>
              </div>
            )}
          </div>

          <div className="flex gap-4 text-sm font-medium">
            {result.signature_coords && result.signature_coords.length > 0 && (
              <div className="flex items-center bg-red-900/20 px-3 py-1.5 rounded-full border border-red-500/30">
                <div className="w-3 h-3 rounded-full bg-red-500 mr-2 shadow-[0_0_8px_#ef4444]"></div>
                <span className="text-red-200">Signature Detected</span>
              </div>
            )}
            {result.stamp_coords && result.stamp_coords.length > 0 && (
              <div className="flex items-center bg-blue-900/20 px-3 py-1.5 rounded-full border border-blue-500/30">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2 shadow-[0_0_8px_#0ea5e9]"></div>
                <span className="text-green-400">Stamp Detected</span>
              </div>
            )}
          </div>
        </div>

        {/* Extracted Information */}
        <div className="space-y-5 relative z-10">
          <h4 className="text-lg font-bold text-gray-200 flex items-center tracking-wide">
            <svg className="w-5 h-5 mr-3 text-agri-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Extracted Intelligence
          </h4>

          <div className="bg-finance-dark/40 rounded-xl p-5 border border-finance-dark shadow-inner space-y-4">
            {/* Performance Metrics */}
            <div className="grid grid-cols-3 gap-3">
              {result.processing_time !== undefined && (
                <div className="bg-finance-dark rounded-xl p-3 shadow-md border border-finance-dark text-center hover:border-green-500/30 transition-colors">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 mb-1">Time Elapsed</div>
                  <div className="text-lg font-bold text-agri-accent font-mono">{result.processing_time.toFixed(2)}s</div>
                </div>
              )}
              {result.confidence !== undefined && (
                <div className="bg-finance-dark rounded-xl p-3 shadow-md border border-finance-dark text-center hover:border-green-500/30 transition-colors">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 mb-1">Confidence Score</div>
                  <div className="text-lg font-bold text-green-400 font-mono text-glow">{(result.confidence * 100).toFixed(1)}%</div>
                </div>
              )}
              {result.cost_estimate_usd !== undefined && (
                <div className="bg-finance-dark rounded-xl p-3 shadow-md border border-finance-dark text-center hover:border-agri-accent/30 transition-colors">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 mb-1">API Cost Estimate</div>
                  <div className="text-lg font-bold text-green-300 font-mono underline decoration-agri-accent/30 underline-offset-2">${result.cost_estimate_usd.toFixed(4)}</div>
                </div>
              )}
            </div>

            <div className="bg-finance-dark rounded-xl p-4 shadow-md border border-finance-dark/80">
              <div className="flex items-center gap-2 mb-3 border-b border-finance-dark pb-2">
                <FileOutput className="w-4 h-4 text-agri-accent" />
                <h5 className="text-[11px] font-bold text-gray-300 uppercase tracking-widest">Structured Output</h5>
              </div>
              <div className="text-sm text-gray-300 whitespace-pre-wrap max-h-96 overflow-y-auto font-mono bg-finance-dark/80 p-4 rounded-lg border border-finance-dark custom-scrollbar shadow-inner leading-relaxed">
                {result.extracted_text || 'No text extracted'}
              </div>
            </div>

            {/* Reasoning Output (Chain of Thought) */}
            {result.timing_breakdown?.reasoning_output && (
              <div className="bg-green-400/10 rounded-xl border border-green-500/20 overflow-hidden text-glow">
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-green-400/20 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Brain className="w-5 h-5 text-agri-accent drop-shadow-[0_0_8px_#38bdf8]" />
                    <h5 className="text-[11px] font-bold text-green-400 uppercase tracking-widest">
                      VLM Neural Reasoning Analysis
                    </h5>
                  </div>
                  {showReasoning ? (
                    <ChevronUp className="w-5 h-5 text-agri-accent" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-agri-accent" />
                  )}
                </button>
                {showReasoning && (
                  <div className="px-5 pb-5">
                    <div className="text-[11px] text-agri-accent/80 mb-3 uppercase tracking-wider">
                      Internal processing steps before structured output generation
                    </div>
                    <div className="text-sm text-green-400/90 whitespace-pre-wrap max-h-96 overflow-y-auto font-mono bg-finance-dark/60 p-4 rounded-lg border border-green-500/20 shadow-inner custom-scrollbar relative">
                      <div className="absolute top-0 left-0 w-1 h-full bg-green-500/50" />
                      {result.timing_breakdown.reasoning_output}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Detection Status */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-finance-dark rounded-xl p-4 shadow-md border border-finance-dark">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-300 tracking-wide">Signature</span>
                  {result.signature_coords && result.signature_coords.length > 0 ? (
                    <span className="inline-flex items-center px-2.5 py-1 rounded bg-red-900/20 text-[11px] font-bold text-red-400 border border-red-500/30 uppercase tracking-wider">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                      Detected
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-1 rounded bg-finance-dark text-[11px] font-bold text-gray-400 border border-finance-dark uppercase tracking-wider opacity-70">
                      Not Found
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-finance-dark rounded-xl p-4 shadow-md border border-finance-dark">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-300 tracking-wide">Stamp</span>
                  {result.stamp_coords && result.stamp_coords.length > 0 ? (
                    <span className="inline-flex items-center px-2.5 py-1 rounded bg-green-400/20 text-[11px] font-bold text-agri-accent border border-green-500/30 uppercase tracking-wider text-glow">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                      Detected
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-1 rounded bg-finance-dark text-[11px] font-bold text-gray-400 border border-finance-dark uppercase tracking-wider opacity-70">
                      Not Found
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Cropped Signature and Stamp */}
            {(signatureCrop || stampCrop) && (
              <div className="bg-finance-dark rounded-xl p-5 shadow-md border border-finance-dark">
                <h5 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-4 border-b border-finance-dark pb-2">Isolated Visual Elements</h5>
                <div className="grid grid-cols-2 gap-5">
                  {signatureCrop && (
                    <div className="space-y-3">
                      <div className="text-[10px] font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_5px_#ef4444]" />
                        Signature Region
                      </div>
                      <div className="border border-red-500/20 rounded-xl p-2 bg-finance-dark/50 shadow-inner group overflow-hidden">
                        <img src={signatureCrop} alt="Signature" className="w-full h-auto filter grayscale group-hover:grayscale-0 transition-all duration-500 hover:scale-105" />
                      </div>
                    </div>
                  )}
                  {stampCrop && (
                    <div className="space-y-3">
                      <div className="text-[10px] font-bold text-agri-accent uppercase tracking-widest flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_5px_#0ea5e9]" />
                        Stamp Region
                      </div>
                      <div className="border border-green-500/20 rounded-xl p-2 bg-finance-dark/50 shadow-inner group overflow-hidden">
                        <img src={stampCrop} alt="Stamp" className="w-full h-auto filter grayscale group-hover:grayscale-0 transition-all duration-500 hover:scale-105" />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Coordinates Info */}
            {(result.signature_coords?.length > 0 || result.stamp_coords?.length > 0) && (
              <div className="bg-finance-dark rounded-xl p-4 shadow-md border border-finance-dark opacity-80 hover:opacity-100 transition-opacity">
                <h5 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Bounding Box Coordinates</h5>
                <div className="text-xs space-y-2 font-mono">
                  {result.signature_coords?.length > 0 && (
                    <div className="flex gap-2 items-start">
                      <span className="font-semibold text-red-500 bg-red-900/20 px-1 rounded">SIG:</span>
                      <code className="text-gray-400 break-all bg-finance-dark/50 px-2 py-0.5 rounded border border-finance-dark shadow-inner flex-1">
                        {JSON.stringify(result.signature_coords)}
                      </code>
                    </div>
                  )}
                  {result.stamp_coords?.length > 0 && (
                    <div className="flex gap-2 items-start mt-2">
                      <span className="font-semibold text-green-500 bg-green-400/20 px-1 rounded">STM:</span>
                      <code className="text-gray-400 break-all bg-finance-dark/50 px-2 py-0.5 rounded border border-finance-dark shadow-inner flex-1">
                        {JSON.stringify(result.stamp_coords)}
                      </code>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hidden canvas for resolution preview generation */}
      <canvas ref={previewCanvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default ResultCard;
