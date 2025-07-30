#!/usr/bin/env python3
import sys
import git
sys.path.append('.')
from github_monitor import InternshipGitHubMonitor

# Create monitor instance
monitor = InternshipGitHubMonitor()

# Get the repo
repo_path = "monitored_repos/Summer2026-Internships"
repo = git.Repo(repo_path)

# Get recent commits with internship keywords
recent_commits = list(repo.iter_commits(max_count=10))
print("🔍 Analyzing recent commits for internships...")

for commit in recent_commits:
    commit_msg = commit.message.strip()
    if any(keyword in commit_msg.lower() for keyword in ['intern', 'listing', 'added']):
        print(f"\n�� Commit: {commit.hexsha[:8]} - {commit_msg}")
        
        # Parse this specific commit
        internships = monitor.parse_new_commits(repo, [commit], "Summer2026-Internships")
        print(f"   Found {len(internships)} internships in this commit")
        
        for internship in internships:
            print(f"   • {internship.get('company', 'Unknown')} - {internship.get('role', 'Unknown')}")

print("\n✅ Analysis complete!")
