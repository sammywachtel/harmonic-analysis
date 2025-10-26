// File upload zone - drag-and-drop interface with file picker fallback
// This gives users a nice visual target for uploading music files

import { useRef, useState } from 'react';

interface FileUploadZoneProps {
  onFileSelected: (file: File) => void;
  acceptedTypes?: string[];
  maxSizeMB?: number;
  disabled?: boolean;
}

const FileUploadZone = ({
  onFileSelected,
  acceptedTypes = ['.xml', '.musicxml', '.mxl', '.mid', '.midi'],
  maxSizeMB = 10,
  disabled = false,
}: FileUploadZoneProps) => {
  // State management - track whether user is dragging over the zone
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Main play: handle drag events to show visual feedback
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
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

  // Big play: handle the drop event and validate the file
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      onFileSelected(files[0]);
    }
  };

  // Fallback: handle file picker selection
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelected(files[0]);
    }
  };

  // Click to open file picker
  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400 bg-gray-50 hover:bg-gray-100'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
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
        <div className="text-5xl">📁</div>
        <div>
          <p className="text-lg font-semibold text-gray-900">
            {isDragging ? 'Drop file here' : 'Drop file or click to browse'}
          </p>
          <p className="text-sm text-gray-600 mt-2">
            Accepted formats: {acceptedTypes.join(', ')}
          </p>
          <p className="text-sm text-gray-600">
            Maximum file size: {maxSizeMB}MB
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUploadZone;
