/**
 * Jest-compatible expect() shim
 *
 * 基于 node:assert/strict 实现 Jest 风格的断言 API，
 * 使测试文件只需将 describe/test 改为 node:test 形式。
 *
 * 用法: import expect from '../../src/utils/expect.mjs'
 */
import assert from 'node:assert/strict';

export default function expect(actual) {
  const wrapper = {
    toBe(expected) {
      assert.strictEqual(actual, expected);
    },
    toEqual(expected) {
      assert.deepStrictEqual(actual, expected);
    },
    toBeTruthy() {
      assert.ok(actual);
    },
    toBeFalsy() {
      assert.ok(!actual);
    },
    toBeGreaterThanOrEqual(expected) {
      assert.ok(typeof actual === 'number' && actual >= expected,
        `Expected ${actual} to be >= ${expected}`);
    },
    toBeGreaterThan(expected) {
      assert.ok(typeof actual === 'number' && actual > expected,
        `Expected ${actual} to be > ${expected}`);
    },
    toBeLessThanOrEqual(expected) {
      assert.ok(typeof actual === 'number' && actual <= expected,
        `Expected ${actual} to be <= ${expected}`);
    },
    toBeLessThan(expected) {
      assert.ok(typeof actual === 'number' && actual < expected,
        `Expected ${actual} to be < ${expected}`);
    },
    toContain(expected) {
      if (typeof actual === 'string' && typeof expected === 'string') {
        assert.ok(actual.includes(expected),
          `Expected "${actual}" to contain "${expected}"`);
      } else {
        assert.ok(actual.includes(expected));
      }
    },
    toMatch(regex) {
      assert.ok(regex.test(actual),
        `Expected "${actual}" to match ${regex}`);
    },
    toHaveLength(len) {
      assert.strictEqual(actual.length, len);
    },
    toBeNull() {
      assert.strictEqual(actual, null);
    },
    toBeDefined() {
      assert.notStrictEqual(actual, undefined);
    },
    toBeUndefined() {
      assert.strictEqual(actual, undefined);
    },
    toBeInstanceOf(cls) {
      assert.ok(actual instanceof cls);
    },
    toHaveProperty(keyPath, value) {
      const keys = Array.isArray(keyPath) ? keyPath : keyPath.split('.');
      let obj = actual;
      for (const key of keys) {
        if (obj === undefined || obj === null) {
          assert.fail(`Expected object to have property ${keyPath}`);
        }
        obj = obj[key];
      }
      if (arguments.length > 1) {
        assert.deepStrictEqual(obj, value);
      }
    },
    get not() {
      return {
        toBe(expected) {
          assert.notStrictEqual(actual, expected);
        },
        toEqual(expected) {
          assert.notDeepStrictEqual(actual, expected);
        },
        toContain(expected) {
          assert.ok(!actual.includes(expected),
            `Expected "${actual}" not to contain "${expected}"`);
        },
        toBeNull() {
          assert.notStrictEqual(actual, null);
        },
        toBeUndefined() {
          assert.notStrictEqual(actual, undefined);
        },
        toBeTruthy() {
          assert.ok(!actual);
        },
        toBeFalsy() {
          assert.ok(actual);
        },
      };
    },
  };
  return wrapper;
}
