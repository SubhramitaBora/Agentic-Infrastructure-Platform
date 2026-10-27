import os

from dotenv import load_dotenv


load_dotenv()


JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
ATLASSIAN_API_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "AD")

# Confluence Cloud uses the same Atlassian email/API token pair as Jira, when
# the account has Confluence product access and page/space permissions.
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", JIRA_BASE_URL)
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", JIRA_EMAIL)


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "SubhramitaBora")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Agentic-Workflow")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hydra").strip().casefold()

HYDRA_LITELLM_BASE_URL = os.getenv("HYDRA_LITELLM_BASE_URL")
HYDRA_API_KEY = os.getenv("HYDRA_API_KEY")
HYDRA_MODEL = os.getenv("HYDRA_MODEL")
HYDRA_TIMEOUT = int(os.getenv("HYDRA_TIMEOUT", "120"))
