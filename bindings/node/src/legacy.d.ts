// SPDX-License-Identifier: Apache-2.0

import type { TikaOptions } from './api.js';


export type TikaCallback<T> = (error: Error | null, value?: T) => void;
export type TikaExtractCallback = (
  error: Error | null,
  text?: string,
  metadata?: unknown,
) => void;
export type TikaLanguageCallback = (
  error: Error | null,
  language?: string,
  reasonablyCertain?: boolean | null,
) => void;

export interface LegacyExtractResult {
  text: string;
  metadata: unknown;
}

export function extract(
  source: string | URL,
  options?: TikaOptions | TikaExtractCallback,
  callback?: TikaExtractCallback,
): Promise<LegacyExtractResult>;

export function text(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string>,
  callback?: TikaCallback<string>,
): Promise<string>;
export function xhtml(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string>,
  callback?: TikaCallback<string>,
): Promise<string>;
export function meta(
  source: string | URL,
  options?: TikaOptions | TikaCallback<unknown>,
  callback?: TikaCallback<unknown>,
): Promise<unknown>;
export function type(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string>,
  callback?: TikaCallback<string>,
): Promise<string>;
export function charset(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string | null>,
  callback?: TikaCallback<string | null>,
): Promise<string | null>;
export function encoding(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string | null>,
  callback?: TikaCallback<string | null>,
): Promise<string | null>;
export function typeAndCharset(
  source: string | URL,
  options?: TikaOptions | TikaCallback<string>,
  callback?: TikaCallback<string>,
): Promise<string>;
export function language(
  value: string,
  callback?: TikaLanguageCallback,
): Promise<string>;
