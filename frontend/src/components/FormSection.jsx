import React, { useEffect, useState } from "react";

const FormSection = ({ ocrData, onVerify }) => {
    const [formData, setFormData] = useState({});

    // Update form anytime new ocrData arrives
    useEffect(() => {
        if (ocrData && typeof ocrData === "object") {
            const cleaned = {};

            // Extract canonical fields if available
            if (ocrData.fields && typeof ocrData.fields === "object") {
                Object.keys(ocrData.fields).forEach((key) => {
                    cleaned[key] = ocrData.fields[key] ?? "";
                });
            } else {
                // Fallback: use top-level keys (old format)
                Object.keys(ocrData).forEach((key) => {
                    if (!key.endsWith('_confidence') && !['raw_text', 'raw_lines', 'text', 'lines', 'average_confidence', 'fields', 'fields_meta'].includes(key)) {
                        cleaned[key] = ocrData[key] ?? "";
                    }
                });
            }

            setFormData(cleaned);
        }
    }, [ocrData]);

    const handleChange = (e) => {
        const { name, value } = e.target;

        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onVerify(formData);
    };

    const sortedKeys = Object.keys(formData).sort();
    // filter out non-field keys so we can render only editable text inputs
    const displayKeys = sortedKeys.filter(k => {
        if (['raw_text', 'lines', 'average_confidence', 'fields', 'fields_meta', 'text', 'raw_lines', 'confidence', 'error'].includes(k)) return false;
        if (k.endsWith('_confidence')) return false;
        return true;
    });

    return (
        <div className="max-w-6xl mx-auto">
            <div className="text-center md:text-left mb-8">
                <h2 className="text-4xl font-bold gradient-text mb-3 text-gray-800">
                    Review Extracted Data
                </h2>
                <p className="text-gray-700">Verify and edit the information extracted from your document</p>

                {ocrData && ocrData.confidence !== undefined && (
                    <div className="mt-4 inline-flex items-center px-3 py-2 bg-gray-50 rounded-lg shadow-sm">
                        <div className="text-xs text-gray-500 mr-3">Extraction confidence</div>
                        <div className={`font-bold ${ocrData.confidence > 75 ? 'text-green-600' : ocrData.confidence > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {ocrData.confidence}%
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="glass-card p-8">
                {displayKeys.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {displayKeys.map((key, index) => (
                            <div
                                key={key}
                                className="group"
                                style={{ animationDelay: `${index * 0.1}s` }}
                            >
                                <label className="block text-sm font-semibold text-purple-700 mb-2 capitalize">
                                    {key.replace(/_/g, " ")}
                                </label>

                                <input
                                    type="text"
                                    name={key}
                                    value={formData[key] ?? ""}
                                    onChange={handleChange}
                                    className="input-field group-hover:border-purple-400 transition-all w-full px-4 py-2 border border-gray-300 rounded-lg"
                                    placeholder={`Enter ${key.replace(/_/g, " ")}`}
                                />
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-yellow-800">
                            No fields were extracted from the document. Please check the image quality and try again.
                        </p>
                    </div>
                )}

                <div className="mt-8 flex justify-center">
                    <button
                        type="submit"
                        disabled={displayKeys.length === 0}
                        className={`px-12 py-4 text-lg flex items-center space-x-3 rounded-lg font-semibold text-white transition-all ${
                            displayKeys.length === 0
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-purple-600 hover:bg-purple-700 shadow-lg'
                        }`}
                    >
                        <svg
                            className="w-6 h-6"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                        <span>Verify Data</span>
                    </button>
                </div>
            </form>

            {/* Display raw extracted text for transparency */}
            {ocrData && ocrData.text && (
                <div className="mt-6 p-4 bg-gray-50 rounded">
                    <h4 className="font-semibold mb-2 text-gray-800">Extracted Raw Text</h4>
                    <pre className="text-xs bg-white p-3 rounded border border-gray-200 max-h-48 overflow-auto text-gray-700 whitespace-pre-wrap">
                        {ocrData.text}
                    </pre>
                </div>
            )}

            {/* Display errors if any */}
            {ocrData && ocrData.error && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded">
                    <p className="text-red-700 font-semibold">Extraction Error</p>
                    <p className="text-red-600 text-sm">{ocrData.error}</p>
                </div>
            )}
        </div>
    );
};

export default FormSection;
