import cv2
import numpy as np

def highlight_component_changes(image_path, components_before, components_after, output_path):
    """
    Draws red rectangles around components that have moved (by more than 0.1) between 
    components_before and components_after, based on the output image at image_path.
    Annotates each box with the reference (ref) of the component.

    Args:
        image_path (str): Path to the board image (PNG).
        components_before (list): List of Component objects (from PCBData) before change.
        components_after (list): List of Component objects (from PCBData) after change.
        output_path (str): Path to write the output image.
    """
    # Load the board image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image at {image_path}")

    # Build dictionaries of components by ref
    before_dict = {comp.ref: comp for comp in components_before if hasattr(comp, 'ref')}
    after_dict = {comp.ref: comp for comp in components_after if hasattr(comp, 'ref')}

    for ref, after_comp in after_dict.items():
        before_comp = before_dict.get(ref)
        if before_comp is not None:
            # Compare coordinates
            old_x, old_y = before_comp.x, before_comp.y
            new_x, new_y = after_comp.x, after_comp.y
            dist = ((new_x - old_x)**2 + (new_y - old_y)**2) ** 0.5
            if dist > 0.1:
                # Draw a red rectangle around the new component position

                # Define rectangle region (assuming (x,y) are in image coordinates)
                # If they are in mm or similar, image scaling may be needed.
                # We'll use a fixed box size for the highlight.
                box_w, box_h = 40, 20  # pixels, arbitrary but visible
                px = int(round(new_x))
                py = int(round(new_y))
                top_left = (px - box_w//2, py - box_h//2)
                bottom_right = (px + box_w//2, py + box_h//2)

                # Draw rectangle
                cv2.rectangle(image, top_left, bottom_right, color=(0,0,255), thickness=2)

                # Put reference text above the rectangle
                font = cv2.FONT_HERSHEY_SIMPLEX
                text_pos = (top_left[0], top_left[1] - 8)
                cv2.putText(image, ref, text_pos, font, 0.7, (0,0,255), 2, cv2.LINE_AA)

    # Save output image
    cv2.imwrite(output_path, image)