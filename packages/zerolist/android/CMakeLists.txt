cmake_minimum_required(VERSION 3.4.1)
project(Zerolist)

set (CMAKE_VERBOSE_MAKEFILE ON)

add_library(
    react-native-zerolist    STATIC
    ../cpp/ZerolistImpl.cpp
)

set_target_properties(
    react-native-zerolist PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

target_include_directories(
    react-native-zerolist    PUBLIC
    ../cpp
)

# Zig 엔진 (zero-copy SIMD) — ABI 별 정적 라이브러리 선택
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(ZIG_ENGINE_DIR "android-arm64")
elseif(ANDROID_ABI STREQUAL "x86_64")
    set(ZIG_ENGINE_DIR "android-x86_64")
else()
    message(FATAL_ERROR "ZeroList: 지원하지 않는 ANDROID_ABI=${ANDROID_ABI} (arm64-v8a/x86_64만 지원)")
endif()

set(ZIG_ENGINE_LIB
    "${CMAKE_CURRENT_SOURCE_DIR}/../zig/zig-out/${ZIG_ENGINE_DIR}/libzerolist_engine.a")
if(NOT EXISTS "${ZIG_ENGINE_LIB}")
    message(FATAL_ERROR "ZeroList: Zig 엔진 미빌드 — zig/build.zig 실행 필요: ${ZIG_ENGINE_LIB}")
endif()

add_library(zerolist_engine STATIC IMPORTED)
set_target_properties(zerolist_engine PROPERTIES
    IMPORTED_LOCATION "${ZIG_ENGINE_LIB}")

target_link_libraries(
    react-native-zerolist    jsi
    reactnative
    react_codegen_ZerolistSpec
    zerolist_engine
    log
)
