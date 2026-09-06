# Contributing

Contributions are always welcome, no matter how large or small!

We want this community to be friendly and respectful to each other. Please follow it in all your interactions with the project. Before contributing, please read the [code of conduct](./CODE_OF_CONDUCT.md).

## Development workflow

The repository uses Bun workspaces: `packages/zerolist` is the library and
`apps/example` is the example application. CI pins Node from `.nvmrc`, Bun
1.3.11 and Zig 0.16.0. Install with the committed lockfile:

```sh
bun install --frozen-lockfile
bun run lint
bun run typecheck
bun run test --runInBand
bun run build:lib
bun run --cwd apps/example build:web
```

`typecheck` checks the library build project. Android/iOS CI also compile the
example app. Web lists using Android Fabric components are unavailable on web;
they are not substituted with another engine for performance comparisons.

Generate the native module code after changing its spec or on a fresh checkout:

```sh
bun run codegen
```

Android release build (JDK 17+, SDK 36, NDK 27.1.12297006 and CMake 3.22.1):

```sh
bun run zig:build
bun run codegen
cd apps/example/android
./gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a
```

The example JNI bridge currently supports arm64. Gradle resolves RN tools
through Node so both hoisted and isolated workspace installs work.

For iOS, build the Zig XCFramework before installing pods. The Apple packaging
script repacks archives with `libtool` to satisfy Mach-O member alignment:

```sh
bun run zig:apple
bun run codegen
cd apps/example/ios
pod install
xcodebuild -workspace ZerolistExample.xcworkspace -scheme ZerolistExample \
  -configuration Release -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' ARCHS=arm64 \
  CODE_SIGNING_ALLOWED=NO build
```

Start the development server with `bun run example:start`. JavaScript changes
can reload in a development build; native changes require rebuilding the app.
For benchmarks, rebuild/install the release APK and validate the layout before
collecting measurements. Keep recording separate from performance runs.

### Commit message convention

We follow the [conventional commits specification](https://www.conventionalcommits.org/en) for our commit messages:

- `fix`: bug fixes, e.g. fix crash due to deprecated method.
- `feat`: new features, e.g. add new method to the module.
- `refactor`: code refactor, e.g. migrate from class components to hooks.
- `docs`: changes into documentation, e.g. add usage example for the module.
- `test`: adding or updating tests, e.g. add integration tests using detox.
- `chore`: tooling changes, e.g. change CI config.

Our pre-commit hooks verify that your commit message matches this format when committing.

### Publishing to npm

We use [release-it](https://github.com/release-it/release-it) to make it easier to publish new versions. It handles common tasks like bumping version based on semver, creating tags and releases etc.

To publish new versions, run the following:

```sh
bunx release-it
```

### Scripts

The `package.json` file contains various scripts for common tasks:

- `yarn`: setup project by installing dependencies.
- `yarn typecheck`: type-check files with TypeScript.
  - `yarn lint`: lint files with [ESLint](https://eslint.org/).
    - `yarn test`: run unit tests with [Jest](https://jestjs.io/).
  - `yarn example start`: start the Metro server for the example app.
- `yarn example android`: run the example app on Android.
- `yarn example ios`: run the example app on iOS.
  - `yarn example web`: run the example app on Web.
- `yarn example build:web`: build the example app for Web.

### Sending a pull request

> **Working on your first pull request?** You can learn how from this _free_ series: [How to Contribute to an Open Source Project on GitHub](https://app.egghead.io/playlists/how-to-contribute-to-an-open-source-project-on-github).

When you're sending a pull request:

- Prefer small pull requests focused on one change.
- Verify that linters and tests are passing.
- Review the documentation to make sure it looks good.
- Follow the pull request template when opening a pull request.
- For pull requests that change the API or implementation, discuss with maintainers first by opening an issue.
