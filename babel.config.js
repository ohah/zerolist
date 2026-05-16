// jest(babel-jest) 가 라이브러리 TS/TSX 를 변환할 때 사용.
// 앱 번들은 apps/example/babel.config.js(bob preset) 가 따로 담당.
module.exports = {
  presets: ['module:@react-native/babel-preset'],
};
