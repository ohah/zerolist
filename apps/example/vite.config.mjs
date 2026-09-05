import { defineConfig, mergeConfig } from 'vite';

import config from 'react-native-builder-bob/vite-config';
import pack from '../../packages/zerolist/package.json' with { type: 'json' };

export default defineConfig((env) =>
  mergeConfig(config(env), {
    resolve: {
      alias: {
        'react-native': new URL('./src/web/reactNative.ts', import.meta.url)
          .pathname,
        [pack.name]: new URL(
          '../../packages/zerolist/src/index.tsx',
          import.meta.url
        ).pathname,
      },
      dedupe: Object.keys(pack.peerDependencies),
    },
  })
);
