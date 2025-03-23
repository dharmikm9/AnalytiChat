import os

# Function to check if a response ends with a local image path
def extract_image_path(response):
    """Checks if a response ends with a local image path and returns it."""
    image_extensions = [".png", ".jpg", ".jpeg", ".gif"]
    for ext in image_extensions:
        if response.lower().endswith(ext): # case insensitive check.
            if os.path.exists(response):
                return response
    return None