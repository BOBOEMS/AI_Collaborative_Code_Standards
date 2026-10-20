'use strict';
// Route A local GUI host client. Model credentials stay in the GUI process.
// Protocol source: agent-hub/scripts/dsh-host-client.cjs, verified 2026-10-20.
const fs=require('fs');
const os=require('os');
const path=require('path');
const http=require('http');
const crypto=require('crypto');
const {discover,authority}=require('./dsh_discovery.cjs');
const b64u=value=>Buffer.from(value).toString('base64url');
const samePath=(a,b)=>process.platform==='win32'?path.resolve(a).toLowerCase()===path.resolve(b).toLowerCase():path.resolve(a)===path.resolve(b);

class Failure extends Error {
  constructor(code,message,uncertain=false,details={}) {super(message);this.code=code;this.uncertain=uncertain;this.details=details;}
}
function credentials(driver) {
  const explicit=driver.credentials || (driver.credentials_env?process.env[driver.credentials_env]:process.env.DSH_CREDENTIAL_FILE);
  if (driver.credentials_env && !explicit) throw new Failure('backend_unavailable','DSH credential file locator is unset');
  const home=driver.dsh_home || process.env.DSH_HOME || path.join(os.homedir(),'.dsh');
  return explicit || path.join(home,'.credentials.yaml');
}
function cookieFor(driver,endpoint) {
  let text;
  try {text=fs.readFileSync(credentials(driver),'utf8');} catch {throw new Failure('backend_unavailable','DSH browser-session credential file is unavailable');}
  // Extract only the browser-session signing secret, never refs.CMDC_API_KEY.
  const match=text.match(/secret:\s*([A-Za-z0-9_-]{43})/);
  if (!match) throw new Failure('backend_unavailable','DSH browser-session signing credential is unavailable');
  const body=b64u(JSON.stringify({version:1,authority:endpoint,issuedAt:Date.now(),expiresAt:Date.now()+3600000}));
  return 'dsh-auth-'+b64u(crypto.createHash('sha256').update(endpoint).digest())+'=v1.'+body+'.'+
    b64u(crypto.createHmac('sha256',Buffer.from(match[1],'base64url')).update(body).digest());
}
class Host {
  constructor(driver,endpoint) {
    this.driver=driver;this.authority=authority(endpoint);this.cookie=cookieFor(driver,this.authority);
  }
  static async connect(driver) {
    let selected;
    try {
      selected=await discover(driver,async endpoint=>{
        try {const value=await new Host(driver,endpoint).call('session/list',{_request:{}});return Array.isArray(value?.items);} catch {return false;}
      });
    } catch (error) {
      if (error instanceof Failure) throw error;
      throw new Failure(error.code || 'invalid_config',error.message,false,error.authorities?{authorities:error.authorities}:{});
    }
    const host=new Host(driver,selected.authority);host.discoverySource=selected.source;
    return host;
  }
  call(endpoint,args,{mutation=false,rpcId,timeoutMs}={}) {
    return new Promise((resolve,reject)=>{
      const body=JSON.stringify({type:'client-request',rpcId:rpcId || crypto.randomUUID(),method:endpoint,payload:{args}});
      const [host,port]=this.authority.split(':');
      const request=http.request({host,port:Number(port),path:'/api/'+endpoint,method:'POST',
        headers:{host:this.authority,cookie:this.cookie,'content-type':'application/json','content-length':Buffer.byteLength(body)}},response=>{
        let text='';
        response.on('data',chunk=>{text+=chunk;if (Buffer.byteLength(text)>32*1024*1024) request.destroy(new Failure('native_unknown','Host acknowledgement exceeds size limit',mutation));});
        response.on('error',()=>reject(new Failure('native_unknown',endpoint+': response interrupted',mutation)));
        response.on('end',()=>{try {
          if (response.statusCode!==200) throw new Failure('native_rejected',endpoint+': HTTP '+response.statusCode,mutation && response.statusCode>=500);
          const envelope=JSON.parse(text);
          const value=envelope.type==='server-response'?envelope.result:envelope;
          if (value?.ok!==true) {
            const native=value?.error || {};
            throw new Failure('native_rejected',endpoint+': '+(native.code || 'request rejected'),false,
              {native_code:native.code, cursor:Number(/past cursor (\d+)/.exec(native.message || '')?.[1]) || undefined});
          }
          resolve(value.value);
        } catch (error) {reject(error instanceof Failure?error:new Failure('native_unknown',endpoint+': malformed acknowledgement',mutation));}});
      });
      request.on('error',error=>reject(error instanceof Failure?error:new Failure('backend_unavailable',endpoint+': '+error.code,mutation && error.code!=='ECONNREFUSED')));
      request.setTimeout(timeoutMs || 15000,()=>request.destroy(new Failure('native_unknown',endpoint+': timeout',mutation)));
      request.end(body);
    });
  }
  async inspect(target,options={}) {
    const rows=(await this.call('session/list',{_request:{}},options)).items;
    const row=rows.find(item=>item.sessionId===target.session_id);
    if (!row) throw new Failure('not_found','DSH session is absent from the native GUI registry');
    if (!row.cwd || !samePath(row.cwd,target.cwd)) throw new Failure('workspace_mismatch','DSH native workspace differs from the configured target');
    const projections=await this.call('session/projections',{request:{sessionId:target.session_id}},options);
    return {session_id:row.sessionId,cwd:row.cwd,running:row.running,
      model:projections?.values?.modelSelection || null,title:projections?.values?.title || null,
      cursor:projections?.asOfSeq ?? null,turns:projections?.values?.sessionStats?.turns ?? null,
      authority:this.authority,discovery_source:this.discoverySource};
  }
  async select(target) {
    const selection={provider:target.provider,model:target.model,reasoningEffort:target.reasoning_effort};
    const result=await this.call('session/selectModel',{request:{sessionId:target.session_id,...selection}},{mutation:true});
    if (Object.keys(selection).some(key=>result.selected?.[key]!==selection[key])) throw new Failure('settings_mismatch','DSH did not confirm the requested native model selection');
    return selection;
  }
  async page(id,cursor,maxMessages=200,options={}) {
    if (!Number.isSafeInteger(cursor) || cursor<0) throw new Failure('state_unknown','DSH native history cursor is unavailable');
    return this.call('session/page',{request:{address:{kind:'session',sessionId:id},throughSeq:cursor,maxMessages}},options);
  }
  async read(target,{limit=200,includeEvents=false,timeoutMs}={}) {
    if (!Number.isInteger(limit) || limit<1 || limit>1000) throw new Failure('invalid_request','Read limit must be 1..1000');
    const current=await this.inspect(target,{timeoutMs});
    const page=await this.page(target.session_id,current.cursor,limit,{timeoutMs});
    const messages=[],turnEnds=[];
    let activeTurn=null;
    for (const row of page.records || []) {
      const event=row.event;
      if (!event) continue;
      const data=event.data || {};
      if (event.type==='turn/start') activeTurn=data.turn;
      if (event.type==='turn/end') turnEnds.push({turn:data.turn,seq:event.seq,reason:{kind:data.reason?.kind,code:data.reason?.error?.code}});
      if (event.type!=='assistant/message' && event.type!=='user/message') continue;
      const message=data.message || data;
      if (event.type==='user/message' && message.source?.kind!=='user') continue;
      const text=(message.content || []).filter(part=>part.type==='text').map(part=>part.text).join('\n');
      if (text) messages.push({role:event.type==='assistant/message'?'assistant':'user',seq:event.seq,
        turn:data.turn ?? activeTurn,request_id:message.source?.rpcId || data.source?.rpcId || null,text});
    }
    return {...current,messages,assistant:messages.filter(m=>m.role==='assistant').map(m=>m.text).join('\n'),
      turn_ends:turnEnds,has_more:page.hasMore===true,...(includeEvents?{events:(page.records || []).filter(row=>
        /^(assistant\/message|user\/message|tool\/|turn\/|step\/)/.test(row.event?.type || ''))}: {})};
  }
  async wait(target,{timeoutSeconds=30,baselineSeq,expectedTurn,dispatchId}={}) {
    if (!Number.isFinite(timeoutSeconds) || timeoutSeconds<0 || timeoutSeconds>45) throw new Failure('invalid_request','Wait timeout must be 0..45 seconds per call');
    const deadline=Date.now()+timeoutSeconds*1000;
    let result;
    do {
      result=await this.read(target,{limit:1000,timeoutMs:Math.max(100,Math.min(5000,deadline-Date.now()))});
      const matched=result.messages.find(message=>message.role==='user' && message.request_id===dispatchId && message.seq>baselineSeq);
      const turn=expectedTurn ?? matched?.turn;
      const end=result.turn_ends.find(item=>item.turn===turn && item.seq>baselineSeq);
      const idle=result.running===false;
      if (idle && (!dispatchId || end)) return {...result,timed_out:false,idle:true,
        turn_ended:!!end,execution_succeeded:end?end.reason?.kind==='completed':null,
        completion:end || null,request_association:matched?.turn===turn?'native_request_id':dispatchId?'expected_turn':'idle_only'};
      if (Date.now()>=deadline) break;
      await new Promise(resolve=>setTimeout(resolve,Math.min(1000,deadline-Date.now())));
    } while (true);
    return {...result,timed_out:true,idle:result.running===false,turn_ended:false,execution_succeeded:null,completion:null};
  }
}
module.exports={Host,Failure,cookieFor,credentials};
