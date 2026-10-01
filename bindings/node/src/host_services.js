// SPDX-License-Identifier: Apache-2.0

import { randomBytes } from 'node:crypto';
import { once } from 'node:events';
import { createServer } from 'node:net';


const HOST_PROTOCOL_VERSION = '1.0';
const JAVA_APE_RUNTIME = 'java-ape';
const JAVA_NATIVE_CAPABILITY = 'java.native';


export const AWT_INITIALIZERS = new Set([
  'java/awt/Toolkit.initIDs()V',
  'java/awt/image/BufferedImage.initIDs()V',
  'java/awt/image/ColorModel.initIDs()V',
  'java/awt/image/IndexColorModel.initIDs()V',
  'java/awt/image/Raster.initIDs()V',
  'java/awt/image/SampleModel.initIDs()V',
  'java/awt/image/SinglePixelPackedSampleModel.initIDs()V',
  'sun/awt/image/ByteComponentRaster.initIDs()V',
  'sun/awt/image/BytePackedRaster.initIDs()V',
  'sun/awt/image/BufImgSurfaceData.initIDs(Ljava/lang/Class;Ljava/lang/Class;)V',
  'sun/awt/image/IntegerComponentRaster.initIDs()V',
  'sun/java2d/Disposer.initIDs()V',
  'sun/java2d/SurfaceData.initIDs()V',
  'sun/java2d/loops/GraphicsPrimitiveMgr.initIDs(Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;)V',
  'sun/java2d/pipe/SpanClipRenderer.initIDs(Ljava/lang/Class;Ljava/lang/Class;)V',
]);


function nativeIdentity(parameters) {
  return `${parameters.owner}.${parameters.name}${parameters.descriptor}`;
}


function response(id, result) {
  return { jsonrpc: '2.0', id, result };
}


function responseError(id, code, message, type) {
  return {
    jsonrpc: '2.0',
    id,
    error: { code, message, data: { type } },
  };
}


function serialize(message) {
  const body = Buffer.from(JSON.stringify(message), 'utf8');
  const header = Buffer.from(
    `Content-Length: ${body.length}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n`,
    'ascii',
  );

  return Buffer.concat([header, body]);
}


class TikaHostService {
  constructor() {
    this.calls = [];
  }

  invoke(parameters) {
    const identity = nativeIdentity(parameters);

    this.calls.push(identity);

    if (AWT_INITIALIZERS.has(identity)) {
      return { return: { type: 'void' } };
    }

    throw new Error(`unsupported Tika Java native method: ${identity}`);
  }
}


class JsonRpcConnection {
  constructor(socket, token, service) {
    this._socket = socket;
    this._token = token;
    this._service = service;
    this._input = Buffer.alloc(0);
  }

  listen() {
    this._socket.on('data', (chunk) => this._receive(chunk));
    this._socket.on('error', (error) => {
      if (error.code !== 'ECONNRESET') {
        throw error;
      }
    });
  }

  _receive(chunk) {
    this._input = Buffer.concat([this._input, chunk]);

    while (true) {
      const message = this._readMessage();
      if (message === null) {
        return;
      }

      this._dispatch(message);
    }
  }

  _readMessage() {
    const headerEnd = this._input.indexOf('\r\n\r\n');
    if (headerEnd === -1) {
      return null;
    }

    const header = this._input.subarray(0, headerEnd).toString('ascii');
    const lengthLine = header.split('\r\n').find((line) => (
      line.toLowerCase().startsWith('content-length:')
    ));
    if (lengthLine === undefined) {
      this._socket.destroy(new Error('JSON-RPC message has no Content-Length'));
      return null;
    }

    const length = Number(lengthLine.split(':', 2)[1].trim());
    const bodyStart = headerEnd + 4;
    const bodyEnd = bodyStart + length;
    if (this._input.length < bodyEnd) {
      return null;
    }

    const body = this._input.subarray(bodyStart, bodyEnd);
    this._input = this._input.subarray(bodyEnd);

    return JSON.parse(body.toString('utf8'));
  }

  _dispatch(message) {
    if (message.method === 'host.initialize') {
      this._initialize(message);
      return;
    }

    if (message.method === 'java.native.invoke') {
      this._nativeInvoke(message);
      return;
    }

    this._write(responseError(message.id, -32601, 'unknown host method', 'unsupported'));
  }

  _initialize(message) {
    const parameters = message.params;
    if (
      parameters.protocolVersions.length !== 1
      || parameters.protocolVersions[0] !== HOST_PROTOCOL_VERSION
    ) {
      this._write(responseError(message.id, -32602, 'unexpected host protocol versions', 'protocol'));
      return;
    }

    if (parameters.runtime.name !== JAVA_APE_RUNTIME) {
      this._write(responseError(message.id, -32602, 'unexpected host runtime', 'protocol'));
      return;
    }

    if (parameters.token !== this._token) {
      this._write(responseError(message.id, -32001, 'invalid host token', 'unauthorized'));
      return;
    }

    this._write(response(message.id, {
      protocolVersion: HOST_PROTOCOL_VERSION,
      capabilities: [JAVA_NATIVE_CAPABILITY],
    }));
  }

  _nativeInvoke(message) {
    try {
      this._write(response(message.id, this._service.invoke(message.params)));
    } catch (error) {
      this._write(responseError(message.id, -32002, error.message, 'unsupported'));
    }
  }

  _write(message) {
    this._socket.write(serialize(message));
  }
}


export class TikaHostServices {
  constructor() {
    this._token = randomBytes(32).toString('base64url');
    this._service = new TikaHostService();
    this._server = createServer((socket) => {
      this._sockets.add(socket);
      socket.once('close', () => this._sockets.delete(socket));

      new JsonRpcConnection(socket, this._token, this._service).listen();
    });
    this._sockets = new Set();
    this._started = false;
  }

  get calls() {
    return [...this._service.calls];
  }

  async start() {
    if (this._started) {
      return;
    }

    this._server.listen(0, '127.0.0.1');
    await once(this._server, 'listening');
    this._server.unref();
    this._started = true;
  }

  environment() {
    if (!this._started) {
      throw new Error('Tika Host Services must be started before use');
    }

    const address = this._server.address();
    if (address === null || typeof address === 'string') {
      throw new Error('Tika Host Services has no TCP address');
    }

    return {
      APE_HOST: `127.0.0.1:${address.port}`,
      APE_HOST_TOKEN: this._token,
      APE_VIRTUAL_LIBRARIES: 'awt,fontmanager',
    };
  }

  close() {
    if (!this._started) {
      return;
    }

    for (const socket of this._sockets) {
      socket.destroy();
    }

    this._server.close();
    this._started = false;
  }
}
