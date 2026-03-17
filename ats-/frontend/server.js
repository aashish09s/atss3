import express from 'express';
import path from 'path';
import http from 'http';
import https from 'https';
import { fileURLToPath, URL } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const API_TARGET = process.env.API_TARGET || 'http://127.0.0.1:8000';

// Minimal proxy to forward API calls to FastAPI so frontend/server.js can serve as an edge layer
app.use('/api', (req, res) => {
  try {
    const targetUrl = new URL(req.originalUrl, API_TARGET);
    const options = {
      protocol: targetUrl.protocol,
      hostname: targetUrl.hostname,
      port: targetUrl.port,
      path: `${targetUrl.pathname}${targetUrl.search}`,
      method: req.method,
      headers: {
        ...req.headers,
        host: targetUrl.host,
      },
    };

    const proxyRequest = (targetUrl.protocol === 'https:' ? https : http).request(
      options,
      (proxyResponse) => {
        res.writeHead(proxyResponse.statusCode || 500, proxyResponse.headers);
        proxyResponse.pipe(res, { end: true });
      }
    );

    proxyRequest.on('error', (err) => {
      console.error('API proxy error:', err.message);
      res.status(502).json({ detail: 'API proxy error' });
    });

    req.pipe(proxyRequest, { end: true });
  } catch (error) {
    console.error('API proxy setup error:', error.message);
    res.status(500).json({ detail: 'API proxy setup error' });
  }
});

// Serve static files from the dist directory
app.use(express.static(path.join(__dirname, 'dist')));

// Handle React Router - serve index.html for all non-API routes
app.use((req, res, next) => {
  // Skip API routes
  if (req.path.startsWith('/api')) {
    return next();
  }
  // Serve index.html for all other routes
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on http://0.0.0.0:${PORT}`);
});

