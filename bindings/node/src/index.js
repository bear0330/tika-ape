// SPDX-License-Identifier: Apache-2.0

export {
  configure,
  detect,
  detectEncoding,
  detectLanguage,
  extract as extractMarkdown,
  extractJson,
  extractText,
  extractXml,
  metadata,
  raw,
} from './api.js';
export {
  charset,
  encoding,
  extract,
  language,
  meta,
  text,
  type,
  typeAndCharset,
  xhtml,
} from './legacy.js';
export {
  APEEvent,
  APEEventError,
  APEProcessError,
  APEProcessResult,
  APETimeoutError,
  ProcessSession,
} from './_runtime.js';
