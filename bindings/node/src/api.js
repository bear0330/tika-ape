// SPDX-License-Identifier: Apache-2.0

import {
  copyFileSync,
  existsSync,
  mkdtempSync,
  rmSync,
} from 'node:fs';
import {
  basename,
  isAbsolute,
  join,
  relative,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';

import { createClient } from './client.js';
import { TikaHostServices } from './host_services.js';


const DEFAULT_CLIENT = createClient();
const DEFAULT_CONFIG = fileURLToPath(
  new URL('./config/default.json', import.meta.url),
);
const INLINE_IMAGES_CONFIG = fileURLToPath(
  new URL('./config/inline-images.json', import.meta.url),
);

let hostServicesEnabled = true;
let inlineImagesEnabled = false;
let hostServices = null;


export function configure({ hostServices: useHostServices = true, inlineImages = false } = {}) {
  if (!useHostServices && hostServices !== null) {
    hostServices.close();
    hostServices = null;
  }

  hostServicesEnabled = useHostServices;
  inlineImagesEnabled = inlineImages;
}


async function client() {
  if (!hostServicesEnabled) {
    return DEFAULT_CLIENT;
  }

  if (hostServices === null) {
    hostServices = new TikaHostServices();
    await hostServices.start();
  }

  return createClient({ environment: hostServices.environment() });
}


function configPath(config) {
  if (config !== undefined && config !== null) {
    return config;
  }

  if (inlineImagesEnabled) {
    return INLINE_IMAGES_CONFIG;
  }

  return DEFAULT_CONFIG;
}


function sourcePath(source) {
  const candidate = source instanceof URL && source.protocol === 'file:'
    ? fileURLToPath(source)
    : String(source);

  if (!existsSync(candidate)) {
    return { source: candidate, cleanup: null };
  }

  const sourcePath = resolve(candidate);
  const relativePath = relative(process.cwd(), sourcePath);

  if (
    !isAbsolute(relativePath)
    && !relativePath.startsWith(`..${sep}`)
    && relativePath !== '..'
  ) {
    return { source: relativePath.split(sep).join('/'), cleanup: null };
  }

  const temporaryDirectory = mkdtempSync(join(process.cwd(), '.tika-ape-'));
  const stagedPath = join(temporaryDirectory, basename(sourcePath));
  copyFileSync(sourcePath, stagedPath);

  return {
    source: relative(process.cwd(), stagedPath).split(sep).join('/'),
    cleanup: () => rmSync(temporaryDirectory, { recursive: true, force: true }),
  };
}


async function invoke(operation, source, options = {}) {
  const tikaClient = await client();
  const stagedSource = sourcePath(source);
  const parameters = {
    ...options,
    source: stagedSource.source,
    config: configPath(options.config),
  };

  try {
    return await tikaClient.invoke(operation, parameters);
  } finally {
    stagedSource.cleanup?.();
  }
}


export function extract(source, options = {}) {
  return invoke('extract', source, options);
}


export function extractText(source, options = {}) {
  return invoke('extractText', source, options);
}


export function extractXml(source, options = {}) {
  return invoke('extractXml', source, options);
}


export function extractJson(source, options = {}) {
  return invoke('extractJson', source, options);
}


export function metadata(source, options = {}) {
  return invoke('metadata', source, options);
}


export function detect(source, options = {}) {
  return invoke('detect', source, options);
}


export async function detectEncoding(source, options = {}) {
  const document = await extractJson(source, options);

  return document['Content-Encoding'] ?? document['tk:detected-encoding'] ?? null;
}


export async function detectLanguage(source, options = {}) {
  return invoke('detectLanguage', source, options);
}


export async function raw(arguments_, options = {}) {
  const tikaClient = await client();

  return tikaClient.raw(arguments_, options);
}


export function hostServiceCalls() {
  if (hostServices === null) {
    return [];
  }

  return hostServices.calls;
}
