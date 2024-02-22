import requests
from dotenv import load_dotenv
from datetime import datetime
import os

# Load environment variables from .env file
load_dotenv()

# Set your GitHub Personal Access Token
access_token = os.getenv("GITHUB_ACCESS_TOKEN")

# Set the repository owner and name
repo_owner = os.getenv("REPO_OWNER")
repo_name = os.getenv("REPO_NAME")


# Make a GET request to retrieve pull requests
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=closed"
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    pull_requests = response.json()

    approval_times_per_author = {}

    for pr in pull_requests:
        author = pr["user"]["login"]
        submission_time = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        if pr["merged_at"]:
            approval_time = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
            approval_duration = (approval_time - submission_time).total_seconds() / 3600

            if author not in approval_times_per_author:
                approval_times_per_author[author] = []

            approval_times_per_author[author].append(approval_duration)

    for author, approval_times in approval_times_per_author.items():
        average_approval_time = sum(approval_times) / len(approval_times)
        print(
            f"Author: {author}, Average Approval Time: {average_approval_time:.2f} hours"
        )

else:
    print(f"Failed to retrieve pull requests. Status code: {response.status_code}")
