#!/usr/bin/env python3
"""
Image-to-Image Keyframe Generation Demo

This script demonstrates how to use the new I2I keyframe generation mode
with Gemini API for character consistency and Veo3 for video generation.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Add parent directory to path to import pipeline modules
sys.path.append(str(Path(__file__).parent.parent))

from pipeline import run_pipeline
from keyframe_generator import generate_keyframe_with_gemini

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_i2i_config():
    """Create configuration for I2I keyframe generation"""
    config = {
        # Generation mode
        'generation_mode': 'keyframe',

        # Video backend - Veo3 for I2V generation
        'default_video_generation_backend': 'veo3',

        # Google Veo3 configuration
        'google_veo': {
            'project_id': os.getenv('GCP_PROJECT_ID', 'your-project-id'),
            'credentials_path': 'credentials.json',
            'region': 'us-central1',
            'veo_model': 'veo-3.0-generate-preview',
        },

        # I2I mode configuration
        'i2i_mode': {
            'enabled': True,
            'backend': 'gemini',
            'model': 'gemini-2.0-flash-exp',
            'reference_images': {
                'character1': 'examples/character1.png',
                'character2': 'examples/character2.png',
                'setting': 'examples/setting.png'
            },
            'prompt_template': "Generate an image maintaining the visual consistency of {character_name} and {setting_description}. Scene: {prompt}",
            'single_keyframe_mode': True,
            'keyframe_position': 'first'
        },

        # API keys
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),

        # Image generation settings
        'image_generation_model': 'gemini-2.0-flash-exp',
        'image_size': '1024x1024',  # Square for Veo3 compatibility
        'video_aspect_ratio': '16:9',  # Output video aspect ratio

        # Video generation parameters
        'segment_duration_seconds': 5.0,
        'frame_num': 81,
        'sample_steps': 40,
        'sample_shift': 5.0,
        'guide_scale': 5.0,
        'base_seed': 42,

        # Output configuration
        'output_dir': 'output/i2i_demo',

        # Prompt enhancement
        'prompt_enhancement_model': 'gpt-4o-mini',

        # Remote API settings
        'remote_api_settings': {
            'max_retries': 3,
            'timeout': 600
        }
    }

    return config

def generate_single_i2i_keyframe():
    """Demo: Generate a single I2I keyframe with character consistency"""
    logger.info("Generating single I2I keyframe with Gemini...")

    # Check for API key
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        return None

    # Reference images for consistency
    reference_images = {
        'hero': 'examples/character1.png',
        'castle': 'examples/setting.png'
    }

    # Check if reference images exist
    for name, path in reference_images.items():
        if not os.path.exists(path):
            logger.warning(f"Reference image not found: {path}")
            logger.info(f"Please provide a {name} reference image at: {path}")

    # Generate keyframe
    output_path = 'output/i2i_demo/keyframe_001.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        result = generate_keyframe_with_gemini(
            prompt="A brave knight standing at the castle gates at sunset, dramatic lighting",
            output_path=output_path,
            gemini_api_key=gemini_api_key,
            reference_images_dir='examples',
            model_name='gemini-2.0-flash-exp'
        )
        logger.info(f"Keyframe generated successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to generate keyframe: {e}")
        return None

def run_full_i2i_pipeline():
    """Demo: Run full pipeline with I2I keyframe generation and Veo3 video generation"""
    logger.info("Running full I2I pipeline demo...")

    # Create configuration
    config = create_i2i_config()

    # Save config to file for reference
    config_path = 'output/i2i_demo/pipeline_config.yaml'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info(f"Configuration saved to: {config_path}")

    # Story prompt for multi-segment video
    story_prompt = """
    A brave knight's journey to save the kingdom.
    First, the knight stands at the castle gates preparing for the quest.
    Then, the knight rides through the enchanted forest encountering magical creatures.
    Next, the knight battles a fierce dragon in the mountain pass.
    Finally, the knight returns victorious to the castle with the treasure.
    """

    # Run the pipeline
    try:
        result = run_pipeline(
            config_file=config_path,
            prompt=story_prompt,
            max_segments=4
        )
        logger.info(f"Pipeline completed successfully. Output: {result}")
        return result
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return None

def demo_character_consistency():
    """Demo: Generate multiple keyframes with character consistency"""
    logger.info("Demonstrating character consistency across multiple keyframes...")

    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        return

    # Reference images
    reference_images = {
        'main_character': 'examples/character1.png'
    }

    # Scene descriptions maintaining character consistency
    scenes = [
        "The character walking through a forest path in morning light",
        "The same character sitting by a campfire at night",
        "The character climbing a rocky mountain trail",
        "The character standing victorious at the mountain peak"
    ]

    generated_keyframes = []
    previous_frame = None

    for i, scene in enumerate(scenes, 1):
        output_path = f'output/i2i_demo/consistent_frame_{i:03d}.png'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            # Use previous frame as input for I2I transformation
            result = generate_keyframe_with_gemini(
                prompt=scene,
                output_path=output_path,
                gemini_api_key=gemini_api_key,
                input_image_path=previous_frame,  # Use previous frame for consistency
                reference_images_dir='examples',
                model_name='gemini-2.0-flash-exp'
            )

            logger.info(f"Generated keyframe {i}: {result}")
            generated_keyframes.append(result)
            previous_frame = result  # Update for next iteration

        except Exception as e:
            logger.error(f"Failed to generate keyframe {i}: {e}")
            break

    logger.info(f"Generated {len(generated_keyframes)} consistent keyframes")
    return generated_keyframes

def main():
    """Main demo function"""
    import argparse

    parser = argparse.ArgumentParser(description='I2I Keyframe Generation Demo')
    parser.add_argument('--mode', choices=['single', 'consistency', 'pipeline'],
                       default='single',
                       help='Demo mode to run')
    parser.add_argument('--gemini-api-key',
                       help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--openai-api-key',
                       help='OpenAI API key (or set OPENAI_API_KEY env var)')

    args = parser.parse_args()

    # Set API keys from arguments if provided
    if args.gemini_api_key:
        os.environ['GEMINI_API_KEY'] = args.gemini_api_key
    if args.openai_api_key:
        os.environ['OPENAI_API_KEY'] = args.openai_api_key

    # Run selected demo mode
    if args.mode == 'single':
        generate_single_i2i_keyframe()
    elif args.mode == 'consistency':
        demo_character_consistency()
    elif args.mode == 'pipeline':
        run_full_i2i_pipeline()

    logger.info("Demo completed")

if __name__ == "__main__":
    main()
