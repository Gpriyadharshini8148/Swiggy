from concurrent.futures import ThreadPoolExecutor

# Create a global thread pool executor
executor = ThreadPoolExecutor(max_workers=5)
# This will be used for sending emails and SMS asynchronously without creating new threads each time
