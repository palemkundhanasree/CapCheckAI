import React, { useState, useRef } from 'react';
import { Upload, Volume2, X, AlertCircle } from 'lucide-react';

interface AudioUploaderProps {
  onSubmit: (file: File) => void;
  isLoading: boolean;
}

export const AudioUploader: React.FC<AudioUploaderProps> = ({ onSubmit, isLoading }) => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSelectFile = (selectedFile: File) => {
    setError(null);
    const validExtensions = ['.wav', '.mp3', '.m4a', '.ogg'];
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setError(`Invalid audio format '${ext}'. Supported: WAV, MP3, M4A, OGG`);
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File exceeds audio limit of 50MB.');
      return;
    }

    setFile(selectedFile);
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an audio file to check.');
      return;
    }
    onSubmit(file);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
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
            accept=".wav,.mp3,.m4a,.ogg"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) handleSelectFile(e.target.files[0]);
            }}
          />
          <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-3">
            <Volume2 className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-semibold text-slate-900">Click to upload audio, or drag and drop</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            WAV, MP3, M4A or OGG files up to 50MB. Analyzes spectral timbre and speech synthesis markers.
          </p>
        </div>
      ) : (
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-md bg-white border border-slate-200 flex items-center justify-center text-blue-600">
              <Volume2 className="w-5 h-5" />
            </div>
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
        <Volume2 className="w-4 h-4" />
        <span>{isLoading ? 'Scanning Spectral Timbre...' : 'Scan Audio for Synthetic Voices'}</span>
      </button>
    </form>
  );
};
