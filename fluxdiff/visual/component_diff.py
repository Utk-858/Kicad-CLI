import cv2
import numpy as np
import re

def generate_component_visual_diff(before_png, after_png, before_components, after_components, output_path):
    """
    Generates a visual diff image showing added, removed, and moved components.

    Args:
        before_png (str): Path to 'before' board image (PNG).
        after_png (str): Path to 'after' board image (PNG) - base image for drawing.
        before_components (list): List of Component objects before change.
        after_components (list): List of Component objects after change.
        output_path (str): Path to write the output image.
    """
    # Load the after image (visualizes current state)
    image = cv2.imread(after_png)
    if image is None:
        raise FileNotFoundError(f"Could not load image at {after_png}")

    img_height, img_width = image.shape[:2]

    # Filter out placeholder references (e.g., 'REF**')
    ref_pattern = re.compile(r"REF\*\*")
    def is_valid_ref(ref):
        return not ref_pattern.fullmatch(ref)

    before_dict = {comp.ref: comp for comp in before_components if hasattr(comp, 'ref') and is_valid_ref(comp.ref)}
    after_dict  = {comp.ref: comp for comp in after_components  if hasattr(comp, 'ref') and is_valid_ref(comp.ref)}

    # Board size estimation from the union of both sets of components
    all_x = []
    all_y = []
    for comp in list(before_dict.values()) + list(after_dict.values()):
        if hasattr(comp, 'x') and hasattr(comp, 'y'):
            all_x.append(comp.x)
            all_y.append(comp.y)
    # Fallback if nothing found
    if not all_x or not all_y:
        raise ValueError("No component positions found for scaling.")

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    board_width  = max_x - min_x if max_x != min_x else 1
    board_height = max_y - min_y if max_y != min_y else 1

    scale_x = img_width / board_width
    scale_y = img_height / board_height

    # Drawing parameters
    box_w, box_h = 60, 30  # pixels

    # Track drawn refs to avoid duplicate labeling
    drawn_refs = set()

    # 1. Draw ADDED components (green)
    for ref, after_comp in after_dict.items():
        if ref not in before_dict:
            px = int(round((after_comp.x - min_x) * scale_x))
            py = int(round((after_comp.y - min_y) * scale_y))
            top_left     = (px - box_w // 2, py - box_h // 2)
            bottom_right = (px + box_w // 2, py + box_h // 2)
            cv2.rectangle(image, top_left, bottom_right, color=(0, 255, 0), thickness=3)
            label = f"ADDED: {ref}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_pos = (top_left[0], top_left[1] - 10)
            cv2.putText(image, label, text_pos, font, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            drawn_refs.add(ref)

    # 2. Draw REMOVED components (red)
    for ref, before_comp in before_dict.items():
        if ref not in after_dict:
            px = int(round((before_comp.x - min_x) * scale_x))
            py = int(round((before_comp.y - min_y) * scale_y))
            top_left     = (px - box_w // 2, py - box_h // 2)
            bottom_right = (px + box_w // 2, py + box_h // 2)
            cv2.rectangle(image, top_left, bottom_right, color=(0, 0, 255), thickness=3)
            label = f"REMOVED: {ref}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_pos = (top_left[0], top_left[1] - 10)
            cv2.putText(image, label, text_pos, font, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            drawn_refs.add(ref)

    # 3. Draw MOVED components (yellow)
    for ref in set(before_dict.keys()) & set(after_dict.keys()):
        before_comp = before_dict[ref]
        after_comp = after_dict[ref]
        # Compute Euclidean distance in board units
        dist = ((after_comp.x - before_comp.x) ** 2 + (after_comp.y - before_comp.y) ** 2) ** 0.5
        if dist > 0.1:
            px = int(round((after_comp.x - min_x) * scale_x))
            py = int(round((after_comp.y - min_y) * scale_y))
            top_left     = (px - box_w // 2, py - box_h // 2)
            bottom_right = (px + box_w // 2, py + box_h // 2)
            cv2.rectangle(image, top_left, bottom_right, color=(0, 255, 255), thickness=3)
            label = f"MOVED: {ref}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_pos = (top_left[0], top_left[1] - 10)
            cv2.putText(image, label, text_pos, font, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
            drawn_refs.add(ref)

    cv2.imwrite(output_path, image)