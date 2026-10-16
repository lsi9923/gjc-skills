import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { health, idle, launcher, startApp, codexBinary, route, run } from './manage.mjs';

const taskHome = process.env.USERPROFILE || os.homedir();
const store = path.join(process.env.LOCALAPPDATA, 'CodexWebGPTSetup');
const scriptRoot = path.dirname(fileURLToPath(import.meta.url));
const normalize = text => text.replace(/\\_/g, '_').trim();

export function inspectProbe(result, expected, answer) {
  const events = result.stdout.split(/\r?\n/).flatMap(line => {
    try { return [JSON.parse(line)]; } catch { return []; }
  });
  const errors = events.filter(e => e.type === 'error' || e.type === 'turn.failed');
  const tools = events.filter(e => e.type === 'item.completed' && e.item?.type === 'command_execution');
  const message = normalize(answer);
  return {
    ok: result.code === 0 && message === expected && errors.length === 0 && events.some(e => e.type === 'turn.completed'),
    exitCode: result.code,
    response: message.slice(0, 300),
    threadId: events.find(e => e.type === 'thread.started')?.thread_id,
    completed: events.some(e => e.type === 'turn.completed'),
    toolCount: tools.length,
    toolsSucceeded: tools.every(e => e.item.exit_code === 0),
    errors: errors.map(e => String(e.message || e.error?.message || 'turn.failed').slice(0, 500)),
  };
}

export function probeArguments(base, directory, output, prompt, thread) {
  return ['exec', ...base, '--cd', directory, ...(thread ? ['resume'] : []),
    '--json', '--output-last-message', output, ...(thread ? [thread] : []), prompt];
}

export async function repairWeb() {
  await startApp(); await idle();
  const snapshot = await launcher('snapshot');
  if (snapshot.operation && !['completed', 'error', 'failed', 'cancelled'].includes(snapshot.operation.status)) {
    throw new Error('A launcher operation is active; settings were not changed');
  }
  const backup = path.join(store, 'backups', `web-repair-${Date.now()}`);
  fs.mkdirSync(backup, { recursive: true });
  const targets = [
    path.join(taskHome, '.codex', 'config.toml'),
    path.join(taskHome, '.codex-chatgpt-web', 'config.json'),
    path.join(process.env.APPDATA, 'Codex Web GPT', 'launcher-state.json'),
  ];
  const manifest = targets.filter(fs.existsSync).map((target, index) => {
    const saved = path.join(backup, `snapshot-${index}.bak`);
    fs.copyFileSync(target, saved); return { target, backup: saved };
  });
  fs.writeFileSync(path.join(backup, 'manifest.json'), JSON.stringify(manifest, null, 2));
  if (snapshot.state?.experimentalBiggerContext) await launcher('setBiggerContext', [false]);
  await idle();
  const tuned = await run('python.exe', [path.join(scriptRoot, 'repair_context.py')], {
    input: JSON.stringify({ path: targets[0], backup: path.join(backup, 'context-before.bak') }), timeout: 15000,
  });
  if (tuned.code) throw new Error('Context settings could not be validated; original snapshots are retained');
  const current = await launcher('snapshot');
  const report = { checkedAt: new Date().toISOString(), backup,
    biggerContext: current.state?.experimentalBiggerContext,
    context: JSON.parse(tuned.stdout), restartCodexRequired: true,
    modelAndEffortPreserved: true, approvalSettingsPreserved: true };
  if (report.biggerContext !== false) throw new Error('Launcher did not apply standard context');
  fs.mkdirSync(path.join(store, 'reports'), { recursive: true });
  fs.writeFileSync(path.join(store, 'reports', 'web-repair.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

async function waitForProbeRelease() {
  const deadline = Date.now() + 60000;
  while (true) {
    const state = await health();
    if (!state.active_http_turns && !state.active_browser_turns) return;
    if (Date.now() >= deadline) throw new Error('Previous probe has not released the connection; no new request was submitted');
    await new Promise(resolve => setTimeout(resolve, 500));
  }
}

export async function verifyWeb(high = false, continuation = false) {
  await startApp(); await idle();
  const effort = high ? 'high' : 'medium';
  const reportPath = path.join(store, 'reports', `web-verification-${effort}.json`);
  const previous = continuation ? JSON.parse(fs.readFileSync(reportPath, 'utf8')) : null;
  const directory = previous?.directory || path.join(store, 'probes', `web-${Date.now()}`);
  if (!path.resolve(directory).startsWith(path.resolve(store, 'probes') + path.sep)) throw new Error('Probe directory is outside the test scope');
  fs.mkdirSync(directory, { recursive: true });
  const binary = codexBinary();
  const base = ['--ignore-user-config', '--skip-git-repo-check', '--sandbox', 'read-only',
    '--model', 'chatgpt-web/gpt-6-sol', '-c', `model_reasoning_effort="${effort}"`,
    '-c', `openai_base_url="${route()}/v1"`];
  const report = { checkedAt: new Date().toISOString(), directory, effort,
    version: (await health()).version, nativeShellVerified: false,
    tests: previous?.tests?.filter(test => test.ok && test.completed) || [] };
  const probes = [
    { name: 'fresh-response', expected: 'WEB_SMOKE_OK',
      prompt: 'Connectivity test. Reply exactly WEB_SMOKE_OK. Do not use tools or inspect files.' },
    { name: 'same-chat-tool', expected: 'WEB_TOOL_OK',
      prompt: 'Connectivity test. Use exec_command once. The cmd argument must equal exactly: ' + JSON.stringify("Get-StartApps | Where-Object { $_.Name -match 'Codex|OpenAI' } | Format-Table -AutoSize") + '\nThis read-only command has an existing user approval rule. Set yield_time_ms 1000 and max_output_tokens 200. Wait for its result, using write_stdin if needed. Only if exit code is 0, reply exactly WEB_TOOL_OK. Do not change settings, request escalation, or inspect other files.' },
    { name: 'same-chat-followup', expected: 'WEB_RESUME_OK',
      prompt: 'Follow-up connectivity test. Reply exactly WEB_RESUME_OK. Do not use tools or inspect files.' },
  ];
  if (report.tests.some((test, index) => test.name !== probes[index]?.name)) throw new Error('Previous probe sequence is not reusable');
  let thread = report.tests[0]?.threadId;
  try {
    for (const probe of probes.slice(report.tests.length)) {
      await waitForProbeRelease();
      const output = path.join(directory, `${probe.name}.txt`);
      const args = probeArguments(base, directory, output, probe.prompt, thread);
      console.log(`Testing ${probe.name} (${effort})...`);
      const started = Date.now();
      const result = await run(binary.exe, [...binary.prefix, ...args], { cwd: directory, timeout: 180000 });
      fs.writeFileSync(path.join(directory, `${probe.name}.jsonl`), result.stdout);
      fs.writeFileSync(path.join(directory, `${probe.name}.stderr.txt`), result.stderr);
      const answer = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
      const checked = inspectProbe(result, probe.expected, answer);
      if (probe.name === 'same-chat-tool') checked.ok &&= checked.toolCount > 0 && checked.toolsSucceeded;
      report.tests.push({ name: probe.name, seconds: Math.round((Date.now() - started) / 100) / 10, ...checked });
      thread ||= checked.threadId;
      console.log(JSON.stringify(report.tests.at(-1)));
      if (!checked.ok || !thread) throw new Error(`${probe.name} failed; inspect the saved probe logs`);
    }
    await waitForProbeRelease();
    report.ok = true;
    report.nativeShellVerified = true;
  } catch (error) {
    report.ok = false; report.error = error.message; process.exitCode = 1;
  } finally {
    report.health = await health().catch(() => ({ status: 'unavailable' }));
    fs.mkdirSync(path.join(store, 'reports'), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`REPORT: ${reportPath}`);
  }
  return report;
}
