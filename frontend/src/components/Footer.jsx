import React from "react";

const Footer = () => {
    return (
        <footer className="relative mt-20 border-t border-gray-200 bg-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">

                <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">

                    {/* Brand Section */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center space-x-3 mb-4">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                <span className="text-2xl font-bold text-white">D</span>
                            </div>
                            <h3 className="text-2xl font-black gradient-text tracking-tight">
                                DocuScan AI
                            </h3>
                        </div>

                        <p className="text-gray-700 max-w-md leading-relaxed mb-4">
                            Transform physical documents into digital data instantly with
                            cutting-edge AI-powered OCR technology.
                        </p>

                        <div className="flex space-x-4">
                            <a aria-label="GitHub" href="#" className="text-gray-600 hover:text-gray-900 transition">
                                <span className="text-2xl">🐙</span>
                            </a>
                            <a aria-label="Twitter" href="#" className="text-gray-600 hover:text-gray-900 transition">
                                <span className="text-2xl">🐦</span>
                            </a>
                            <a aria-label="LinkedIn" href="#" className="text-gray-600 hover:text-gray-900 transition">
                                <span className="text-2xl">💼</span>
                            </a>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h4 className="text-gray-800 font-bold mb-4">Quick Links</h4>
                        <ul className="space-y-2">
                            <li><a href="#features" className="footer-link">Features</a></li>
                            <li><a href="#how-it-works" className="footer-link">How It Works</a></li>
                            <li><a href="#use-cases" className="footer-link">Use Cases</a></li>
                            <li><a href="#" className="footer-link">Documentation</a></li>
                        </ul>
                    </div>

                    {/* Support */}
                    <div>
                        <h4 className="text-gray-800 font-bold mb-4">Support</h4>
                        <ul className="space-y-2">
                            <li><a href="#" className="footer-link">Help Center</a></li>
                            <li><a href="#" className="footer-link">Privacy Policy</a></li>
                            <li><a href="#" className="footer-link">Terms of Service</a></li>
                            <li><a href="#" className="footer-link">Contact Us</a></li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-gray-300">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                        <p className="text-gray-600 text-sm tracking-tight">
                            © 2025 APM Pvt. Ltd. All rights reserved. Built with ❤️ using MERN Stack.
                        </p>

                        <div className="flex space-x-6 text-sm text-gray-600">
                            <span>🔒 Secure</span>
                            <span>⚡ Fast</span>
                            <span>🎯 Accurate</span>
                        </div>
                    </div>
                </div>

            </div>
        </footer>
    );
};

export default Footer;
