const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;
const DIST_DIR = path.join(__dirname, 'dist');

// Remove trailing slashes (redirect /about/ to /about)
app.use((req, res, next) => {
  if (req.path !== '/' && req.path.endsWith('/')) {
    const query = req.url.slice(req.path.length);
    return res.redirect(301, req.path.slice(0, -1) + query);
  }
  next();
});

// Serve static files
app.use(express.static(DIST_DIR));

// Middleware to handle routes without .html extension
app.use((req, res, next) => {
  // Skip if it's already a file with extension
  if (path.extname(req.path)) {
    return next();
  }

  // Try to serve the .html file
  const htmlPath = path.join(DIST_DIR, req.path + '.html');
  
  if (fs.existsSync(htmlPath)) {
    return res.sendFile(htmlPath);
  }
  
  next();
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(`Serving files from: ${DIST_DIR}`);
});
