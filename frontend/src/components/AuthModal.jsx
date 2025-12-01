import React, { useState } from 'react';

const AuthModal = ({ onClose, onAuthSuccess }) => {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const url = `http://localhost:5000/api/auth/${mode}`;
      const body = mode === 'register' ? { email, password, name } : { email, password };
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Auth failed');
      onAuthSuccess && onAuthSuccess({ token: data.token, user: data.user });
      onClose && onClose();
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold">{mode === 'login' ? 'Login' : 'Register'}</h3>
          <button onClick={onClose} className="text-gray-500">✕</button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {mode === 'register' && (
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Name" className="w-full border rounded px-3 py-2" />
          )}
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" type="email" className="w-full border rounded px-3 py-2" />
          <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" className="w-full border rounded px-3 py-2" />
          {error && <div className="text-red-600 text-sm">{error}</div>}
          <div className="flex items-center justify-between">
            <button type="submit" disabled={loading} className="btn-primary px-4 py-2 rounded">
              {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create account'}
            </button>
            <button type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className="text-sm text-gray-600 underline">
              {mode === 'login' ? 'Create account' : 'Already have an account?'}
            </button>
          </div>
        </form>
        <div className="mt-4 text-center">
          <div className="text-sm text-gray-600 mb-2">Or sign in with</div>
          <button onClick={() => window.open('http://localhost:5000/api/auth/google', '_blank', 'width=500,height=700')} className="px-4 py-2 bg-white border rounded shadow inline-flex items-center space-x-2">
            <img src="/assets/google_logo.svg" alt="google" className="w-5 h-5" />
            <span>Google</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
