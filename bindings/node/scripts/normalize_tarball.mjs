#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
//
// Tika APE - Node release archive normalizer
// Copyright (C) 2025-2026 Tika APE contributors

import { gunzipSync, gzipSync } from 'node:zlib';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';


const archivePath = resolve(process.argv[2]);
const archive = Buffer.from(gunzipSync(readFileSync(archivePath)));
let offset = 0;

while (offset < archive.length) {
  const header = archive.subarray(offset, offset + 512);
  const name = header.subarray(0, 100).toString('utf8').replace(/\0.*$/, '');
  const prefix = header.subarray(345, 500).toString('utf8').replace(/\0.*$/, '');
  const path = prefix.length === 0 ? name : `${prefix}/${name}`;
  const size = Number.parseInt(
    header.subarray(124, 136).toString('ascii').replace(/\0.*$/, '').trim(),
    8,
  );

  if (name.length === 0) {
    break;
  }

  if (path === 'package/src/bin/tika.com') {
    header.write('0000755\0', 100, 'ascii');
    header.fill(0x20, 148, 156);

    let checksum = 0;
    for (const byte of header) {
      checksum += byte;
    }

    header.write(`${checksum.toString(8).padStart(6, '0')}\0 `, 148, 'ascii');
  }

  offset += 512 + Math.ceil(size / 512) * 512;
}

writeFileSync(archivePath, gzipSync(archive));
