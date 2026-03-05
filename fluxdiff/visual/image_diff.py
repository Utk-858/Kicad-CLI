import cv2
import numpy as np

def generate_visual_diff(before_image, after_image, output_path):
    """
    Generate a visual diff overlay between two images.

    Args:
        before_image (str): Path to the 'before' image.
        after_image (str): Path to the 'after' image.
        output_path (str): Path to save the diff overlay PNG.
    """
    # Load images
    before = cv2.imread(before_image)
    after = cv2.imread(after_image)

    if before is None or after is None:
        raise FileNotFoundError("One of the input images could not be loaded.")

    # Resize images to equal size if needed
    if before.shape != after.shape:
        h = min(before.shape[0], after.shape[0])
        w = min(before.shape[1], after.shape[1])
        before = cv2.resize(before, (w, h))
        after = cv2.resize(after, (w, h))

    # Convert to grayscale
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    # Compute absolute difference
    diff = cv2.absdiff(before_gray, after_gray)

    # Threshold to detect differences
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    # Mask for areas in before (removed = red)
    removed_mask = cv2.bitwise_and(thresh, cv2.compare(before_gray, after_gray, cv2.CMP_GT))
    # Mask for areas in after (added = green)
    added_mask = cv2.bitwise_and(thresh, cv2.compare(after_gray, before_gray, cv2.CMP_GT))

    # Create colored overlay: copy original after image to overlay
    overlay = after.copy()

    # Red for removed (areas present in before, not in after)
    overlay[removed_mask > 0] = [0, 0, 255]
    # Green for added (areas present in after, not in before)
    overlay[added_mask > 0] = [0, 255, 0]

    # Also blend with the original for context (optional, 70% original, 30% diff)
    blended = cv2.addWeighted(after, 0.7, overlay, 0.3, 0)

    # Save overlay
    cv2.imwrite(output_path, blended)
