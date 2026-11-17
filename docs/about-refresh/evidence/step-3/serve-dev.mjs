import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../../../../',import.meta.url));
const server=await createServer({root,logLevel:'warn',server:{host:'127.0.0.1',port:0,strictPort:true}});
await server.listen();
console.log(JSON.stringify({port:server.httpServer.address().port}));
let closing=false;
async function close(){if(closing)return;closing=true;await server.close();process.exit(0)}
process.on('SIGTERM',close);process.on('SIGINT',close);
