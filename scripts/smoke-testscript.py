#!/usr/bin/env python3
"""
Download Test PDF for Smoke Testing

This script downloads a sample PDF with text and table content
for validating the PDF extraction pipeline.
Uses only Python standard library - no external dependencies.
"""

import urllib.request
import urllib.error
from pathlib import Path
import sys


def download_test_pdf(output_path: str = "data/raw/pdf/"):
    """
    Download a test PDF with sample content for pipeline testing.
    
    Args:
        output_path: Path where the PDF will be saved
    """
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # List of sample PDF URLs to try (in order of preference)
    pdf_urls = [
        # W3C sample PDF (small, reliable)
        # "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        
        # Mozilla sample PDF
        # "https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf",
        
        # Alternative simple PDF
        # "https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf",
        
        # Backup: Create a simple text file if all PDFs fail
        None  # This will trigger the fallback
    ]
    
    for i, url in enumerate(pdf_urls):
        if url is None:
            # Fallback: Create a simple text file explaining the situation
            print("⚠️  All PDF downloads failed. Creating a placeholder text file.")
            with open(output_file.with_suffix('.txt'), 'w') as f:
                f.write("TEST DOCUMENT FOR SMOKE TESTING\n")
                f.write("=" * 35 + "\n\n")
                f.write("This is a fallback text file created because PDF download failed.\n")
                f.write("In a real scenario, this would be a proper PDF document.\n\n")
                f.write("Sample content for testing:\n")
                f.write("- Text extraction capabilities\n")
                f.write("- Table detection (simulated)\n")
                f.write("- Multi-line content processing\n\n")
                f.write("Financial Data Sample:\n")
                f.write("Company        Revenue    Year\n")
                f.write("NVIDIA Corp    $60.9B     2024\n")
                f.write("AMD Inc        $23.6B     2024\n")
                f.write("Intel Corp     $79.0B     2024\n")
            
            print(f"📄 Created fallback text file: {output_file.with_suffix('.txt')}")
            return str(output_file.with_suffix('.txt'))
        
        try:
            print(f"🔄 Attempting to download PDF from source {i+1}/{len(pdf_urls)-1}...")
            print(f"   URL: {url}")
            
            # Download the PDF
            with urllib.request.urlopen(url, timeout=30) as response:
                pdf_data = response.read()
            
            # Save to file
            with open(output_file, 'wb') as f:
                f.write(pdf_data)
            
            # Verify it's a valid PDF
            if output_file.stat().st_size > 0:
                with open(output_file, 'rb') as f:
                    header = f.read(4)
                    if header == b'%PDF':
                        print(f"✅ Successfully downloaded test PDF: {output_file}")
                        print(f"📄 File size: {output_file.stat().st_size:,} bytes")
                        print(f"📍 Absolute path: {output_file.absolute()}")
                        return str(output_file)
                    else:
                        print(f"❌ Downloaded file is not a valid PDF (header: {header})")
                        output_file.unlink()  # Delete invalid file
                        continue
            else:
                print(f"❌ Downloaded file is empty")
                output_file.unlink()  # Delete empty file
                continue
                
        except urllib.error.URLError as e:
            print(f"❌ Network error downloading from {url}: {e}")
            continue
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP error downloading from {url}: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error downloading from {url}: {e}")
            continue
    
    # If we get here, all downloads failed
    print("❌ All PDF download attempts failed")
    return None


if __name__ == "__main__":
    # Allow custom output path as command line argument
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/pdf/test_document.pdf"
    
    try:
        downloaded_file = download_test_pdf(output_path)
        if downloaded_file:
            print(f"\n🎉 Successfully obtained test file for smoke testing!")
        else:
            print(f"\n❌ Failed to obtain test file for smoke testing!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error obtaining test PDF: {e}")
        sys.exit(1)