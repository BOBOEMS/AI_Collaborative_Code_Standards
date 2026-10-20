'use strict';
// Route A: all operations occur inside the running GUI host.
const {Host,Failure}=require('./dsh_host_client.cjs');
async function main() {
  let input = ''; for await (const chunk of process.stdin) input += chunk;
  const {action, target, title, prompt, request_id, options={}} = JSON.parse(input.replace(/^\uFEFF/, ''));
  const host = await Host.connect(target.driver);
  let result;
  if (action === 'create') {
    const workspace = (await host.call('workspace/create', {request: {path: target.cwd}}, {mutation:true})).workspace;
    if (!workspace?.workspaceId) throw new Failure('creation_unknown', 'DSH did not acknowledge a workspace identity', true);
    const created = await host.call('session/create', {request: {workspaceId: workspace.workspaceId}}, {mutation:true});
    if (!/^session-[0-9a-f-]{36}$/i.test(created.sessionId || '')) throw new Failure('creation_unknown', 'DSH did not acknowledge a native session identity', true);
    process.stdout.write(JSON.stringify({created: true, session_id: created.sessionId}) + '\n');
    target.session_id = created.sessionId;
    if (title) await host.call('session/rename', {request: {sessionId: target.session_id, title}}, {mutation:true});
    await host.select(target);
    result = await host.inspect(target);
  } else if (action === 'inspect') {
    result = await host.inspect(target);
  } else if (action === 'send') {
    const current = await host.inspect(target);
    if (current.running !== false) throw new Failure('busy', 'DSH idle state is not confirmed');
    await host.select(target);
    const response = await host.call('session/prompt', {request: {sessionId: target.session_id, requestId: request_id,
      mode: 'queue', content: [{type: 'text', text: prompt}], clientTimeZone: target.driver.time_zone || 'UTC'}}, {mutation:true,rpcId:request_id});
    if (response.accepted !== true) throw new Failure('not_accepted', 'DSH did not accept the prompt');
    result = {accepted:true,session_id:target.session_id,execution_complete:false,
      baseline_seq:current.cursor,expected_turn:typeof current.turns==='number'?current.turns+1:null,
      dispatch_id:request_id,authority:host.authority,discovery_source:host.discoverySource};
  } else if (action==='probe') {
    const sessions=await host.call('session/list',{_request:{}});
    result={connected:true,authority:host.authority,discovery_source:host.discoverySource,session_count:sessions.items.length};
  } else if (action==='read') {
    result=await host.read(target,options);
  } else if (action==='wait') {
    result=await host.wait(target,options);
  } else throw new Failure('unsupported', 'Unknown DSH operation');
  process.stdout.write(JSON.stringify(result) + '\n');
}
main().catch(error => {
  process.stdout.write(JSON.stringify({ok: false, code: error.code || 'bridge_unknown',
    message: error instanceof Failure ? error.message : 'DSH bridge preflight failed', uncertain: error.uncertain === true,
    details:error instanceof Failure?error.details:{}}) + '\n');
  process.exitCode = 1;
});
