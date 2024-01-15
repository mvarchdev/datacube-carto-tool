import os
import shutil
from joblib import hash

def clear_cache(memory, func, *args, **kwargs):
    """
    Clears the cache for a specific function call with given arguments.

    This function creates a unique identifier for a cached function call
    using its arguments and then deletes the corresponding cache directory
    if it exists.

    :param memory: A joblib Memory object used for caching.
    :type memory: joblib.Memory
    :param func: The function whose cache needs to be cleared.
    :type func: function
    :param args: Positional arguments passed to the function.
    :param kwargs: Keyword arguments passed to the function.
    """
    # Create a unique hash for the given function and arguments
    func_id = memory.func_id(func)
    args_id = hash((args, kwargs))
    cache_path = os.path.join(memory.cache_dir, func_id, args_id)

    # Check and remove the cache directory if it exists
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
