/* eslint-disable no-console */
/**
 * CRA build helper for environments where delete/unlink is blocked.
 *
 * Problem:
 *   `react-scripts build` always tries to clean the target build folder by deleting files.
 *   In some locked-down Windows environments, deletes/unlinks fail (EPERM/Access denied).
 *
 * Approach:
 *  1) Build into a fresh, unique BUILD_PATH (no pre-existing files to delete).
 *  2) Copy the generated output into the stable `build/` folder by overwriting files only.
 *     We intentionally do not delete any old hashed assets in `build/` (they're harmless).
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function pad2(n) {
  return String(n).padStart(2, '0');
}

function buildStamp() {
  const d = new Date();
  return [
    d.getFullYear(),
    pad2(d.getMonth() + 1),
    pad2(d.getDate()),
    pad2(d.getHours()),
    pad2(d.getMinutes()),
    pad2(d.getSeconds()),
  ].join('');
}

function copyTree(srcDir, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  const entries = fs.readdirSync(srcDir, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(srcDir, entry.name);
    const destPath = path.join(destDir, entry.name);

    if (entry.isDirectory()) {
      copyTree(srcPath, destPath);
      continue;
    }

    if (entry.isSymbolicLink()) {
      // CRA build output should not contain symlinks, but handle defensively.
      const target = fs.readlinkSync(srcPath);
      try {
        fs.symlinkSync(target, destPath);
      } catch (err) {
        // If it already exists or symlinks are blocked, fall back to copying contents.
        try {
          fs.copyFileSync(srcPath, destPath);
        } catch {
          throw err;
        }
      }
      continue;
    }

    fs.mkdirSync(path.dirname(destPath), { recursive: true });
    fs.copyFileSync(srcPath, destPath);
  }
}

function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const stamp = buildStamp();
  const tempBuildRel = `build_tmp_${stamp}`;
  const tempBuild = path.join(projectRoot, tempBuildRel);
  const finalBuild = path.join(projectRoot, 'build');

  const reactScriptsBin = path.join(
    projectRoot,
    'node_modules',
    '.bin',
    process.platform === 'win32' ? 'react-scripts.cmd' : 'react-scripts'
  );

  if (!fs.existsSync(reactScriptsBin)) {
    console.error(`Could not find react-scripts binary at: ${reactScriptsBin}`);
    process.exit(1);
  }

  console.log(`Building CRA client into: ${tempBuildRel}`);

  const env = { ...process.env, BUILD_PATH: tempBuildRel };
  const spawnArgs =
    process.platform === 'win32'
      ? { command: 'cmd.exe', args: ['/c', reactScriptsBin, 'build'] }
      : { command: reactScriptsBin, args: ['build'] };

  const result = spawnSync(spawnArgs.command, spawnArgs.args, {
    cwd: projectRoot,
    stdio: 'inherit',
    env,
  });

  if (result.error) {
    console.error('Failed to run react-scripts build:', result.error);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status || 1);
  }

  console.log(`Copying build output into: build/ (overwrites only; no deletes)`);
  fs.mkdirSync(finalBuild, { recursive: true });
  copyTree(tempBuild, finalBuild);

  // Ensure Catalyst metadata files that live at project root also get into build/.
  // CRA won't copy these automatically, and deletes are blocked so we must overwrite in place.
  const clientPackageSrc = path.join(projectRoot, 'client-package.json');
  const clientPackageDest = path.join(finalBuild, 'client-package.json');
  if (fs.existsSync(clientPackageSrc)) {
    fs.copyFileSync(clientPackageSrc, clientPackageDest);
  }

  console.log('Build complete.');
  console.log(`Note: temp build folder kept (delete is blocked): ${tempBuildRel}`);
}

main();
