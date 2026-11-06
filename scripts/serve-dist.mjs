import { createServer } from 'node:http';
import { readFile, readdir } from 'node:fs/promises';
import { resolve, join, extname } from 'node:path';
import { gzipSync } from 'node:zlib';

// Local production review server. Deploy dist/ to a static host separately.
const directory = resolve(process.argv[2] ?? 'dist');
const port = Number(process.argv[3] ?? 4174);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid port.');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.webp': 'image/webp', '.mp4': 'video/mp4' };
const files = new Map();
async function collect(folder, prefix = '') {
  for (const entry of await readdir(folder, { withFileTypes: true })) {
    const relative = `${prefix}/${entry.name}`;
    if (entry.isDirectory()) await collect(join(folder, entry.name), relative);
    else if (entry.isFile()) {
      const raw = await readFile(join(folder, entry.name));
      files.set(relative, { raw, gzip: gzipSync(raw), type: types[extname(entry.name)] ?? 'application/octet-stream' });
    }
  }
}
await collect(directory);
if (!files.has('/index.html')) throw new Error('Build output has no index.html.');
createServer((request, response) => {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    response.writeHead(405, { Allow: 'GET, HEAD', 'Content-Length': 0 });response.end();return;
  }
  let pathname;
  try { pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname); }
  catch { response.writeHead(400, { 'Content-Length': 0 });response.end();return; }
  const file = files.get(pathname === '/' ? '/index.html' : pathname);
  if (!file) { response.writeHead(404, { 'Content-Length': 0 });response.end();return; }
  const compressed = /\bgzip\b/.test(request.headers['accept-encoding'] ?? '');
  const body = compressed ? file.gzip : file.raw;
  response.writeHead(200, {
    'Content-Type': file.type,
    'Content-Length': body.length,
    'Cache-Control': pathname.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
    Vary: 'Accept-Encoding',
    ...(compressed ? { 'Content-Encoding': 'gzip' } : {}),
  });
  response.end(request.method === 'HEAD' ? undefined : body);
}).listen(port, '127.0.0.1', () => process.stdout.write(`Production review server: ${directory}, port ${port}, loopback only\n`));
