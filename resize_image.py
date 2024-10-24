from moviepy.editor import *
from PIL import Image
import os
import logger_config

def start(thumbnail_path):
    logger_config.info(f"Checking thumbnail size: {thumbnail_path}")
    max_file_size = 2 * 1024 * 1024  # 2 MB
    try:
        img = Image.open(thumbnail_path)
        file_size = os.path.getsize(thumbnail_path)
        if file_size > max_file_size:
            logger_config.info(f"Resizing thumbnail {thumbnail_path}")
            quality = 95
            img = img.convert('P', palette=Image.ADAPTIVE)
            img.save(thumbnail_path, format='PNG', optimize=True, quality=quality)
            file_size = os.path.getsize(thumbnail_path)
            while file_size > max_file_size:
                img = Image.open(thumbnail_path)
                img.save(thumbnail_path, format='PNG', optimize=True, quality=quality)
                file_size = os.path.getsize(thumbnail_path)
                quality -= 5
                logger_config.info(f'for rezising image; {file_size} max_file_size: {max_file_size}', 10)
            logger_config.info(f"Resized thumbnail to {file_size / 1024:.2f} KB with quality {quality}%")
        else:
            logger_config.info(f"Thumbnail {thumbnail_path} is within size limits")
        return thumbnail_path
    except Exception as e:
        logger_config.error(f"Error resizing thumbnail: {str(e)}")
        return thumbnail_path
    
if __name__ == "__main__":
    start("video/qGtcWu-thumbnail.png")