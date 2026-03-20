import React, { useCallback, useState } from 'react';
import { Upload, FileText, Image as ImageIcon, X } from 'lucide-react';

const FileUpload = ({ onFilesSelected, disabled }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFiles = (files) => {
    const validFiles = files.filter(file => {
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
      return validTypes.includes(file.type);
    });

    if (validFiles.length !== files.length) {
      alert('Some files were skipped. Only images (JPEG, PNG, GIF, WEBP) and PDF files are supported.');
    }

    setSelectedFiles(prev => [...prev, ...validFiles]);
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleProcess = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles);
      setSelectedFiles([]);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full space-y-6">
      {/* Upload Zone */}
      <div
        className={`upload-zone relative rounded-2xl p-6 text-center cursor-pointer ${dragActive ? 'drag-active' : ''
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && document.getElementById('fileInput').click()}
      >
        <input
          id="fileInput"
          type="file"
          multiple
          accept="image/*,.pdf"
          onChange={handleFileInput}
          className="hidden"
          disabled={disabled}
        />

        <div className="flex flex-col items-center justify-center space-y-4 relative z-10">
          <div className="p-5 bg-green-500/10 rounded-full border border-green-500/30 group-hover:scale-110 transition-transform duration-300">
            <Upload className="w-12 h-12 text-agri-accent" />
          </div>

          <div>
            <p className="text-xl font-bold text-gray-200 mb-2 tracking-wide">
              Drop Document Here
            </p>
            <p className="text-sm text-green-400/60 font-medium">
              Click to browse or drag and drop
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs text-green-400/50 mt-4 bg-finance-dark/50 px-4 py-2 rounded-full border border-finance-dark">
            <ImageIcon className="w-4 h-4" />
            <span>Images & PDF</span>
            <span>•</span>
            <FileText className="w-4 h-4" />
            <span>Auto Layout Parsing</span>
          </div>
        </div>
      </div>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-semibold text-green-400 uppercase tracking-widest">
              Queued Documents ({selectedFiles.length})
            </h3>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-xs text-red-400 hover:text-red-300 font-medium hover:underline transition-all"
            >
              Clear Queue
            </button>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-finance-dark/60 backdrop-blur-md p-4 rounded-xl border border-green-500/20 hover:border-agri-accent/50 hover:bg-finance-dark/80 transition-all group"
              >
                <div className="flex items-center space-x-4 flex-1 min-w-0">
                  <div className="flex-shrink-0 p-2 bg-finance-dark/50 rounded-lg">
                    {file.type === 'application/pdf' ? (
                      <FileText className="w-6 h-6 text-green-300" />
                    ) : (
                      <ImageIcon className="w-6 h-6 text-agri-accent" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate group-hover:text-green-400 transition-colors">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatFileSize(file.size)}
                      {file.type === 'application/pdf' && ' • PDF Conversion Enabled'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                  className="ml-3 p-2 hover:bg-red-500/20 rounded-lg transition-colors group/btn"
                  title="Remove file"
                >
                  <X className="w-5 h-5 text-red-400 group-hover/btn:text-red-300" />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={handleProcess}
            disabled={disabled}
            className="w-full relative group overflow-hidden bg-finance-dark border border-green-500/30 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(14,165,233,0.15)] hover:shadow-[0_0_30px_rgba(14,165,233,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3 mt-4"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-green-600 opacity-80 group-hover:opacity-100 transition-opacity" />
            <Upload className="w-5 h-5 relative z-10" />
            <span className="relative z-10 tracking-widest uppercase text-sm">Initiate Analysis ({selectedFiles.length})</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
