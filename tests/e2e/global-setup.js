const fs = require('fs');
const path = require('path');
const { execFileSync, spawn } = require('child_process');

const workspace = path.resolve(__dirname, '../..');
const python =
    process.env.PYTHON ||
    (process.platform === 'win32'
        ? path.join(workspace, '.venv', 'Scripts', 'python.exe')
        : path.join(workspace, '.venv', 'bin', 'python'));

async function esperarServidor(server, output) {
    const deadline = Date.now() + 30_000;
    while (Date.now() < deadline) {
        if (server.exitCode !== null) {
            throw new Error(`Servidor Flask encerrou antes dos testes.\n${output.join('')}`);
        }
        try {
            const response = await fetch('http://127.0.0.1:5179/api/health');
            if (response.ok) return;
        } catch {
            // O processo ainda está inicializando.
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
    throw new Error(`Servidor Flask não respondeu em 30 segundos.\n${output.join('')}`);
}

async function encerrarServidor(server) {
    if (server.exitCode !== null) return;
    server.kill();
    await Promise.race([
        new Promise((resolve) => server.once('exit', resolve)),
        new Promise((resolve) => setTimeout(resolve, 1_000))
    ]);
    if (server.exitCode !== null) return;
    if (process.platform === 'win32') {
        try {
            execFileSync('taskkill', ['/pid', String(server.pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
        } catch {
            // O sinal anterior já pode ter encerrado o processo antes do taskkill.
        }
    } else {
        server.kill('SIGKILL');
    }
}

module.exports = async () => {
    if (!fs.existsSync(python)) throw new Error(`Python do ambiente virtual não encontrado: ${python}`);
    const output = [];
    const server = spawn(python, ['app.py'], {
        cwd: workspace,
        env: {
            ...process.env,
            DATA_AUTO_REFRESH_HOURS: '0',
            FLASK_DEBUG: '0',
            FLASK_HOST: '127.0.0.1',
            FLASK_PORT: '5179'
        },
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true
    });
    server.stdout.on('data', (chunk) => output.push(chunk.toString()));
    server.stderr.on('data', (chunk) => output.push(chunk.toString()));

    try {
        await esperarServidor(server, output);
    } catch (error) {
        await encerrarServidor(server);
        throw error;
    }
    return () => encerrarServidor(server);
};
