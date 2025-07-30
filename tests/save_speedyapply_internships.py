#!/usr/bin/env python3
import sys
sys.path.append('.')
from github_monitor import InternshipGitHubMonitor

print("💾 Parsing and saving internships from 2026-SWE-College-Jobs...")

# Create monitor instance
monitor = InternshipGitHubMonitor()

# Read current README
with open('monitored_repos/2026-SWE-College-Jobs/README.md', 'r') as f:
    readme_content = f.read()

# Parse internships
internships = monitor._parse_speedyapply_format(readme_content, "2026-SWE-College-Jobs", "speedyapply_parse")
print(f"✅ Found {len(internships)} internships!")

# Save to database
if internships:
    monitor.save_internships(internships)
    print(f"💾 Saved internships to database!")

# Show all internships found
print(f"\n📊 All internships found:")
for i, internship in enumerate(internships, 1):
    print(f"  {i:2d}. {internship['company']} - {internship['role']}")
    print(f"      📍 {internship['location']}")
    if internship['application_link']:
        print(f"      🔗 {internship['application_link'][:60]}...")
    print()
