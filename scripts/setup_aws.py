#!/usr/bin/env python3
"""
AWS Setup Helper for UW Internship Finder
Helps configure AWS credentials for EC2 monitoring
"""

import os
import sys
import subprocess
from pathlib import Path

def check_aws_cli():
    """Check if AWS CLI is installed"""
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        print(f"✅ AWS CLI found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ AWS CLI not found")
        return False

def install_aws_cli():
    """Install AWS CLI using pip"""
    print("Installing AWS CLI...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'awscli'])
        print("✅ AWS CLI installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install AWS CLI")
        return False

def check_boto3():
    """Check if boto3 is installed"""
    try:
        import boto3
        print("✅ boto3 is available")
        return True
    except ImportError:
        print("❌ boto3 not found")
        return False

def install_boto3():
    """Install boto3 using pip"""
    print("Installing boto3...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'boto3'])
        print("✅ boto3 installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install boto3")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        import boto3
        client = boto3.client('sts')
        response = client.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {response.get('Account', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        return False

def setup_aws_credentials():
    """Guide user through AWS credential setup"""
    print("\n" + "="*60)
    print("🔐 AWS CREDENTIALS SETUP")
    print("="*60)
    
    print("\nYou need to configure AWS credentials to monitor your EC2 instances.")
    print("You can do this in several ways:")
    print("\n1. Using AWS CLI (Recommended):")
    print("   aws configure")
    print("   Then enter your:")
    print("   - AWS Access Key ID")
    print("   - AWS Secret Access Key")
    print("   - Default region (e.g., us-west-2)")
    print("   - Default output format (json)")
    
    print("\n2. Using Environment Variables:")
    print("   export AWS_ACCESS_KEY_ID=your-access-key-id")
    print("   export AWS_SECRET_ACCESS_KEY=your-secret-access-key")
    print("   export AWS_DEFAULT_REGION=us-west-2")
    
    print("\n3. For EC2 Instances:")
    print("   Use IAM roles (no keys needed)")
    
    print("\n🔑 To get AWS credentials:")
    print("   1. Go to AWS Console > IAM > Users")
    print("   2. Create a new user or select existing user")
    print("   3. Attach policy: EC2ReadOnlyAccess (for monitoring)")
    print("   4. Or EC2FullAccess (for start/stop operations)")
    print("   5. Create access keys in Security credentials tab")
    
    choice = input("\nWould you like to run 'aws configure' now? (y/n): ").lower()
    if choice == 'y':
        try:
            subprocess.run(['aws', 'configure'], check=True)
            print("✅ AWS configuration completed")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Failed to run aws configure")
            return False
    
    return False

def test_ec2_connection():
    """Test connection to EC2"""
    print("\n🔍 Testing EC2 connection...")
    try:
        # Add current directory to path for imports
        current_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(current_dir / 'src'))
        
        from aws_monitor import EC2Monitor
        
        monitor = EC2Monitor()
        
        # Try to get regions (this requires minimal permissions)
        if monitor._get_aws_credentials():
            print("✅ Successfully connected to AWS!")
            
            # Try to get status
            status = monitor.check_all_regions()
            if 'error' not in status:
                print(f"✅ Found {status['total_instances']} EC2 instances across {status['regions_with_instances']} regions")
                
                if status['total_instances'] > 0:
                    print("\nInstance Summary:")
                    print(f"   Running: {status['total_running']} 🟢")
                    print(f"   Stopped: {status['total_stopped']} 🔴")
                    
                    # Show first few instances
                    for region_data in status['regions'][:2]:  # Show first 2 regions
                        print(f"\n   Region: {region_data['region']}")
                        for instance in region_data['instances'][:3]:  # Show first 3 instances
                            status_emoji = "🟢" if instance['state'] == 'running' else "🔴"
                            print(f"     {status_emoji} {instance['name']} ({instance['instance_id']})")
                
                return True
            else:
                print(f"❌ Error checking EC2: {status['error']}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error testing EC2 connection: {e}")
        return False

def main():
    print("🚀 AWS Setup for UW Internship Finder")
    print("="*50)
    
    # Check dependencies
    if not check_aws_cli():
        if not install_aws_cli():
            print("Please install AWS CLI manually: pip install awscli")
            return
    
    if not check_boto3():
        if not install_boto3():
            print("Please install boto3 manually: pip install boto3")
            return
    
    # Check credentials
    if not check_aws_credentials():
        setup_aws_credentials()
        
        # Re-check after setup
        if not check_aws_credentials():
            print("\n❌ Credentials still not working. Please check your setup.")
            return
    
    # Test EC2 connection
    if test_ec2_connection():
        print("\n🎉 AWS setup complete!")
        print("\nYou can now use these commands:")
        print("   python3 main.py aws-status          # Check all EC2 instances")
        print("   python3 main.py excel               # Update Excel with AWS status")
        print("   python3 src/aws_monitor.py          # Direct AWS monitoring")
        print("\nThe AWS status will also be included when you run:")
        print("   python3 main.py excel")
    else:
        print("\n❌ Setup incomplete. Please check your AWS configuration.")
        print("\nTroubleshooting:")
        print("   1. Verify your AWS credentials are correct")
        print("   2. Check that your user has EC2 permissions")
        print("   3. Ensure your default region is set")
        print("   4. Try running: aws sts get-caller-identity")

if __name__ == "__main__":
    main()