const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
// Note: we use direct HTTP calls to Google's endpoints to avoid extra dependencies

// Register
router.post('/register', async (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password) return res.status(400).json({ message: 'Missing fields' });

  try {
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ message: 'User already exists' });

    const salt = await bcrypt.genSalt(10);
    const hashed = await bcrypt.hash(password, salt);

    const user = new User({ email, password: hashed, name });
    await user.save();

    const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
});

// Login
router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ message: 'Missing fields' });

  try {
    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ message: 'Invalid credentials' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ message: 'Invalid credentials' });

    const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
});

// Me
router.get('/me', async (req, res) => {
  const auth = req.headers.authorization;
  if (!auth) return res.status(401).json({ message: 'Unauthorized' });
  try {
    const token = auth.split(' ')[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.id).select('-password');
    res.json({ user });
  } catch (err) {
    res.status(401).json({ message: 'Unauthorized' });
  }
});

module.exports = router;

// --- Google OAuth server-side flow (optional) ---
// Redirects user to Google consent screen.
router.get('/google', (req, res) => {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const redirectUri = `${process.env.BACKEND_URL || 'http://localhost:5000'}/api/auth/google/callback`;
  // build a simple OAuth2 URL for Google
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'code',
    scope: 'openid email profile',
    access_type: 'offline',
    prompt: 'consent'
  });
  const url = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
  res.redirect(url);
});

// Callback endpoint to exchange code for tokens and create/login user
router.get('/google/callback', async (req, res) => {
  const code = req.query.code;
  if (!code) return res.status(400).send('Missing code');
  try {
    const redirectUri = `${process.env.BACKEND_URL || 'http://localhost:5000'}/api/auth/google/callback`;
    // Exchange code for tokens using direct HTTP request to Google's token endpoint
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: process.env.GOOGLE_CLIENT_ID,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code'
      })
    });
    const tokens = await tokenRes.json();
    // fetch userinfo
    const userInfoRes = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
    const data = await userInfoRes.json();
    // find or create user
    let user = await User.findOne({ email: data.email });
    if (!user) {
      user = new User({ email: data.email, password: '', name: data.name || data.email });
      await user.save();
    }

    const jwt = require('jsonwebtoken');
    const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET, { expiresIn: '7d' });

    // reply with a tiny HTML page that posts the JWT back to the opener window then closes
    const frontend = process.env.FRONTEND_URL || 'http://localhost:5174';
    const escapedToken = token.replace(/'/g, "\\'");
    res.send(`<!doctype html><html><body><script>
      try { window.opener && window.opener.postMessage({ token: '${escapedToken}' }, '${frontend}'); } catch(e){}
      window.close();
    </script></body></html>`);
  } catch (err) {
    console.error('Google callback error', err);
    res.status(500).send('Google auth failed');
  }
});

// Verify an ID token posted from client-side Google Identity Services
router.post('/google/verify', async (req, res) => {
  const { id_token } = req.body;
  if (!id_token) return res.status(400).json({ message: 'Missing id_token' });
  try {
    // verify the id_token by hitting Google's tokeninfo endpoint
    const verifyRes = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(id_token)}`);
    const payload = await verifyRes.json();
    // tokeninfo returns an error field when invalid
    if (payload.error_description || payload.error) return res.status(401).json({ message: 'Invalid id_token' });
    // ensure the token audience matches our client id
    if (payload.aud !== process.env.GOOGLE_CLIENT_ID) return res.status(401).json({ message: 'Invalid token audience' });
    const { email, name } = payload;

    let user = await User.findOne({ email });
    if (!user) {
      user = new User({ email, password: '', name });
      await user.save();
    }

    const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    console.error('Google verify error', err);
    res.status(401).json({ message: 'Invalid id_token' });
  }
});
