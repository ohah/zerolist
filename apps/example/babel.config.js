const path = require('path');
const { getConfig } = require('react-native-builder-bob/babel-config');
const pkg = require('../../packages/zerolist/package.json');

// bob/babel-config 는 root 에서 bob 설정(source)을 읽어
// 라이브러리 소스에 bob preset 을 적용한다. 따라서 babel 의
// root 는 모노레포 루트가 아니라 라이브러리 패키지 디렉토리다.
const root = path.resolve(__dirname, '../../packages/zerolist');

module.exports = getConfig(
  {
    presets: ['module:@react-native/babel-preset'],
  },
  { root, pkg }
);
