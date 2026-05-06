// Drag-and-drop file picker. Coral primary border on dragover, dashed slate
// otherwise. Eighth-note glyph instead of an emoji folder so it shares the
// header's typographic voice.

import { useRef, useState } from 'react';

interface FileUploadZoneProps {
  onFileSelected: (file: File) => void;
  acceptedTypes?: string[];
  maxSizeMB?: number;
  disabled?: boolean;
  /** Override the centered headline. */
  hint?: string;
}

const NoteIcon = () => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className="w-10 h-10 text-slate-400 mx-auto"
    fill="currentColor"
  >
    <path d="M19 3v11.55a4 4 0 1 1-2-3.46V6.62L9 8.5v8.55a4 4 0 1 1-2-3.46V6l12-3z" />
  </svg>
);

const FileUploadZone = ({
  onFileSelected,
  acceptedTypes = ['.xml', '.musicxml', '.mxl', '.mid', '.midi'],
  maxSizeMB = 10,
  disabled = false,
  hint,
}: FileUploadZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;
    const files = e.dataTransfer.files;
    if (files && files.length > 0) onFileSelected(files[0]);
  };
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) onFileSelected(files[0]);
  };
  const handleClick = () => {
    if (!disabled && fileInputRef.current) fileInputRef.current.click();
  };

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => { if (!disabled && (e.key === 'Enter' || e.key === ' ')) handleClick(); }}
      className={`border-2 border-dashed rounded-xl px-6 py-10 text-center cursor-pointer transition-all duration-200 ${
        isDragging
          ? 'border-primary-500 bg-primary-50/60'
          : 'border-slate-300 hover:border-primary-400 bg-slate-50/40 hover:bg-slate-50'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileInput}
        accept={acceptedTypes.join(',')}
        className="hidden"
        disabled={disabled}
      />

      <div className="space-y-3">
        <NoteIcon />
        <div>
          <p className="text-base font-semibold text-slate-900 font-serif">
            {hint ?? (isDragging ? 'Drop file here' : 'Drop a file or click to browse')}
          </p>
          <p className="text-xs text-slate-600 mt-2 font-mono">
            {acceptedTypes.join(' · ')} · max {maxSizeMB} MB
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUploadZone;
