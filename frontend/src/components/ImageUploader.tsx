import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, X, AlertCircle } from 'lucide-react';

interface ImageUploaderProps {
  onSubmit: (file: File, context?: string) => void;
  isLoading: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onSubmit, isLoading }) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [context, setContext] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSelectFile = (selectedFile: File) => {
    setError(null);
    const validExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setError(`Unsupported file format '${ext}'. Please upload JPG, PNG, or WebP.`);
      return;
    }

    if (selectedFile.size > 25 * 1024 * 1024) {
      setError('File is too large (maximum size is 25MB).');
      return;
    }

    setFile(selectedFile);
    const url = URL.createObjectURL(selectedFile);
    setPreview(url);
  };

  const clearFile = () => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an image file to check.');
      return;
    }
    onSubmit(file, context.trim() || undefined);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Drag & Drop Area */}
      {!file ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files?.[0]) handleSelectFile(e.dataTransfer.files[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 sm:p-10 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50/50'
              : 'border-slate-200 hover:border-slate-300 bg-slate-50'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) handleSelectFile(e.target.files[0]);
            }}
          />
          <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-3">
            <Upload className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-semibold text-slate-900">Click to upload an image, or drag and drop</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Supports JPEG, PNG, and WebP images up to 25MB.
          </p>
        </div>
      ) : (
        /* Preview Card */
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {preview && (
              <img src={preview} alt="Upload preview" className="w-14 h-14 object-cover rounded-md border border-slate-200" />
            )}
            <div>
              <p className="text-sm font-medium text-slate-900 truncate max-w-xs">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for inspection</p>
            </div>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Caption context */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
          Caption or Claim associated with this photo (Optional)
        </label>
        <input
          type="text"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. 'Photo claimed to show a flood in Paris yesterday'"
          className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-colors"
          disabled={isLoading}
        />
      </div>

      {error && (
        <div className="flex items-center space-x-2 text-xs text-red-700 bg-red-50 p-3 rounded-lg border border-red-200">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || !file}
        className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
      >
        <ImageIcon className="w-4 h-4" />
        <span>{isLoading ? 'Scanning Camera Noise & Artifacts...' : 'Check Image Authenticity'}</span>
      </button>
    </form>
  );
};
