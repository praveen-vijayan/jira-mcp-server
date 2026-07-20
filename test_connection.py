#!/usr/bin/env python3
"""
Test script to verify Jira connection and credentials.
Run this before starting the MCP server to ensure everything is configured correctly.
"""

import os
import sys
import requests
from dotenv import load_dotenv

def test_connection():
    """Test Jira connection with current credentials."""
    
    # Load environment variables
    load_dotenv()
    
    jira_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    jira_email = os.getenv("JIRA_EMAIL", "")
    jira_token = os.getenv("JIRA_API_TOKEN", "")
    
    print("🔍 Testing Jira Connection...")
    print(f"   URL: {jira_url}")
    print(f"   Email: {jira_email}")
    print(f"   Token: {'*' * len(jira_token) if jira_token else '(not set)'}")
    print()
    
    # Check if credentials are set
    if not all([jira_url, jira_email, jira_token]):
        print("❌ ERROR: Missing credentials in .env file")
        print("   Please set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN")
        return False
    
    # Test connection
    try:
        print("📡 Connecting to Jira...")
        response = requests.get(
            f"{jira_url}/rest/api/2/myself",
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connection successful!")
            print(f"   Logged in as: {user_data.get('displayName', 'Unknown')}")
            print(f"   Account ID: {user_data.get('accountId', 'Unknown')}")
            print()
            
            # Test project access
            project_key = os.getenv("JIRA_PROJECT_KEY", "")
            if project_key:
                print(f"🔍 Testing project access: {project_key}")
                proj_response = requests.get(
                    f"{jira_url}/rest/api/2/project/{project_key}",
                    auth=(jira_email, jira_token),
                    headers={"Accept": "application/json"},
                    timeout=10
                )
                
                if proj_response.status_code == 200:
                    proj_data = proj_response.json()
                    print(f"✅ Project access confirmed: {proj_data.get('name', project_key)}")
                else:
                    print(f"⚠️  Cannot access project {project_key} (Status: {proj_response.status_code})")
                    print(f"   You may not have permissions or the project key is incorrect")
            
            print()
            print("🎉 All tests passed! You can now start the MCP server.")
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("   Check your email and API token are correct")
            return False
            
        elif response.status_code == 403:
            print("❌ Access forbidden!")
            print("   Your account may not have API access enabled")
            return False
            
        else:
            print(f"❌ Connection failed with status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error!")
        print("   Cannot reach Jira server. Check your JIRA_BASE_URL")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Connection timeout!")
        print("   Server is not responding. Check your network connection")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

# Made with Bob
