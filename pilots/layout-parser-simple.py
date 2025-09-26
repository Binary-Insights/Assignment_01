import layoutparser as lp
import cv2
import numpy as np

# Load image
image = cv2.imread("data/page1.jpg")
if image is None:
    print("Error: Could not load image from data/page1.jpg")
    print("Please make sure the image file exists")
    exit(1)

image = image[..., ::-1]  # Convert BGR to RGB

print("Image loaded successfully")
print(f"Image shape: {image.shape}")

# Initialize model
print("Loading LayoutParser model...")
model = lp.Detectron2LayoutModel(
    'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
)
print("Model loaded successfully!")

# Detect layout
print("Detecting layout...")
layout = model.detect(image)
print(f"Detected {len(layout)} blocks")

# Draw bounding boxes
print("Drawing bounding boxes...")
result_image = lp.draw_box(image, layout, box_width=3)

# Save result - handle both PIL Image and numpy array
output_path = "data/layout_detection_result.jpg"

try:
    if hasattr(result_image, 'save'):
        # It's a PIL Image
        result_image.save(output_path)
        print(f"✅ Layout detection result saved to: {output_path} (PIL Image)")
    else:
        # It's a numpy array
        cv2.imwrite(output_path, result_image[..., ::-1])  # Convert RGB back to BGR for saving
        print(f"✅ Layout detection result saved to: {output_path} (numpy array)")
except Exception as e:
    print(f"Error saving with first method: {e}")
    try:
        # Alternative: Convert PIL to numpy array and save
        result_array = np.array(result_image)
        cv2.imwrite(output_path, result_array[..., ::-1])  # Convert RGB to BGR
        print(f"✅ Layout detection result saved to: {output_path} (converted to array)")
    except Exception as e2:
        print(f"Error with fallback method: {e2}")
        # Final fallback: save as PNG with PIL
        try:
            result_image.save("data/layout_detection_result.png")
            print(f"✅ Layout detection result saved to: data/layout_detection_result.png (PNG format)")
        except Exception as e3:
            print(f"All save methods failed: {e3}")

# Print detected blocks information
print("\n=== Detected Blocks ===")
for i, block in enumerate(layout):
    block_type = model.label_map.get(block.type, f"Type_{block.type}")
    print(f"Block {i+1}: {block_type} (confidence: {block.score:.3f})")
    print(f"  Bounding box: ({block.block.x_1:.0f}, {block.block.y_1:.0f}) -> ({block.block.x_2:.0f}, {block.block.y_2:.0f})")
    print(f"  Size: {block.block.width:.0f} x {block.block.height:.0f}")
    print()

print(f"🎉 Layout detection completed successfully!")
print(f"📁 Check the output image: {output_path}")