/** Restore the repository's lossless gzip evidence using only Node20 built-ins. */
import {createHash} from 'node:crypto';
import {createReadStream, createWriteStream} from 'node:fs';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {fileURLToPath} from 'node:url';
import {createGunzip} from 'node:zlib';

const manifestName = 'output/COMPRESSED_EVIDENCE.json';
const defaultRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hex256 = /^[a-f0-9]{64}$/;

function relativePath(value, kind) {
  if (typeof value !== 'string' || value.includes('\\') || value.includes('\0') ||
      path.posix.isAbsolute(value) || path.posix.normalize(value) !== value ||
      value.split('/').some(part => part === '' || part === '.' || part === '..')) {
    throw new Error(`Unsafe ${kind} path`);
  }
  if (!value.startsWith('output/') || value === manifestName) throw new Error(`Invalid ${kind} scope`);
  if (kind === 'gzip' && (!value.startsWith('output/compressed-evidence/') || !value.endsWith('.gz'))) {
    throw new Error('Gzip must be a local output/compressed-evidence asset');
  }
  if (kind === 'raw' && (!value.endsWith('.json') || value.startsWith('output/compressed-evidence/'))) {
    throw new Error('Raw destination must be an output JSON outside compressed assets');
  }
  return value;
}

async function safePath(root, relative, {createParents = false} = {}) {
  const parts = relative.split('/');
  let current = root;
  for (let index = 0; index < parts.length; index += 1) {
    current = path.join(current, parts[index]);
    let stat;
    try { stat = await fs.lstat(current); }
    catch (error) {
      if (error.code !== 'ENOENT') throw error;
      if (index < parts.length - 1 && createParents) {
        try { await fs.mkdir(current); }
        catch (mkdirError) { if (mkdirError.code !== 'EEXIST') throw mkdirError; }
        stat = await fs.lstat(current);
      } else if (index < parts.length - 1) throw new Error(`Missing parent: ${relative}`);
      else return current;
    }
    if (stat.isSymbolicLink()) throw new Error(`Symlink is not allowed: ${relative}`);
    if (index < parts.length - 1 && !stat.isDirectory()) throw new Error(`Non-directory parent: ${relative}`);
    if (index === parts.length - 1 && !stat.isFile()) throw new Error(`Not a regular file: ${relative}`);
  }
  return current;
}

async function fingerprint(filename) {
  const hash = createHash('sha256');
  let bytes = 0;
  for await (const chunk of createReadStream(filename)) { bytes += chunk.length; hash.update(chunk); }
  return {bytes, sha256: hash.digest('hex')};
}

async function verify(filename, bytes, sha256, label) {
  const stat = await fs.lstat(filename);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size !== bytes) throw new Error(`${label}: size/type mismatch`);
  const actual = await fingerprint(filename);
  if (actual.bytes !== bytes || actual.sha256 !== sha256) throw new Error(`${label}: SHA256 mismatch`);
}

export async function restoreEvidence(destinationRoot = defaultRoot, log = console.log) {
  const root = await fs.realpath(destinationRoot);
  const manifestPath = await safePath(root, manifestName);
  if ((await fs.stat(manifestPath)).size > 2 ** 20) throw new Error('Unexpectedly large compressed evidence index');
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  if (manifest.schema !== 'qfactoria-compressed-evidence.v1' || manifest.compression !== 'gzip' ||
      !Array.isArray(manifest.files) || manifest.files.length === 0) throw new Error('Unsupported evidence index');
  const destinations = new Set();
  const assets = new Set();
  // Validate the entire index before creating any destination directories/files.
  for (const entry of manifest.files) {
    relativePath(entry.path, 'raw'); relativePath(entry.gzip_path, 'gzip');
    if (![entry.raw_bytes, entry.gzip_bytes].every(size => Number.isSafeInteger(size) && size > 0) ||
        entry.gzip_bytes >= 100 * 2 ** 20 || !hex256.test(entry.raw_sha256) || !hex256.test(entry.gzip_sha256)) {
      throw new Error('Invalid evidence size/hash');
    }
    const rawKey = entry.path.toLowerCase(), gzipKey = entry.gzip_path.toLowerCase();
    if (destinations.has(rawKey) || assets.has(gzipKey)) throw new Error('Duplicate evidence path');
    destinations.add(rawKey); assets.add(gzipKey);
  }
  const results = [];
  for (const entry of manifest.files) {
    const compressed = await safePath(root, entry.gzip_path);
    await verify(compressed, entry.gzip_bytes, entry.gzip_sha256, entry.gzip_path);
    const target = await safePath(root, entry.path, {createParents: true});
    try {
      await fs.lstat(target);
      await verify(target, entry.raw_bytes, entry.raw_sha256, entry.path);
      results.push({path: entry.path, restored: false});
      log(`[evidence] verified ${entry.path}`);
      continue;
    } catch (error) { if (error.code !== 'ENOENT') throw error; }

    const staging = await fs.mkdtemp(path.join(path.dirname(target), '.restore-compressed-'));
    const partial = path.join(staging, 'content.partial');
    const ready = path.join(staging, 'content.verified');
    try {
      const hash = createHash('sha256');
      let bytes = 0;
      const checker = new Transform({transform(chunk, encoding, callback) {
        bytes += chunk.length;
        if (bytes > entry.raw_bytes) { callback(new Error(`${entry.path}: expanded size exceeds index`)); return; }
        hash.update(chunk); callback(null, chunk);
      }});
      await pipeline(createReadStream(compressed), createGunzip(), checker,
                     createWriteStream(partial, {flags: 'wx', mode: 0o600}));
      if (bytes !== entry.raw_bytes || hash.digest('hex') !== entry.raw_sha256) {
        throw new Error(`${entry.path}: restored size/SHA256 mismatch`);
      }
      await fs.rename(partial, ready); // Atomically promote only this run's verified staging file.
      // Exclusive atomic publication: rename alone could overwrite a concurrent
      // destination. A same-filesystem hard link fails safely with EEXIST.
      try { await fs.link(ready, target); }
      catch (error) {
        if (error.code !== 'EEXIST') throw error;
        await safePath(root, entry.path);
        await verify(target, entry.raw_bytes, entry.raw_sha256, entry.path);
      }
      results.push({path: entry.path, restored: true});
      log(`[evidence] restored ${entry.path}`);
    } finally {
      // Touch only unique paths created by this invocation, never existing raws.
      for (const ownFile of [partial, ready]) {
        try { await fs.unlink(ownFile); } catch (error) { if (error.code !== 'ENOENT') throw error; }
      }
      await fs.rmdir(staging);
    }
  }
  return results;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length && !(args.length === 2 && args[0] === '--root')) {
    console.error('Usage: node scripts/restore-compressed-evidence.mjs [--root DIRECTORY]');
    process.exitCode = 1;
  } else {
    try { await restoreEvidence(args.length ? path.resolve(args[1]) : defaultRoot); }
    catch (error) { console.error(`[evidence] ${error.message}`); process.exitCode = 1; }
  }
}
