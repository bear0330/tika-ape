// SPDX-License-Identifier: Apache-2.0

import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

import {
  detect,
  detectEncoding,
  detectLanguage,
  extractMarkdown,
  extractJson,
  extractText,
} from '../src/index.js';


const testDirectory = fileURLToPath(new URL('.', import.meta.url));
const fixturePath = `${testDirectory}/fixtures/sample.txt`;
const htmlFixturePath = `${testDirectory}/fixtures/remote.html`;
const absoluteFixtureUrl = new URL('./fixtures/sample.txt', import.meta.url);
const externalFixturePath = fileURLToPath(
  new URL('../../../tests/fixtures/sample.txt', import.meta.url),
);

const extracted = await extractMarkdown(fixturePath);
const detectedType = await detect(fixturePath);
const document = await extractJson(fixturePath);
const encoding = await detectEncoding(fixturePath);
const language = await detectLanguage(htmlFixturePath);
const absoluteText = await extractText(absoluteFixtureUrl);
const externalText = await extractText(externalFixturePath);

assert.match(extracted, /APEBind turns portable CLI applications/);
assert.equal(detectedType, 'text/plain');

assert.match(document['Content-Type'], /^text\/plain/);
assert.equal(encoding, 'windows-1252');
assert.equal(language, 'eng');
assert.match(absoluteText, /APEBind turns portable CLI applications/);
assert.match(externalText, /APEBind turns portable CLI applications/);
