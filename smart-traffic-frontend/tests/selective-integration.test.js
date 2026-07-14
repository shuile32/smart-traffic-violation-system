import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const source = path => readFile(new URL(path, import.meta.url), 'utf8')

test('profile edits backend contact fields and uses role avatars', async () => {
  const profile = await source('../src/views/Profile.vue')
  assert.match(profile, /form\.email/)
  assert.match(profile, /form\.phone/)
  assert.match(profile, /updateProfile\(\{ phone: form\.phone, email: form\.email \}\)/)
  assert.match(profile, /\/images\/admin\.jpg/)
  assert.match(profile, /\/images\/reviewer\.jpg/)
  assert.match(profile, /\/images\/citizen\.jpg/)
  assert.match(profile, /userStore\.logout\(\)/)
  assert.match(profile, /router\.push\('\/login'\)/)
})

test('all layouts use the shared header and route-aware cache shell', async () => {
  const header = await source('../src/components/HeaderActions.vue')
  assert.match(header, /<AnnouncementBell \/>/)
  for (const name of ['AdminLayout', 'ReviewLayout', 'CitizenLayout']) {
    const layout = await source(`../src/layouts/${name}.vue`)
    assert.match(layout, /<HeaderActions/)
    assert.match(layout, /<BackToTop/)
    assert.match(layout, /meta\.keepAlive/)
    assert.doesNotMatch(layout, /cachedViews|:include=/)
  }
})

test('admin placeholders are removed and case detail is shared', async () => {
  const router = await source('../src/router/index.js')
  assert.doesNotMatch(router, /admin\/drivers|admin\/database|DriverList|DatabaseMaintain/)
  assert.match(router, /path: 'violations\/:id'[\s\S]*views\/review\/CaseDetail\.vue/)
  assert.match(router, /keepAlive: true/)
})

test('app provides a global render error boundary', async () => {
  const app = await source('../src/App.vue')
  assert.match(app, /onErrorCaptured/)
  assert.match(app, /window\.location\.reload\(\)/)
})
