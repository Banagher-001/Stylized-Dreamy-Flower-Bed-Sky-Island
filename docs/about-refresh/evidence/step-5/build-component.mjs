import { build } from 'vite';
import { readFile,writeFile,readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
const root=fileURLToPath(new URL('../../../../',import.meta.url));
const result=await build({root,configFile:false,base:'./',logLevel:'warn',build:{write:false,assetsInlineLimit:Infinity,minify:true,rollupOptions:{input:resolve(root,'dev/about-refresh/index.html')}}});
const output=(Array.isArray(result)?result:[result]).flatMap(x=>x.output),decode=x=>typeof x==='string'?x:Buffer.from(x).toString('utf8');
const scripts=output.filter(x=>x.type==='chunk'),css=output.filter(x=>x.type==='asset'&&x.fileName.endsWith('.css'));
if(scripts.length!==1||css.length!==1||scripts[0].imports.length)throw Error('Review must remain standalone');
let html=decode(output.find(x=>x.type==='asset'&&x.fileName.endsWith('index.html')).source);
html=html.replace(/<script\b[^>]*\bsrc="[^"]+"[^>]*><\/script>/g,()=>`<script type="module">${scripts[0].code.replaceAll('</script','<\\/script')}</script>`).replace(/<link\b[^>]*rel="stylesheet"[^>]*>/g,()=>`<style>${decode(css[0].source)}</style>`);
if(/\b(?:href|src)="(?!data:|#)[^"]+"/.test(html))throw Error('External runtime dependency');
const target=resolve(root,'docs/about-refresh/evidence/step-5/component-preview.html');await writeFile(target,html);
const sha=data=>createHash('sha256').update(data).digest('hex'),sources=[];
for(const folder of ['src/tour/about-refresh','src/assets/tool-marks'])for(const name of (await readdir(resolve(root,folder))).sort()){
 const path=`${folder}/${name}`,raw=await readFile(resolve(root,path));sources.push({path,bytes:raw.length,sha256:sha(raw)});
}
await writeFile(new URL('component-build.json',import.meta.url),JSON.stringify({output:{path:'docs/about-refresh/evidence/step-5/component-preview.html',bytes:Buffer.byteLength(html),sha256:sha(html)},sources,entry:'dev/about-refresh/index.html',standalone:true,additionalWebGLRenderer:false},null,2)+'\n');
console.log(JSON.stringify({reviewBuilt:true,bytes:Buffer.byteLength(html),sha256:sha(html)}));
