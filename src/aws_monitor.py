#!/usr/bin/env python3
"""
AWS EC2 Monitoring for UW Internship Finder
Check EC2 instance status and integrate with Excel reports
"""

import boto3
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

class EC2Monitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ec2_client = None
        self.instance_data = []
        
    def _get_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured"""
        try:
            # Try to create EC2 client
            self.ec2_client = boto3.client('ec2')
            
            # Test credentials by making a simple call
            self.ec2_client.describe_regions()
            return True
            
        except NoCredentialsError:
            print("❌ AWS credentials not found.")
            print("Please configure AWS credentials using one of these methods:")
            print("1. AWS CLI: aws configure")
            print("2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print("3. IAM roles (if running on EC2)")
            return False
            
        except Exception as e:
            print(f"❌ Error connecting to AWS: {e}")
            return False
    
    def check_ec2_instances(self, region_name: str = None) -> Dict:
        """Check status of all EC2 instances"""
        if not self._get_aws_credentials():
            return {"error": "AWS credentials not configured", "instances": []}
        
        try:
            # If no region specified, check current region or default to us-west-2
            if region_name:
                self.ec2_client = boto3.client('ec2', region_name=region_name)
            
            # Get all instances
            response = self.ec2_client.describe_instances()
            
            instances = []
            total_running = 0
            total_stopped = 0
            total_instances = 0
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    total_instances += 1
                    
                    # Get instance name from tags
                    instance_name = "No Name"
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            instance_name = tag['Value']
                            break
                    
                    state = instance['State']['Name']
                    if state == 'running':
                        total_running += 1
                    elif state == 'stopped':
                        total_stopped += 1
                    
                    instance_info = {
                        'instance_id': instance['InstanceId'],
                        'name': instance_name,
                        'state': state,
                        'instance_type': instance['InstanceType'],
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                        'launch_time': instance.get('LaunchTime', '').strftime('%Y-%m-%d %H:%M:%S') if instance.get('LaunchTime') else 'N/A',
                        'availability_zone': instance['Placement']['AvailabilityZone'],
                        'vpc_id': instance.get('VpcId', 'N/A'),
                        'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                        'key_name': instance.get('KeyName', 'N/A'),
                        'monitoring': instance['Monitoring']['State'],
                        'region': self.ec2_client.meta.region_name
                    }
                    instances.append(instance_info)
            
            # Store for Excel integration
            self.instance_data = instances
            
            summary = {
                'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'region': self.ec2_client.meta.region_name,
                'total_instances': total_instances,
                'running': total_running,
                'stopped': total_stopped,
                'other_states': total_instances - total_running - total_stopped,
                'instances': instances
            }
            
            return summary
            
        except ClientError as e:
            error_msg = f"AWS API Error: {e.response['Error']['Message']}"
            self.logger.error(error_msg)
            return {"error": error_msg, "instances": []}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "instances": []}
    
    def check_all_regions(self) -> Dict:
        """Check EC2 instances in all regions"""
        if not self._get_aws_credentials():
            return {"error": "AWS credentials not configured", "regions": []}
        
        try:
            # Get all regions
            regions_response = self.ec2_client.describe_regions()
            regions = [region['RegionName'] for region in regions_response['Regions']]
            
            all_results = []
            total_instances = 0
            total_running = 0
            total_stopped = 0
            
            print(f"🔍 Checking {len(regions)} AWS regions...")
            
            for region in regions:
                print(f"   Checking {region}...")
                result = self.check_ec2_instances(region)
                
                if 'error' not in result:
                    if result['total_instances'] > 0:
                        all_results.append(result)
                        total_instances += result['total_instances']
                        total_running += result['running']
                        total_stopped += result['stopped']
                
            return {
                'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'total_regions_checked': len(regions),
                'regions_with_instances': len(all_results),
                'total_instances': total_instances,
                'total_running': total_running,
                'total_stopped': total_stopped,
                'regions': all_results
            }
            
        except Exception as e:
            error_msg = f"Error checking regions: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "regions": []}
    
    def start_instance(self, instance_id: str, region_name: str = None) -> Dict:
        """Start a stopped EC2 instance"""
        if not self._get_aws_credentials():
            return {"error": "AWS credentials not configured"}
        
        try:
            if region_name:
                self.ec2_client = boto3.client('ec2', region_name=region_name)
            
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])
            
            return {
                'success': True,
                'instance_id': instance_id,
                'previous_state': response['StartingInstances'][0]['PreviousState']['Name'],
                'current_state': response['StartingInstances'][0]['CurrentState']['Name'],
                'message': f"Instance {instance_id} is starting up"
            }
            
        except ClientError as e:
            return {"error": f"Failed to start instance: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def stop_instance(self, instance_id: str, region_name: str = None) -> Dict:
        """Stop a running EC2 instance"""
        if not self._get_aws_credentials():
            return {"error": "AWS credentials not configured"}
        
        try:
            if region_name:
                self.ec2_client = boto3.client('ec2', region_name=region_name)
            
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            
            return {
                'success': True,
                'instance_id': instance_id,
                'previous_state': response['StoppingInstances'][0]['PreviousState']['Name'],
                'current_state': response['StoppingInstances'][0]['CurrentState']['Name'],
                'message': f"Instance {instance_id} is stopping"
            }
            
        except ClientError as e:
            return {"error": f"Failed to stop instance: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_instance_costs(self, days: int = 30) -> Dict:
        """Get estimated costs for EC2 instances (approximate)"""
        # Note: This is a basic cost estimation. For accurate billing, use AWS Cost Explorer API
        
        if not self.instance_data:
            return {"error": "No instance data available. Run check_ec2_instances first."}
        
        # Basic pricing estimates (US regions, subject to change)
        instance_pricing = {
            't2.nano': 0.0058,      # per hour
            't2.micro': 0.0116,     # per hour
            't2.small': 0.023,      # per hour
            't2.medium': 0.046,     # per hour
            't2.large': 0.093,      # per hour
            't3.nano': 0.0052,
            't3.micro': 0.0104,
            't3.small': 0.021,
            't3.medium': 0.042,
            't3.large': 0.083,
        }
        
        total_estimated_cost = 0
        instance_costs = []
        
        for instance in self.instance_data:
            instance_type = instance['instance_type']
            hourly_rate = instance_pricing.get(instance_type, 0.0116)  # Default to t2.micro
            
            if instance['state'] == 'running':
                daily_cost = hourly_rate * 24
                monthly_cost = daily_cost * days
                total_estimated_cost += monthly_cost
                
                instance_costs.append({
                    'instance_id': instance['instance_id'],
                    'name': instance['name'],
                    'instance_type': instance_type,
                    'state': instance['state'],
                    'hourly_rate': hourly_rate,
                    'daily_cost': daily_cost,
                    'monthly_cost': monthly_cost
                })
        
        return {
            'period_days': days,
            'total_estimated_cost': round(total_estimated_cost, 2),
            'currency': 'USD',
            'note': 'This is an estimate. Check AWS billing console for actual costs.',
            'instances': instance_costs
        }
    
    def print_status_report(self, status_data: Dict):
        """Print a formatted status report"""
        if 'error' in status_data:
            print(f"❌ Error: {status_data['error']}")
            return
        
        print("\n" + "="*60)
        print("🖥️  AWS EC2 INSTANCE STATUS REPORT")
        print("="*60)
        
        if 'regions' in status_data:  # Multi-region report
            print(f"📊 Summary:")
            print(f"   • Total Regions Checked: {status_data['total_regions_checked']}")
            print(f"   • Regions with Instances: {status_data['regions_with_instances']}")
            print(f"   • Total Instances: {status_data['total_instances']}")
            print(f"   • Running: {status_data['total_running']} 🟢")
            print(f"   • Stopped: {status_data['total_stopped']} 🔴")
            print(f"   • Checked: {status_data['timestamp']}")
            
            for region_data in status_data['regions']:
                print(f"\n📍 Region: {region_data['region']}")
                self._print_instances(region_data['instances'])
                
        else:  # Single region report
            print(f"📍 Region: {status_data['region']}")
            print(f"📊 Summary: {status_data['total_instances']} total, "
                  f"{status_data['running']} running 🟢, "
                  f"{status_data['stopped']} stopped 🔴")
            print(f"⏰ Checked: {status_data['timestamp']}")
            
            self._print_instances(status_data['instances'])
        
        print("\n" + "="*60)
    
    def _print_instances(self, instances: List[Dict]):
        """Helper method to print instance details"""
        if not instances:
            print("   No instances found in this region.")
            return
        
        for instance in instances:
            status_emoji = "🟢" if instance['state'] == 'running' else "🔴" if instance['state'] == 'stopped' else "🟡"
            print(f"\n   {status_emoji} {instance['name']} ({instance['instance_id']})")
            print(f"      Type: {instance['instance_type']}")
            print(f"      State: {instance['state']}")
            print(f"      Public IP: {instance['public_ip']}")
            print(f"      Zone: {instance['availability_zone']}")
            if instance['launch_time'] != 'N/A':
                print(f"      Launched: {instance['launch_time']}")


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS EC2 Monitor for UW Internship Finder')
    parser.add_argument('--region', '-r', help='Specific region to check (default: all regions)')
    parser.add_argument('--start', help='Start instance by ID')
    parser.add_argument('--stop', help='Stop instance by ID')
    parser.add_argument('--costs', '-c', action='store_true', help='Show cost estimates')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    monitor = EC2Monitor()
    
    if args.start:
        result = monitor.start_instance(args.start, args.region)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if 'error' in result:
                print(f"❌ {result['error']}")
            else:
                print(f"✅ {result['message']}")
        return
    
    if args.stop:
        result = monitor.stop_instance(args.stop, args.region)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if 'error' in result:
                print(f"❌ {result['error']}")
            else:
                print(f"✅ {result['message']}")
        return
    
    # Check instance status
    if args.region:
        status_data = monitor.check_ec2_instances(args.region)
    else:
        status_data = monitor.check_all_regions()
    
    if args.json:
        print(json.dumps(status_data, indent=2))
    else:
        monitor.print_status_report(status_data)
        
        if args.costs and 'instances' in status_data:
            cost_data = monitor.get_instance_costs()
            if 'error' not in cost_data:
                print(f"\n💰 Cost Estimates (30 days):")
                print(f"   Total: ${cost_data['total_estimated_cost']}")
                for inst in cost_data['instances']:
                    print(f"   • {inst['name']}: ${inst['monthly_cost']:.2f}/month")


if __name__ == "__main__":
    main()