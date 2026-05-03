#!/usr/bin/env python3
"""
将 amalgamation 版 sqlite3（sqlite3.c + sqlite3.h）编译为静态库并安装到 teamtalk/.sdk/sqlite3/。

安装布局（与其它 SDK 一致）:
    .sdk/sqlite3/include/sqlite3.h
    .sdk/sqlite3/lib/libsqlite3.a

静态库默认带 -fPIC，便于被链入其它共享库（.so）。

使用方法:
    python3 build_sqlite3.py build     # 仅编译（产物在 build/sqlite3/）
    python3 build_sqlite3.py install   # 编译并安装到 .sdk
    python3 build_sqlite3.py clean     # 删除 build/sqlite3/
    python3 build_sqlite3.py all       # clean + build + install（默认）

依赖: C 编译器（gcc/cc）、归档工具 ar（Windows 下建议 MSYS2/MinGW 自带的 gcc+ar）。
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


class Sqlite3Builder:
    def __init__(self):
        self.script_dir = Path(__file__).resolve().parent
        self.src_dir = self.script_dir / "sqlite3"
        self.build_dir = self.script_dir / "build" / "sqlite3"
        self.install_dir = self.script_dir.parent / ".sdk" / "sqlite3"
        self.platform_name = platform.system()
        self.is_windows = self.platform_name == "Windows"

    def run_command(self, cmd, description=None, cwd=None):
        if description:
            print(f"\n{description}")
        if cwd:
            print(f"工作目录: {cwd}")
        print(f"执行命令: {' '.join(cmd)}")
        r = subprocess.run(cmd, cwd=cwd)
        if r.returncode != 0:
            print(f"错误: 命令失败 (退出码 {r.returncode})")
            sys.exit(1)

    def _find_cc(self):
        for name in ("gcc", "cc", "clang"):
            p = shutil.which(name)
            if p:
                return p
        return None

    def check_environment(self):
        banner("检查编译环境")
        print(f"操作系统: {self.platform_name}")
        print(f"源码目录: {self.src_dir}")
        print(f"构建目录: {self.build_dir}")
        print(f"安装目录: {self.install_dir}")

        c_file = self.src_dir / "sqlite3.c"
        h_file = self.src_dir / "sqlite3.h"
        if not c_file.is_file():
            print(f"\n错误: 未找到 {c_file}")
            sys.exit(1)
        if not h_file.is_file():
            print(f"\n错误: 未找到 {h_file}")
            sys.exit(1)

        cc = self._find_cc()
        if not cc:
            print("\n错误: 未找到 C 编译器（gcc / cc / clang）")
            print("  Linux: sudo apt-get install build-essential")
            print("  Windows: 请使用 MSYS2 并安装 mingw-w64-x86_64-gcc")
            sys.exit(1)
        print(f"\n  ✓ C 编译器: {cc}")

        if not shutil.which("ar"):
            print("\n错误: 未找到 ar（制作 .a 需要）")
            print("  请安装 binutils / MSYS2 base-devel")
            sys.exit(1)
        print("  ✓ ar")

        print("\n✓ 环境检查通过!")

    def clean(self):
        banner("清理 build/sqlite3")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"已删除: {self.build_dir}")
        else:
            print("构建目录不存在，跳过")
        print("✓ 清理完成")

    def do_build(self):
        banner("编译 libsqlite3.a")

        self.build_dir.mkdir(parents=True, exist_ok=True)
        cc = self._find_cc()
        c_src = self.src_dir / "sqlite3.c"
        obj = self.build_dir / "sqlite3.o"
        lib = self.build_dir / "libsqlite3.a"

        compile_cmd = [
            cc,
            "-c",
            "-O2",
            "-fPIC",
            "-DSQLITE_THREADSAFE=1",
            "-DSQLITE_ENABLE_FTS5",
            "-DSQLITE_ENABLE_JSON1",
            str(c_src),
            "-o",
            str(obj),
        ]
        if not self.is_windows:
            # 与线程安全实现一致，最终程序链接时通常仍需 -pthread
            compile_cmd.insert(compile_cmd.index(str(c_src)), "-pthread")

        self.run_command(compile_cmd, description="编译 sqlite3.c -> sqlite3.o")

        self.run_command(
            ["ar", "rcs", str(lib), str(obj)],
            cwd=str(self.build_dir),
            description="打包静态库 libsqlite3.a",
        )

        ranlib = shutil.which("ranlib")
        if ranlib:
            self.run_command([ranlib, str(lib)], cwd=str(self.build_dir), description="ranlib（可选）")

        print("\n✓ 编译完成")

    def do_install(self):
        banner("安装到 .sdk/sqlite3")

        lib = self.build_dir / "libsqlite3.a"
        if not lib.is_file():
            print("未找到 libsqlite3.a，先执行编译…")
            self.do_build()

        inc_dst = self.install_dir / "include"
        lib_dst = self.install_dir / "lib"
        inc_dst.mkdir(parents=True, exist_ok=True)
        lib_dst.mkdir(parents=True, exist_ok=True)

        shutil.copy2(self.src_dir / "sqlite3.h", inc_dst / "sqlite3.h")
        shutil.copy2(lib, lib_dst / "libsqlite3.a")

        print(f"头文件: {inc_dst / 'sqlite3.h'}")
        print(f"静态库: {lib_dst / 'libsqlite3.a'}")
        print("\n✓ 安装完成")

        banner("其它工程中使用（示例）")
        sdk = self.install_dir
        print("CMake:")
        print(f'  target_include_directories(your_target PRIVATE "{sdk}/include")')
        print(f'  target_link_libraries(your_target PRIVATE "{sdk}/lib/libsqlite3.a")')
        print("Linux 链接可执行文件/共享库时通常还需: pthread dl m（按平台增减）")
        print('  例如: target_link_libraries(your_target PRIVATE pthread dl m)')


def main():
    parser = argparse.ArgumentParser(
        description="编译 sqlite3 amalgamation 并安装到 teamtalk/.sdk/sqlite3/"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["build", "install", "clean", "all"],
        help="build / install / clean / all（默认 all）",
    )
    args = parser.parse_args()

    try:
        b = Sqlite3Builder()
        if args.command != "clean":
            b.check_environment()

        if args.command == "clean":
            b.clean()
        elif args.command == "build":
            b.do_build()
            print("\n✓ 构建结束（未写入 .sdk，可执行 install）")
        elif args.command == "install":
            b.do_install()
            print("\n✓ 安装流程结束")
        else:
            banner("sqlite3 完整流程")
            b.clean()
            b.do_build()
            b.do_install()
            print("\n✓ 全部完成")

        return 0
    except KeyboardInterrupt:
        print("\n已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
