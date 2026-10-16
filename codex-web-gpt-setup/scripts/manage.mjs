import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { spawn, execFileSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';

const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const home = process.env.USERPROFILE || os.homedir();
const local = process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local');
const roaming = process.env.APPDATA || path.join(home, 'AppData', 'Roaming');
const codexHome = process.env.CODEX_HOME || path.join(home, '.codex');
const omoHome = process.env.OMO_CODING_AGENT_DIR || path.join(home, '.omo', 'agent');
const gjcHome = process.env.GJC_CODING_AGENT_DIR || path.join(home, '.gjc', 'agent');
const webHome = path.join(home, '.codex-chatgpt-web');
const store = path.join(local, 'CodexWebGPTSetup');
const appExe = path.join(local, 'Programs', 'Codex Web GPT', 'Codex Web GPT.exe');
const WEB_MODEL = 'chatgpt-web/gpt-6-sol';
// Web-only routing. Never silently switch agent runners to subscription providers.
const OMO_MODEL = 'codex-web-gpt/chatgpt-web/gpt-6-sol';
const GJC_MODEL = 'codex-web-gpt/chatgpt-web/gpt-6-sol:high';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const exists = p => fs.existsSync(p);
const readJson = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const say = value => console.log(typeof value === 'string' ? value : JSON.stringify(value, null, 2));
const fail = (message, code = 1) => { const error = new Error(message); error.exitCode = code; throw error; };

export function copyPackage(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    if (['tests', '__pycache__'].includes(entry.name)) continue;
    const input = path.join(from, entry.name), output = path.join(to, entry.name);
    if (entry.isDirectory()) copyPackage(input, output);
    else if (entry.isFile()) fs.writeFileSync(output, fs.readFileSync(input));
    else fail('Skill package contains an unsupported link');
  }
}

export function parseJsonc(text) {
  let clean = '', quoted = false, escaped = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i], next = text[i + 1];
    if (quoted) {
      clean += c;
      if (escaped) escaped = false;
      else if (c === '\\') escaped = true;
      else if (c === '"') quoted = false;
    } else if (c === '"') { quoted = true; clean += c; }
    else if (c === '/' && next === '/') { while (i < text.length && text[i] !== '\n') i++; clean += '\n'; }
    else if (c === '/' && next === '*') {
      i += 2;
      while (i < text.length && !(text[i] === '*' && text[i + 1] === '/')) i++;
      if (i === text.length) throw new Error('Unterminated JSONC comment');
      i++; clean += ' ';
    } else clean += c;
  }
  let result = ''; quoted = false; escaped = false;
  for (let i = 0; i < clean.length; i++) {
    const c = clean[i];
    if (!quoted && c === ',' && /^\s*[}\]]/.test(clean.slice(i + 1))) continue;
    result += c;
    if (quoted) {
      if (escaped) escaped = false;
      else if (c === '\\') escaped = true;
      else if (c === '"') quoted = false;
    } else if (c === '"') quoted = true;
  }
  return JSON.parse(result.replace(/^\uFEFF/, ''));
}

export function tuneEntry(entry = {}) {
  const value = { ...entry, model: OMO_MODEL, models: [{ model: OMO_MODEL, reasoning: 'high' }], reasoning: 'high' };
  for (const key of ['variant', 'reasoningEffort', 'thinking', 'fallback_models']) delete value[key];
  return value;
}

export function tuneOmo(config, roles, categories) {
  const result = structuredClone(config);
  function tune(view) {
    view.model_profile = OMO_MODEL + ':high';
    view.agents ??= {}; view.categories ??= {};
    for (const name of new Set([...roles, ...Object.keys(view.agents)])) view.agents[name] = tuneEntry(view.agents[name]);
    for (const name of new Set([...categories, ...Object.keys(view.categories)])) view.categories[name] = tuneEntry(view.categories[name]);
  }
  tune(result);
  // Existing runtime-specific views may override the global view.
  for (const key of ['[native]', '[senpi]', '[codex]', '[opencode]']) if (result[key] && Object.keys(result[key]).length) tune(result[key]);
  return result;
}

function backupDir() { const dir = path.join(store, 'backups', `${new Date().toISOString().replace(/[:.]/g, '-')}-${randomUUID().slice(0, 8)}`); fs.mkdirSync(dir, { recursive: true }); return dir; }
export function registerOmoWebModel(provider) {
  if (!provider || !Array.isArray(provider.models)) fail('OmO codex-web-gpt provider/model catalog is missing');
  const output = structuredClone(provider);
  if (!output.models.some(model => model.id === WEB_MODEL)) {
    const prototype = output.models.find(model => model.id === 'chatgpt-web/gpt-5.6-sol');
    if (!prototype) fail('OmO web provider has no compatible model template');
    output.models.unshift({ ...prototype, id: WEB_MODEL, name: 'ChatGPT Web · GPT-6 Sol High', reasoning: true });
  }
  return output;
}
export function registerGjcWebModel(yaml) {
  if (yaml.includes('id: "chatgpt-web/gpt-6-sol"')) return yaml;
  const location = /(^  codex-web-gpt:\s*\r?\n(?:^(?:    |\s*$).*\r?\n)*?^    models:\s*\r?\n)/m;
  if (!location.test(yaml)) fail('GJC codex-web-gpt models section is missing');
  return yaml.replace(location, '$1      - id: "chatgpt-web/gpt-6-sol"\n        name: "ChatGPT Web · GPT-6 Sol High"\n        reasoning: true\n        input: [text, image]\n        contextWindow: 256000\n        maxTokens: 32000\n');
}
function registerWebCatalogs(target, dir, manifest) {
  if (target === 'all' || target === 'omo') {
    const file = path.join(omoHome, 'models.json');
    if (!exists(file)) fail('OmO codex-web-gpt catalog missing; cannot safely select web model');
    const config = readJson(file);
    if (!config.providers?.['codex-web-gpt']) fail('OmO web provider missing');
    config.providers['codex-web-gpt'] = registerOmoWebModel(config.providers['codex-web-gpt']);
    saveJson(file, config, dir, manifest);
  }
  if (target === 'all' || target === 'gjc') {
    const file = path.join(gjcHome, 'models.yml');
    if (!exists(file)) fail('GJC codex-web-gpt catalog missing; cannot safely select web model');
    const before = fs.readFileSync(file, 'utf8');
    const after = registerGjcWebModel(before);
    if (after !== before) {
      const saved = path.join(dir, `file-${manifest.length}.bak`);
      fs.copyFileSync(file, saved);
      manifest.push({ target: file, backup: saved });
      fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
      fs.writeFileSync(file, after, 'utf8');
    }
  }
}
function saveJson(file, value, backup, manifest) {
  const text = JSON.stringify(value, null, 2) + '\n';
  if (exists(file) && fs.readFileSync(file, 'utf8') === text) return;
  const saved = path.join(backup, `file-${manifest.length}.bak`);
  if (exists(file)) fs.copyFileSync(file, saved);
  manifest.push({ target: file, backup: exists(file) ? saved : null });
  fs.writeFileSync(path.join(backup, 'manifest.json'), JSON.stringify(manifest, null, 2));
  fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, text, 'utf8');
}
function exeOnPath(name) {
  for (const directory of (process.env.PATH || '').split(path.delimiter)) {
    const candidate = path.join(directory.replace(/^"|"$/g, ''), name);
    if (exists(candidate)) return candidate;
  }
  return null;
}
export async function run(file, args, { input, timeout = 180000, inherit = false, env = process.env, cwd } = {}) {
  return await new Promise((resolve, reject) => {
    const child = spawn(file, args, { windowsHide: true, stdio: inherit ? 'inherit' : ['pipe', 'pipe', 'pipe'], shell: false, env, cwd });
    let stdout = '', stderr = '';
    child.stdout?.on('data', chunk => { stdout += chunk; });
    child.stderr?.on('data', chunk => { stderr += chunk; });
    if (child.stdin) child.stdin.end(input);
    const timer = setTimeout(() => { child.kill(); reject(new Error('Verification subprocess timed out')); }, timeout);
    child.once('error', error => { clearTimeout(timer); reject(error); });
    child.once('close', code => { clearTimeout(timer); resolve({ code, stdout, stderr }); });
  });
}
async function request(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(15000) });
  if (!response.ok) fail(`HTTP ${response.status}: ${new URL(url).pathname}`);
  return await response.json();
}
export function route() {
  const config = readJson(path.join(webHome, 'config.json'));
  if (!['127.0.0.1', 'localhost'].includes(config.host) || !Number.isInteger(config.port)) fail('Expected a local loopback bridge');
  return `http://${config.host}:${config.port}`;
}
export async function health() { return request(`${route()}/healthz`); }
export async function idle() {
  const state = await health();
  if (state.active_http_turns || state.active_browser_turns) fail('A ChatGPT/Codex turn is active. Retry after it finishes.', 3);
}
export async function launcher(method, args = [], timeout = 180000) {
  const allowed = new Set(['snapshot', 'doctor', 'smokeTest', 'verifyMcp', 'setupCore', 'setupMcp', 'openLogin', 'setLanguage', 'setAutostart', 'setBiggerContext', 'setSkillAttachments', 'setFreshConversationPerTurn', 'setUseSavedChats', 'setPreference', 'setBrowserInteractionMode', 'windowControl']);
  if (!allowed.has(method)) fail('Unknown launcher method');
  const descriptor = readJson(path.join(webHome, 'runtime', 'launcher-browser.json'));
  const endpoint = new URL(descriptor.endpoint);
  if (!['127.0.0.1', 'localhost'].includes(endpoint.hostname)) fail('Launcher endpoint must be local');
  const targets = await request(`${endpoint.origin}/json/list`);
  const target = targets.find(t => t.type === 'page' && t.url.startsWith('file:') && t.url.includes('app.asar/dist/index.html'));
  if (!target) fail('Launcher control API is unavailable; start Codex Web GPT');
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(target.webSocketDebuggerUrl);
    let settled = false;
    const end = (error, value) => { if (settled) return; settled = true; clearTimeout(timer); socket.close(); error ? reject(error) : resolve(value); };
    const timer = setTimeout(() => end(new Error(`Launcher ${method} timed out`)), timeout);
    socket.addEventListener('open', () => socket.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: {
      expression: `(async()=>JSON.stringify(await window.codexWebLauncher[${JSON.stringify(method)}](...${JSON.stringify(args)})))()`, awaitPromise: true, returnByValue: true,
    } })));
    socket.addEventListener('message', event => {
      const result = JSON.parse(event.data);
      if (result.id !== 1) return;
      if (result.error || result.result?.exceptionDetails) return end(new Error(`Launcher ${method} failed; inspect the app Activity panel`));
      let value = result.result?.result?.value;
      if (typeof value === 'string') value = JSON.parse(value);
      end(null, value);
    });
    socket.addEventListener('error', () => end(new Error('Launcher connection failed')));
    socket.addEventListener('close', () => end(new Error(`Launcher closed before ${method} completed`)));
  });
}
export async function startApp() {
  if (!exists(appExe)) await installApp(false);
  try { await launcher('snapshot'); return; } catch {}
  const child = spawn(appExe, [], { detached: true, windowsHide: true, stdio: 'ignore' }); child.unref();
  for (let i = 0; i < 45; i++) { try { await launcher('snapshot'); return; } catch {} await sleep(1000); }
  fail('Launcher did not become ready in 45 seconds');
}
async function catalog() {
  const authPath = path.join(codexHome, 'auth.json');
  if (!exists(authPath)) fail('Native Codex login is missing. Run codex login, then retry.', 2);
  const tokens = readJson(authPath).tokens;
  if (!tokens?.access_token) fail('ChatGPT OAuth login is required for the native Codex route', 2);
  const headers = { Authorization: `Bearer ${tokens.access_token}` };
  if (tokens.account_id) headers['ChatGPT-Account-Id'] = tokens.account_id;
  const result = await request(`${route()}/v1/models?client_version=0.159.2`, { headers });
  const models = result.models || result.data || result;
  if (!Array.isArray(models)) fail('Unexpected model catalog');
  const row = models.find(m => (m.slug || m.id) === WEB_MODEL);
  if (!row?.supported_reasoning_levels?.some(level => (level.effort || level) === 'high')) fail('This account does not advertise GPT-6 Sol High', 2);
  return models.filter(m => m.visibility !== 'hide' && (m.slug || m.id || '').startsWith('chatgpt-web/')).map(m => ({ model: m.slug || m.id, name: m.display_name, efforts: m.supported_reasoning_levels?.map(l => l.effort || l) }));
}
export function codexBinary() {
  const shim = exeOnPath('codex.cmd');
  const roots = [shim && path.dirname(shim), path.join(local, 'Programs', 'nodejs'), path.join(roaming, 'npm')].filter(Boolean);
  for (const root of roots) {
    const js = path.join(root, 'node_modules', '@openai', 'codex', 'bin', 'codex.js');
    if (exists(js)) return { exe: process.execPath, prefix: [js] };
  }
  const exe = exeOnPath('codex.exe');
  if (exe) return { exe, prefix: [] };
  fail('Native Codex CLI is missing. Install @openai/codex with npm.', 2);
}
function omoBinary() {
  const exe = exeOnPath('omo.exe');
  if (!exe) fail('Native omo.exe is missing. This integration targets OmO Native, not the old omo.cmd shim.', 2);
  return exe;
}
function gjcBinary(required = true) {
  const exe = [path.join(local, 'gjc', 'gjc.exe'), exeOnPath('gjc.exe')].find(p => p && exists(p));
  if (!exe && required) fail('GJC native executable is missing. Install GJC first.', 2);
  return exe;
}
async function gjcConfig(key) {
  const result = await run(gjcBinary(), ['config', 'get', key, '--json']);
  if (result.code) fail('GJC does not support setting: ' + key, 2);
  try { return JSON.parse(result.stdout).value; } catch { fail('Unexpected GJC configuration output'); }
}
export function tuneGjcMappings(roles, overrides, names) {
  const modelRoles = { ...roles };
  for (const name of new Set(['default', 'executor', 'architect', 'planner', 'critic', 'image', ...Object.keys(modelRoles)])) modelRoles[name] = GJC_MODEL;
  const agentModelOverrides = { ...overrides };
  for (const name of new Set(['executor', 'architect', 'planner', 'critic', ...names, ...Object.keys(agentModelOverrides)])) agentModelOverrides[name] = GJC_MODEL;
  return { modelRoles, agentModelOverrides };
}
function gjcAgentNames(project) {
  const names = new Set();
  const roots = [path.join(gjcHome, 'agents'), path.join(home, '.gjc', 'agents')];
  if (project) roots.push(path.join(process.cwd(), '.gjc', 'agents'));
  for (const root of roots) {
    if (!exists(root)) continue;
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      if (!entry.isFile() || !entry.name.endsWith('.md')) continue;
      const text = fs.readFileSync(path.join(root, entry.name), 'utf8').replace(/^\uFEFF/, '');
      const header = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text)?.[1];
      const name = header && /^name:\s*['"]?([a-zA-Z0-9_-]+)['"]?\s*$/m.exec(header)?.[1];
      if (!name) fail('Unsupported GJC agent frontmatter: ' + entry.name);
      // The native task selector overrides model frontmatter. Reject a separate
      // explicit low thinking field instead of silently claiming it is High.
      const thinking = /^(?:thinkingLevel|thinking):\s*['"]?([^'"\s]+)['"]?\s*$/m.exec(header)?.[1];
      if (thinking && thinking !== 'high') fail('GJC agent explicitly overrides High: ' + name);
      names.add(name);
    }
  }
  return [...names];
}
async function configureGjc(dir, manifest, project) {
  gjcBinary();
  const tuned = tuneGjcMappings(await gjcConfig('modelRoles') || {}, await gjcConfig('task.agentModelOverrides') || {}, gjcAgentNames(project));
  const configPath = path.join(gjcHome, 'config.yml');
  const saved = path.join(dir, `file-${manifest.length}.bak`);
  if (exists(configPath)) fs.copyFileSync(configPath, saved);
  manifest.push({ target: configPath, backup: exists(configPath) ? saved : null });
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  // Use GJC's own YAML parser and durable config writer; no extra dependency.
  if (await gjcConfig('modelProfile.default')) {
    const result = await run(gjcBinary(), ['config', 'reset', 'modelProfile.default', '--json']);
    if (result.code) fail('GJC automatic profile reset failed');
  }
  const settings = { modelRoles: tuned.modelRoles, 'task.agentModelOverrides': tuned.agentModelOverrides, defaultThinkingLevel: 'high', modelProviderOrder: ['codex-web-gpt'], 'task.autorouting.enabled': false };
  for (const [key, value] of Object.entries(settings)) {
    if (JSON.stringify(await gjcConfig(key)) === JSON.stringify(value)) continue;
    const result = await run(gjcBinary(), ['config', 'set', key, typeof value === 'object' ? JSON.stringify(value) : String(value), '--json']);
    if (result.code || JSON.stringify(await gjcConfig(key)) !== JSON.stringify(value)) fail('GJC setting failed: ' + key);
  }
  return { provider: 'codex-web-gpt', model: WEB_MODEL, effort: 'high', verified: false, roles: Object.keys(tuned.modelRoles), agents: Object.keys(tuned.agentModelOverrides), config: configPath };
}
function discoverOmo() {
  const runtimeRoot = path.join(home, '.omo', 'binary-runtime');
  const versions = exists(runtimeRoot) ? fs.readdirSync(runtimeRoot).filter(v => /^\d+\.\d+\.\d+$/.test(v)).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })).reverse() : [];
  const runtime = versions.map(v => path.join(runtimeRoot, v, 'plugin', 'extensions', 'omo-task.js')).find(exists);
  if (!runtime) fail('OmO Native task runtime is missing; cannot prove its agent/category names');
  const text = fs.readFileSync(runtime, 'utf8');
  const roles = [...text.matchAll(/name:"([a-z][a-z0-9-]+)",description:.{0,1000}?mode:"(?:subagent|primary|all)"/g)].map(m => m[1]);
  const categories = [...text.matchAll(/name:"([a-z][a-z0-9-]+)",config:\{model:/g)].map(m => m[1]);
  if (!roles.length || !categories.length) fail('Unsupported OmO task runtime; agent discovery failed');
  return { roles: [...new Set(roles)], categories: [...new Set(categories)] };
}
async function configureAgents(target = 'all', project = false) {
  if (!['all', 'codex', 'omo', 'gjc'].includes(target)) fail('agents target must be all, codex, omo, or gjc');
  const dir = backupDir(); const manifest = [];
  const previous = path.join(store, 'reports', 'agents.json');
  const report = { ...(exists(previous) ? readJson(previous) : {}), backup: dir };
  if (target === 'all' && !gjcBinary(false)) {
    registerWebCatalogs('omo', dir, manifest);
  } else if (target !== 'codex') registerWebCatalogs(target, dir, manifest);
  if (target === 'all' || target === 'omo') {
    omoBinary();
    const discovered = discoverOmo();
    const settingsPath = path.join(omoHome, 'settings.json');
    const settings = exists(settingsPath) ? readJson(settingsPath) : {};
    settings.defaultProvider = 'codex-web-gpt'; settings.defaultModel = WEB_MODEL; settings.defaultThinkingLevel = 'high';
    settings.modelThinkingLevels = { ...settings.modelThinkingLevels, [OMO_MODEL]: 'high' };
    settings.modelLastOnThinkingLevels = { ...settings.modelLastOnThinkingLevels, [OMO_MODEL]: 'high' };
    settings.recommendedModels = [WEB_MODEL];
    settings.warnings = { ...settings.warnings, offRecommendedModel: true };
    settings.retry = { ...settings.retry, fallbackChains: { ...settings.retry?.fallbackChains, [OMO_MODEL]: [] } };
    saveJson(settingsPath, settings, dir, manifest);
    const configDir = project ? path.join(process.cwd(), '.omo') : path.join(home, '.omo');
    const configPath = exists(path.join(configDir, 'omo.jsonc')) ? path.join(configDir, 'omo.jsonc') : path.join(configDir, 'omo.json');
    const config = exists(configPath) ? parseJsonc(fs.readFileSync(configPath, 'utf8')) : {};
    const tuned = tuneOmo(config, discovered.roles, discovered.categories);
    saveJson(configPath, tuned, dir, manifest);
    report.omo = { provider: 'codex-web-gpt', model: WEB_MODEL, effort: 'high', verified: false, roles: Object.keys(tuned.agents), categories: Object.keys(tuned.categories), config: configPath };
  }
  if (target === 'all' || target === 'codex') {
    await catalog();
    const result = await run(exeOnPath('python.exe') || 'python', [path.join(source, 'scripts', 'config_agents.py')], { input: JSON.stringify({ codexHome, sharedSkills: path.join(home, '.agents', 'skills'), model: WEB_MODEL, backup: dir }) });
    if (result.code) fail('Codex agent TOML validation failed. Inspect role sources; backup path: ' + dir);
    report.codex = { ...JSON.parse(result.stdout), model: WEB_MODEL, effort: 'high' };
  }
  if (target === 'gjc' || (target === 'all' && gjcBinary(false))) report.gjc = await configureGjc(dir, manifest, project);
  else if (target === 'all') report.gjc = { skipped: true, reason: 'GJC is not installed' };
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  fs.mkdirSync(path.join(store, 'reports'), { recursive: true }); fs.writeFileSync(path.join(store, 'reports', 'agents.json'), JSON.stringify(report, null, 2));
  say(report);
}
async function setup(args) {
  if (path.resolve(codexHome).toLowerCase() !== path.resolve(home, '.codex').toLowerCase()) fail('Launcher integration uses the default .codex home. Remove CODEX_HOME override before setup.', 2);
  await startApp();
  let snapshot = await launcher('snapshot');
  if (!snapshot.browser?.authenticated) { await launcher('openLogin'); fail('Complete sign-in in the opened app, then repeat setup.', 2); }
  if (snapshot.operation && !['completed', 'error', 'failed', 'cancelled'].includes(snapshot.operation.status)) fail('A launcher operation is active. Retry after it completes.', 3);
  try { await idle(); } catch (error) { if (exists(path.join(webHome, 'config.json'))) throw error; }
  const dir = backupDir(); const manifest = [];
  for (const file of [path.join(codexHome, 'config.toml'), path.join(webHome, 'config.json'), path.join(roaming, 'Codex Web GPT', 'launcher-state.json')]) {
    if (!exists(file)) continue;
    const saved = path.join(dir, `snapshot-${manifest.length}.bak`); fs.copyFileSync(file, saved); manifest.push({ target: file, backup: saved });
  }
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  if (!snapshot.smokePassed) { const smoke = await launcher('smokeTest'); if (!smoke?.ok) fail('Browser smoke test failed'); }
  const tunnelId = option(args, '--tunnel-id'), keyFile = option(args, '--runtime-key-file');
  if (!!tunnelId !== !!keyFile) fail('Supply both --tunnel-id and --runtime-key-file', 2);
  if (tunnelId) {
    if (!/^tunnel_[a-f0-9]{32}$/.test(tunnelId)) fail('Invalid tunnel ID', 2);
    const runtimeKey = fs.readFileSync(path.resolve(keyFile), 'utf8').trim();
    if (runtimeKey.length < 20) fail('Runtime key file is empty or incomplete', 2);
    const result = await launcher('setupMcp', [{ tunnelId, runtimeKey, replace: true, interactionMode: 'automatic' }]);
    if (!result?.ok) fail('Full MCP setup failed');
  } else if (!snapshot.state?.coreSetupComplete || !snapshot.mcpCredentialsConfigured) {
    if (!snapshot.mcpCredentialsConfigured) fail('Full mode needs a saved tunnel or --tunnel-id plus --runtime-key-file. See SETUP_KO.md.', 2);
    if (!(await launcher('setupMcp', [{ interactionMode: 'automatic' }]))?.ok) fail('MCP reconnection failed');
  }
  snapshot = await launcher('snapshot');
  if (!snapshot.state?.coreSetupComplete) { if (!(await launcher('setupCore'))?.ok) fail('Core setup failed'); }
  if (snapshot.state?.browserInteractionMode !== 'automatic') {
    const changed = await launcher('setBrowserInteractionMode', ['automatic']);
    if (changed?.credentialsRequired) fail('Automatic mode tunnel credentials are required', 2);
  }
  await launcher('setLanguage', ['ko']);
  await launcher('setAutostart', [true]);
  for (const [key, method, desired] of [
    ['experimentalBiggerContext', 'setBiggerContext', args.includes('--bigger-context')], ['experimentalSkillAttachments', 'setSkillAttachments', false],
    ['experimentalFreshConversationPerTurn', 'setFreshConversationPerTurn', false], ['useSavedChats', 'setUseSavedChats', false],
  ]) if (snapshot.state?.[key] !== desired) await launcher(method, [desired]);
  await launcher('setPreference', ['keepRunningOnClose', true]);
  await launcher('setPreference', ['showBrowserDuringTurns', true]);
  const config = readJson(path.join(webHome, 'config.json'));
  if (config.autoApproveToolCalls || config.zeroRiskProEnabled) fail('Current approval/Zero Risk options differ from the documented preset. Change them in the app before applying this preset.', 2);
  await configureAgents(option(args, '--agents') || 'codex', args.includes('--project'));
  const check = await launcher('verifyMcp'); if (!check?.ok) fail('Connector verification failed; attach the connector in ChatGPT settings');
  say('SETUP_OK: GPT-6 High configured. Run verify --omo --gjc for real response verification.');
}
async function verify(includeOmo, includeGjc) {
  await startApp(); await idle(); const models = await catalog();
  const audit = await run(exeOnPath('python.exe') || 'python', [path.join(source, 'scripts', 'config_agents.py')], { input: JSON.stringify({ action: 'audit', codexHome, model: WEB_MODEL }) });
  if (audit.code) fail('Codex role configuration audit failed. Run setup --agents all.');
  const doctor = await launcher('doctor'); if (!doctor?.ok) fail('Launcher doctor failed');
  const connector = await launcher('verifyMcp'); if (!connector?.ok) fail('Connector verification failed');
  const binary = codexBinary(); const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-web-gpt-test-'));
  const output = path.join(cwd, 'answer.txt');
  say('Testing native Codex GPT-6 High response...');
  const native = await run(binary.exe, [...binary.prefix, 'exec', '--ignore-user-config', '--skip-git-repo-check', '--sandbox', 'read-only', '--cd', cwd, '--model', WEB_MODEL,
    '-c', 'model_reasoning_effort="high"', '-c', `openai_base_url="${route()}/v1"`, '--json', '--output-last-message', output,
    'Connectivity test: reply exactly CODEX_GPT6_HIGH_OK. Do not use tools or inspect files.']);
  const answer = exists(output) ? fs.readFileSync(output, 'utf8').replace(/\\_/g, '_').trim() : '';
  if (native.code || answer !== 'CODEX_GPT6_HIGH_OK') fail('Native Codex GPT-6 High response verification failed');
  const report = { checkedAt: new Date().toISOString(), version: (await health()).version, models, codexRoles: JSON.parse(audit.stdout), nativeCodexHigh: true, response: answer, connector: true };
  if (includeOmo) {
    const configRoot = path.join(home, '.omo');
    const configPath = exists(path.join(configRoot, 'omo.jsonc')) ? path.join(configRoot, 'omo.jsonc') : path.join(configRoot, 'omo.json');
    const config = parseJsonc(fs.readFileSync(configPath, 'utf8'));
    for (const entry of [...Object.values(config.agents || {}), ...Object.values(config.categories || {})]) {
      if (entry.model !== OMO_MODEL || entry.reasoning !== 'high' || entry.models?.length !== 1 || entry.models[0]?.model !== OMO_MODEL || entry.models[0]?.reasoning !== 'high') fail('omo role/category configuration audit failed');
    }
    if (config.model_profile !== OMO_MODEL + ':high') fail('omo main profile is not pinned to GPT-6 High');
    report.omoRoles = { roles: Object.keys(config.agents || {}).length, categories: Object.keys(config.categories || {}).length, allGPT6High: true };
    say('Testing OmO Native GPT-6 High response...');
    const result = await run(omoBinary(), ['--offline', '--mode', 'json', '--no-model-fallback', '--no-tools', '--no-skills', '--no-context-files', '--no-session', '-p', 'Reply exactly OMO_GPT6_HIGH_OK.']);
    const events = result.stdout.split(/\r?\n/).flatMap(line => { try { return [JSON.parse(line)]; } catch { return []; } });
    const message = events.findLast(e => e.type === 'turn_end' && e.message?.role === 'assistant')?.message;
    const text = message?.content?.filter(c => c.type === 'text').map(c => c.text).join('').trim();
    if (result.code || text !== 'OMO_GPT6_HIGH_OK' || message.model !== WEB_MODEL || message.provider !== 'codex-web-gpt' || message.thinkingLevel !== 'high') fail('OmO web-only request failed (the local bridge requires native Codex turn_id metadata). Subscription fallback is disabled.');
    report.omoNativeHigh = true; report.omoResponse = text; report.omoActual = { model: message.model, provider: message.provider, effort: message.thinkingLevel };
  }
  if (includeGjc) Object.assign(report, await verifyGjc(cwd));
  fs.mkdirSync(path.join(store, 'reports'), { recursive: true }); fs.writeFileSync(path.join(store, 'reports', 'verification.json'), JSON.stringify(report, null, 2)); say(report);
}
async function verifyGjc(cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'gjc-gpt-test-'))) {
    const report = {};
    const roles = await gjcConfig('modelRoles'), overrides = await gjcConfig('task.agentModelOverrides');
    const expected = tuneGjcMappings(roles, overrides, gjcAgentNames(true));
    if (JSON.stringify(roles) !== JSON.stringify(expected.modelRoles) || JSON.stringify(overrides) !== JSON.stringify(expected.agentModelOverrides)
        || await gjcConfig('defaultThinkingLevel') !== 'high' || await gjcConfig('modelProfile.default') || await gjcConfig('task.autorouting.enabled')) fail('GJC role/model/High configuration audit failed');
    say('Testing GJC saved GPT-6 default response...');
    const result = await run(gjcBinary(), ['--mode', 'json', '--no-session', '--no-tools', '--no-lsp', '--no-rules', '--no-mcp', '--no-title', '-p', 'Connectivity test. Return the exact text GJC_GPT6_HIGH_OK with no punctuation or extra text.'], { cwd });
    const events = result.stdout.split(/\r?\n/).flatMap(line => { try { return [JSON.parse(line)]; } catch { return []; } });
    const message = events.findLast(e => e.type === 'turn_end' && e.message?.role === 'assistant')?.message;
    const text = message?.content?.filter(c => c.type === 'text').map(c => c.text).join('').trim();
    const diagnostic = { exitCode: result.code, response: text, model: message?.model, provider: message?.provider, stopReason: message?.stopReason, eventTypes: [...new Set(events.map(e => e.type))] };
    fs.mkdirSync(path.join(store, 'reports'), { recursive: true });
    fs.writeFileSync(path.join(store, 'reports', 'gjc-response.json'), JSON.stringify(diagnostic, null, 2));
    if (result.code || text !== 'GJC_GPT6_HIGH_OK' || message?.model !== WEB_MODEL || message?.provider !== 'codex-web-gpt') fail('GJC web-only request failed (the local bridge requires native Codex turn_id metadata). Subscription fallback is disabled.');
    report.gjcNative = true; report.gjcResponse = text;
    report.gjcActual = { model: message.model, provider: message.provider };
    report.gjcConfiguration = { effort: 'high', roles: Object.keys(roles).length, agents: Object.keys(overrides).length, allGPT6High: true, effortSource: 'native config audit; JSON response does not expose thinkingLevel' };
    return report;
}
async function installApp(upgrade) {
  const release = await request('https://api.github.com/repos/miuuyy/codex-chatgpt-web/releases/latest', { headers: { 'User-Agent': 'CodexWebGPTSetup' } });
  const version = release.tag_name?.replace(/^v/, '');
  if (!/^\d+\.\d+\.\d+$/.test(version || '')) fail('Unexpected release version');
  const asset = release.assets.find(a => a.name === `codex-web-gpt-${version}-win-x64.exe`);
  if (!asset || !/^sha256:[a-f0-9]{64}$/.test(asset.digest || '')) fail('Release has no verifiable Windows x64 installer');
  if (exists(appExe) && !upgrade) return;
  if (exists(appExe)) {
    await startApp(); await idle();
    if ((await health()).version === version) { say(`Already installed: ${version}`); return; }
  }
  const dir = path.join(store, 'downloads'); fs.mkdirSync(dir, { recursive: true }); const installer = path.join(dir, asset.name);
  const expected = asset.digest.slice(7);
  const hash = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  if (!exists(installer) || hash(installer) !== expected) {
    say(`Downloading verified release ${version}...`);
    const response = await fetch(asset.browser_download_url, { signal: AbortSignal.timeout(180000) });
    if (!response.ok) fail(`Installer download HTTP ${response.status}`);
    fs.writeFileSync(installer, Buffer.from(await response.arrayBuffer()));
  }
  if (hash(installer) !== expected) fail('Installer SHA256 mismatch; installation stopped');
  if (exists(appExe)) {
    await launcher('setPreference', ['keepRunningOnClose', false]);
    // Closing the window calls the app's normal shutdown path.
    try { await launcher('windowControl', ['close'], 10000); } catch {}
    let stopped = false;
    for (let i = 0; i < 45; i++) {
      try { await launcher('snapshot'); } catch { stopped = true; break; }
      await sleep(1000);
    }
    if (!stopped) fail('Normal app shutdown failed; installer was not started');
  }
  const result = await run('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', '$taskProcess = Start-Process -FilePath $env:CODEX_WEB_GPT_INSTALLER -ArgumentList "/S","/currentuser" -WindowStyle Hidden -Wait -PassThru; exit $taskProcess.ExitCode'], { timeout: 300000, env: { ...process.env, CODEX_WEB_GPT_INSTALLER: installer } });
  if (result.code) fail('Windows installer failed');
  if (!exists(appExe)) fail('Installer exited but the application executable is missing');
  await startApp(); await launcher('setPreference', ['keepRunningOnClose', true]); say(`APP_INSTALLED: ${version}`);
}
function option(args, name) { const i = args.indexOf(name); if (i < 0) return null; if (!args[i + 1] || args[i + 1].startsWith('--')) fail(`${name} needs a value`, 2); return args[i + 1]; }
async function installSkill() {
  const canonical = path.join(store, 'skill');
  if (path.resolve(source) !== path.resolve(canonical)) copyPackage(source, canonical);
  const locations = [path.join(home, '.agents', 'skills'), path.join(codexHome, 'skills'), path.join(home, '.claude', 'skills'), path.join(home, '.gemini', 'skills'), path.join(home, '.config', 'opencode', 'skills'), path.join(gjcHome, 'skills')];
  for (const root of locations) copyPackage(canonical, path.join(root, 'codex-web-gpt-setup'));
  const dir = backupDir(); const manifest = []; const settingsPath = path.join(omoHome, 'settings.json');
  const settings = exists(settingsPath) ? readJson(settingsPath) : {};
  const skill = path.join(canonical, 'SKILL.md');
  settings.skills = [...new Set([...(settings.skills || []), skill])]; saveJson(settingsPath, settings, dir, manifest);
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  const bin = path.join(home, '.local', 'bin'); fs.mkdirSync(bin, { recursive: true });
  fs.writeFileSync(path.join(bin, 'codex-web-gpt.cmd'), '@echo off\r\nsetlocal EnableExtensions DisableDelayedExpansion\r\ncall "%LOCALAPPDATA%\\CodexWebGPTSetup\\skill\\scripts\\codex-web-gpt.cmd" %*\r\nexit /b %ERRORLEVEL%\r\n', 'utf8');
  fs.writeFileSync(path.join(bin, 'omo-gpt6.cmd'), '@echo off\r\nsetlocal EnableExtensions DisableDelayedExpansion\r\n"%USERPROFILE%\\.local\\bin\\omo.exe" --provider codex-web-gpt --model chatgpt-web/gpt-6-sol --thinking high --no-recommended-models --no-model-fallback %*\r\nexit /b %ERRORLEVEL%\r\n', 'utf8');
  fs.writeFileSync(path.join(bin, 'gjc-gpt6.cmd'), '@echo off\r\nsetlocal EnableExtensions DisableDelayedExpansion\r\nif exist "%LOCALAPPDATA%\\gjc\\gjc.exe" (\r\n  "%LOCALAPPDATA%\\gjc\\gjc.exe" --model codex-web-gpt/chatgpt-web/gpt-6-sol --thinking high %*\r\n) else (\r\n  call gjc --model codex-web-gpt/chatgpt-web/gpt-6-sol --thinking high %*\r\n)\r\nexit /b %ERRORLEVEL%\r\n', 'utf8');
  say({ installed: true, command: path.join(bin, 'codex-web-gpt.cmd'), skillLocations: locations, omoSkill: skill, backup: dir });
}
async function status() {
  const result = { appInstalled: exists(appExe), app: appExe, codexHome, omoHome, gjcHome, gjcInstalled: !!gjcBinary(false), command: path.join(home, '.local', 'bin', 'codex-web-gpt.cmd') };
  try {
    const s = await launcher('snapshot');
    result.version = s.version; result.authenticated = s.browser?.authenticated; result.state = Object.fromEntries(['language', 'autoStart', 'keepRunningOnClose', 'showBrowserDuringTurns', 'autoApproveToolCalls', 'browserInteractionMode', 'experimentalBiggerContext', 'experimentalSkillAttachments', 'experimentalFreshConversationPerTurn', 'useSavedChats', 'coreSetupComplete', 'mcpSetupComplete'].map(k => [k, s.state?.[k]]));
    result.health = await health();
  } catch { result.launcherReachable = false; }
  if (exists(path.join(omoHome, 'settings.json'))) { const s = readJson(path.join(omoHome, 'settings.json')); result.omo = { provider: s.defaultProvider, model: s.defaultModel, effort: s.defaultThinkingLevel }; }
  if (exists(path.join(store, 'reports', 'agents.json'))) result.agentConfiguration = readJson(path.join(store, 'reports', 'agents.json'));
  say(result);
}
function restore(directory) {
  const full = path.resolve(directory || ''); const root = path.resolve(store, 'backups') + path.sep;
  if (!full.startsWith(root)) fail('Restore only accepts a backup created by this tool');
  const manifests = ['manifest.json', 'codex-manifest.json'].map(f => path.join(full, f)).filter(exists);
  const entries = manifests.flatMap(readJson);
  if (!entries.length) fail('No restorable files in this backup');
  for (const entry of entries) {
    if (!entry.backup) continue;
    const saved = path.resolve(entry.backup);
    if (!saved.startsWith(full + path.sep) || !exists(saved)) fail('Invalid backup entry');
    const target = path.resolve(entry.target);
    const allowed = [codexHome, omoHome, gjcHome, webHome].some(root => target.startsWith(path.resolve(root) + path.sep))
      || [path.join(home, '.omo', 'omo.jsonc'), path.join(home, '.omo', 'omo.json'), path.join(roaming, 'Codex Web GPT', 'launcher-state.json')].some(file => target === path.resolve(file))
      || (target.startsWith(path.resolve(process.cwd(), '.omo') + path.sep) && /omo\.jsonc?$/.test(target));
    if (!allowed) fail('Backup target is outside this tool configuration scope');
    fs.copyFileSync(saved, entry.target);
  }
  say(`RESTORED: ${entries.length} recorded files. Restart affected agents.`);
}
export async function main(args = process.argv.slice(2)) {
  if (process.platform !== 'win32') fail('This package supports Windows CMD');
  if (Number(process.versions.node.split('.')[0]) < 22) fail('Node.js 22 or newer is required', 2);
  const command = args.shift() || 'help';
  switch (command) {
    case 'install': return installSkill();
    case 'status': return status();
    case 'models': await startApp(); return say(await catalog());
    case 'login': await startApp(); await launcher('openLogin'); return say('Complete sign-in in the app, then repeat setup.');
    case 'setup': return setup(args);
    case 'agents': return configureAgents(args[0] || 'all', args.includes('--project'));
    case 'verify': return verify(args.includes('--omo'), args.includes('--gjc'));
    case 'repair-web': return (await import('./web_repair.mjs')).repairWeb();
    case 'verify-web': return (await import('./web_repair.mjs')).verifyWeb(args.includes('--high'), args.includes('--continue'));
    case 'verify-gjc': return say(await verifyGjc());
    case 'update': return installApp(true);
    case 'restore': return restore(args[0]);
    case 'run': { await startApp(); await catalog(); const binary = codexBinary(); const result = await run(binary.exe, [...binary.prefix, '--model', WEB_MODEL, '-c', 'model_reasoning_effort="high"', ...args], { inherit: true, timeout: 43200000 }); process.exitCode = result.code; return; }
    case 'help': case '--help': case '-h': return say('codex-web-gpt install | status | models | login | setup [--agents all|codex|omo|gjc] [--project] [--tunnel-id ID --runtime-key-file PATH] | agents all|codex|omo|gjc [--project] | verify [--omo] [--gjc] | verify-gjc | update | restore BACKUP_DIRECTORY | run [CODEX_ARGS]\nExit codes: 0 success; 1 failure; 2 missing prerequisite/login; 3 active request.\nDocs: ' + path.join(source, 'references', 'SETUP_KO.md'));
    default: fail('Unknown command: ' + command, 2);
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(`ERROR: ${error.message}`); process.exitCode = error.exitCode || 1; });
}
