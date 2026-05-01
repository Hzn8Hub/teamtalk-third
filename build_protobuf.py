#!/usr/bin/env python3
"""
编译并安装 protobuf 到 teamtalk/.sdk/protobuf/ 目录
支持 Windows(MinGW/MSYS2), Linux, macOS
统一使用 g++ 编译器和 make 构建系统

使用方法:
    python3 build_protobuf.py          # 正常构建
    python3 build_protobuf.py --clean  # 强制清理后重新构建
    python3 build_protobuf.py --help   # 显示帮助
"""

import os
import sys
import subprocess
import multiprocessing
import platform
import shutil
import argparse
from pathlib import Path


class ProtobufBuilder:
    """Protobuf 构建器 - 跨平台统一构建"""
    
    def __init__(self, force_clean=False):
        # 获取脚本所在目录 (teamtalk-third)
        self.script_dir = Path(__file__).resolve().parent
        
        # .sdk 目录在脚本所在目录的父目录下
        # 例如: teamtalk/teamtalk-third/ -> teamtalk/.sdk/
        self.install_dir = self.script_dir.parent / ".sdk" / "protobuf"
        
        # 设置源码目录
        self.protobuf_source_dir = self.script_dir / "protobuf-2.6.1"
        
        # 设置构建目录（统一在 build 目录下）
        self.build_dir = self.script_dir / "build" / "protobuf"
        
        # 获取CPU核心数
        self.cpu_count = multiprocessing.cpu_count()
        
        # 检测操作系统
        self.platform_name = platform.system()
        self.is_windows = self.platform_name == 'Windows'
        
        # 是否强制清理
        self.force_clean = force_clean
    
    def run_command(self, cmd, shell=False, description=None):
        """执行命令并处理错误"""
        if description:
            print(f"\n{description}")
        
        print(f"执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        
        result = subprocess.run(cmd, shell=shell)
        
        if result.returncode != 0:
            print(f"错误: 命令执行失败 (退出码: {result.returncode})")
            sys.exit(1)
        
        return result
    
    def check_tool(self, tool):
        """检查工具是否存在"""
        return shutil.which(tool) is not None
    
    def clean(self):
        """清理之前的编译结果"""
        print("\n" + "="*60)
        print("清理旧的编译结果")
        print("="*60)
        
        # 检查构建目录是否存在
        if self.build_dir.exists():
            print(f"删除构建目录: {self.build_dir}")
            try:
                shutil.rmtree(self.build_dir)
                print("✓ 清理完成")
            except Exception as e:
                print(f"清理时出错: {e}")
                print("请手动删除构建目录:")
                print(f"  rm -rf {self.build_dir}")
                sys.exit(1)
        else:
            print("未检测到之前的编译结果，跳过清理")
        
        # 同时清理源码目录中的旧文件（如果有的话）
        old_files_in_source = [
            self.protobuf_source_dir / "Makefile",
            self.protobuf_source_dir / "config.log",
            self.protobuf_source_dir / "config.status",
        ]
        
        old_files_exist = any(f.exists() for f in old_files_in_source)
        if old_files_exist:
            print("\n检测到源码目录中有旧的编译文件，正在清理...")
            os.chdir(self.protobuf_source_dir)
            try:
                result = subprocess.run(
                    ['make', 'distclean'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if result.returncode == 0:
                    print("✓ 源码目录清理完成")
            except Exception as e:
                print(f"源码目录清理警告: {e}")
                print("继续执行...")
    
    def check_environment(self):
        """检查编译环境"""
        print("\n" + "="*60)
        print("检查编译环境")
        print("="*60)
        print(f"操作系统: {self.platform_name}")
        print(f"Python版本: {sys.version.split()[0]}")
        print(f"CPU核心数: {self.cpu_count}")
        print(f"脚本目录: {self.script_dir}")
        print(f"源码目录: {self.protobuf_source_dir}")
        print(f"构建目录: {self.build_dir}")
        print(f"安装目录: {self.install_dir}")
        
        # 检查源码目录
        if not self.protobuf_source_dir.exists():
            print(f"\n错误: protobuf源码目录不存在: {self.protobuf_source_dir}")
            sys.exit(1)
        
        # 统一检查必要工具
        required_tools = {
            'make': 'GNU Make 构建工具',
            'g++': 'C++ 编译器',
            'gcc': 'C 编译器'
        }
        
        print("\n检查必要工具:")
        missing_tools = []
        
        for tool, desc in required_tools.items():
            if self.check_tool(tool):
                print(f"  ✓ {tool} - {desc}")
            else:
                print(f"  ✗ {tool} - {desc} (未找到)")
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"\n错误: 缺少必要工具: {', '.join(missing_tools)}")
            self.print_install_instructions()
            sys.exit(1)
        
        print("\n环境检查通过!")
    
    def print_install_instructions(self):
        """打印工具安装说明"""
        print("\n" + "="*60)
        print("工具安装说明")
        print("="*60)
        
        if self.is_windows:
            print("\nWindows 平台 - 请安装 MSYS2 (推荐):")
            print("  1. 下载并安装 MSYS2: https://www.msys2.org/")
            print("  2. 在 MSYS2 终端中运行:")
            print("     pacman -S base-devel mingw-w64-x86_64-toolchain")
            print("  3. 将以下路径添加到系统 PATH:")
            print("     C:\\msys64\\mingw64\\bin")
            print("     C:\\msys64\\usr\\bin")
            print("\n或者安装 MinGW-w64:")
            print("  下载: https://www.mingw-w64.org/downloads/")
        else:
            print("\nLinux 平台:")
            print("  Ubuntu/Debian:")
            print("    sudo apt-get update")
            print("    sudo apt-get install build-essential")
            print("\n  CentOS/RHEL:")
            print("    sudo yum groupinstall 'Development Tools'")
            print("\n  Fedora:")
            print("    sudo dnf groupinstall 'Development Tools'")
            print("\nmacOS 平台:")
            print("  安装 Xcode Command Line Tools:")
            print("    xcode-select --install")
    
    def configure(self):
        """配置 protobuf"""
        print("\n" + "="*60)
        print("配置 protobuf (使用外部构建目录)")
        print("="*60)
        
        # 创建安装目录
        self.install_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建安装目录: {self.install_dir}")
        
        # 创建构建目录
        self.build_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建构建目录: {self.build_dir}")
        
        # 进入构建目录
        os.chdir(self.build_dir)
        print(f"进入构建目录: {self.build_dir}")
        
        # 检查 configure 脚本
        configure_script = self.protobuf_source_dir / "configure"
        if not configure_script.exists():
            print("\nconfigure 脚本不存在，尝试生成...")
            autogen_script = self.protobuf_source_dir / "autogen.sh"
            if autogen_script.exists():
                # 需要在源码目录运行 autogen.sh
                os.chdir(self.protobuf_source_dir)
                self.run_command(['sh', str(autogen_script)], description="运行 autogen.sh")
                os.chdir(self.build_dir)
            else:
                print("错误: 未找到 configure 或 autogen.sh")
                sys.exit(1)
        
        # 运行 configure（从构建目录指向源码目录）
        configure_cmd = [
            'sh',
            str(configure_script),
            f'--prefix={self.install_dir}'
        ]
        self.run_command(configure_cmd, description="\n运行 configure (外部构建)")
        
        print("✓ 配置完成")
        print(f"  提示: 所有编译文件都将生成在 {self.build_dir}")
        print(f"  提示: 源码目录 {self.protobuf_source_dir} 保持干净")
    
    def build(self):
        """编译 protobuf"""
        print("\n" + "="*60)
        print("编译 protobuf")
        print("="*60)
        
        # 确保在构建目录
        os.chdir(self.build_dir)
        
        # 运行 make
        make_cmd = ['make', f'-j{self.cpu_count}']
        self.run_command(make_cmd, description=f"使用 {self.cpu_count} 个CPU核心并行编译")
        
        print("✓ 编译完成")
    
    def install(self):
        """安装 protobuf"""
        print("\n" + "="*60)
        print("安装 protobuf")
        print("="*60)
        
        # 确保在构建目录
        os.chdir(self.build_dir)
        
        # 运行 make install
        install_cmd = ['make', 'install']
        self.run_command(install_cmd, description="安装到目标目录")
        
        print("✓ 安装完成")
    
    def verify(self):
        """验证安装"""
        print("\n" + "="*60)
        print("验证安装")
        print("="*60)
        
        # protoc 可执行文件路径
        protoc_name = 'protoc.exe' if self.is_windows else 'protoc'
        protoc_path = self.install_dir / 'bin' / protoc_name
        
        if not protoc_path.exists():
            print(f"警告: protoc 可执行文件未找到: {protoc_path}")
            return False
        
        # 检查版本
        try:
            # Python 3.6 兼容
            result = subprocess.run(
                [str(protoc_path), '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✓ protoc 安装成功")
                print(f"  版本: {version}")
                print(f"  路径: {protoc_path}")
                return True
            else:
                print("警告: 无法获取 protoc 版本信息")
                return False
        except Exception as e:
            print(f"警告: 验证时出错: {e}")
            return False
    
    def print_summary(self):
        """打印安装摘要和使用说明"""
        print("\n" + "="*60)
        print("安装完成")
        print("="*60)
        
        bin_dir = self.install_dir / 'bin'
        lib_dir = self.install_dir / 'lib'
        include_dir = self.install_dir / 'include'
        
        print(f"\n安装位置:")
        print(f"  根目录: {self.install_dir}")
        print(f"  可执行文件: {bin_dir}")
        print(f"  库文件: {lib_dir}")
        print(f"  头文件: {include_dir}")
        
        print(f"\n使用说明:")
        print(f"要使用已安装的 protobuf，请设置以下环境变量:")
        
        if self.is_windows:
            print(f"\nWindows (PowerShell):")
            print(f"  $env:Path = \"{bin_dir};$env:Path\"")
            
            print(f"\nWindows (CMD):")
            print(f"  set PATH={bin_dir};%PATH%")
            
            print(f"\nWindows (MSYS2/MinGW Bash):")
            # 转换为Unix风格路径
            unix_bin = str(bin_dir).replace('\\', '/').replace('C:', '/c')
            unix_lib = str(lib_dir).replace('\\', '/').replace('C:', '/c')
            print(f"  export PATH={unix_bin}:$PATH")
            print(f"  export LD_LIBRARY_PATH={unix_lib}:$LD_LIBRARY_PATH")
        else:
            print(f"\nLinux/macOS (Bash/Zsh):")
            print(f"  export PATH={bin_dir}:$PATH")
            print(f"  export LD_LIBRARY_PATH={lib_dir}:$LD_LIBRARY_PATH")
            print(f"  export PKG_CONFIG_PATH={lib_dir / 'pkgconfig'}:$PKG_CONFIG_PATH")
        
        print("\n" + "="*60)
    
    def run(self):
        """执行完整的构建流程"""
        print("\n" + "="*60)
        print("protobuf 跨平台构建脚本")
        print("统一使用 g++ 编译器")
        print("="*60)
        
        try:
            # 1. 清理旧的编译结果
            self.clean()
            
            # 2. 检查环境
            self.check_environment()
            
            # 3. 配置
            self.configure()
            
            # 4. 编译
            self.build()
            
            # 5. 安装
            self.install()
            
            # 6. 验证
            self.verify()
            
            # 7. 打印摘要
            self.print_summary()
            
            print("\n✓ 全部完成!")
            return 0
            
        except KeyboardInterrupt:
            print("\n\n操作被用户中断")
            return 1
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='编译并安装 protobuf 到 teamtalk/.sdk/protobuf/ 目录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 build_protobuf.py          # 正常构建
  python3 build_protobuf.py --clean  # 强制清理后重新构建
        """
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='强制清理之前的编译结果后重新构建（推荐在遇到路径相关错误时使用）'
    )
    
    args = parser.parse_args()
    
    builder = ProtobufBuilder(force_clean=args.clean)
    sys.exit(builder.run())


if __name__ == "__main__":
    main()
