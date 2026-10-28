#!/usr/bin/env python3
"""
Demo script showing Redis job queue infrastructure usage.

This script demonstrates how to:
1. Initialize the queue infrastructure
2. Enqueue jobs
3. Monitor job status
4. Handle job state transitions

Note: This requires a running Redis server.
"""

import asyncio
import time
from datetime import datetime, timezone

from api.config import RedisConfig
from api.queue import initialize_queue_infrastructure, get_job_queue
from api.models import JobCreateRequest, JobStatus


async def demo_queue_operations():
    """Demonstrate queue operations"""

    print("🚀 Redis Job Queue Infrastructure Demo")
    print("=" * 50)

    # Initialize queue infrastructure
    print("\n1. Initializing queue infrastructure...")
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0
    )

    try:
        redis_manager, job_queue = initialize_queue_infrastructure(redis_config)
        print("✅ Queue infrastructure initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize queue infrastructure: {e}")
        print("💡 Make sure Redis is running on localhost:6379")
        return

    # Create a test job
    print("\n2. Creating a test job...")
    request = JobCreateRequest(prompt="A beautiful sunset over the mountains")
    effective_config = {
        "generator": "test",
        "output_path": "/tmp/test_video.mp4"
    }

    try:
        job_data = job_queue.enqueue_job(request, effective_config, job_timeout=300)
        job_id = job_data.id
        print(f"✅ Job created with ID: {job_id}")
        print(f"   Status: {job_data.status}")
        print(f"   Created: {job_data.created_at}")
        print(f"   Prompt: {job_data.prompt}")
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        return

    # Demonstrate job status updates
    print(f"\n3. Demonstrating job status transitions for {job_id}...")

    # Simulate job processing
    status_updates = [
        (JobStatus.STARTED, 0, "Job started processing"),
        (JobStatus.PROGRESS, 25, "Generating keyframes"),
        (JobStatus.PROGRESS, 50, "Creating video segments"),
        (JobStatus.PROGRESS, 75, "Assembling final video"),
        (JobStatus.FINISHED, 100, "Video generation completed")
    ]

    for status, progress, log_message in status_updates:
        # Update job status
        success = job_queue.update_job_status(job_id, status, progress=progress)
        if success:
            print(f"   📊 Status: {status.value} ({progress}%)")

        # Add log message
        job_queue.add_job_log(job_id, log_message)

        # Simulate processing time
        await asyncio.sleep(0.5)

    # Simulate GCS upload for finished job
    if status == JobStatus.FINISHED:
        gcs_uri = f"gs://ttv-api-artifacts/2025-08/{job_id}/final_video.mp4"
        job_queue.update_job_status(job_id, JobStatus.FINISHED, gcs_uri=gcs_uri)
        print(f"   📁 Artifact uploaded: {gcs_uri}")

    # Retrieve final job data
    print(f"\n4. Retrieving final job data...")
    final_job = job_queue.get_job(job_id)
    if final_job:
        print(f"   ID: {final_job.id}")
        print(f"   Status: {final_job.status}")
        print(f"   Progress: {final_job.progress}%")
        print(f"   Duration: {(final_job.finished_at - final_job.created_at).total_seconds():.1f}s")
        print(f"   GCS URI: {final_job.gcs_uri}")
        print(f"   Log entries: {len(final_job.logs)}")

    # Show job logs
    print(f"\n5. Job logs:")
    logs = job_queue.get_job_logs(job_id, tail=5)
    for log in logs:
        print(f"   📝 {log}")

    # Demonstrate queue statistics
    print(f"\n6. Queue statistics:")
    stats = job_queue.get_queue_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Demonstrate job state validation
    print(f"\n7. Job state transition validation:")
    from api.queue import JobStateManager

    test_transitions = [
        (JobStatus.QUEUED, JobStatus.STARTED, True),
        (JobStatus.QUEUED, JobStatus.FINISHED, False),
        (JobStatus.FINISHED, JobStatus.STARTED, False),
        (JobStatus.PROGRESS, JobStatus.CANCELED, True)
    ]

    for from_status, to_status, expected in test_transitions:
        is_valid = JobStateManager.is_valid_transition(from_status, to_status)
        result = "✅" if is_valid == expected else "❌"
        print(f"   {result} {from_status.value} → {to_status.value}: {is_valid}")

    # Cleanup
    print(f"\n8. Cleanup...")
    redis_manager.close()
    print("✅ Redis connections closed")

    print(f"\n🎉 Demo completed successfully!")


def demo_job_cancellation():
    """Demonstrate job cancellation"""

    print("\n" + "=" * 50)
    print("🛑 Job Cancellation Demo")
    print("=" * 50)

    # Initialize queue infrastructure
    redis_config = RedisConfig()

    try:
        redis_manager, job_queue = initialize_queue_infrastructure(redis_config)
        print("✅ Queue infrastructure initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # Create a job to cancel
    request = JobCreateRequest(prompt="A long video that we'll cancel")
    job_data = job_queue.enqueue_job(request, {})
    job_id = job_data.id

    print(f"📝 Created job {job_id}")

    # Start the job
    job_queue.update_job_status(job_id, JobStatus.STARTED)
    job_queue.add_job_log(job_id, "Job started processing")
    print(f"▶️  Job started")

    # Cancel the job
    success = job_queue.cancel_job(job_id)
    if success:
        print(f"🛑 Job cancellation requested")

        # Check final status
        final_job = job_queue.get_job(job_id)
        if final_job:
            print(f"   Final status: {final_job.status}")
            print(f"   Last log: {final_job.logs[-1] if final_job.logs else 'No logs'}")

    # Cleanup
    redis_manager.close()
    print("✅ Cleanup completed")


if __name__ == "__main__":
    print("Redis Job Queue Infrastructure Demo")
    print("This demo requires a running Redis server on localhost:6379")
    print()

    try:
        # Run the main demo
        asyncio.run(demo_queue_operations())

        # Run cancellation demo
        demo_job_cancellation()

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
