import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import test from 'node:test'

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')


test('auth API exposes email verification and reset endpoints', () => {
  const source = read('src/api/auth.js')

  assert.match(
    source,
    /export const sendRegisterEmailCode = \(data\) => request\.post\('\/auth\/register\/email-code', data\)/
  )
  assert.match(
    source,
    /export const sendPasswordResetEmailCode = \(data\) => request\.post\('\/auth\/password-reset\/email-code', data\)/
  )
  assert.match(
    source,
    /export const resetPassword = \(data\) => request\.post\('\/auth\/password-reset', data\)/
  )
})


test('registration delegates verification to the backend', () => {
  const source = read('src/views/auth/Register.vue')

  assert.match(source, /sendRegisterEmailCode\(\{ email: form\.email \}\)/)
  assert.match(source, /verification_code: form\.verification_code/)
  assert.match(source, /:loading="codeLoading"/)
  assert.match(source, /onBeforeUnmount\(stopCountdown\)/)
  assert.match(source, /await sendRegisterEmailCode[\s\S]*startCountdown\(\)/)
  assert.ok(source.includes('pattern: /^\\d{6}$/'))
  assert.doesNotMatch(source, /Math\.random|sentCode|演示模式|前端验证码校验/)
})


test('forgot password route and login entry are wired', () => {
  const router = read('src/router/index.js')
  const login = read('src/views/auth/Login.vue')

  assert.match(router, /path: '\/forgot-password'/)
  assert.match(router, /name: 'ForgotPassword'/)
  assert.match(router, /ForgotPassword\.vue/)
  assert.match(login, /router\.push\('\/forgot-password'\)/)
})


test('forgot password page sends and resets without persistence', () => {
  const pageUrl = new URL('../src/views/auth/ForgotPassword.vue', import.meta.url)
  assert.equal(existsSync(pageUrl), true, 'ForgotPassword.vue must exist')
  const source = read('src/views/auth/ForgotPassword.vue')

  assert.match(source, /sendPasswordResetEmailCode\(\{ email: form\.email \}\)/)
  assert.match(
    source,
    /resetPassword\(\{[\s\S]*email: form\.email,[\s\S]*verification_code: form\.verification_code,[\s\S]*new_password: form\.new_password/
  )
  assert.match(source, /onBeforeUnmount\(stopCountdown\)/)
  assert.match(source, /sendLoading/)
  assert.match(source, /resetLoading/)
  assert.match(source, /两次密码不一致/)
  assert.ok(source.includes('pattern: /^\\d{6}$/'))
  assert.doesNotMatch(source, /localStorage|sessionStorage|useUserStore/)
})
