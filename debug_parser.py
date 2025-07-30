#!/usr/bin/env python3
import sys
sys.path.append('.')
from github_monitor import InternshipGitHubMonitor

# Create monitor instance
monitor = InternshipGitHubMonitor()

# Read current README
with open('monitored_repos/Summer2026-Internships/README.md', 'r') as f:
    readme_content = f.read()

repo_name = "Summer2026-Internships"
print(f"🔍 Debugging parser for repo: {repo_name}")

# Check the condition
print(f"📝 Checking 'SimplifyJobs' in '{repo_name}': {'SimplifyJobs' in repo_name}")
print(f"📝 Checking 'speedyapply' in '{repo_name}': {'speedyapply' in repo_name}")

# Test the SimplifyJobs format parser directly
print(f"\n🧪 Testing _parse_simplify_jobs_format directly...")
internships = monitor._parse_simplify_jobs_format(readme_content, repo_name, "test_hash")
print(f"✅ Found {len(internships)} internships with direct call!")

# Test table row parsing on actual lines
print(f"\n🔍 Testing on actual table lines...")
lines = readme_content.split('\n')
table_lines = [line for line in lines if line.startswith('| **[')]
print(f"📊 Found {len(table_lines)} table lines starting with '| **['")

if table_lines:
    print(f"📄 Sample table line: {table_lines[0][:100]}...")
    
    # Test parsing first line
    test_internship = monitor._parse_table_row(table_lines[0], repo_name, "test_hash", "Software Engineering")
    print(f"🧪 Parsed result: {test_internship}")
