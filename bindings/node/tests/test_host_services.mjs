// SPDX-License-Identifier: Apache-2.0

import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

import { APEProcessError, configure, extractXml } from '../src/index.js';
import { AWT_INITIALIZERS } from '../src/host_services.js';
import { hostServiceCalls } from '../src/api.js';


const testDirectory = fileURLToPath(new URL('.', import.meta.url));
const inlineImagesPdf = `${testDirectory}/fixtures/tika-inline-images.pdf`;
const imageReportPdf = `${testDirectory}/fixtures/rwservlet.pdf`;

configure({ hostServices: false, inlineImages: true });

await assert.rejects(
  extractXml(inlineImagesPdf),
  (error) => error instanceof APEProcessError
    && error.result.stderr.includes('ColorModel')
    && error.result.stderr.includes('no awt in system library path'),
);

configure({ hostServices: true, inlineImages: true });

const extracted = await extractXml(inlineImagesPdf);
const report = await extractXml(imageReportPdf);
const invoked = new Set(hostServiceCalls());

assert.equal(extracted.match(/embedded:image-/g)?.length, 2);
assert.match(extracted, /embedded:image-0\.jpg/);
assert.match(extracted, /embedded:image-1\.tif/);
assert.match(report, /Allegheny County Health Department/);
assert.ok([...invoked].every((service) => AWT_INITIALIZERS.has(service)));
assert.ok(invoked.has('java.awt.image.BufferedImage.initIDs()V'));
assert.ok(invoked.has('java.awt.image.ColorModel.initIDs()V'));
assert.ok(invoked.has('java.awt.image.Raster.initIDs()V'));
assert.ok(invoked.has('sun.java2d.Disposer.initIDs()V'));

configure({ hostServices: false });
