import cairosvg
from PIL import Image
import logger_config

def convert_svg_to_jpg(svg_file_path, jpg_file_path, width, height):
    try:
        # Convert SVG to PNG first
        png_file_path = 'temp_image.png'  # Temporary file name for the PNG
        cairosvg.svg2png(url=svg_file_path, write_to=png_file_path)
        
        # Open the PNG and convert it to JPEG
        with Image.open(png_file_path) as img:
            # Resize the image
            img = img.resize((width, height), Image.LANCZOS)
            # Convert to JPEG and save
            img.convert('RGB').save(jpg_file_path, 'JPEG')
            print(f'jpg_file_path {jpg_file_path}')
    except Exception as e:
        print(f"Error in convert_svg_to_jpg: {e}")

# if __name__ == "__main__":
#     # Example usage
#     svg_file = 'chess/chess_board.svg'  # Replace with your SVG file path
#     jpg_file = 'chess/chess_board.jpg'  # Desired output JPEG file path
#     desired_width = 1920  # Set your desired width for YouTube video
#     desired_height = 1080  # Set your desired height for YouTube video
#     convert_svg_to_jpg(svg_file, jpg_file, desired_width, desired_height)