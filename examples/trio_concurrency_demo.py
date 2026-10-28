#!/usr/bin/env python3
"""
Demo script showing Trio structured concurrency implementation.

This script demonstrates:
1. Trio-based job execution with structured concurrency
2. Cancellation handling with proper cleanup
3. Resource management with task groups
4. Fallback mechanisms for asyncio dependencies
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import from workers
sys.path.insert(0, str(Path(__file__).parent.parent))

import trio

from workers.trio_executor import (
    TrioJobExecutor,
    trio_job_context,
    AsyncioTrioBridge,
    get_trio_executor,
    initialize_trio_executor
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_job_function(job_id: str, cancellation_token, process_manager) -> str:
    """
    Demo job function that simulates video generation work

    Args:
        job_id: Job identifier
        cancellation_token: Cancellation token for cooperative cancellation
        process_manager: Process manager for subprocess handling

    Returns:
        Job result string
    """
    logger.info(f"Starting demo job {job_id}")

    try:
        # Phase 1: Setup (simulate configuration loading)
        logger.info(f"Job {job_id}: Setting up configuration")
        await trio.sleep(0.5)

        if cancellation_token.is_cancelled():
            logger.info(f"Job {job_id}: Cancelled during setup")
            raise trio.Cancelled()

        # Phase 2: Processing (simulate video generation)
        logger.info(f"Job {job_id}: Processing video generation")

        # Simulate work with periodic cancellation checks
        for i in range(5):
            if cancellation_token.is_cancelled():
                logger.info(f"Job {job_id}: Cancelled during processing (step {i})")
                raise trio.Cancelled()

            logger.info(f"Job {job_id}: Processing step {i+1}/5")
            await trio.sleep(0.3)

        # Phase 3: Finalization (simulate upload)
        logger.info(f"Job {job_id}: Finalizing and uploading")
        await trio.sleep(0.2)

        if cancellation_token.is_cancelled():
            logger.info(f"Job {job_id}: Cancelled during finalization")
            raise trio.Cancelled()

        result = f"gs://demo-bucket/{job_id}/final_video.mp4"
        logger.info(f"Job {job_id}: Completed successfully - {result}")
        return result

    except trio.Cancelled:
        logger.info(f"Job {job_id}: Handling cancellation")
        # Simulate cleanup
        await trio.sleep(0.1)
        raise
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error - {e}")
        raise


async def demo_asyncio_fallback():
    """Demonstrate asyncio fallback mechanism"""
    logger.info("Demonstrating asyncio fallback mechanism")

    # Sync function
    def sync_calculation(x: int, y: int) -> int:
        time.sleep(0.1)  # Simulate work
        return x * y + 42

    # Async function
    async def async_calculation(x: int, y: int) -> int:
        await asyncio.sleep(0.1)  # Simulate async work
        return x + y * 2

    # Run both through the bridge
    sync_result = await AsyncioTrioBridge.run_asyncio_function(sync_calculation, 5, 3)
    async_result = await AsyncioTrioBridge.run_asyncio_function(async_calculation, 5, 3)

    logger.info(f"Sync function result: {sync_result}")
    logger.info(f"Async function result: {async_result}")

    return sync_result, async_result


async def demo_structured_concurrency():
    """Demonstrate structured concurrency with multiple jobs"""
    logger.info("🚀 Starting Trio Structured Concurrency Demo")
    logger.info("=" * 60)

    # Initialize Trio executor
    executor = initialize_trio_executor()

    # Demo 1: Single job execution
    logger.info("\n📋 Demo 1: Single Job Execution")
    logger.info("-" * 40)

    try:
        result = await executor.execute_job("demo_job_1", demo_job_function, timeout=10.0)
        logger.info(f"✅ Single job completed: {result}")
    except Exception as e:
        logger.error(f"❌ Single job failed: {e}")

    # Demo 2: Multiple concurrent jobs
    logger.info("\n📋 Demo 2: Multiple Concurrent Jobs")
    logger.info("-" * 40)

    async with trio.open_nursery() as nursery:
        results = {}

        async def run_job(job_id: str):
            try:
                result = await executor.execute_job(job_id, demo_job_function, timeout=10.0)
                results[job_id] = result
                logger.info(f"✅ Job {job_id} completed: {result}")
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed: {e}")
                results[job_id] = f"FAILED: {e}"

        # Start multiple jobs concurrently
        for i in range(3):
            job_id = f"concurrent_job_{i+1}"
            nursery.start_soon(run_job, job_id)

    logger.info(f"📊 Concurrent jobs results: {len(results)} jobs completed")

    # Demo 3: Job cancellation
    logger.info("\n📋 Demo 3: Job Cancellation")
    logger.info("-" * 40)

    async with trio.open_nursery() as nursery:
        job_id = "cancellable_job"

        async def start_and_cancel_job():
            # Start job
            nursery.start_soon(executor.execute_job, job_id, demo_job_function, 10.0)

            # Wait a bit then cancel
            await trio.sleep(1.0)
            logger.info(f"🛑 Cancelling job {job_id}")

            success = executor.cancel_job(job_id)
            if success:
                logger.info(f"✅ Job {job_id} cancellation initiated")
            else:
                logger.warning(f"⚠️ Job {job_id} could not be cancelled")

        try:
            await start_and_cancel_job()
        except Exception as e:
            logger.info(f"Expected cancellation result: {e}")

    # Demo 4: Resource management with context
    logger.info("\n📋 Demo 4: Resource Management")
    logger.info("-" * 40)

    cleanup_called = False

    def cleanup_callback():
        nonlocal cleanup_called
        cleanup_called = True
        logger.info("🧹 Cleanup callback executed")

    async with trio_job_context("resource_demo_job") as (token, manager):
        token.add_cleanup_callback(cleanup_callback)
        logger.info("📦 Job context created with cleanup callback")
        await trio.sleep(0.1)

    if cleanup_called:
        logger.info("✅ Resource cleanup completed successfully")
    else:
        logger.warning("⚠️ Resource cleanup was not called")

    # Demo 5: Asyncio fallback
    logger.info("\n📋 Demo 5: Asyncio Fallback Mechanism")
    logger.info("-" * 40)

    try:
        sync_result, async_result = await demo_asyncio_fallback()
        logger.info(f"✅ Asyncio fallback demo completed")
        logger.info(f"   Sync result: {sync_result}, Async result: {async_result}")
    except Exception as e:
        logger.error(f"❌ Asyncio fallback demo failed: {e}")

    logger.info("\n🎉 Trio Structured Concurrency Demo Completed!")
    logger.info("=" * 60)


async def demo_subprocess_management():
    """Demonstrate subprocess management with cancellation"""
    logger.info("\n📋 Subprocess Management Demo")
    logger.info("-" * 40)

    from workers.trio_executor import ProcessManager, TrioCancellationToken

    with trio.CancelScope() as cancel_scope:
        token = TrioCancellationToken("subprocess_demo", cancel_scope)
        manager = ProcessManager("subprocess_demo", token)

        try:
            # Start a simple process
            logger.info("🔧 Starting subprocess: echo 'Hello from subprocess'")
            process = await manager.start_process(["echo", "Hello from subprocess"], timeout=5.0)
            logger.info(f"✅ Subprocess completed with exit code: {process.returncode}")

            # Start a longer process and cancel it
            logger.info("🔧 Starting long-running subprocess: sleep 5")

            async with trio.open_nursery() as nursery:
                async def start_long_process():
                    try:
                        await manager.start_process(["sleep", "5"], timeout=10.0)
                        logger.info("Long process completed (unexpected)")
                    except Exception as e:
                        logger.info(f"Long process cancelled as expected: {e}")

                nursery.start_soon(start_long_process)

                # Cancel after a short delay
                await trio.sleep(0.5)
                logger.info("🛑 Cancelling long-running subprocess")
                token.cancel()

        except Exception as e:
            logger.error(f"❌ Subprocess demo failed: {e}")
        finally:
            manager.cleanup_all_processes()
            logger.info("🧹 Subprocess cleanup completed")


def main():
    """Main demo function"""
    print("🎬 Trio Structured Concurrency Demo")
    print("This demo shows the implementation of structured concurrency")
    print("with Trio for the video generation API server.\n")

    try:
        # Run the main demo
        trio.run(demo_structured_concurrency)

        # Run subprocess demo
        trio.run(demo_subprocess_management)

        print("\n✨ All demos completed successfully!")
        print("\nKey features demonstrated:")
        print("  ✅ Structured concurrency with task groups")
        print("  ✅ Cooperative cancellation with cleanup")
        print("  ✅ Resource management and cleanup callbacks")
        print("  ✅ Subprocess management with signal handling")
        print("  ✅ Asyncio fallback mechanisms")
        print("  ✅ Concurrent job execution")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
