'use strict';
// Local desktop API; not the DeepSeek inference API or a headless CLI shim.
const fs = require('fs');
const crypto = require('crypto');
const http = require('http');
const path = require('path');
const b64u = b => Buffer.from(b).toString('base64url');
const samePath = (a, b) => process.platform === 'win32'
  ? path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase() : path.resolve(a) === path.resolve(b);
class Failure extends Error {
  constructor(code, message, uncertain = false) {super(message); this.code = code; this.uncertain = uncertain;}
}
class Host {
  constructor(driver) {
    this.authority = driver.authority;
    if (!/^127\.0\.0\.1:\d+$/.test(this.authority)) throw new Failure('invalid_config', 'DSH requires its configured loopback host');
    const credentialPath = driver.credentials || process.env[driver.credentials_env || 'DSH_CREDENTIAL_FILE'];
    if (!credentialPath) throw new Failure('backend_unavailable', 'DSH credential file locator is unset');
    const match = fs.readFileSync(credentialPath, 'utf8').match(/secret:\s*([A-Za-z0-9_-]{43})/);
    if (!match) throw new Failure('backend_unavailable', 'DSH browser-session credential is unavailable');
    const secret = Buffer.from(match[1], 'base64url');
    const body = b64u(JSON.stringify({version: 1, authority: this.authority, issuedAt: Date.now(), expiresAt: Date.now() + 3600000}));
    const name = 'dsh-auth-' + b64u(crypto.createHash('sha256').update(this.authority).digest());
    this.cookie = name + '=v1.' + body + '.' + b64u(crypto.createHmac('sha256', secret).update(body).digest());
  }
  call(endpoint, args, mutation = false) {
    return new Promise((resolve, reject) => {
      const body = JSON.stringify({type: 'client-request', rpcId: crypto.randomUUID(), method: endpoint, payload: {args}});
      const [host, port] = this.authority.split(':');
      const req = http.request({host, port: Number(port), path: '/api/' + endpoint, method: 'POST',
        headers: {host: this.authority, cookie: this.cookie, 'content-type': 'application/json', 'content-length': Buffer.byteLength(body)}}, res => {
        let text = ''; res.on('data', c => {text += c;});
        res.on('end', () => {try {
          if (res.statusCode !== 200) throw new Failure('native_rejected', endpoint + ': HTTP ' + res.statusCode, mutation && res.statusCode >= 500);
          const envelope = JSON.parse(text);
          const value = envelope.type === 'server-response' ? envelope.result : envelope;
          if (!value.ok) throw new Failure('native_rejected', endpoint + ': native request rejected');
          resolve(value.value);
        } catch (error) {reject(error instanceof Failure ? error : new Failure('native_unknown', endpoint + ': malformed acknowledgement', mutation));}});
      });
      req.on('error', error => reject(new Failure('backend_unavailable', endpoint + ': ' + error.code, mutation && error.code !== 'ECONNREFUSED')));
      req.setTimeout(15000, () => req.destroy(new Failure('native_unknown', endpoint + ': timeout', mutation)));
      req.end(body);
    });
  }
  async inspect(target) {
    const rows = (await this.call('session/list', {_request: {}})).items;
    const row = rows.find(r => r.sessionId === target.session_id);
    if (!row) throw new Failure('not_found', 'DSH session is absent from the native registry');
    if (!row.cwd || !samePath(row.cwd, target.cwd)) throw new Failure('workspace_mismatch', 'DSH native workspace differs from the configured target');
    const projections = await this.call('session/projections', {request: {sessionId: target.session_id}});
    return {session_id: row.sessionId, cwd: row.cwd, running: row.running,
      model: projections?.values?.modelSelection || null, title: projections?.values?.title || null};
  }
  async select(target) {
    const selection = {provider: target.provider, model: target.model, reasoningEffort: target.reasoning_effort};
    const result = await this.call('session/selectModel', {request: {sessionId: target.session_id, ...selection}}, true);
    if (Object.keys(selection).some(key => result.selected?.[key] !== selection[key]))
      throw new Failure('settings_mismatch', 'DSH did not confirm the requested native model selection');
    return selection;
  }
}
async function main() {
  let input = ''; for await (const chunk of process.stdin) input += chunk;
  const {action, target, title, prompt, request_id} = JSON.parse(input.replace(/^\uFEFF/, ''));
  const host = new Host(target.driver);
  let result;
  if (action === 'create') {
    const workspace = (await host.call('workspace/create', {request: {path: target.cwd}}, true)).workspace;
    if (!workspace?.workspaceId) throw new Failure('creation_unknown', 'DSH did not acknowledge a workspace identity', true);
    const created = await host.call('session/create', {request: {workspaceId: workspace.workspaceId}}, true);
    if (!/^session-[0-9a-f-]{36}$/i.test(created.sessionId || '')) throw new Failure('creation_unknown', 'DSH did not acknowledge a native session identity', true);
    process.stdout.write(JSON.stringify({created: true, session_id: created.sessionId}) + '\n');
    target.session_id = created.sessionId;
    if (title) await host.call('session/rename', {request: {sessionId: target.session_id, title}}, true);
    await host.select(target);
    result = await host.inspect(target);
  } else if (action === 'inspect') {
    result = await host.inspect(target);
  } else if (action === 'send') {
    const current = await host.inspect(target);
    if (current.running !== false) throw new Failure('busy', 'DSH idle state is not confirmed');
    await host.select(target);
    const response = await host.call('session/prompt', {request: {sessionId: target.session_id, requestId: request_id,
      mode: 'queue', content: [{type: 'text', text: prompt}], clientTimeZone: target.driver.time_zone || 'UTC'}}, true);
    if (response.accepted !== true) throw new Failure('not_accepted', 'DSH did not accept the prompt');
    result = {accepted: true, session_id: target.session_id, execution_complete: false};
  } else throw new Failure('unsupported', 'Unknown DSH operation');
  process.stdout.write(JSON.stringify(result) + '\n');
}
main().catch(error => {
  process.stdout.write(JSON.stringify({ok: false, code: error.code || 'bridge_unknown',
    message: error instanceof Failure ? error.message : 'DSH bridge preflight failed', uncertain: error.uncertain === true}) + '\n');
  process.exitCode = 1;
});
