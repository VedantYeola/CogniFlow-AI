import React, { useState, ChangeEvent } from 'react';
import { uploadData } from 'aws-amplify/storage';

export const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [percentage, setPercentage] = useState<number>(0);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setStatus('');
      setPercentage(0);
    }
  };

  const handleUpload = async () => {
    if (!file) return alert("Please select a file first!");

    try {
      setStatus('Uploading...');
      const result = await uploadData({
        // This path matches the IAM policy we set in the CDK backend
        path: ({ identityId }) => `private/${identityId}/${file.name}`,
        data: file,
        options: {
          onProgress: ({ transferredBytes, totalBytes }) => {
            if (totalBytes) {
              setPercentage(Math.round((transferredBytes / totalBytes) * 100));
            }
          }
        }
      }).result;

      setStatus(`Success! Uploaded to S3.`);
      console.log('Path:', result.path);
    } catch (error) {
      console.error("Upload failed:", error);
      setStatus('Upload failed. Check console for details.');
    }
  };

  return (
    <div style={{ padding: '20px', border: '2px dashed #007bff', borderRadius: '12px', textAlign: 'center' }}>
      <h3>Secure File Upload</h3>
      <input type="file" onChange={handleFileChange} style={{ marginBottom: '15px' }} />
      <br />
      <button 
        onClick={handleUpload} 
        disabled={!file || status === 'Uploading...'}
        style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px' }}
      >
        {status === 'Uploading...' ? `Uploading ${percentage}%` : 'Upload to S3'}
      </button>
      {status && <p style={{ marginTop: '10px', color: status.includes('Success') ? 'green' : 'red' }}>{status}</p>}
    </div>
  );
};