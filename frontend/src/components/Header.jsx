import React, { useState, useEffect } from 'react';

const Header = () => {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out ${
                scrolled
                    ? 'glass-card backdrop-blur-2xl shadow-xl'
                    : 'bg-white/60 backdrop-blur-sm'
            }`}
            style={{ willChange: 'transform' }}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 md:h-20">
                    
                    {/* Logo */}
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
                            <span className="text-2xl font-bold text-white">D</span>
                        </div>
                        <div>
                            <h2 className="text-xl md:text-2xl font-black gradient-text leading-tight">
                                DocuScan AI
                            </h2>
                            <p className="text-xs text-gray-600 hidden sm:block -mt-1">
                                AI-Powered OCR
                            </p>
                        </div>
                    </div>

                    {/* Desktop Navigation */}
                    <nav
                        aria-label="Main Navigation"
                        className="hidden md:flex items-center space-x-8"
                    >
                        <a
                            href="#features"
                            className="text-gray-700 hover:text-purple-600 transition-colors font-medium"
                        >
                            Features
                        </a>
                        <a
                            href="#how-it-works"
                            className="text-gray-700 hover:text-purple-600 transition-colors font-medium"
                        >
                            How It Works
                        </a>
                        <a
                            href="#use-cases"
                            className="text-gray-700 hover:text-purple-600 transition-colors font-medium"
                        >
                            Use Cases
                        </a>
                    </nav>

                    {/* CTA Button */}
                    <div className="flex items-center space-x-4">
                        <button
                            className="bg-white hover:bg-yellow-300 text-purple-700 font-bold 
                                px-6 py-2 rounded-lg transition-all duration-300 
                                hover:scale-105 shadow-lg"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
