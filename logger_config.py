import time

def custom_print(msg, seconds=0):  # Renamed to avoid conflict with built-in print
    try:
        if seconds == 0:
            print(msg)  # Use the built-in print to display the message immediately
        else:
            for i in range(seconds, 0, -1):
                print(f"{msg} : {i}")
                time.sleep(1)  # Use 1 second intervals between messages
    except Exception as e:
        print(f"Error: {e}")

def info(msg, seconds=0):
    custom_print(f"\033[1;32m-{msg}\033[0m", seconds)  # Green

def warning(msg, seconds=0):
    custom_print(f"\033[1;93m-{msg}\033[0m", seconds)  # Bright Yellow (closest to orange)

def success(msg, seconds=0):
    custom_print(f"\033[1;34m-{msg}\033[0m", seconds)  # Blue

def error(msg, seconds=0):
    custom_print(f"\033[1;31m-{msg}\033[0m", seconds)  # Red

# Usage example
# if __name__ == "__main__":
#     info("Information message", 5)
#     warning("Warning message", 5)
#     success("Success message", 5)
#     error("Error message", 5)