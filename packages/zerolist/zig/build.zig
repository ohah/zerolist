//! ZeroList 엔진 빌드 스크립트 (Zig 0.16)
//!
//! iOS(기기/시뮬레이터) + Android(arm64/x86_64) 정적 라이브러리를
//! 한 번에 빌드한다. Windows 는 고려하지 않는다.
//!
//! 산출물: zig-out/<triple>/libzerolist_engine.a

const std = @import("std");

const Build = struct {
    name: []const u8,
    query: std.Target.Query,
};

const matrix = [_]Build{
    // iOS 실기기 (arm64)
    .{ .name = "ios-arm64", .query = .{ .cpu_arch = .aarch64, .os_tag = .ios } },
    // iOS 시뮬레이터 (Apple Silicon = arm64)
    .{ .name = "ios-arm64-simulator", .query = .{ .cpu_arch = .aarch64, .os_tag = .ios, .abi = .simulator } },
    // Android arm64 (실기기 대부분)
    .{ .name = "android-arm64", .query = .{ .cpu_arch = .aarch64, .os_tag = .linux, .abi = .android } },
    // Android x86_64 (에뮬레이터)
    .{ .name = "android-x86_64", .query = .{ .cpu_arch = .x86_64, .os_tag = .linux, .abi = .android } },
};

pub fn build(b: *std.Build) void {
    // PoC 는 성능 검증이 목적이므로 기본 ReleaseFast
    const optimize = b.standardOptimizeOption(.{ .preferred_optimize_mode = .ReleaseFast });

    for (matrix) |m| {
        const resolved = b.resolveTargetQuery(m.query);

        const mod = b.createModule(.{
            .root_source_file = b.path("engine.zig"),
            .target = resolved,
            .optimize = optimize,
            .strip = true,
            // RN 의 공유 라이브러리(.so/.dylib)에 링크되므로
            // 위치 독립 코드(PIC) 필수.
            .pic = true,
        });

        const lib = b.addLibrary(.{
            .name = "zerolist_engine",
            .linkage = .static,
            .root_module = mod,
        });

        const install = b.addInstallArtifact(lib, .{
            .dest_dir = .{ .override = .{ .custom = m.name } },
        });
        b.getInstallStep().dependOn(&install.step);
    }
}
