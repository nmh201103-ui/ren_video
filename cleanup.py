"""
Cleanup script để xóa các file không cần thiết và optimize codebase
"""
import os
import shutil

def cleanup():
    # 1. Remove temporary test files
    temp_files = [
        'tmp_test_gen.py',
        'tmp_run.py', 
        'test_compare_modes.py',
        'test_modes.py',
        'test_remove_bg.py'
    ]
    
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"✅ Deleted: {f}")
    
    # 2. Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(cache_path)
            print(f"✅ Deleted cache: {cache_path}")
    
    # 3. Clean temp assets
    temp_dir = 'assets/temp'
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            if f != '.gitkeep':
                os.remove(os.path.join(temp_dir, f))
        print(f"✅ Cleaned: {temp_dir}")
    
    # 4. Remove old logs (keep last 5)
    log_dir = 'logs'
    if os.path.exists(log_dir):
        logs = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
        if len(logs) > 5:
            for old_log in logs[:-5]:
                os.remove(os.path.join(log_dir, old_log))
                print(f"✅ Deleted old log: {old_log}")
    
    print("\n🎉 Cleanup complete!")

if __name__ == "__main__":
    cleanup()
