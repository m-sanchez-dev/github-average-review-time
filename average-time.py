from dotenv import load_dotenv
import os
import requests
from datetime import datetime, time, timedelta


# Load environment variables from .env file
load_dotenv()

working_hours_start = time(int(os.environ.get("WORKING_HOURS_START", 7)), 0)
working_hours_end = time(int(os.environ.get("WORKING_HOURS_END", 20)), 0)


def check_env_variables():
    access_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")

    if not access_token or not repo_owner or not repo_name:
        print(
            "Please set GITHUB_ACCESS_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME environment variables."
        )
        exit()


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


def get_approval_time_for_pr(pr_number):
    access_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if not response.status_code == 200:
        return None

    timeline_data = response.json()

    for event in timeline_data:
        if event["state"] == "APPROVED":
            return datetime.strptime(event["submitted_at"], "%Y-%m-%dT%H:%M:%SZ")


def filter_pull_requests_by_date(pull_requests):
    filtered_pull_requests = []
    latest_date = datetime.strptime(
        os.environ.get("LATEST_DATE", "2022-12-31"), "%Y-%m-%d"
    )

    for pr in pull_requests:

        created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if created_at >= latest_date:
            filtered_pull_requests.append(pr)

    return filtered_pull_requests, len(pull_requests) > len(filtered_pull_requests)


def get_all_pull_requests():
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")
    access_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    print("Retrieving pull requests...")
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    params = {
        "state": "closed",
        "per_page": 100,  # Adjust as needed
        "page": 1,  # Start from the first page
        "sort": "created",
        "direction": "desc",  # Sort in descending order (newest first)
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    all_pull_requests = []

    while True:
        response = requests.get(url, params=params, headers=headers)

        if not response.status_code == 200:
            print(
                f"Failed to retrieve pull requests. Status code: {response.status_code}"
            )
            break

        pull_requests = response.json()
        if not pull_requests:
            break

        filtered_pull_requests, removed_old_pull_requests = (
            filter_pull_requests_by_date(pull_requests)
        )

        all_pull_requests.extend(filtered_pull_requests)
        print(f"{len(all_pull_requests)} PRs retrieved", end="\r", flush=True)

        if removed_old_pull_requests:
            break

        # Move to the next page
        params["page"] += 1

    print(f"Retrieved {len(all_pull_requests)} pull requests")
    return all_pull_requests


check_env_variables()


# Accumulate approval times across all pages
total_approval_times = {}

pull_requests = get_all_pull_requests()
analyzed_prs = 0

for pr in pull_requests:
    created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")

    author = pr["user"]["login"]

    if not pr["merged_at"]:
        continue  # Skip if the pull request has not been merged

    pr_number = pr["number"]
    approval_time = get_approval_time_for_pr(pr_number)

    if not approval_time:
        continue

    # Initialize adjusted approval duration
    approval_duration = 0

    # Iterate through days between submission and approval
    current_day = created_at.date()

    while current_day <= approval_time.date():
        # Determine the relevant working hours for the current day
        current_start_time = max(
            created_at, datetime.combine(current_day, working_hours_start)
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

        # Add the time spent on the current day to the total approval
        # duration
        approval_duration += current_duration

        # Move to the next day
        current_day += timedelta(days=1)

    analyzed_prs += 1
    print(f"{analyzed_prs} PRs analyzed", end="\r", flush=True)

    if author not in total_approval_times:
        total_approval_times[author] = []

    total_approval_times[author].append(approval_duration)

print(f"Analyzed {analyzed_prs}")
# Display the total average approval times
for author, approval_times in total_approval_times.items():
    average_approval_time = sum(approval_times) / len(approval_times)
    hours, remainder = divmod(average_approval_time * 3600, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(
        f"Author: {author}, Total Average Approval Time: {int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"
    )
