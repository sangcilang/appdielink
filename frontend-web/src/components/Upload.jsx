import React, { useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { upload as blobUpload } from '@vercel/blob/client';
import { authApi, documentApi, getApiErrorMessage } from '../services/api';

const VERCEL_FUNCTION_BODY_LIMIT_BYTES = 4_500_000;

export const Upload = ({ onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const useClientUpload = file.size > VERCEL_FUNCTION_BODY_LIMIT_BYTES;

      if (!useClientUpload) {
        const response = await documentApi.upload(file);
        toast.success('File uploaded successfully');
        onUploadSuccess(response.data);
        fileInputRef.current.value = '';
        return;
      }

      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) {
        throw new Error('Authentication required');
      }

      const me = await authApi.me();
      const userId = me?.data?.id;
      if (!userId) {
        throw new Error('Authentication required');
      }

      const blob = await blobUpload(`uploads/${userId}/${file.name}`, file, {
        access: 'private',
        handleUploadUrl: '/api/blob/upload',
        clientPayload: JSON.stringify({ token: accessToken }),
      });

      const response = await documentApi.registerBlob({
        filename: file.name,
        blob_url: blob.url,
        file_size: file.size,
        content_type: file.type || null,
      });

      toast.success('File uploaded successfully');
      onUploadSuccess(response.data);
      fileInputRef.current.value = '';
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Upload failed'));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <aside className="panel upload-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">Upload</span>
          <h2>Add a document</h2>
        </div>
      </div>

      <label className="upload-dropzone">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          disabled={isUploading}
        />
        <strong>{isUploading ? 'Uploading...' : 'Choose a file'}</strong>
        <span>Click to select a document from your computer.</span>
      </label>
    </aside>
  );
};

export default Upload;
