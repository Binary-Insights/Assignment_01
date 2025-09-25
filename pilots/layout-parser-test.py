import layoutparser as lp
import cv2

image = cv2.imread("data/page1.jpg")
image = image[..., ::-1]
    # Convert the image from BGR (cv2 default loading style)
    # to RGB

model = lp.Detectron2LayoutModel('lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
                                 extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                                 label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"})
    # Load the deep layout model from the layoutparser API
    # For all the supported model, please check the Model
    # Zoo Page: https://layout-parser.readthedocs.io/en/latest/notes/modelzoo.html

layout = model.detect(image)
    # Detect the layout of the input image

# Draw bounding boxes and get the result image
result_image = lp.draw_box(image, layout, box_width=3)
    # Draw the detected layout on the input image

# Save the result image
cv2.imwrite("data/layout_detection_result.jpg", result_image[..., ::-1])  # Convert RGB back to BGR for cv2
print(f"Layout detection result saved to: data/layout_detection_result.jpg")

# Option 1: Display using matplotlib (if available)
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 8))
    plt.imshow(result_image)
    plt.axis('off')
    plt.title('Layout Detection Results')
    plt.show()
    print("Image displayed using matplotlib")
except ImportError:
    print("Matplotlib not available - image saved to file only")

# Option 2: Display using PIL (alternative)
try:
    from PIL import Image
    pil_image = Image.fromarray(result_image)
    pil_image.show()  # This will open the default image viewer
    print("Image opened in default viewer")
except Exception as e:
    print(f"Could not open image viewer: {e}")

print(f"Layout type: {type(layout)}")
print(f"Number of detected blocks: {len(layout)}")

# Print details of each detected block
for i, block in enumerate(layout):
    print(f"Block {i}: Type={block.type}, Score={block.score:.3f}, BBox={block.block}")

