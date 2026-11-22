import assert from 'node:assert/strict';
import { test } from 'node:test';
import worker from '../src/worker.ts';

test('the local browser shell renders without outbound API access', async (t) => {
  const outbound = t.mock.method(globalThis, 'fetch', () => {
    throw new Error('This offline test must never call an external service');
  });
  const response = await worker.fetch(new Request('https://example.invalid/'), {
    APP_NAME: 'Example Invite Tool',
    LOGO_URL: '',
    THEME_PRIMARY_COLOR: '#123456',
  });
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /text\/html/);
  assert.match(await response.text(), /Example Invite Tool/);
  assert.equal(outbound.mock.callCount(), 0);
});

test('integration API documentation and MCP routes remain absent', async (t) => {
  const outbound = t.mock.method(globalThis, 'fetch', () => {
    throw new Error('This offline test must never call an external service');
  });
  for (const path of ['/api/docs', '/api/openapi.json', '/mcp']) {
    const response = await worker.fetch(new Request(`https://example.invalid${path}`), {});
    assert.equal(response.status, 404, path);
  }
  assert.equal(outbound.mock.callCount(), 0);
});
