'use strict';
const readline = require('readline');
const input = readline.createInterface({input: process.stdin});
input.on('line', line => {
  const request = JSON.parse(line);
  if (request.id === undefined) return;
  let result = {};
  if (request.method === 'tools/list') result = {tools: [{name: 'read_thread'}, {name: 'send_message_to_thread'}]};
  if (request.method === 'tools/call') {
    const args = request.params.arguments;
    const value = request.params.name === 'read_thread' ? {thread: {id: args.threadId, cwd: process.cwd(), status: {type: 'idle'}}} : {status: 'queued', echoed: args.prompt};
    result = {content: [{type: 'text', text: JSON.stringify(value)}]};
  }
  process.stdout.write(JSON.stringify({jsonrpc: '2.0', id: request.id, result}) + '\n');
});
