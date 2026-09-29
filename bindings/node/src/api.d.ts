// SPDX-License-Identifier: Apache-2.0

import type { APEProcessResult, ProcessSession, RawOptions } from './_runtime.js';


export interface ConfigureOptions {
  hostServices?: boolean;
  inlineImages?: boolean;
}

export interface TikaOptions {
  config?: string;
  password?: string;
  encoding?: string;
  prettyPrint?: boolean;
}

export function configure(options?: ConfigureOptions): void;
export function extract(source: string | URL, options?: TikaOptions): Promise<string>;
export function extractText(source: string | URL, options?: TikaOptions): Promise<string>;
export function extractXml(source: string | URL, options?: TikaOptions): Promise<string>;
export function extractJson(source: string | URL, options?: TikaOptions): Promise<unknown>;
export function metadata(source: string | URL, options?: TikaOptions): Promise<string>;
export function detect(source: string | URL, options?: TikaOptions): Promise<string>;
export function detectEncoding(source: string | URL, options?: TikaOptions): Promise<string | null>;
export function detectLanguage(source: string | URL, options?: TikaOptions): Promise<string | null>;
export function raw(
  arguments_: readonly unknown[],
  options?: RawOptions,
): Promise<APEProcessResult | ProcessSession>;
