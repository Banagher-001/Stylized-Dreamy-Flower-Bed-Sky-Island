import { createReadStream } from 'node:fs';
import { realpath, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Dependency-free local preview for the downloadable static site.
const project = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const options = { port: 4173, base: '/', open: false, strict: false, json: false, directory: undefined };
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg',
  '.mp4': 'video/mp4', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8' };
const nodeVersion = process.versions.node.split('.').map(Number);
function requireNode() {
  if (nodeVersion[0] < 22 || (nodeVersion[0] === 22 && nodeVersion[1] < 12))
    throw new Error('请安装 Node.js LTS 24；本项目最低需要 Node.js 22.12。');
}
function finish(response, status, headers = {}) {
  response.writeHead(status, { 'Content-Length': 0, ...headers });response.end();
}
async function exists(path) { try { return (await stat(path)).isFile(); } catch { return false; } }

async function main() {
  requireNode();
  if (args.includes('--check-node')) { console.log(`Node.js ${process.versions.node} 可以运行此项目。`);return; }
  if (args.includes('--help')) {
    console.log('node scripts/preview-site.mjs [--dir 路径] [--port 4173] [--base /sakan/] [--strict-port] [--open]');return;
  }
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--open') options.open = true;
    else if (arg === '--json') options.json = true;
    else if (arg === '--strict-port') options.strict = true;
    else if (['--dir', '--port', '--base'].includes(arg)) {
      const value = args[++i];if (!value || value.startsWith('--')) throw new Error(`${arg} 缺少参数。`);
      if (arg === '--dir') options.directory = resolve(value);
      else if (arg === '--port') options.port = Number(value);
      else options.base = value;
    } else throw new Error(`不认识的参数：${arg}。使用 --help 查看说明。`);
  }
  if (!Number.isInteger(options.port) || options.port < 0 || options.port > 65535) throw new Error('端口需要是 0～65535 的整数。');
  if (!/^\/(?:[A-Za-z0-9_-]+\/)*$/.test(options.base)) throw new Error('子路径使用 /sakan/ 这样的格式。');
  let directory = options.directory;
  if (!directory) {
    if (await exists(resolve(project, 'SITE-PACKAGE.txt'))) directory = project;
    else if (await exists(resolve(project, 'dist/index.html'))) directory = resolve(project, 'dist');
    else throw new Error('请先运行 START-DEV.cmd 修改网页，或在源码目录运行 npm.cmd ci 和 npm.cmd run build，再启动预览。');
  }
  directory = await realpath(directory);
  if (!await exists(resolve(directory, 'index.html'))) throw new Error('预览目录缺少 index.html，请重新解压完整成品包。');
  const server = createServer(async (request, response) => {
    try {
      if (!['GET', 'HEAD'].includes(request.method)) { finish(response, 405, { Allow: 'GET, HEAD' });return; }
      const url = new URL(request.url, 'http://127.0.0.1');
      let pathname;
      try { pathname = decodeURIComponent(url.pathname); } catch { finish(response, 400);return; }
      if (options.base !== '/' && pathname === options.base.slice(0, -1)) {
        finish(response, 308, { Location: options.base + url.search });return;
      }
      if (!pathname.startsWith(options.base)) { finish(response, 404);return; }
      let name = pathname.slice(options.base.length);
      if (!name) name = 'index.html';
      if (name.includes('\\') || name.includes('\0') || name.split('/').some(p => p.startsWith('.'))) { finish(response, 404);return; }
      let file;
      try { file = await realpath(resolve(directory, name)); } catch { finish(response, 404);return; }
      const rel = relative(directory, file);
      if (isAbsolute(rel) || rel === '..' || rel.startsWith('..' + sep)) { finish(response, 404);return; }
      const info = await stat(file);if (!info.isFile()) { finish(response, 404);return; }
      const headers = { 'Content-Type': types[extname(file).toLowerCase()] ?? 'application/octet-stream',
        'Content-Length': info.size, 'Accept-Ranges': 'bytes',
        'Cache-Control': name.startsWith('assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
        'X-Content-Type-Options': 'nosniff' };
      let start = 0, end = info.size - 1, status = 200;
      if (request.headers.range) {
        const range = /^bytes=(\d*)-(\d*)$/.exec(request.headers.range);
        if (!range || (!range[1] && !range[2]) || !info.size) { finish(response, 416, { 'Content-Range': `bytes */${info.size}` });return; }
        start = range[1] ? Number(range[1]) : Math.max(0, info.size - Number(range[2]));
        end = range[1] ? (range[2] ? Math.min(Number(range[2]), end) : end) : end;
        if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start > end || start >= info.size) {
          finish(response, 416, { 'Content-Range': `bytes */${info.size}` });return;
        }
        status = 206;headers['Content-Range'] = `bytes ${start}-${end}/${info.size}`;headers['Content-Length'] = end - start + 1;
      }
      response.writeHead(status, headers);
      if (request.method === 'HEAD' || !info.size) { response.end();return; }
      const stream = createReadStream(file, { start, end });stream.on('error', () => response.destroy());stream.pipe(response);
    } catch { if (!response.headersSent) finish(response, 500);else response.destroy(); }
  });
  async function listen(port) {
    return new Promise((accept, reject) => {
      const error = e => { server.off('listening', ready);reject(e); };
      const ready = () => { server.off('error', error);accept(); };
      server.once('error', error);server.once('listening', ready);server.listen(port, '127.0.0.1');
    });
  }
  for (let attempt = 0; ; attempt++) {
    try { await listen(options.port + attempt);break; }
    catch (error) {
      if (error.code !== 'EADDRINUSE' || options.strict || !options.port || attempt >= 20 || options.port + attempt >= 65535)
        throw new Error(error.code === 'EADDRINUSE' ? '端口已被占用。关闭自己的旧预览窗口，或使用 --port 指定其他端口。' : error.message);
      console.log(`端口 ${options.port + attempt} 正在使用，尝试下一个端口。`);
    }
  }
  const url = `http://127.0.0.1:${server.address().port}${options.base}`;
  console.log(`\n预览地址：${url}\n此地址只供本机访问。请保留本窗口，按 Ctrl+C 停止预览。`);
  if (options.json) console.log('SAKAN_PREVIEW_READY ' + JSON.stringify({ url, directory, pid: process.pid }));
  if (options.open) {
    const command = process.platform === 'win32' ? 'rundll32.exe' : process.platform === 'darwin' ? 'open' : 'xdg-open';
    const openArgs = process.platform === 'win32' ? ['url.dll,FileProtocolHandler', url] : [url];
    const child = spawn(command, openArgs, { detached: true, stdio: 'ignore' });
    child.on('error', () => console.log('请将上方预览地址复制到浏览器打开。'));child.unref();
  }
  const stop = () => { server.closeIdleConnections();server.close(() => process.exit(0));setTimeout(() => process.exit(0), 2000).unref(); };
  process.once('SIGINT', stop);process.once('SIGTERM', stop);
}
main().catch(error => { console.error(`\n无法启动预览：${error.message}`);process.exitCode = 1; });
