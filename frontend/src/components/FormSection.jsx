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

    return (
        <div className="max-w-6xl mx-auto">
            <div className="text-center md:text-left mb-8">
                <h2 className="text-4xl font-bold gradient-text mb-3 text-gray-800">
                    Review Extracted Data
                </h2>
                <p className="text-gray-700">
                    Verify and edit the information extracted from your document
                </p>
            </div>

            <form onSubmit={handleSubmit} className="glass-card p-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {sortedKeys.map((key, index) => (
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
        </div>
    );
};

export default FormSection;
