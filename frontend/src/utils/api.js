import axios from 'axios';

// Backend base URL.
// In local development, leave this empty — the Vite dev server proxy
// (configured in vite.config.js) forwards all API calls to localhost:7860.
// For production / deployed builds, set VITE_API_BASE at build time:
//   VITE_API_BASE=https://your-backend-url npm run build
const API_BASE = import.meta.env.VITE_API_BASE || '';

// ─── Shared axios instance ────────────────────────────────────────────────────
const api = axios.create({ baseURL: API_BASE });

// ─── Endpoints ────────────────────────────────────────────────────────────────

/**
 * Process a single invoice image.
 * @param {Blob}    imageBlob     - Image blob
 * @param {string}  filename      - Original filename
 * @param {boolean} enhanceImage  - Apply OpenCV enhancement before VLM
 * @param {string}  reasoningMode - "simple" or "reason"
 */
export async function processSingleInvoice(imageBlob, filename, enhanceImage = false, reasoningMode = 'simple') {
  const formData = new FormData();
  formData.append('file', imageBlob, filename);
  formData.append('enhance_image', enhanceImage);
  formData.append('reasoning_mode', reasoningMode);

  const response = await api.post('/process-invoice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Extract invoice fields (alias endpoint /extract).
 */
export async function extractInvoice(formData) {
  const response = await api.post('/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Batch extraction via /extract_batch.
 */
export async function extractBatch(formData) {
  const response = await api.post('/extract_batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Health check.
 */
export async function healthCheck() {
  const response = await api.get('/health');
  return response.data;
}

/**
 * Process multiple invoices sequentially, reporting progress after each.
 * @param {Array<{blob, filename, originalFile, pageNumber}>} images
 * @param {Function} onProgress - called with (index, result) after each file
 */
export async function processBatchInvoices(images, onProgress) {
  const results = [];

  for (let i = 0; i < images.length; i++) {
    try {
      const result = await processSingleInvoice(images[i].blob, images[i].filename);
      const resultWithMetadata = {
        ...result,
        filename: images[i].filename,
        originalFile: images[i].originalFile,
        pageNumber: images[i].pageNumber,
        index: i,
        success: true,
      };
      results.push(resultWithMetadata);
      if (onProgress) onProgress(i, resultWithMetadata);
    } catch (error) {
      const errorResult = {
        filename: images[i].filename,
        originalFile: images[i].originalFile,
        pageNumber: images[i].pageNumber,
        index: i,
        success: false,
        error: error.response?.data?.detail || error.message,
      };
      results.push(errorResult);
      if (onProgress) onProgress(i, errorResult);
    }
  }

  return results;
}

// ─── KrishiIntel AI: Decision Support & Portfolio Intelligence ──────────────

/**
 * Get loan decision support for extracted invoice fields.
 */
export async function getDecisionSupport(assetCost, horsePower, modelName) {
  const response = await api.post('/decision-support', {
    asset_cost: assetCost,
    horse_power: horsePower,
    model_name: modelName,
  });
  return response.data;
}

/**
 * Send a chat query to portoflio intelligence RAG engine.
 */
export async function chatQuery(query) {
  const response = await api.post('/chat', { query });
  return response.data;
}

/**
 * Get portfolio summary statistics.
 */
export async function getPortfolioStats() {
  const response = await api.get('/portfolio/stats');
  return response.data;
}

/**
 * Generate an invoice analysis report (HTML).
 */
export async function generateReport(fields, decisionSupport, docId) {
  const response = await api.post('/generate-report', {
    fields,
    decision_support: decisionSupport,
    doc_id: docId,
  });
  return response.data;
}

/**
 * Generate an invoice analysis report (PDF).
 * Returns a Blob.
 */
export async function generateReportPDF(fields, decisionSupport, docId) {
  const response = await api.post('/generate-report-pdf', {
    fields,
    decision_support: decisionSupport,
    doc_id: docId,
  }, {
    responseType: 'blob'
  });
  return response.data;
}

/**
 * Generate a merged batch PDF for multiple invoices.
 * Returns a Blob.
 */
export async function generateBatchReportPDF(invoices) {
    // invoices: Array of { fields, decision_support, doc_id }
    const response = await api.post('/generate-batch-report-pdf', {
      invoices
    }, {
      responseType: 'blob'
    });
    return response.data;
  }

