// SPDX-License-Identifier: Apache-2.0

import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

import {
  extract,
  language,
  text,
  xhtml,
} from '../src/index.js';


const testDirectory = fileURLToPath(new URL('.', import.meta.url));
const fixturePath = `${testDirectory}/fixtures/sample.txt`;

const textResult = await new Promise((resolve, reject) => {
  text(fixturePath, (error, value) => {
    if (error !== null) {
      reject(error);
      return;
    }

    resolve(value);
  });
});

const extracted = await new Promise((resolve, reject) => {
  extract(fixturePath, (error, value, metadata) => {
    if (error !== null) {
      reject(error);
      return;
    }

    resolve({ value, metadata });
  });
});

const xml = await new Promise((resolve, reject) => {
  xhtml(fixturePath, (error, value) => {
    if (error !== null) {
      reject(error);
      return;
    }

    resolve(value);
  });
});

const detectedLanguage = await new Promise((resolve, reject) => {
  language('This is just some text in English.', (error, value, reasonablyCertain) => {
    if (error !== null) {
      reject(error);
      return;
    }

    resolve({ value, reasonablyCertain });
  });
});

assert.match(textResult, /APEBind turns portable CLI applications/);
assert.match(extracted.value, /APEBind turns portable CLI applications/);
assert.match(extracted.metadata['Content-Type'], /^text\/plain/);
assert.match(xml, /APEBind turns portable CLI applications/);
assert.equal(detectedLanguage.value, 'en');
assert.equal(detectedLanguage.reasonablyCertain, null);
