// Execute the actual browser-worker module using a Node worker-thread bridge.
// This exercises computation/message wiring, not browser rendering or CSP.
import {parentPort,workerData} from 'node:worker_threads';
globalThis.self={postMessage:value=>parentPort.postMessage(value),onmessage:null};
await import(workerData.module);
parentPort.on('message',data=>self.onmessage({data}));
parentPort.postMessage({ready:true});
