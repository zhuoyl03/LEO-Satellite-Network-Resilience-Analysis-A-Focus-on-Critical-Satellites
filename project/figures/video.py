import os
from moviepy.editor import ImageSequenceClip
import sys
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import PROJECT_FIGURES_DIR

def create_video_from_images(image_folder, output_video_path, fps=24):
    # Get a list of all image files in the folder
    image_files = sorted([os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(".png") or img.endswith(".jpg")])
    
    # Create a video clip from the image sequence
    clip = ImageSequenceClip(image_files, fps=fps)
    
    # Write the video file
    clip.write_videofile(output_video_path, codec="libx264")

def render_default_video():
    # Define the image folder and output video path
    image_folder = PROJECT_FIGURES_DIR / "end_to_end_path_plot"
    output_video_path = PROJECT_FIGURES_DIR / "1593_to_1590_Video.mp4"

    # Create the video
    create_video_from_images(image_folder, output_video_path)
