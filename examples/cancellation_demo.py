#!/usr/bin/env python3
"""
Demo script showing job cancellation functionality.

This script demonstrates:
1. Creating a job
2. Checking its status
3. Cancelling the job
4. Verifying cancellation worked
"""

import time
import requests
import json
from typing import Dict, Any


def make_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP request and return JSON response"""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {e.response.text}")
        raise


def demo_job_cancellation(base_url: str = "http://localhost:8000"):
    """Demonstrate job cancellation workflow"""

    print("🎬 Job Cancellation Demo")
    print("=" * 50)

    # Step 1: Create a job
    print("\n1. Creating a new video generation job...")

    job_data = {
        "prompt": "A majestic eagle soaring through mountain peaks at sunset"
    }

    try:
        response = make_request("POST", f"{base_url}/v1/jobs", json=job_data)
        job_id = response["id"]
        print(f"✅ Job created successfully!")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {response['status']}")
        print(f"   Created: {response['created_at']}")

    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        return

    # Step 2: Check initial status
    print(f"\n2. Checking job status...")

    try:
        status_response = make_request("GET", f"{base_url}/v1/jobs/{job_id}")
        print(f"✅ Job status retrieved:")
        print(f"   Status: {status_response['status']}")
        print(f"   Progress: {status_response['progress']}%")

    except Exception as e:
        print(f"❌ Failed to get job status: {e}")
        return

    # Step 3: Wait a moment to let job start processing
    print(f"\n3. Waiting for job to start processing...")
    time.sleep(2)

    try:
        status_response = make_request("GET", f"{base_url}/v1/jobs/{job_id}")
        print(f"✅ Updated job status:")
        print(f"   Status: {status_response['status']}")
        print(f"   Progress: {status_response['progress']}%")

    except Exception as e:
        print(f"❌ Failed to get updated job status: {e}")

    # Step 4: Cancel the job
    print(f"\n4. Cancelling the job...")

    try:
        cancel_response = make_request("POST", f"{base_url}/v1/jobs/{job_id}/cancel", json={})
        print(f"✅ Job cancellation initiated:")
        print(f"   Job ID: {cancel_response['id']}")
        print(f"   Status: {cancel_response['status']}")
        print(f"   Message: {cancel_response['message']}")

    except Exception as e:
        print(f"❌ Failed to cancel job: {e}")
        return

    # Step 5: Verify cancellation
    print(f"\n5. Verifying job was cancelled...")

    try:
        final_status = make_request("GET", f"{base_url}/v1/jobs/{job_id}")
        print(f"✅ Final job status:")
        print(f"   Status: {final_status['status']}")
        print(f"   Progress: {final_status['progress']}%")

        if final_status['status'] == 'canceled':
            print(f"🎉 Job successfully cancelled!")
        else:
            print(f"⚠️  Job status is '{final_status['status']}', not 'canceled'")

    except Exception as e:
        print(f"❌ Failed to verify cancellation: {e}")
        return

    # Step 6: Check job logs
    print(f"\n6. Checking job logs...")

    try:
        logs_response = make_request("GET", f"{base_url}/v1/jobs/{job_id}/logs?tail=10")
        print(f"✅ Job logs (last 10 lines):")
        for i, log_line in enumerate(logs_response['lines'][-5:], 1):  # Show last 5 lines
            print(f"   {i}. {log_line}")

    except Exception as e:
        print(f"❌ Failed to get job logs: {e}")

    # Step 7: Try to cancel already cancelled job
    print(f"\n7. Attempting to cancel already cancelled job...")

    try:
        cancel_response = make_request("POST", f"{base_url}/v1/jobs/{job_id}/cancel", json={})
        print(f"⚠️  Unexpected success: {cancel_response}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:  # Conflict
            error_data = e.response.json()
            print(f"✅ Expected error received:")
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Error: {error_data.get('error', 'Unknown')}")
            print(f"   Message: {error_data.get('message', 'No message')}")
        else:
            print(f"❌ Unexpected error: {e}")
    except Exception as e:
        print(f"❌ Failed to test double cancellation: {e}")

    print(f"\n🎉 Demo completed successfully!")
    print(f"📋 Summary:")
    print(f"   - Job created: {job_id}")
    print(f"   - Job cancelled successfully")
    print(f"   - Cancellation properly prevented on already cancelled job")


def test_cancellation_edge_cases(base_url: str = "http://localhost:8000"):
    """Test edge cases for job cancellation"""

    print("\n🧪 Testing Cancellation Edge Cases")
    print("=" * 50)

    # Test 1: Cancel non-existent job
    print("\n1. Testing cancellation of non-existent job...")

    try:
        cancel_response = make_request("POST", f"{base_url}/v1/jobs/nonexistent-job-id/cancel", json={})
        print(f"⚠️  Unexpected success: {cancel_response}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:  # Not Found
            error_data = e.response.json()
            print(f"✅ Expected error received:")
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Error: {error_data.get('error', 'Unknown')}")
            print(f"   Message: {error_data.get('message', 'No message')}")
        else:
            print(f"❌ Unexpected error: {e}")
    except Exception as e:
        print(f"❌ Failed to test non-existent job cancellation: {e}")

    print(f"\n✅ Edge case testing completed!")


if __name__ == "__main__":
    import sys

    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Using API base URL: {base_url}")

    try:
        # Test basic health endpoint first
        health_response = make_request("GET", f"{base_url}/healthz")
        print(f"✅ API server is healthy: {health_response['status']}")

        # Run the main demo
        demo_job_cancellation(base_url)

        # Run edge case tests
        test_cancellation_edge_cases(base_url)

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print(f"\nMake sure the API server is running at {base_url}")
        print(f"You can start it with: python -m api.main")
        sys.exit(1)
