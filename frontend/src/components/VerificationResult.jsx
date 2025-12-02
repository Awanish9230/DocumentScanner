import React from 'react';

const VerificationResult = ({ results = [], averageConfidence = 0, onReset }) => {
    const getConfidenceColor = (score) => {
        if (score > 80) return 'text-green-600';
        if (score > 50) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getStatusIcon = (status) => {
        if (status === 'Match') return '✓';
        if (status === 'Partial Match') return '⚠';
        return '✗';
    };

    return (
        <div className="max-w-6xl mx-auto">

            {/* Header Section */}
            <div className="p-8 mb-8 text-center bg-white border rounded-xl shadow-md">
                <h2 className="text-4xl font-bold text-gray-800 mb-6">
                    Verification Complete
                </h2>

                <div className="flex items-center justify-center space-x-10">

                    {/* Confidence Score */}
                    <div>
                        <p className="text-gray-600 text-sm mb-1">Overall Confidence</p>
                        <div
                            className={`text-6xl font-black ${getConfidenceColor(averageConfidence)}`}
                        >
                            {averageConfidence}%
                        </div>
                    </div>

                    {/* Summary Counts */}
                    <div className="text-left">
                        <div className="flex items-center space-x-2 mb-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span className="text-gray-700">
                                Match: {results.filter((r) => r.status === 'Match').length}
                            </span>
                        </div>

                        <div className="flex items-center space-x-2 mb-2">
                            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                            <span className="text-gray-700">
                                Partial: {results.filter((r) => r.status === 'Partial Match').length}
                            </span>
                        </div>

                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                            <span className="text-gray-700">
                                Mismatch: {results.filter((r) => r.status === 'Mismatch').length}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Field-by-Field Analysis */}
            <div className="p-8 bg-white border rounded-xl shadow-md">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Field-by-Field Analysis</h3>

                <div className="space-y-4">
                    {results.map((item, index) => (
                        <div
                            key={index}
                            className={`p-4 rounded-xl border shadow-sm 
                                ${
                                    item.status === 'Match'
                                        ? 'border-green-300 bg-green-50'
                                        : item.status === 'Partial Match'
                                        ? 'border-yellow-300 bg-yellow-50'
                                        : 'border-red-300 bg-red-50'
                                }
                            `}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">

                                    {/* Header Row */}
                                    <div className="flex items-center space-x-2 mb-2">
                                        <span className="text-2xl">{getStatusIcon(item.status)}</span>

                                        <h4 className="text-gray-800 font-semibold capitalize">
                                            {item.field.replace(/_/g, ' ')}
                                        </h4>

                                        <span
                                            className={`px-2 py-1 rounded-full text-xs font-semibold
                                                ${
                                                    item.status === 'Match'
                                                        ? 'bg-green-100 text-green-700'
                                                        : item.status === 'Partial Match'
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-red-100 text-red-700'
                                                }
                                            `}
                                        >
                                            {item.similarity}% Match
                                        </span>
                                    </div>

                                    {/* Values Area */}
                                    <div className="grid grid-cols-2 gap-4 mt-3">
                                        <div>
                                            <p className="text-xs text-gray-600 mb-1">OCR Extracted</p>
                                            <pre className="text-gray-800 font-mono text-sm bg-gray-100 p-2 rounded max-h-40 overflow-auto">
                                                {typeof item.ocrValue === 'object' ? JSON.stringify(item.ocrValue, null, 2) : (item.ocrValue || '—')}
                                            </pre>
                                        </div>

                                        <div>
                                            <p className="text-xs text-gray-600 mb-1">User Input</p>
                                            <pre className="text-gray-800 font-mono text-sm bg-gray-100 p-2 rounded max-h-40 overflow-auto">
                                                {typeof item.userValue === 'object' ? JSON.stringify(item.userValue, null, 2) : (item.userValue || '—')}
                                            </pre>
                                        </div>
                                    </div>

                                    <div className="mt-3 text-sm text-gray-600 space-y-1">
                                        <div>OCR Confidence: <strong className={getConfidenceColor(Number(item.ocr_confidence))}>{item.ocr_confidence || 0}%</strong></div>
                                        <div>Combined score: <strong className={getConfidenceColor(Number(item.combinedScore))}>{item.combinedScore || 0}%</strong></div>
                                        {item.notes && (
                                            <div className="text-xs text-gray-500 italic mt-1">Note: {item.notes}</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Reset Button */}
                <div className="mt-8 flex justify-center">
                    <button
                        onClick={onReset}
                        className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl"
                    >
                        Process Another Document
                    </button>
                </div>
            </div>
        </div>
    );
};

export default VerificationResult;
