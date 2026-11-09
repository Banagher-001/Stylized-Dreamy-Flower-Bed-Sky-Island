// Bind deterministic, controller-only checks to the current actual source bytes.
// This injected scheduler is not a browser input or real-time video test.
import { createServer } from 'vite';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const root = fileURLToPath(new URL('../../', import.meta.url));
const out = resolve(root, 'docs/evidence/garden-enhancement-step-4');
const build = JSON.parse(readFileSync(resolve(out, 'build-verification.json'), 'utf8'));
const input = 'src/tour/autoGuide.ts';
const digest = () => createHash('sha256').update(readFileSync(resolve(root, input))).digest('hex');
const before = digest();
if (before !== build.buildInputsSha256[input]) throw Error('Controller source differs from tested build');
const server = await createServer({ root, configFile: false, server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
try {
  const { inspectAutoGuide } = await server.ssrLoadModule('/tests/garden-enhancement/inspect_auto_guide.js');
  const result = inspectAutoGuide();
  if (!result.passed || before !== digest()) throw Error('Controller gate or source identity failed');
  writeFileSync(resolve(out, 'controller-deterministic.json'), JSON.stringify({ ...result, candidateId: build.candidateId, sourceSha256: { [input]: before } }, null, 2) + '\n');
  process.stdout.write(`PASS ${result.cases.length} controller groups bound to ${build.candidateId}\n`);
} finally {
  await server.close();
}
