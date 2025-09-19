import os
import requests
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_sec_filing(cik: str, accession_number: str, output_dir: str) -> None:
    """
    Download SEC filing using direct EDGAR URLs.
    
    Args:
        cik: Company CIK number (without leading zeros)
        accession_number: SEC filing accession number
        output_dir: Directory to save the downloaded files
    """
    # Format CIK with leading zeros
    cik_padded = cik.zfill(10)
    
    # Create the base URL for the filing
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}"
    
    # Create directory structure
    filing_dir = os.path.join(output_dir, "sec-edgar-filings", cik, "10-K", accession_number)
    os.makedirs(filing_dir, exist_ok=True)
    
    # Headers to avoid SEC blocking
    headers = {
        'User-Agent': 'BinaryInsights contact@binaryinsights.dev',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    try:
        # Download the complete submission file
        submission_url = f"{base_url}/{accession_number}.txt"
        logger.info(f"Downloading submission from {submission_url}")
        
        response = requests.get(submission_url, headers=headers)
        response.raise_for_status()
        
        with open(os.path.join(filing_dir, "full-submission.txt"), "wb") as f:
            f.write(response.content)
        
        # Download the XBRL file if available
        try:
            xbrl_url = f"{base_url}/{accession_number}_htm.xml"
            logger.info(f"Attempting to download XBRL from {xbrl_url}")
            
            response = requests.get(xbrl_url, headers=headers)
            response.raise_for_status()
            
            with open(os.path.join(filing_dir, "filing.xbrl"), "wb") as f:
                f.write(response.content)
            
        except requests.RequestException as e:
            logger.warning(f"Could not download XBRL file: {str(e)}")
            
            # Try alternative XBRL file name
            try:
                xbrl_url = f"{base_url}/Financial_Report.xlsx"
                logger.info(f"Attempting to download alternative XBRL from {xbrl_url}")
                
                response = requests.get(xbrl_url, headers=headers)
                response.raise_for_status()
                
                with open(os.path.join(filing_dir, "filing.xbrl"), "wb") as f:
                    f.write(response.content)
                    
            except requests.RequestException as e:
                logger.error(f"Could not download alternative XBRL file: {str(e)}")
        
    except requests.RequestException as e:
        logger.error(f"Error downloading filing: {str(e)}")
        raise

def main():
    # Get absolute path to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(project_root, "data", "raw")
    
    # NVIDIA's CIK and latest 10-K accession number
    cik = "1045810"
    accession_number = "0001045810-24-000029"
    
    try:
        download_sec_filing(cik, accession_number, data_dir)
        logger.info("Successfully downloaded SEC filing")
    except Exception as e:
        logger.error(f"Failed to download SEC filing: {str(e)}")
        raise

if __name__ == "__main__":
    main()