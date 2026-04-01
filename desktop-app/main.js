const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const http = require('http');
const spawn = require('cross-spawn');
const net = require('net');
const fs = require('fs');

let backendProcess = null;
let backendPortFile = null;

function resolveBackendPortFile() {
  const localAppData = process.env.LOCALAPPDATA;
  if (localAppData) {
    return path.join(localAppData, 'Link1Die', 'port.txt');
  }
  return path.join(app.getPath('userData'), 'port.txt');
}

function resolveBackendLogFile() {
  const localAppData = process.env.LOCALAPPDATA;
  if (localAppData) {
    return path.join(localAppData, 'Link1Die', 'logs', 'server.log');
  }
  return path.join(app.getPath('userData'), 'logs', 'server.log');
}

function tryListen(port) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(port, '127.0.0.1', () => {
      const address = server.address();
      const pickedPort = typeof address === 'object' && address ? address.port : port;
      server.close(() => resolve(pickedPort));
    });
  });
}

async function pickFreePort(preferredPorts = []) {
  for (const port of preferredPorts) {
    try {
      // eslint-disable-next-line no-await-in-loop
      return await tryListen(port);
    } catch {
      // keep trying
    }
  }
  return tryListen(0);
}

function waitForHealthy(url, timeoutMs = 20000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(url, (res) => {
        res.resume();
        if (res.statusCode === 200) {
          resolve();
        } else if (Date.now() - startedAt > timeoutMs) {
          reject(new Error(`Health check failed with status ${res.statusCode}`));
        } else {
          setTimeout(attempt, 300);
        }
      });
      req.on('error', () => {
        if (Date.now() - startedAt > timeoutMs) {
          reject(new Error('Backend did not become ready'));
        } else {
          setTimeout(attempt, 300);
        }
      });
    };
    attempt();
  });
}

function waitForPortFile(portFile, timeoutMs = 20000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = () => {
      try {
        if (fs.existsSync(portFile)) {
          const value = String(fs.readFileSync(portFile, 'utf-8')).trim();
          const port = Number.parseInt(value, 10);
          if (Number.isFinite(port) && port > 0) {
            resolve(port);
            return;
          }
        }
      } catch {
        // ignore and retry
      }

      if (Date.now() - startedAt > timeoutMs) {
        reject(new Error('Timed out waiting for backend port'));
        return;
      }

      setTimeout(attempt, 250);
    };
    attempt();
  });
}

async function startBackend(port) {
  const portFile = resolveBackendPortFile();
  backendPortFile = portFile;
  try {
    fs.mkdirSync(path.dirname(portFile), { recursive: true });
  } catch {
    // ignore
  }
  try {
    if (fs.existsSync(portFile)) fs.unlinkSync(portFile);
  } catch {
    // ignore
  }

  const env = {
    ...process.env,
    API_PORT: String(port),
    PORT_FILE: portFile,
    WEB_DIST_DIR: app.isPackaged
      ? path.join(process.resourcesPath, 'web_dist')
      : path.join(__dirname, '..', 'backend', 'web_dist'),
  };

  if (app.isPackaged) {
    const exePath = path.join(process.resourcesPath, 'Link1DieServer.exe');
    backendProcess = spawn(exePath, [], { env, stdio: 'ignore', windowsHide: true });
  } else {
    // Dev mode: requires Python installed (or a backend venv).
    const backendDir = path.join(__dirname, '..', 'backend');
    const venvPython = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python';
    const scriptPath = path.join(backendDir, 'desktop_server.py');
    backendProcess = spawn(pythonCmd, [scriptPath], { env, stdio: 'inherit', windowsHide: true });
  }

  backendProcess.on('error', (err) => {
    dialog.showErrorBox('Link1Die backend failed', String(err));
  });
}

function stopBackend() {
  if (!backendProcess) return;
  try {
    backendProcess.kill();
  } catch {
    // ignore
  }
  backendProcess = null;
  if (backendPortFile) {
    try {
      if (fs.existsSync(backendPortFile)) fs.unlinkSync(backendPortFile);
    } catch {
      // ignore
    }
  }
}

async function createMainWindow() {
  // Prefer letting the backend bind to a free port to avoid race conditions.
  // (Passing 0 means "pick any free port".)
  const preferredPort = app.isPackaged ? 0 : await pickFreePort([51733, 51734, 51735, 51736, 51737]);
  await startBackend(preferredPort);

  const port = await waitForPortFile(resolveBackendPortFile());

  const healthUrl = `http://127.0.0.1:${port}/health`;
  await waitForHealthy(healthUrl);

  const win = new BrowserWindow({
    width: 1200,
    height: 760,
    minWidth: 980,
    minHeight: 640,
    backgroundColor: '#0b1220',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.on('closed', () => stopBackend());

  await win.loadURL(`http://127.0.0.1:${port}/`);
}

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => stopBackend());

app.whenReady().then(async () => {
  try {
    await createMainWindow();
  } catch (err) {
    stopBackend();
    const logFile = resolveBackendLogFile();
    let details = String(err);
    try {
      if (fs.existsSync(logFile)) {
        const logText = fs.readFileSync(logFile, 'utf-8');
        if (logText.trim()) {
          details += `\n\nBackend log:\n${logText.slice(-4000)}`;
        }
      }
    } catch {
      // ignore
    }
    dialog.showErrorBox('Link1Die failed to start', details);
    app.quit();
  }
});
