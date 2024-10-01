import datetime

def track_time(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        
        elapsed_time = end_time - start_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        milliseconds = int((elapsed_seconds - int(elapsed_seconds)) * 1000)
        
        formatted_time = f"{minutes:02}:{seconds:02}.{milliseconds:03}"
        print(f"DEBUG> Time taken by '{func.__name__}': {formatted_time}")
        
        return result
    return wrapper