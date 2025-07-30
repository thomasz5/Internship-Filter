#!/usr/bin/env python3
import sys
sys.path.append('.')
from github_monitor import InternshipGitHubMonitor

print("🔍 Testing speedyapply parser for 2026-SWE-College-Jobs...")

# Create monitor instance
monitor = InternshipGitHubMonitor()

# Read current README
with open('monitored_repos/2026-SWE-College-Jobs/README.md', 'r') as f:
    readme_content = f.read()

repo_name = "2026-SWE-College-Jobs"
print(f"📄 README length: {len(readme_content)} characters")

# Test the speedyapply format parser directly
print(f"\n🧪 Testing _parse_speedyapply_format directly...")
internships = monitor._parse_speedyapply_format(readme_content, repo_name, "test_hash")
print(f"✅ Found {len(internships)} internships!")

# Show first few
for i, internship in enumerate(internships[:10]):
    print(f"  {i+1}. {internship.get('company')} - {internship.get('role')} ({internship.get('location')})")

if len(internships) > 10:
    print(f"  ... and {len(internships) - 10} more!")

# Test parsing on individual line
sample_line = '''| <a href="https://ramp.com"><strong>Ramp</strong></a> | Software Engineer Internship - iOS | New York | $60/hr | <a href="https://jobs.ashbyhq.com/ramp/0f1c331d-21b6-44fb-a326-5357d6e30188"><img src="https://i.imgur.com/JpkfjIq.png" alt="Apply" width="70"/></a> | 76d |'''

print(f"\n🧪 Testing individual line parsing...")
test_result = monitor._parse_speedyapply_table_row(sample_line, repo_name, "test_hash", "FAANG")
print(f"Sample result: {test_result}")
