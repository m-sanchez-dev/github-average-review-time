from dotenv import load_dotenv
import os
import requests
from datetime import datetime, time, timedelta


def calculate_working_hours(
    start_time, end_time, working_hours_start, working_hours_end
):
    start_of_working_hours = max(
        start_time, datetime.combine(start_time.date(), working_hours_start)
    )
    end_of_working_hours = min(
        end_time, datetime.combine(end_time.date(), working_hours_end)
    )
    return max(
        0, (end_of_working_hours - start_of_working_hours).total_seconds() / 3600
    )


def calculate_average_approval_times(
    pull_requests, working_hours_start, working_hours_end
):
    approval_times_per_author = {}

    for pr in pull_requests:
        author = pr["user"]["login"]
        submission_time = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        if not pr["merged_at"]:
            continue  # Skip if the pull request has not been merged

        approval_time = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")

        # Initialize adjusted approval duration
        approval_duration = 0

        # Iterate through days between submission and approval
        current_day = submission_time.date()
        while current_day <= approval_time.date():
            # Determine the relevant working hours for the current day
            current_start_time = max(
                submission_time, datetime.combine(current_day, working_hours_start)
            )
            current_end_time = min(
                approval_time, datetime.combine(current_day, working_hours_end)
            )

            # Calculate the time spent within working hours for the current day
            current_duration = calculate_working_hours(
                current_start_time,
                current_end_time,
                working_hours_start,
                working_hours_end,
            )

            # Add the time spent on the current day to the total approval duration
            approval_duration += current_duration

            # Move to the next day
            current_day += timedelta(days=1)

        if author not in approval_times_per_author:
            approval_times_per_author[author] = []

        approval_times_per_author[author].append(approval_duration)

    return approval_times_per_author


# Load environment variables from .env file
load_dotenv()

access_token = os.environ.get("GITHUB_ACCESS_TOKEN")
repo_owner = os.environ.get("GITHUB_REPO_OWNER")
repo_name = os.environ.get("GITHUB_REPO_NAME")
working_hours_start = time(int(os.environ.get("WORKING_HOURS_START", 7)), 0)
working_hours_end = time(int(os.environ.get("WORKING_HOURS_END", 20)), 0)

if not access_token or not repo_owner or not repo_name:
    print(
        "Please set GITHUB_ACCESS_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME environment variables."
    )
    exit()

# Make a GET request to retrieve pull requests
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=closed"
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    pull_requests = response.json()
    approval_times_per_author = calculate_average_approval_times(
        pull_requests, working_hours_start, working_hours_end
    )

    for author, approval_times in approval_times_per_author.items():
        average_approval_time = sum(approval_times) / len(approval_times)
        print(
            f"Author: {author}, Average Approval Time: {average_approval_time:.2f} hours"
        )

else:
    print(f"Failed to retrieve pull requests. Status code: {response.status_code}")
