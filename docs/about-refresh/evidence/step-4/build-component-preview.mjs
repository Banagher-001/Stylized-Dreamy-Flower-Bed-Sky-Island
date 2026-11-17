import { build } from 'vite';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
const root = fileURLToPath(new URL('../../../../', import.meta.url));
const result = await build({
  configFile: false, root, base: './', logLevel: 'warn',
  build: { write: false, assetsInlineLimit: Infinity, minify: true,
    rollupOptions: { input: resolve(root, 'dev/about-refresh/index.html') } },
});
const outputs = (Array.isArray(result) ? result : [result]).flatMap(item => item.output);
const decode = source => typeof source === 'string' ? source : Buffer.from(source).toString('utf8');
let html = decode(outputs.find(item => item.type === 'asset' && item.fileName.endsWith('index.html')).source);
const scripts = outputs.filter(item => item.type === 'chunk');
const styles = outputs.filter(item => item.type === 'asset' && item.fileName.endsWith('.css'));
if (scripts.length !== 1 || styles.length !== 1 || scripts[0].imports.length || scripts[0].dynamicImports.length) throw Error('Preview must be one standalone bundle');
html = html.replace(/<script\b[^>]*\bsrc="[^"]+"[^>]*><\/script>/g, () => `<script type="module">${scripts[0].code.replaceAll('</script', '<\\/script')}</script>`);
html = html.replace(/<link\b[^>]*rel="stylesheet"[^>]*>/g, () => `<style>${decode(styles[0].source)}</style>`);
if (/\b(?:src|href)="(?!data:|#)[^"]+"/.test(html)) throw Error('External entry dependency');
const target = resolve(root, 'docs/about-refresh/evidence/step-4/component-preview.html');
await writeFile(target, html);
const sha = value => createHash('sha256').update(value).digest('hex');
const names = ['types.ts','dom.ts','content.ts','createToolBrowser.ts','createAboutView.ts','aboutRefresh.css','preview.ts','preview.css'];
const files = [];
for (const name of names) {
  const path = `src/tour/about-refresh/${name}`, data = await readFile(resolve(root,path));
  files.push({path,bytes:data.length,sha256:sha(data)});
}
const record = {generator:'Vite standalone development entry, no production config changes',entry:'dev/about-refresh/index.html',output:{path:'docs/about-refresh/evidence/step-4/component-preview.html',bytes:Buffer.byteLength(html),sha256:sha(html)},sources:files,externalRuntimeDependencies:false,productionIntegration:false};
await writeFile(new URL('component-build.json',import.meta.url),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify({built:true,bytes:record.output.bytes,sha256:record.output.sha256}));
