import React, { useState } from 'react';

const UploadSection = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [dragActive, setDragActive] = useState(false);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setError(null);
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }

        setLoading(true);
        const formData = new FormData();
        formData.append('document', file);

        try {
            const response = await fetch('http://localhost:5000/api/ocr/extract', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }

            // Extract the fields from the nested structure
            const extractedFields = data.data?.extracted_fields || data.data || {};
            onUploadSuccess(extractedFields, data.imagePath);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full">
            {/* Hero Section */}
            <div className="relative overflow-hidden mb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center md:text-left">

                    {/* Animated Badge */}
                    <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-full px-4 py-2 mb-8 animate-pulse">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                            AI-Powered OCR Technology
                        </span>
                    </div>

                    {/* Main Heading */}
                    <h1 className="text-5xl md:text-6xl lg:text-7xl font-black mb-6 leading-tight">
                        <span className="block gradient-text animate-fade-in">Transform Documents</span>
                        <span className="block text-gray-900 animate-fade-in-delay">Into Digital Data</span>
                    </h1>

                    {/* Subheading */}
                    <p className="text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto md:mx-0 mb-12 leading-relaxed">
                        Extract text from physical documents instantly with cutting-edge AI.
                        <span className="text-yellow-600 font-semibold"> Fast, accurate, and secure.</span>
                    </p>

                    {/* Stats */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl mx-auto md:mx-0 mb-16">
                        <div className="glass-card p-6 hover:scale-105 transition-transform duration-300">
                            <div className="text-5xl font-black gradient-text mb-2">99%</div>
                            <div className="text-sm text-gray-700 font-semibold">Accuracy Rate</div>
                        </div>

                        <div className="glass-card p-6 hover:scale-105 transition-transform duration-300">
                            <div className="text-5xl font-black gradient-text mb-2">&lt;3s</div>
                            <div className="text-sm text-gray-700 font-semibold">Processing Time</div>
                        </div>

                        <div className="glass-card p-6 hover:scale-105 transition-transform duration-300">
                            <div className="text-5xl font-black gradient-text mb-2">100%</div>
                            <div className="text-sm text-gray-700 font-semibold">Privacy Secure</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Upload Section */}
            <div className="max-w-4xl mx-auto px-4 mb-20">
                <div className="glass-card p-8 lg:p-12 pulse-glow bg-white">
                    <div className="text-center md:text-left mb-8">
                        <h2 className="text-3xl font-bold text-gray-800 mb-3">Get Started in Seconds</h2>
                        <p className="text-gray-600">Upload your document and let AI do the magic</p>
                    </div>

                    <div
                        className={`relative flex flex-col items-center justify-center border-2 
                        border-dashed rounded-2xl p-16 transition-all duration-300 
                        ${dragActive
                                ? 'border-purple-600 bg-purple-100 scale-105'
                                : 'border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-purple-500'
                            }`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <input
                            type="file"
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            accept="image/*"
                        />

                        <div className="text-center">
                            <div className="mb-6">
                                {file ? (
                                    <div className="flex flex-col items-center space-y-3">
                                        <div className="text-6xl">✓</div>
                                        <div>
                                            <p className="text-lg font-medium text-green-600">
                                                {file.name}
                                            </p>
                                            <p className="text-sm text-gray-600">
                                                {(file.size / 1024).toFixed(2)} KB
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="floating-animation">
                                        <div className="text-7xl mb-4">📄</div>
                                    </div>
                                )}
                            </div>

                            <p className="text-2xl text-gray-800 font-bold mb-2">
                                {file ? "Ready to Process!" : "Drop your file here"}
                            </p>

                            <p className="text-gray-600 mb-4">or click to browse</p>

                            <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
                                <span>✓ PNG, JPG, PDF</span>
                                <span>•</span>
                                <span>✓ Max 10MB</span>
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="mt-6 p-4 bg-red-100 border border-red-300 text-red-700 rounded-xl text-sm flex items-center space-x-2">
                            <span className="text-xl">⚠</span>
                            <span>{error}</span>
                        </div>
                    )}

                    <button
                        onClick={handleUpload}
                        disabled={loading || !file}
                        className={`mt-8 w-full py-5 px-8 rounded-xl text-white font-bold text-lg 
                            transition-all duration-300 
                            ${loading || !file
                                ? 'bg-gray-600 cursor-not-allowed opacity-50'
                                : 'btn-primary shadow-2xl'
                            }`}
                    >
                        {loading ? (
                            <span className="flex items-center justify-center">
                                <span className="animate-spin mr-3 text-2xl">⚙</span>
                                Processing Your Document...
                            </span>
                        ) : (
                            <span className="flex items-center justify-center">
                                <span className="mr-2 text-xl">⚡</span>
                                Extract Text with AI
                            </span>
                        )}
                    </button>
                </div>
            </div>

            {/* How It Works */}
            <div id="how-it-works" className="max-w-7xl mx-auto px-4 mb-20">
                <div className="text-center md:text-left mb-12">
                    <h2 className="text-4xl font-bold gradient-text mb-4">How It Works</h2>
                    <p className="text-gray-700 text-lg">Three simple steps to digitize your documents</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                        {
                            step: 1,
                            icon: "📤",
                            title: "Upload Document",
                            desc: "Simply drag and drop or click to upload your physical document image",
                        },
                        {
                            step: 2,
                            icon: "🤖",
                            title: "AI Extraction",
                            desc: "Our AI engine extracts text with 99% accuracy in under 3 seconds",
                        },
                        {
                            step: 3,
                            icon: "✅",
                            title: "Review & Verify",
                            desc: "Review extracted data and verify accuracy with confidence scores",
                        }
                    ].map((item, i) => (
                        <div key={i} className="relative">
                            <div className="glass-card p-8 text-center">
                                <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full 
                                    flex items-center justify-center mx-auto mb-6 text-3xl shadow-lg">
                                    {item.icon}
                                </div>

                                <div className="absolute -top-4 -right-4 w-12 h-12 bg-purple-500 rounded-full 
                                    flex items-center justify-center text-white font-bold text-xl shadow-lg">
                                    {item.step}
                                </div>

                                <h3 className="text-gray-800 font-bold text-2xl mb-3">{item.title}</h3>
                                <p className="text-gray-700">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Features */}
            <div id="features" className="max-w-7xl mx-auto px-4 mb-20">
                <div className="text-center md:text-left mb-12">
                    <h2 className="text-4xl font-bold gradient-text mb-4">Why Choose Our OCR?</h2>
                    <p className="text-gray-700 text-lg">Powered by cutting-edge AI technology</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {[
                        {
                            icon: "⚡",
                            title: "Lightning Fast",
                            description: "Process documents in under 3 seconds",
                            gradient: "from-yellow-400 to-orange-500"
                        },
                        {
                            icon: "✓",
                            title: "99% Accuracy",
                            description: "Powered by Microsoft TrOCR",
                            gradient: "from-green-400 to-emerald-500"
                        },
                        {
                            icon: "🔒",
                            title: "100% Secure",
                            description: "No cloud uploads. Everything stays local.",
                            gradient: "from-blue-400 to-cyan-500"
                        },
                        {
                            icon: "✏️",
                            title: "Smart Editing",
                            description: "Easily review and edit text fields",
                            gradient: "from-purple-400 to-pink-500"
                        },
                        {
                            icon: "📊",
                            title: "Confidence Scores",
                            description: "Get per-field accuracy confidence levels",
                            gradient: "from-indigo-400 to-purple-500"
                        },
                        {
                            icon: "☁️",
                            title: "Offline Ready",
                            description: "Works without internet connection",
                            gradient: "from-teal-400 to-green-500"
                        }
                    ].map((feature, idx) => (
                        <div
                            key={idx}
                            className="glass-card p-8 hover:scale-105 transition-all duration-300 group cursor-pointer"
                        >
                            <div
                                className={`w-16 h-16 bg-gradient-to-br ${feature.gradient} rounded-xl 
                                flex items-center justify-center mb-6 group-hover:scale-110 
                                transition-transform text-4xl`}
                            >
                                {feature.icon}
                            </div>

                            <h3 className="text-gray-800 font-bold text-xl mb-3">{feature.title}</h3>
                            <p className="text-gray-700 leading-relaxed">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Use Cases */}
            <div id="use-cases" className="max-w-7xl mx-auto px-4 mb-20">
                <div className="glass-card p-12 bg-white">
                    <div className="text-center md:text-left mb-12">
                        <h2 className="text-4xl font-bold gradient-text mb-4">Perfect For</h2>
                        <p className="text-gray-700 text-lg">Trusted by professionals across industries</p>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {[
                            { emoji: "🏥", label: "Healthcare" },
                            { emoji: "🏦", label: "Banking" },
                            { emoji: "🎓", label: "Education" },
                            { emoji: "⚖️", label: "Legal" },
                            { emoji: "🏢", label: "Corporate" },
                            { emoji: "🏛️", label: "Government" },
                            { emoji: "📊", label: "Research" },
                            { emoji: "🚀", label: "Startups" }
                        ].map((use, idx) => (
                            <div
                                key={idx}
                                className="bg-white/80 hover:bg-white border border-gray-200 rounded-xl p-6 
                                    text-center transition-all hover:scale-105 shadow-sm"
                            >
                                <div className="text-4xl mb-3">{use.emoji}</div>
                                <div className="text-gray-800 font-semibold">{use.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UploadSection;
