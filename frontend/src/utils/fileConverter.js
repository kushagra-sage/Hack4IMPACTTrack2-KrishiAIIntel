import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

/**
 * Convert PDF to images
 * @param {File} file - PDF file
 * @returns {Promise<Array>} Array of image data URLs
 */
export async function pdfToImages(file) {
  const images = [];
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 2.0 });
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise;

    images.push({
      dataUrl: canvas.toDataURL('image/jpeg', 0.95),
      pageNumber: pageNum
    });
  }

  return images;
}

/**
 * Convert image file to data URL
 * @param {File} file - Image file
 * @returns {Promise<string>} Image data URL
 */
export function imageToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Convert file to processable format
 * @param {File} file - Input file
 * @returns {Promise<Array>} Array of {dataUrl, filename, pageNumber} objects
 */
export async function convertFileToImages(file) {
  const fileType = file.type;
  
  if (fileType === 'application/pdf') {
    const pdfImages = await pdfToImages(file);
    return pdfImages.map(img => ({
      dataUrl: img.dataUrl,
      filename: `${file.name}_page_${img.pageNumber}`,
      pageNumber: img.pageNumber,
      originalFile: file.name
    }));
  } else if (fileType.startsWith('image/')) {
    const dataUrl = await imageToDataUrl(file);
    return [{
      dataUrl,
      filename: file.name,
      pageNumber: 1,
      originalFile: file.name
    }];
  } else {
    throw new Error('Unsupported file type. Please upload an image or PDF file.');
  }
}

/**
 * Data URL to Blob conversion
 * @param {string} dataUrl - Data URL
 * @returns {Blob} Blob object
 */
export function dataUrlToBlob(dataUrl) {
  const arr = dataUrl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}
