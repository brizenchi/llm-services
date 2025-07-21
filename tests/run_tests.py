#!/usr/bin/env python3
"""
LLM Services 统一测试运行器

提供简单的测试命令接口
"""

import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    try:
        result = subprocess.run([
            sys.executable, "tests/unit_tests/simple_test.py"
        ], cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 单元测试运行失败: {e}")
        return False


def run_quick_api_test(message=None):
    """运行快速API测试"""
    print("⚡ 运行快速API测试...")
    try:
        cmd = [sys.executable, "tests/api_tests/quick_test.py"]
        if message:
            cmd.append(message)
        
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 快速API测试运行失败: {e}")
        return False


def run_full_api_test():
    """运行完整API测试"""
    print("🔬 运行完整API测试...")
    try:
        result = subprocess.run([
            sys.executable, "tests/api_tests/real_api_test.py"
        ], cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 完整API测试运行失败: {e}")
        return False


def run_stream_test():
    """运行流式接口测试"""
    print("🌊 运行流式接口测试...")
    try:
        result = subprocess.run([
            sys.executable, "tests/api_tests/stream_test.py"
        ], cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 流式接口测试运行失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("🚀 运行所有测试...")
    
    results = []
    
    # 1. 单元测试
    results.append(("单元测试", run_unit_tests()))
    
    # 2. 快速API测试
    results.append(("快速API测试", run_quick_api_test()))
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 部分测试失败")
    
    return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLM Services 测试运行器")
    parser.add_argument("command", choices=["unit", "quick", "full", "stream", "all"], 
                       help="测试类型")
    parser.add_argument("-m", "--message", help="自定义测试消息（仅用于quick测试）")
    
    args = parser.parse_args()
    
    if args.command == "unit":
        success = run_unit_tests()
    elif args.command == "quick":
        success = run_quick_api_test(args.message)
    elif args.command == "full":
        success = run_full_api_test()
    elif args.command == "stream":
        success = run_stream_test()
    elif args.command == "all":
        success = run_all_tests()
    else:
        print("❌ 未知的测试类型")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试运行器出错: {e}")
        sys.exit(1) 