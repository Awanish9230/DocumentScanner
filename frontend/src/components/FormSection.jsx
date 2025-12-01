import React, { useEffect, useState } from "react";

const FormSection = ({ ocrData, onVerify }) => {
    const [formData, setFormData] = useState({});

    // Update form anytime new ocrData arrives
    useEffect(() => {
        if (ocrData && typeof ocrData === "object") {
            const cleaned = {};

            Object.keys(ocrData).forEach((key) => {
                cleaned[key] = ocrData[key] ?? ""; // avoid undefined values
            });

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
    const displayKeys = sortedKeys.filter(k => ['raw_text', 'lines', 'average_confidence'].indexOf(k) === -1 && typeof formData[k] === 'string');

    return (
        <div className="max-w-6xl mx-auto">
            <div className="text-center md:text-left mb-8">
                <h2 className="text-4xl font-bold gradient-text mb-3 text-gray-800">
                    Review Extracted Data
                </h2>
                <p className="text-gray-700">Verify and edit the information extracted from your document</p>

                {formData && formData.average_confidence !== undefined && (
                    <div className="mt-4 inline-flex items-center px-3 py-2 bg-gray-50 rounded-lg shadow-sm">
                        <div className="text-xs text-gray-500 mr-3">Model confidence</div>
                        <div className={`font-bold ${formData.average_confidence > 75 ? 'text-green-600' : formData.average_confidence > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {formData.average_confidence}%
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="glass-card p-8">
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
                                className="input-field group-hover:border-purple-400 transition-all"
                                placeholder={`Enter ${key.replace(/_/g, " ")}`}
                            />
                        </div>
                    ))}
                </div>

                <div className="mt-8 flex justify-center">
                    <button
                        type="submit"
                        className="btn-secondary px-12 py-4 text-lg flex items-center space-x-3"
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

            {formData && Array.isArray(formData.lines) && (
                <div className="mt-6 p-4 bg-gray-50 rounded">
                    <h4 className="font-semibold mb-2">Raw OCR lines & confidences</h4>
                    <div className="space-y-2 text-sm">
                        {formData.lines.map((l, idx) => (
                            <div key={idx} className="flex items-center justify-between border rounded p-2">
                                <div className="flex-1 mr-4 text-gray-800">{l.text}</div>
                                <div className={`px-2 py-1 rounded text-xs font-medium ${l.confidence > 75 ? 'bg-green-100 text-green-800' : l.confidence > 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                    {l.confidence}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default FormSection;
