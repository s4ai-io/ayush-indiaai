const { spawn } = require('child_process');
const os = require('os');

const port = 3000;

console.log('\n\x1b[36m%s\x1b[0m', '  ▲ Next.js Dev Server (Secure local network mode)');
console.log(`  ➜  Local:   \x1b[34mhttps://localhost:${port}/\x1b[0m`);

const nets = os.networkInterfaces();
for (const name of Object.keys(nets)) {
  for (const net of nets[name]) {
    // Only display external IPv4 interfaces
    if ((net.family === 'IPv4' || net.family === 4) && !net.internal) {
      console.log(`  ➜  Network: \x1b[34mhttps://${net.address}:${port}/\x1b[0m`);
    }
  }
}
console.log('');

// Spawn next dev process with the SSL and Host settings
const nextDev = spawn('next', [
  'dev',
  '-H', '0.0.0.0',
  '--experimental-https',
  '--experimental-https-key', './dev.key',
  '--experimental-https-cert', './dev.crt'
], { stdio: 'inherit', shell: true });

nextDev.on('exit', (code) => {
  process.exit(code || 0);
});
