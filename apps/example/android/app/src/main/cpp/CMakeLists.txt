cmake_minimum_required(VERSION 3.22)
project(zlbridge)

# ZeroList JNI 브리지: Fabric 스크롤 핸들러(네이티브 스레드)가
# Zig 엔진을 직접 호출(프레임당 JS 0회). 라이브러리의 사전빌드
# Zig 정적 라이브러리 + C 헤더를 그대로 링크.

set(ZL "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../../packages/zerolist")

if(ANDROID_ABI STREQUAL "arm64-v8a")
  set(ZIG_DIR "android-arm64")
elseif(ANDROID_ABI STREQUAL "x86_64")
  set(ZIG_DIR "android-x86_64")
else()
  message(FATAL_ERROR "zlbridge: 미지원 ABI ${ANDROID_ABI}")
endif()

set(ZIG_LIB "${ZL}/zig/zig-out/${ZIG_DIR}/libzerolist_engine.a")
if(NOT EXISTS "${ZIG_LIB}")
  message(FATAL_ERROR "zlbridge: Zig 미빌드 — ${ZIG_LIB} (zig build 필요)")
endif()

add_library(zerolist_engine STATIC IMPORTED)
set_target_properties(zerolist_engine PROPERTIES IMPORTED_LOCATION "${ZIG_LIB}")

add_library(zlbridge SHARED zlbridge.cpp)
target_include_directories(zlbridge PRIVATE "${ZL}/cpp")
target_link_libraries(zlbridge zerolist_engine log)
