from sec_edgar_downloader import Downloader
import os

# Get absolute path to Assignment_01/data/raw
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
download_dir = os.path.join(project_root, "data", "raw")

# Ensure the directory exists
os.makedirs(download_dir, exist_ok=True)

print(f"Download directory: {download_dir}")

# Change working directory to data/raw before downloading
original_cwd = os.getcwd()
os.chdir(download_dir)

try:
    # Initialize downloader (it will create files in current working directory)
    dl = Downloader("BinaryInsights", "copilot@binaryinsights.dev")
    # Download the latest 10-K filing for NVIDIA (CIK: 0001045810)
    dl.get("10-K", "0001045810", amount=1)
finally:
    # Change back to original directory
    os.chdir(original_cwd)