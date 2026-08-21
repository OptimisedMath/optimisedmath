import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const FRONTEND_ROOT = join(import.meta.dirname, '..');
const COMPONENTS_ROOT = join(FRONTEND_ROOT, 'components');
const SESSION_TYPES_PATH = join(FRONTEND_ROOT, 'lib/session/types.ts');

function collectSourceFiles(directory: string): string[] {
  const entries = readdirSync(directory);
  const files: string[] = [];

  for (const entry of entries) {
    const fullPath = join(directory, entry);
    const stats = statSync(fullPath);

    if (stats.isDirectory()) {
      files.push(...collectSourceFiles(fullPath));
      continue;
    }

    if (/\.(tsx?|jsx?)$/.test(entry)) {
      files.push(fullPath);
    }
  }

  return files;
}

describe('ADR-0002 SessionResponse privacy', () => {
  it('SessionView no longer exposes a session field', () => {
    const source = readFileSync(SESSION_TYPES_PATH, 'utf8');
    const sessionViewBlock = source.match(/export interface SessionView \{[\s\S]*?\n\}/)?.[0];

    expect(sessionViewBlock).toBeDefined();
    expect(sessionViewBlock).not.toMatch(/\bsession\s*:\s*SessionResponse/);
  });

  it('no file under frontend/components imports SessionResponse', () => {
    const violations: string[] = [];

    for (const filePath of collectSourceFiles(COMPONENTS_ROOT)) {
      const source = readFileSync(filePath, 'utf8');
      if (/\bSessionResponse\b/.test(source)) {
        violations.push(relative(FRONTEND_ROOT, filePath));
      }
    }

    expect(violations).toEqual([]);
  });

  it('no arena component reads view.session', () => {
    const violations: string[] = [];

    for (const filePath of collectSourceFiles(join(COMPONENTS_ROOT, 'arena'))) {
      const source = readFileSync(filePath, 'utf8');
      if (/view\.session/.test(source)) {
        violations.push(relative(FRONTEND_ROOT, filePath));
      }
    }

    expect(violations).toEqual([]);
  });
});
