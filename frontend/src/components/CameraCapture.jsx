import React, { useState, useRef } from 'react';
import { Camera, ImageUp, UploadCloud } from 'lucide-react';
import { Button } from './ui/button';

export function CameraCapture({ onCapture, disabled }) {
    const [dragActive, setDragActive] = useState(false);
    const [preview, setPreview] = useState(null);
    const fileInputRef = useRef(null);
    const dropRef = useRef(null);

    const handleFile = (file) => {
        if (!file || !file.type.startsWith('image/')) return;

        // Create preview
        const objectUrl = URL.createObjectURL(file);
        setPreview(objectUrl);

        // Pass to parent
        onCapture(file);
    };

    const onChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    return (
        <div className="w-full flex flex-col items-center gap-4">
            {/* Mobile Camera Button (Visible primarily on small screens/touch devices) */}
            <Button
                size="lg"
                className="w-full h-16 text-lg rounded-2xl shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all sm:hidden"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
            >
                <Camera className="mr-2 h-6 w-6" />
                拍照或选图
            </Button>

            {/* Desktop/Tablet Drag & Drop Area */}
            <div
                ref={dropRef}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`hidden sm:flex w-full h-64 border-2 border-dashed rounded-2xl items-center justify-center flex-col gap-4 cursor-pointer transition-colors
          ${dragActive ? 'border-primary bg-primary/10' : 'border-muted-foreground/20 bg-card/40 hover:bg-card/60 hover:border-primary/50'}
          ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
            >
                <UploadCloud className="h-12 w-12 text-muted-foreground" />
                <div className="text-center">
                    <p className="text-lg font-medium">点击此处或将图片拖拽至此</p>
                    <p className="text-sm text-muted-foreground">支持 JPG, PNG 等常见格式</p>
                </div>
            </div>

            {/* Hidden File Input */}
            <input
                type="file"
                accept="image/*"
                capture="environment"
                ref={fileInputRef}
                onChange={onChange}
                className="hidden"
            />

            {/* Image Preview Thumbnail */}
            {preview && (
                <div className="mt-4 w-full max-w-sm rounded-xl overflow-hidden shadow-md border border-border">
                    <img src={preview} alt="Receipt preview" className="w-full h-auto object-cover max-h-48" />
                    <div className="bg-muted p-2 text-xs text-center text-muted-foreground">
                        图片已选择
                    </div>
                </div>
            )}
        </div>
    );
}
