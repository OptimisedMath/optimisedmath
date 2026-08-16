import { describe, expect, it, vi } from 'vitest';
import { reportError } from '@/lib/session/errors';

describe('reportError', () => {
  it('sets the error message from an Error instance', () => {
    const setError = vi.fn();
    const err = new Error('boom');

    reportError(setError, err, 'fallback message', 'Error doing thing:');

    expect(setError).toHaveBeenCalledWith('boom');
  });

  it('sets the fallback message for a non-Error thrown value', () => {
    const setError = vi.fn();

    reportError(setError, 'not an error', 'fallback message', 'Error doing thing:');

    expect(setError).toHaveBeenCalledWith('fallback message');
  });

  it('logs the error with the given label', () => {
    const setError = vi.fn();
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const err = new Error('boom');

    reportError(setError, err, 'fallback message', 'Error doing thing:');

    expect(consoleErrorSpy).toHaveBeenCalledWith('Error doing thing:', err);
    consoleErrorSpy.mockRestore();
  });
});
