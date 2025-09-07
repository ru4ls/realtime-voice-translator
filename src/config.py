# src/config.py

import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account

# --- LOADING LOGIC ---

# 1. Load environment variables from the .env file located at the project root.
#    load_dotenv() automatically finds the .env file in parent directories.
load_dotenv()

# 2. Load and process Google Cloud credentials from the environment.
gcp_credentials_json_str = os.getenv("GCP_CREDENTIALS_JSON")
if not gcp_credentials_json_str:
    raise ValueError("Error: 'GCP_CREDENTIALS_JSON' env var not found. Ensure the .env file exists and is correctly populated.")

gcp_credentials_dict = json.loads(gcp_credentials_json_str)
CREDENTIALS = service_account.Credentials.from_service_account_info(gcp_credentials_dict)
PROJECT_ID = CREDENTIALS.project_id

# 3. Create robust paths to the configuration files.
_current_dir = os.path.dirname(os.path.abspath(__file__))  # -> /path/to/project/src
_root_dir = os.path.dirname(_current_dir)                  # -> /path/to/project

def _get_config_path(file_name: str) -> str:
    """Constructs an absolute path to a file in the 'configs' directory."""
    return os.path.join(_root_dir, 'configs', file_name)

# 4. Helper function to load JSON configuration files.
def _load_json_config(file_path: str):
    """Reads and parses a JSON configuration file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Configuration file not found at path: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")

# --- LOADED CONFIGURATION DATA ---

# 5. Load language lists.
SUPPORTED_LANGUAGES = _load_json_config(_get_config_path('target_languages.json'))


# 6. Other static settings.
#    SAMPLE_RATE is no longer needed here as it's determined dynamically in services.py,
#    but we can keep it for reference or other potential uses.
SAMPLE_RATE = 16000