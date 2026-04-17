import { existsSync } from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const [, , inputArg, outputArg] = process.argv;

if (!inputArg || !outputArg) {
  console.error('Usage: node export-single-page-pdf.mjs <input-html-or-url> <output-pdf>');
  process.exit(1);
}

const chromeCandidates = [
  process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
].filter(Boolean);

const executablePath = chromeCandidates.find((candidate) => existsSync(candidate));

if (!executablePath) {
  console.error('Chrome or Edge executable was not found. Set CHROME_PATH if needed.');
  process.exit(1);
}

const inputPath = path.resolve(inputArg);
const outputPath = path.resolve(outputArg);

function toPageUrl(input) {
  if (/^(https?:|file:\/\/)/i.test(input)) {
    return input;
  }

  return `file:///${path.resolve(input).replace(/\\/g, '/')}`;
}

const pageUrl = toPageUrl(inputArg);

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: ['--disable-gpu']
});

try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000, deviceScaleFactor: 1 });
  await page.goto(pageUrl, { waitUntil: 'networkidle0' });
  await page.emulateMediaType('screen');

  const viewportHeight = await page.evaluate(() => window.innerHeight);

  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
      }

      .h-screen {
        height: ${viewportHeight}px !important;
      }

      .min-h-screen {
        min-height: ${viewportHeight}px !important;
      }

      .animate-fade-in {
        opacity: 1 !important;
        transform: none !important;
      }
    `
  });

  await page.evaluate(async () => {
    if (document.fonts?.ready) {
      await document.fonts.ready;
    }

    document.querySelectorAll('.animate-fade-in').forEach((element) => {
      element.classList.add('visible');
    });

    window.scrollTo(0, 0);

    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });

  const { width, height } = await page.evaluate(() => {
    const body = document.body;
    const root = document.documentElement;

    return {
      width: Math.ceil(
        Math.max(
          body?.scrollWidth ?? 0,
          body?.offsetWidth ?? 0,
          body?.clientWidth ?? 0,
          root.scrollWidth,
          root.offsetWidth,
          root.clientWidth
        )
      ),
      height: Math.ceil(
        Math.max(
          body?.scrollHeight ?? 0,
          body?.offsetHeight ?? 0,
          body?.clientHeight ?? 0,
          root.scrollHeight,
          root.offsetHeight,
          root.clientHeight
        )
      )
    };
  });

  const paddedHeight = Math.ceil(height + Math.max(200, height * 0.08));

  await page.addStyleTag({
    content: `
      @page {
        size: ${width}px ${paddedHeight}px;
        margin: 0;
      }
    `
  });

  await page.pdf({
    path: outputPath,
    printBackground: true,
    displayHeaderFooter: false,
    width: `${width}px`,
    height: `${paddedHeight}px`,
    preferCSSPageSize: true,
    margin: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0
    }
  });

  console.log(`Exported single-page PDF: ${outputPath}`);
  console.log(`Page size: ${width}px x ${paddedHeight}px`);
} finally {
  await browser.close();
}