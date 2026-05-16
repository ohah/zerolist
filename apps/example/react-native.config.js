const path = require('path');
const pkg = require('../../packages/zerolist/package.json');
const libRoot = path.join(__dirname, '../../packages/zerolist');

module.exports = {
  project: {
    ios: {
      automaticPodsInstallation: true,
    },
  },
  dependencies: {
    [pkg.name]: {
      root: libRoot,
      platforms: {
        // Codegen script incorrectly fails without this
        // So we explicitly specify the platforms with empty object
        ios: {},
        android: {},
      },
    },
  },
};
