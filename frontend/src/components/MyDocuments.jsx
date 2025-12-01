import React, { useEffect, useState } from 'react';

const MyDocuments = ({ authToken }) => {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchDocs = async () => {
    if (!authToken) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/documents', { headers: { Authorization: `Bearer ${authToken}` } });
      const data = await res.json();
      setDocs(data.docs || []);
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchDocs(); }, [authToken]);

  const handleDelete = async (id) => {
    if (!confirm('Delete this document?')) return;
    try {
      const res = await fetch(`http://localhost:5000/api/documents/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${authToken}` } });
      const data = await res.json();
      if (data.success) setDocs(d => d.filter(x => x._id !== id));
    } catch (err) { console.error(err); }
  };

  if (!authToken) return <div className="p-8 bg-white rounded shadow text-center">Please login to view your documents.</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Your Documents</h2>
      {loading ? <div>Loading…</div> : (
        <div className="space-y-4">
          {docs.length === 0 && <div className="text-sm text-gray-500">No documents yet.</div>}
          {docs.map(doc => (
            <div key={doc._id} className="flex items-center justify-between border rounded p-3">
              <div>
                <div className="font-semibold">{doc.title}</div>
                <div className="text-xs text-gray-500">{new Date(doc.createdAt).toLocaleString()}</div>
              </div>
              <div className="flex items-center space-x-2">
                {doc.pdfPath && (
                  <a className="px-3 py-2 bg-purple-600 text-white rounded" href={`http://localhost:5000${doc.pdfPath}`} target="_blank" rel="noreferrer">Download PDF</a>
                )}
                <button onClick={() => handleDelete(doc._id)} className="px-3 py-2 bg-red-500 text-white rounded">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyDocuments;
