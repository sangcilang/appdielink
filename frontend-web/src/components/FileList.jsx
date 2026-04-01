import React, { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import { documentApi, getApiErrorMessage } from '../services/api';
import ShareLink from './ShareLink';

export const FileList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState([]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await documentApi.listDocuments();
      setDocuments(response.data);
      setSelectedDocIds((currentSelectedIds) =>
        currentSelectedIds.filter((docId) =>
          response.data.some((document) => document.id === docId),
        ),
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to load documents'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentApi.deleteDocument(docId);
        setDocuments((currentDocuments) =>
          currentDocuments.filter((document) => document.id !== docId),
        );
        setSelectedDocIds((currentSelectedIds) =>
          currentSelectedIds.filter((selectedId) => selectedId !== docId),
        );
        toast.success('Document deleted');
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'Delete failed'));
      }
    }
  };

  const allSelected = useMemo(
    () => documents.length > 0 && selectedDocIds.length === documents.length,
    [documents, selectedDocIds],
  );

  const toggleDocumentSelection = (docId) => {
    setSelectedDocIds((currentSelectedIds) =>
      currentSelectedIds.includes(docId)
        ? currentSelectedIds.filter((selectedId) => selectedId !== docId)
        : [...currentSelectedIds, docId],
    );
  };

  const toggleSelectAll = () => {
    setSelectedDocIds(allSelected ? [] : documents.map((document) => document.id));
  };

  if (loading) {
    return (
      <section className="panel file-panel">
        <div className="empty-state">Loading documents...</div>
      </section>
    );
  }

  return (
    <section className="panel file-panel">
      <div className="panel-header panel-header-split">
        <div>
          <span className="panel-kicker">Library</span>
          <h2>Your documents</h2>
        </div>
        <div className="panel-meta">
          <span>{documents.length} files</span>
        </div>
      </div>

      <div className="share-strip">
        <ShareLink selectedDocIds={selectedDocIds} />
      </div>

      <div className="table-wrap">
        <table className="document-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleSelectAll}
                  aria-label="Select all files"
                />
              </th>
              <th>Title</th>
              <th>Size</th>
              <th>Type</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td className="checkbox-cell">
                  <input
                    type="checkbox"
                    checked={selectedDocIds.includes(doc.id)}
                    onChange={() => toggleDocumentSelection(doc.id)}
                    aria-label={`Select ${doc.title}`}
                  />
                </td>
                <td>
                  <div className="document-title">{doc.title}</div>
                </td>
                <td>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</td>
                <td>{doc.file_type}</td>
                <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="danger-button"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {documents.length === 0 && (
        <div className="empty-state">No documents yet. Upload your first file to begin.</div>
      )}
    </section>
  );
};

export default FileList;
