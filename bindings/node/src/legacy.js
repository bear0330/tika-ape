// SPDX-License-Identifier: Apache-2.0

import {
  detect,
  detectEncoding,
  extractJson,
  extractText,
  extractXml,
  raw,
} from './api.js';

function splitOptionsAndCallback(options, callback) {
  if (typeof options === 'function') {
    return { options: {}, callback: options };
  }

  return { options: options ?? {}, callback };
}

function invokeCallback(task, callback, result) {
  if (typeof callback === 'function') {
    task.then(
      (value) => callback(null, ...result(value)),
      (error) => callback(error),
    );
  }

  return task;
}

function withCallback(operation, source, options, callback) {
  const task = operation(source, options);

  return invokeCallback(task, callback, (value) => [value]);
}

async function languageFromText(value) {
  const result = await raw(['--language', '-'], { input: value });

  return result.stdout.trim();
}

async function typeAndCharsetFromSource(source, options) {
  const metadata = await extractJson(source, options);

  return metadata['Content-Type'] ?? detect(source, options);
}

function legacyLanguageCode(languageCode) {
  try {
    return new Intl.Locale(languageCode).language ?? languageCode;
  } catch (error) {
    if (error instanceof RangeError) {
      return languageCode;
    }

    throw error;
  }
}

export function extract(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);
  const task = Promise.all([
    extractText(source, invocation.options),
    extractJson(source, invocation.options),
  ]).then(([text, metadata]) => ({ text, metadata }));

  return invokeCallback(
    task,
    invocation.callback,
    (result) => [result.text, result.metadata],
  );
}


export function text(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(extractText, source, invocation.options, invocation.callback);
}


export function xhtml(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(extractXml, source, invocation.options, invocation.callback);
}


export function meta(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(extractJson, source, invocation.options, invocation.callback);
}


export function type(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(detect, source, invocation.options, invocation.callback);
}


export function charset(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(detectEncoding, source, invocation.options, invocation.callback);
}


export function encoding(source, options, callback) {
  return charset(source, options, callback);
}


export function typeAndCharset(source, options, callback) {
  const invocation = splitOptionsAndCallback(options, callback);

  return withCallback(
    typeAndCharsetFromSource,
    source,
    invocation.options,
    invocation.callback,
  );
}


export function language(value, callback) {
  const task = languageFromText(value);

  return invokeCallback(
    task.then(legacyLanguageCode),
    callback,
    (languageCode) => [languageCode, null],
  );
}
