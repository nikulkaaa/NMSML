import os
import ssl
import urllib3
import requests
from unittest.mock import patch

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom session that ignores SSL
class NoSSLSession(requests.Session):
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Override request to disable SSL verification.
        
        :param method: HTTP method
        :param url: URL to request
        :param kwargs: Additional arguments
        :return: HTTP response
        """
        kwargs['verify'] = False
        return super().request(method, url, **kwargs)

# Monkey patch requests to use our custom session
original_session = requests.Session

def patched_session() -> requests.Session:
    """
    Return a session that ignores SSL verification.

    :return: requests.Session with SSL verification disabled
    """
    return NoSSLSession()

# Apply the patch
requests.Session = patched_session

# Also patch the ssl context
ssl._create_default_https_context = ssl._create_unverified_context

print("Loading dataset with SSL verification disabled...")

try:
    from datasets import load_dataset
    # To avoid rate limits, you can use a Hugging Face token:
    # ds = load_dataset("ArlingtonCL2/DogSpeak_Dataset", use_auth_token="your_hf_token_here")
    ds = load_dataset("ArlingtonCL2/DogSpeak_Dataset")
    print("Dataset loaded successfully!")
    print(f"Dataset info: {ds}")
except Exception as e:
    print(f"Failed to load dataset: {e}")
    print("\nAlternative solution: Manual download")
    print("You can manually download the dataset from:")
    print("https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset")
    print("Or try using git clone with:")
    print("git clone https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset")
