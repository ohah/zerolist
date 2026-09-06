/**
 * @type {import('@react-native-community/cli-types').UserDependencyConfig}
 */
module.exports = {
  dependency: {
    platforms: {
      android: {
        packageImportPath: 'import com.zerolist.ZerolistPackage;',
        packageInstance: 'new ZerolistPackage()',
        componentDescriptors: ['ZlPoolListComponentDescriptor'],
        cmakeListsPath: 'generated/jni/CMakeLists.txt',
        cxxModuleCMakeListsModuleName: 'react-native-zerolist',
        cxxModuleCMakeListsPath: 'CMakeLists.txt',
        cxxModuleHeaderName: 'ZerolistImpl',
      },
    },
  },
};
