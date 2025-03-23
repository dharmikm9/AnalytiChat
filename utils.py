import os


def extract_image_path(response):
    """Checks if the response contains a valid path ending with a .png image file, and returns the path."""

    # Ensure response is a string.
    if not isinstance(response, str):
        return None

    # List of image extensions to check.
    image_extensions = [".png"]

    # Iterate through the image extensions.
    for ext in image_extensions:
        # Check if the response ends with the image extension (case insensitive).
        if response.lower().endswith(ext.lower()):
            # Check if the path exists and is a valid file.
            if os.path.exists(response):
                return response

    # Return None if no valid image path found.
    return None