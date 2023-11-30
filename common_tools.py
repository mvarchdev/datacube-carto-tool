import os
import shutil
from joblib import hash

def clear_cache(memory, func, *args, **kwargs):
    # Create a hash for the given function and arguments
    func_id = memory.func_id(func)
    args_id = hash((args, kwargs))
    cache_path = os.path.join(memory.cache_dir, func_id, args_id)

    # Remove the cache directory if it exists
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)