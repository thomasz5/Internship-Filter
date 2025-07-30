#!/usr/bin/env python3
import sys
sys.path.append('.')
from github_monitor import InternshipGitHubMonitor

print("🔍 Force parsing current README content...")

# Create monitor instance
monitor = InternshipGitHubMonitor()

# Read current README
with open('monitored_repos/Summer2026-Internships/README.md', 'r') as f:
    readme_content = f.read()

print(f"📄 README length: {len(readme_content)} characters")

# Force parse with current commit hash
internships = monitor.parse_readme_for_internships(readme_content, "Summer2026-Internships", "force_parse")

print(f"✅ Found {len(internships)} internships!")

# Show first few
for i, internship in enumerate(internships[:10]):
    print(f"  {i+1}. {internship.get('company')} - {internship.get('role')} ({internship.get('location')})")

if len(internships) > 10:
    print(f"  ... and {len(internships) - 10} more!")

# Save to database if we found any
if internships:
    print(f"\n💾 Saving {len(internships)} internships to database...")
    saved_count = monitor.save_internships(internships)
    print(f"✅ Saved {saved_count} new internships!")
