import React, { useState, useEffect } from 'react';

const ProfileMenu = ({ user, onLogout, onOpenDocs }) => {
    const [open, setOpen] = useState(false);

    const initials = (user && (user.name || user.email)) ? (user.name ? user.name.split(' ').map(n => n[0]).slice(0,2).join('') : user.email[0].toUpperCase()) : '?';

    return (
        <div className="relative inline-block text-left">
            <button onClick={() => setOpen(v => !v)} className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white flex items-center justify-center font-semibold shadow-md focus:outline-none">
                {initials}
            </button>

            {open && (
                <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-3">
                    <div className="px-4 py-2 border-b border-gray-100">
                        <div className="font-semibold text-gray-800">{user.name || user.email}</div>
                        <div className="text-xs text-gray-500">{user.email}</div>
                    </div>
                    <div className="py-2">
                        <button onClick={() => { onOpenDocs && onOpenDocs(); setOpen(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm">My Documents</button>
                        <button onClick={() => { onLogout && onLogout(); setOpen(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-red-600">Logout</button>
                    </div>
                </div>
            )}
        </div>
    );
};

const Header = ({ authToken, user, onAuthChange, onShowMyDocs, onGoHome, theme, toggleTheme }) => {
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
                    <div className="flex items-center space-x-3" style={{cursor: 'pointer'}} onClick={() => { if (typeof onGoHome === 'function') onGoHome(); }}>
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
                            href="#home"
                            onClick={(e) => { e.preventDefault(); if (typeof onGoHome === 'function') onGoHome(); }}
                            className="text-gray-700 hover:text-purple-600 transition-colors font-medium"
                        >
                            Home
                        </a>
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

                    {/* Profile / Auth area */}
                    <div className="flex items-center space-x-3 relative">
                        {/* theme toggle */}
                        <button aria-label="Toggle theme" onClick={() => typeof toggleTheme === 'function' && toggleTheme()} className="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-transparent text-gray-700 dark:text-gray-200 transition-all">
                            <span id="theme-icon">{(typeof theme !== 'undefined' && theme === 'dark') || (typeof document !== 'undefined' && document.documentElement.classList.contains('dark')) ? '🌙' : '☀️'}</span>
                        </button>

                        {!authToken && (
                            <button
                                onClick={() => window.dispatchEvent(new CustomEvent('openAuthModal'))}
                                className="bg-white hover:bg-yellow-300 text-purple-700 font-bold px-4 py-2 rounded-lg transition-all duration-300 hover:scale-105 shadow-lg"
                            >
                                Login / Register
                            </button>
                        )}

                        {authToken && user && (
                            <ProfileMenu user={user} onLogout={() => onAuthChange && onAuthChange({ token: null, user: null })} onOpenDocs={() => onShowMyDocs && onShowMyDocs('mydocs')} />
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

 

export default Header;
