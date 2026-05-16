const path = require('path');
const { getDefaultConfig } = require('@react-native/metro-config');
const { getConfig } = require('react-native-builder-bob/metro-config');
const pkg = require('../../packages/zerolist/package.json');

const root = path.resolve(__dirname, '../..');

const defaultConfig = getDefaultConfig(__dirname);

// RN 0.85 의 resolver.blockList 는 단일 RegExp 인데
// react-native-monorepo-config@0.3.4 는 이를 배열로 spread 한다
// ([...(blockList || [])] → RegExp 는 iterable 이 아님 → 크래시).
// helper 에 넘기기 전에 배열로 정규화한다.
if (defaultConfig.resolver?.blockList instanceof RegExp) {
  defaultConfig.resolver.blockList = [defaultConfig.resolver.blockList];
}

/**
 * Metro configuration
 * https://facebook.github.io/metro/docs/configuration
 *
 * @type {import('metro-config').MetroConfig}
 */
module.exports = getConfig(defaultConfig, {
  root,
  pkg,
  project: __dirname,
});
