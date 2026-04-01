import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { accessApi, getApiErrorMessage } from '../services/api';

async function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.setAttribute('readonly', '');
  textArea.style.position = 'absolute';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea);
}

export const ShareLink = ({ selectedDocIds }) => {
  const [shareData, setShareData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copying, setCopying] = useState(false);

  useEffect(() => {
    setShareData(null);
  }, [selectedDocIds]);

  const selectedCount = selectedDocIds.length;

  const generateShareLink = async () => {
    if (!selectedCount) {
      toast.info('Select at least one file first');
      return;
    }

    setLoading(true);
    try {
      const response = await accessApi.createShareLink(selectedDocIds);
      setShareData(response.data);
      toast.success(
        `Share link created for ${selectedCount} file${selectedCount > 1 ? 's' : ''}. It will expire in 5 minutes.`,
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to create share link'));
    } finally {
      setLoading(false);
    }
  };

  const copyShareLink = async () => {
    if (!shareData?.share_url) {
      return;
    }

    setCopying(true);
    try {
      await copyTextToClipboard(shareData.share_url);
      toast.success('Share link copied to clipboard');
    } catch {
      toast.error('Could not copy the share link');
    } finally {
      setCopying(false);
    }
  };

  const expiresAtLabel = shareData?.expires_at
    ? new Date(shareData.expires_at).toLocaleString()
    : null;

  return (
    <div className="share-card">
      <div className="share-card-top">
        <div>
          <p className="share-title">Create 5 minute download link</p>
          <p className="share-subtitle">
            {selectedCount
              ? `${selectedCount} file${selectedCount > 1 ? 's' : ''} selected`
              : 'Choose one or more files below'}
          </p>
        </div>
        <button
          onClick={generateShareLink}
          disabled={loading || !selectedCount}
          className="primary-button compact-button"
        >
          {loading ? 'Creating...' : 'Create link'}
        </button>
      </div>

      {shareData && (
        <div className="share-result">
          <p className="share-validity">Valid until {expiresAtLabel}</p>
          <p className="share-help">
            Opening this link will download all selected files together.
          </p>
          <a
            href={shareData.share_url}
            target="_blank"
            rel="noreferrer"
            className="share-url"
          >
            {shareData.share_url}
          </a>
          <div className="share-actions">
            <button
              onClick={copyShareLink}
              disabled={copying}
              className="secondary-button compact-button"
            >
              {copying ? 'Copying...' : 'Copy link'}
            </button>
            <a
              href={shareData.share_url}
              target="_blank"
              rel="noreferrer"
              className="ghost-link compact-button"
            >
              Open link
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShareLink;
