# Invoice Extractor Frontend

A modern, interactive React frontend for the Invoice Information Extractor application.

## Features

- 📁 **Multiple File Upload**: Support for images (JPEG, PNG, GIF, WEBP) and PDF files
- 🔄 **PDF Conversion**: Automatic PDF to image conversion in the browser
- 📊 **Batch Processing**: Process multiple files sequentially with real-time progress
- 🎨 **Visual Detection**: Display bounding boxes for detected signatures and stamps
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- ⚡ **Real-time Updates**: See results as they are processed

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend API URL (default: http://localhost:8000)

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Preview Production Build

```bash
npm run preview
```

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **PDF.js** - PDF rendering and conversion
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Usage

1. **Upload Files**: Drag and drop or click to select images/PDFs
2. **Process**: Click "Process" button to send files to the backend
3. **View Results**: See extracted text, signatures, and stamps with visual indicators
4. **Batch Processing**: Multiple files are processed one by one with progress tracking

## API Integration

The frontend expects the following backend endpoints:

- `POST /process-invoice` - Process a single invoice image
  - Request: FormData with 'file' field
  - Response: JSON with extracted_text, signature_coords, stamp_coords

## Features in Detail

### PDF to Image Conversion
- Converts multi-page PDFs to individual images
- Each page is processed separately
- High-quality conversion using PDF.js

### Bounding Box Visualization
- Red boxes for signatures
- Blue boxes for stamps
- Drawn directly on the canvas over the image

### Batch Processing
- Sequential processing to avoid overwhelming the backend
- Real-time progress updates
- Individual error handling per file

## Customization

### Styling
Edit `tailwind.config.js` to customize colors and theme.

### API Endpoint
Update `VITE_API_URL` in `.env` file.

### Supported File Types
Modify the `accept` attribute in FileUpload.jsx and validation logic.

## Troubleshooting

**CORS Issues**: Make sure your backend allows requests from the frontend origin.

**PDF Not Loading**: Check that PDF.js worker is properly loaded (check browser console).

**API Errors**: Verify backend is running and accessible at the configured URL.
