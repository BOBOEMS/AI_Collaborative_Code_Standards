'use strict';
// Route A, adapted from agent-hub/scripts/discover-dsh-host.cjs (2026-10-20).
// Discovery only performs readonly requests on loopback. Mutations never retry.
const http = require('http');
const {execFile} = require('child_process');
const {promisify} = require('util');
const execute = promisify(execFile);

function authority(value) {
  if (typeof value !== 'string' || !/^127\.0\.0\.1:\d{1,5}$/.test(value) || Number(value.split(':')[1]) < 1 || Number(value.split(':')[1]) > 65535)
    throw new Error('Use a 127.0.0.1:port desktop authority');
  return value;
}
function probe(port, timeoutMs = 500) {
  return new Promise(resolve => {
    const body = JSON.stringify({type:'client-request',rpcId:'session-tool-discovery',method:'session/list',payload:{args:{_request:{}}}});
    const request = http.request({host:'127.0.0.1',port,path:'/api/session/list',method:'POST',
      headers:{'content-type':'application/json','content-length':Buffer.byteLength(body)}}, response => {
      let text = '';
      response.on('data', chunk => {text += chunk; if (text.length > 1048576) request.destroy();});
      response.on('end', () => {
        let envelope = false;
        try {const value=JSON.parse(text); envelope=value.type==='server-response' && typeof value.result?.ok==='boolean';} catch {}
        resolve(envelope || (response.statusCode===401 && /unauthorized/i.test(text)));
      });
      response.on('error', () => resolve(false));
    });
    request.on('error', () => resolve(false));
    request.setTimeout(timeoutMs, () => {request.destroy(); resolve(false);});
    request.end(body);
  });
}
async function candidatePorts(driver) {
  if (driver.discovery_ports !== undefined) {
    if (!Array.isArray(driver.discovery_ports) || !driver.discovery_ports.length || driver.discovery_ports.length > 1024 ||
        driver.discovery_ports.some(p => !Number.isInteger(p) || p<1 || p>65535)) throw new Error('Invalid discovery_ports');
    return [...new Set(driver.discovery_ports)];
  }
  if (process.platform==='win32') {
    try {
      const {stdout}=await execute('netstat.exe',['-ano','-p','tcp'],{windowsHide:true,timeout:5000,maxBuffer:4*1024*1024});
      const ports=[];
      for (const line of stdout.split(/\r?\n/)) {
        const fields=line.trim().split(/\s+/);
        if (fields[0]==='TCP' && fields[3]==='LISTENING' && /^(127\.0\.0\.1|0\.0\.0\.0):\d+$/.test(fields[1]))
          ports.push(Number(fields[1].split(':')[1]));
      }
      if (ports.length) return [...new Set(ports)].sort((a,b)=>a-b);
    } catch {} // No installation or privileged command is needed for the fallback.
  }
  const ports=[];
  for (const [lo,hi] of [[19380,19400],[63000,64000],[3000,3200]])
    for (let port=lo;port<=hi;port++) ports.push(port);
  return ports;
}
async function discover(driver, authenticate) {
  const explicit=driver.authority || process.env[driver.authority_env || 'DSH_AUTHORITY'];
  if (explicit) return {authority:authority(explicit),source:driver.authority?'configured':'environment'};
  const ports=await candidatePorts(driver);
  const found=[];
  let cursor=0;
  await Promise.all(Array.from({length:Math.min(32,ports.length)},async()=>{
    while (cursor<ports.length) {
      const port=ports[cursor++];
      if (!await probe(port)) continue;
      const candidate='127.0.0.1:'+port;
      if (await authenticate(candidate)) found.push(candidate);
    }
  }));
  if (!found.length) {const error=new Error('No authenticated running DSH GUI host found on loopback');error.code='backend_unavailable';throw error;}
  if (found.length!==1) {const error=new Error('Multiple authenticated DSH hosts found; select connection.authority explicitly');error.code='ambiguous_host';error.authorities=found.sort();throw error;}
  return {authority:found[0],source:'auto_discovery'};
}
module.exports={authority,probe,candidatePorts,discover};
