import React, { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import UploadSection from './components/UploadSection';
import FormSection from './components/FormSection';
import VerificationResult from './components/VerificationResult';

function App() {
  const [step, setStep] = useState('upload'); // upload, edit, verify
  const [ocrData, setOcrData] = useState(null);
  const [imagePath, setImagePath] = useState(null);
  const [verificationResults, setVerificationResults] = useState(null);
  const [averageConfidence, setAverageConfidence] = useState(0);

  const handleUploadSuccess = (data, imgPath) => {
    setOcrData(data);
    setImagePath(imgPath);
    setStep('edit');
  };

  const handleVerify = async (userData) => {
    try {
      const response = await fetch('http://localhost:5000/api/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ocrData, userData }),
      });

      const data = await response.json();
      setVerificationResults(data.results);
      setAverageConfidence(data.averageConfidence);
      setStep('verify');
    } catch (err) {
      console.error('Verification failed:', err);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setOcrData(null);
    setImagePath(null);
    setVerificationResults(null);
    setAverageConfidence(0);
  };

  return (

    <div className="min-h-screen bg-white overflow-x-hidden">
      <Header />

      <div className="pt-20 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">

        {/* Progress Steps */}
        {step !== 'upload' && (
          <div className="mb-12 flex items-center justify-center space-x-8">

            {/* Step 1 */}
            <div className="flex items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold
                ${step === 'edit' || step === 'verify'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-600'}
              `}>
                ✓
              </div>
              <span className="ml-3 text-lg font-medium text-gray-800">Upload</span>
            </div>

            <div className="w-16 h-1 bg-gray-200"></div>

            {/* Step 2 */}
            <div className="flex items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold
                ${step === 'edit'
                    ? 'bg-purple-500 text-white'
                    : step === 'verify'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-600'}
              `}>
                {step === 'verify' ? '✓' : '2'}
              </div>
              <span className="ml-3 text-lg font-medium text-gray-800">Review Data</span>
            </div>

            <div className="w-16 h-1 bg-gray-200"></div>

            {/* Step 3 */}
            <div className="flex items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold
                ${step === 'verify'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-200 text-gray-600'}
              `}>
                3
              </div>
              <span className="ml-3 text-lg font-medium text-gray-800">Verify</span>
            </div>
          </div>
        )}

        {/* Upload Step */}
        {step === 'upload' && (
          <UploadSection onUploadSuccess={handleUploadSuccess} />
        )}

        {/* Edit / Review Step */}
        {step === 'edit' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">

            {/* Image View Card */}
            <div className="bg-white shadow-lg rounded-2xl p-6 border border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">📄 Uploaded Document</h3>
              {imagePath && (
                <img
                  src={`http://localhost:5000${imagePath}`}
                  alt="Uploaded Document"
                  className="w-full h-auto rounded-xl border border-gray-300"
                />
              )}
            </div>

            {/* Editable Form */}
            <FormSection ocrData={ocrData} onVerify={handleVerify} />
          </div>
        )}

        {/* Verification Step */}
        {step === 'verify' && (
          <VerificationResult
            results={verificationResults}
            averageConfidence={averageConfidence}
            onReset={handleReset}
          />
        )}
      </div>

      <Footer />
    </div>
  );
}

export default App;
