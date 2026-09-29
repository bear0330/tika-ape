// SPDX-License-Identifier: Apache-2.0

import { randomBytes } from 'node:crypto';
import { once } from 'node:events';
import { createServer } from 'node:http';


export const AWT_INITIALIZERS = new Set([
  'java.awt.Toolkit.initIDs()V',
  'java.awt.image.BufferedImage.initIDs()V',
  'java.awt.image.ColorModel.initIDs()V',
  'java.awt.image.IndexColorModel.initIDs()V',
  'java.awt.image.Raster.initIDs()V',
  'java.awt.image.SampleModel.initIDs()V',
  'java.awt.image.SinglePixelPackedSampleModel.initIDs()V',
  'sun.awt.image.ByteComponentRaster.initIDs()V',
  'sun.awt.image.BytePackedRaster.initIDs()V',
  'sun.awt.image.IntegerComponentRaster.initIDs()V',
  'sun.java2d.Disposer.initIDs()V',
]);


class UnsupportedNativeMethod extends Error {}


class TikaHostService {
  constructor() {
    this.calls = [];
  }

  invoke(service) {
    this.calls.push(service);

    if (AWT_INITIALIZERS.has(service)) {
      return { type: 'void' };
    }

    throw new UnsupportedNativeMethod(service);
  }
}


function frame(header) {
  const encodedHeader = Buffer.from(JSON.stringify(header), 'utf8');
  const message = Buffer.allocUnsafe(4 + encodedHeader.length);

  message.writeUInt32BE(encodedHeader.length);
  encodedHeader.copy(message, 4);

  return message;
}


async function readRequest(request) {
  const chunks = [];

  for await (const chunk of request) {
    chunks.push(chunk);
  }

  const body = Buffer.concat(chunks);
  const headerLength = body.readUInt32BE();
  const header = JSON.parse(body.subarray(4, 4 + headerLength).toString('utf8'));

  return header;
}


export class TikaHostServices {
  constructor() {
    this._token = randomBytes(32).toString('base64url');
    this._service = new TikaHostService();
    this._server = createServer((request, response) => {
      void this._handleRequest(request, response);
    });
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
      JAVA_APE_HOST: `http://127.0.0.1:${address.port}`,
      JAVA_APE_HOST_TOKEN: this._token,
      JAVA_APE_VIRTUAL_LIBRARIES: 'awt,fontmanager',
    };
  }

  close() {
    if (!this._started) {
      return;
    }

    this._server.close();
    this._started = false;
  }

  async _handleRequest(request, response) {
    if (request.method !== 'POST' || request.url !== '/v1/invoke') {
      response.writeHead(404);
      response.end();
      return;
    }

    if (request.headers.authorization !== `Bearer ${this._token}`) {
      this._send(response, {
        ok: false,
        error: { type: 'unauthorized', message: 'invalid host token' },
      });
      return;
    }

    let header;

    try {
      header = await readRequest(request);
    } catch {
      response.writeHead(400);
      response.end();
      return;
    }

    try {
      const result = this._service.invoke(header.service);

      this._send(response, { ok: true, return: result });
    } catch (error) {
      if (!(error instanceof UnsupportedNativeMethod)) {
        throw error;
      }

      this._send(response, {
        ok: false,
        error: {
          type: 'unsupported',
          message: `unsupported Tika host service: ${header.service}`,
        },
      });
    }
  }

  _send(response, header) {
    const message = frame(header);

    response.writeHead(200, {
      'Content-Type': 'application/vnd.java-ape-host; version=1',
      'Content-Length': message.length,
    });
    response.end(message);
  }
}
