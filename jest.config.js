// 2-프로젝트 분리:
//  - logic: 순수 가상화/레퍼런스 로직(React/RN 비의존). node 환경,
//    babel-jest 변환만. bun 호이스팅·RN preset 영향 없이 견고하게 대량
//    테스트가 도는 지점.
//  - native: RN 컴포넌트(ZeroList) 테스트. @react-native/jest-preset +
//    @testing-library/react-native. (RN 0.85 공식 조합 = jest 29)
//
// 규약: 순수 로직 = *.test.ts, 컴포넌트 = *.test.tsx
const ignore = [
  '<rootDir>/apps/example/node_modules',
  '<rootDir>/packages/zerolist/lib/',
];

module.exports = {
  projects: [
    {
      displayName: 'logic',
      testEnvironment: 'node',
      roots: ['<rootDir>/packages/zerolist'],
      testMatch: ['**/__tests__/**/*.test.ts'],
      modulePathIgnorePatterns: ignore,
      transform: { '^.+\\.[tj]sx?$': 'babel-jest' },
    },
    {
      displayName: 'native',
      preset: '@react-native/jest-preset',
      roots: ['<rootDir>/packages/zerolist'],
      testMatch: ['**/__tests__/**/*.test.tsx'],
      modulePathIgnorePatterns: ignore,
      transformIgnorePatterns: [
        'node_modules/(?!(.*/)?(jest-)?@?react-native|@react-native-community|@react-navigation)',
      ],
    },
  ],
};
