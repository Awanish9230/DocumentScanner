import React, { useState } from 'react';
import Header from './components/Header';
import AuthModal from './components/AuthModal';
import MyDocuments from './components/MyDocuments';
import Footer from './components/Footer';
import UploadSection from './components/UploadSection';
import FormSection from './components/FormSection';
import VerificationResult from './components/VerificationResult';

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [theme, setTheme] = useState(localStorage.getItem('theme') || null);
  const [step, setStep] = useState('upload'); // upload, edit, verify
  const [ocrData, setOcrData] = useState(null);
  const [imagePath, setImagePath] = useState(null);
  const [verificationResults, setVerificationResults] = useState(null);
  const [averageConfidence, setAverageConfidence] = useState(0);

  const handleUploadSuccess = (data, imgPath) => {
    setOcrData(data);
    setImagePath(imgPath);
    setStep('edit');
    // if user is logged in, save document for the user
    if (authToken) {
      fetch('http://localhost:5000/api/documents/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
        body: JSON.stringify({ title: 'OCR Extraction', ocrData: data, imagePath: imgPath })
      }).then(res => res.json()).then(res => {
        console.log('Saved doc', res);
      }).catch(err => console.error('Error saving doc', err));
    }
  };

  const setAuth = ({ token, user }) => {
    setAuthToken(token);
    setUser(user || null);
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
    if (user) localStorage.setItem('user', JSON.stringify(user));
    else localStorage.removeItem('user');
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

  const [showAuthModal, setShowAuthModal] = useState(false);

  // listen for global events from Header
  React.useEffect(() => {
    const open = () => setShowAuthModal(true);
    window.addEventListener('openAuthModal', open);
    return () => window.removeEventListener('openAuthModal', open);
  }, []);

  // Apply theme (light/dark) to document element and persist
  React.useEffect(() => {
    const t = theme || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (t === 'dark') document.documentElement.classList.add('dark-mode'); else document.documentElement.classList.remove('dark-mode');
    localStorage.setItem('theme', t);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));

  // if redirected back from Google OAuth, there may be a token in the url
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('token');
    if (t) {
      // validate user info from backend
      fetch('http://localhost:5000/api/auth/me', { headers: { Authorization: `Bearer ${t}` } })
        .then(r => r.json())
        .then(data => {
          if (data && data.user) {
            setAuth({ token: t, user: data.user });
            // remove token from URL
            params.delete('token');
            const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
            window.history.replaceState({}, document.title, newUrl);
          }
        }).catch(() => {});
    }
  }, []);

  // listen for messages posted by the google popup window
  React.useEffect(() => {
    const handler = (ev) => {
      try {
        if (ev.data && ev.data.token) {
          const t = ev.data.token;
          // validate token with backend and set auth
          fetch('http://localhost:5000/api/auth/me', { headers: { Authorization: `Bearer ${t}` } })
            .then(r => r.json())
            .then(data => {
              if (data && data.user) {
                setAuth({ token: t, user: data.user });
                setShowAuthModal(false);
              }
            }).catch(() => {});
        }
      } catch (e) {}
    };

    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  // listen for header's toggleTheme events and map to state
  React.useEffect(() => {
    const onToggle = () => toggleTheme();
    window.addEventListener('toggleTheme', onToggle);
    return () => window.removeEventListener('toggleTheme', onToggle);
  }, [theme]);

  return (

    <div className="min-h-screen bg-white overflow-x-hidden">
      <Header authToken={authToken} user={user} onAuthChange={setAuth} onShowMyDocs={(s) => setStep('mydocs')} onGoHome={() => setStep('upload')} theme={theme} toggleTheme={toggleTheme} />

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

        {step === 'mydocs' && (
          <MyDocuments authToken={authToken} />
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

      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} onAuthSuccess={(info) => { setAuth(info); setShowAuthModal(false); }} />
      )}
    </div>
  );
}

export default App;
