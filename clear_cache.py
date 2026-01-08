"""
清除所有Python和Numba缓存的脚本
"""
import os
import shutil
import glob

def clear_cache():
    """清除所有缓存文件"""
    print("=" * 60)
    print("清除缓存")
    print("=" * 60)
    
    # 1. 清除__pycache__目录
    print("\n1. 清除__pycache__目录...")
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            pycache_dirs.append(pycache_path)
            try:
                shutil.rmtree(pycache_path)
                print(f"  ✓ 已清除: {pycache_path}")
            except Exception as e:
                print(f"  ✗ 清除失败: {pycache_path} - {e}")
    
    if not pycache_dirs:
        print("  没有找到__pycache__目录")
    
    # 2. 清除.pyc文件
    print("\n2. 清除.pyc文件...")
    pyc_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                pyc_files.append(pyc_path)
                try:
                    os.remove(pyc_path)
                    print(f"  ✓ 已清除: {pyc_path}")
                except Exception as e:
                    print(f"  ✗ 清除失败: {pyc_path} - {e}")
    
    if not pyc_files:
        print("  没有找到.pyc文件")
    
    # 3. 清除Numba缓存
    print("\n3. 清除Numba缓存...")
    try:
        import numba
        cache_dir = numba.config.CACHE_DIR
        if cache_dir and os.path.exists(cache_dir):
            cache_items = os.listdir(cache_dir)
            for item in cache_items:
                item_path = os.path.join(cache_dir, item)
                if os.path.isdir(item_path):
                    try:
                        shutil.rmtree(item_path)
                        print(f"  ✓ 已清除Numba缓存: {item}")
                    except Exception as e:
                        print(f"  ✗ 清除失败: {item} - {e}")
        else:
            print(f"  Numba缓存目录不存在: {cache_dir}")
    except ImportError:
        print("  Numba未安装，跳过Numba缓存清除")
    except Exception as e:
        print(f"  清除Numba缓存时出错: {e}")
    
    # 4. 清除其他缓存目录
    print("\n4. 清除其他缓存目录...")
    other_cache_dirs = ['.pytest_cache', '.mypy_cache', '.ruff_cache']
    for cache_dir in other_cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✓ 已清除: {cache_dir}")
            except Exception as e:
                print(f"  ✗ 清除失败: {cache_dir} - {e}")
    
    print("\n" + "=" * 60)
    print("缓存清除完成！")
    print("=" * 60)

if __name__ == '__main__':
    clear_cache()









