"""
Image Utilities - Image processing and manipulation
"""

import asyncio
from typing import Optional, Tuple, List, Dict, Any, BinaryIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import aiohttp
from io import BytesIO

class ImageUtils:
    """Image processing utilities"""
    
    @staticmethod
    async def download_image(url: str, 
                           timeout: int = 10) -> Optional[BytesIO]:
        """
        Download image from URL
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            BytesIO object with image data or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        content = await response.read()
                        return BytesIO(content)
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None
            
    @staticmethod
    async def resize_image(image: Image.Image, 
                         size: Tuple[int, int],
                         keep_aspect: bool = True) -> Image.Image:
        """
        Resize image
        
        Args:
            image: PIL Image object
            size: Target size (width, height)
            keep_aspect: Whether to maintain aspect ratio
            
        Returns:
            Resized image
        """
        if keep_aspect:
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return image
        else:
            return image.resize(size, Image.Resampling.LANCZOS)
            
    @staticmethod
    async def crop_image(image: Image.Image,
                       box: Tuple[int, int, int, int]) -> Image.Image:
        """
        Crop image
        
        Args:
            image: PIL Image object
            box: Crop box (left, upper, right, lower)
            
        Returns:
            Cropped image
        """
        return image.crop(box)
        
    @staticmethod
    async def convert_format(image: Image.Image,
                           format: str = "PNG") -> BytesIO:
        """
        Convert image to different format
        
        Args:
            image: PIL Image object
            format: Target format (PNG, JPEG, etc.)
            
        Returns:
            BytesIO with converted image
        """
        output = BytesIO()
        image.save(output, format=format)
        output.seek(0)
        return output
        
    @staticmethod
    async def apply_filter(image: Image.Image,
                         filter_name: str,
                         **kwargs) -> Image.Image:
        """
        Apply filter to image
        
        Args:
            image: PIL Image object
            filter_name: Filter to apply
            **kwargs: Filter parameters
            
        Returns:
            Filtered image
        """
        filters = {
            "blur": lambda img: img.filter(ImageFilter.GaussianBlur(
                kwargs.get("radius", 2)
            )),
            "sharpen": lambda img: img.filter(ImageFilter.SHARPEN),
            "contour": lambda img: img.filter(ImageFilter.CONTOUR),
            "detail": lambda img: img.filter(ImageFilter.DETAIL),
            "edge_enhance": lambda img: img.filter(ImageFilter.EDGE_ENHANCE),
            "emboss": lambda img: img.filter(ImageFilter.EMBOSS),
            "smooth": lambda img: img.filter(ImageFilter.SMOOTH),
            "grayscale": lambda img: ImageEnhance.Color(img).enhance(0),
            "sepia": lambda img: ImageUtils._apply_sepia(img),
            "brightness": lambda img: ImageEnhance.Brightness(img).enhance(
                kwargs.get("factor", 1.5)
            ),
            "contrast": lambda img: ImageEnhance.Contrast(img).enhance(
                kwargs.get("factor", 1.5)
            ),
            "color": lambda img: ImageEnhance.Color(img).enhance(
                kwargs.get("factor", 1.5)
            )
        }
        
        if filter_name in filters:
            return filters[filter_name](image)
        else:
            return image
            
    @staticmethod
    def _apply_sepia(image: Image.Image) -> Image.Image:
        """Apply sepia tone to image"""
        width, height = image.size
        pixels = image.load()
        
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                
                # Sepia formula
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                pixels[x, y] = (
                    min(255, tr),
                    min(255, tg),
                    min(255, tb)
                )
                
        return image
        
    @staticmethod
    async def add_text_to_image(image: Image.Image,
                              text: str,
                              position: Tuple[int, int] = (10, 10),
                              font_size: int = 20,
                              font_color: Tuple[int, int, int] = (255, 255, 255),
                              font_path: Optional[str] = None) -> Image.Image:
        """
        Add text to image
        
        Args:
            image: PIL Image object
            text: Text to add
            position: Text position (x, y)
            font_size: Font size
            font_color: Font color (R, G, B)
            font_path: Path to font file
            
        Returns:
            Image with text
        """
        draw = ImageDraw.Draw(image)
        
        try:
            if font_path and Path(font_path).exists():
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        draw.text(position, text, font=font, fill=font_color)
        return image
        
    @staticmethod
    async def add_watermark(image: Image.Image,
                          watermark_text: str,
                          opacity: float = 0.5) -> Image.Image:
        """
        Add watermark to image
        
        Args:
            image: PIL Image object
            watermark_text: Watermark text
            opacity: Watermark opacity (0.0 to 1.0)
            
        Returns:
            Watermarked image
        """
        # Create watermark layer
        watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        # Calculate text size and position
        text_width, text_height = draw.textsize(watermark_text, font)
        
        # Position watermark diagonally
        x = image.width - text_width - 10
        y = image.height - text_height - 10
        
        # Draw text with opacity
        draw.text((x, y), watermark_text, font=font, 
                 fill=(255, 255, 255, int(255 * opacity)))
                 
        # Composite with original image
        return Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')
        
    @staticmethod
    async def create_thumbnail(image: Image.Image,
                             size: Tuple[int, int] = (128, 128)) -> Image.Image:
        """
        Create thumbnail from image
        
        Args:
            image: PIL Image object
            size: Thumbnail size
            
        Returns:
            Thumbnail image
        """
        return await ImageUtils.resize_image(image, size, keep_aspect=True)
        
    @staticmethod
    async def extract_exif(image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract EXIF data from image
        
        Args:
            image_path: Path to image file
            
        Returns:
            EXIF data dictionary
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                
                if exif_data:
                    # Convert tag IDs to readable names
                    from PIL.ExifTags import TAGS
                    
                    readable_exif = {}
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        readable_exif[tag_name] = value
                        
                    return readable_exif
                    
        except Exception as e:
            print(f"Error extracting EXIF from {image_path}: {e}")
            
        return {}
        
    @staticmethod
    async def get_image_info(image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get image information
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image information dictionary
        """
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "has_alpha": img.mode in ('RGBA', 'LA', 'P'),
                    "is_animated": getattr(img, "is_animated", False),
                    "frames": getattr(img, "n_frames", 1)
                }
        except Exception as e:
            print(f"Error getting image info for {image_path}: {e}")
            return {}
            
    @staticmethod
    async def create_gradient(size: Tuple[int, int],
                            start_color: Tuple[int, int, int],
                            end_color: Tuple[int, int, int],
                            direction: str = "horizontal") -> Image.Image:
        """
        Create gradient image
        
        Args:
            size: Image size (width, height)
            start_color: Start color (R, G, B)
            end_color: End color (R, G, B)
            direction: Gradient direction (horizontal/vertical)
            
        Returns:
            Gradient image
        """
        image = Image.new('RGB', size)
        draw = ImageDraw.Draw(image)
        
        width, height = size
        
        if direction == "horizontal":
            for x in range(width):
                # Calculate color at this position
                ratio = x / width
                r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
                g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
                b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
                
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        else:  # vertical
            for y in range(height):
                ratio = y / height
                r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
                g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
                b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
                
                draw.line([(0, y), (width, y)], fill=(r, g, b))
                
        return image
        
    @staticmethod
    async def create_color_image(size: Tuple[int, int],
                               color: Tuple[int, int, int]) -> Image.Image:
        """
        Create solid color image
        
        Args:
            size: Image size
            color: Fill color (R, G, B)
            
        Returns:
            Solid color image
        """
        return Image.new('RGB', size, color)
        
    @staticmethod
    async def merge_images(images: List[Image.Image],
                         direction: str = "horizontal",
                         spacing: int = 0) -> Image.Image:
        """
        Merge multiple images
        
        Args:
            images: List of PIL Image objects
            direction: Merge direction (horizontal/vertical)
            spacing: Spacing between images
            
        Returns:
            Merged image
        """
        if not images:
            return Image.new('RGB', (1, 1), (255, 255, 255))
            
        if direction == "horizontal":
            # Calculate total width and max height
            total_width = sum(img.width for img in images) + \
                         spacing * (len(images) - 1)
            max_height = max(img.height for img in images)
            
            # Create new image
            merged = Image.new('RGB', (total_width, max_height), (255, 255, 255))
            
            # Paste images
            x_offset = 0
            for img in images:
                merged.paste(img, (x_offset, (max_height - img.height) // 2))
                x_offset += img.width + spacing
        else:  # vertical
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images) + \
                          spacing * (len(images) - 1)
            
            merged = Image.new('RGB', (max_width, total_height), (255, 255, 255))
            
            y_offset = 0
            for img in images:
                merged.paste(img, ((max_width - img.width) // 2, y_offset))
                y_offset += img.height + spacing
                
        return merged
        
    @staticmethod
    async def create_welcome_image(user_data: Dict[str, Any],
                                 group_data: Dict[str, Any]) -> Optional[Path]:
        """
        Create welcome image with user and group info
        
        Args:
            user_data: User information
            group_data: Group information
            
        Returns:
            Path to created image or None
        """
        try:
            # Create image size
            width, height = 800, 600
            
            # Create background
            background = await ImageUtils.create_gradient(
                (width, height),
                (41, 128, 185),  # Blue
                (52, 152, 219),  # Lighter blue
                "vertical"
            )
            
            draw = ImageDraw.Draw(background)
            
            # Try to load Bangla font
            try:
                font_path = "assets/fonts/kalpurush.ttf"
                title_font = ImageFont.truetype(font_path, 48)
                name_font = ImageFont.truetype(font_path, 64)
                info_font = ImageFont.truetype(font_path, 32)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                name_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                
            # Add title
            title = "স্বাগতম!"
            title_width, title_height = draw.textsize(title, title_font)
            draw.text(
                ((width - title_width) // 2, 50),
                title,
                font=title_font,
                fill=(255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0)
            )
            
            # Add user name
            user_name = user_data.get("first_name", "অতিথি")
            name_width, name_height = draw.textsize(user_name, name_font)
            draw.text(
                ((width - name_width) // 2, 200),
                user_name,
                font=name_font,
                fill=(255, 255, 255),
                stroke_width=3,
                stroke_fill=(41, 128, 185)
            )
            
            # Add group info
            group_name = group_data.get("title", "গ্রুপ")
            group_info = f"{group_name} এ আপনাকে স্বাগতম"
            info_width, info_height = draw.textsize(group_info, info_font)
            draw.text(
                ((width - info_width) // 2, 300),
                group_info,
                font=info_font,
                fill=(236, 240, 241)
            )
            
            # Add member count
            member_count = group_data.get("member_count", 0)
            member_text = f"সদস্য সংখ্যা: {member_count}"
            member_width, member_height = draw.textsize(member_text, info_font)
            draw.text(
                ((width - member_width) // 2, 350),
                member_text,
                font=info_font,
                fill=(189, 195, 199)
            )
            
            # Add decorative elements
            draw.rectangle([(50, 50), (width - 50, height - 50)], 
                         outline=(255, 255, 255), width=5)
                         
            # Save image
            timestamp = int(time.time())
            filename = f"welcome_{user_data.get('id', 'user')}_{timestamp}.png"
            filepath = Path("data/cache/images") / filename
            
            await FileUtils.ensure_directory(filepath.parent)
            background.save(filepath, "PNG", quality=95)
            
            return filepath
            
        except Exception as e:
            print(f"Error creating welcome image: {e}")
            return None
            
    @staticmethod
    async def create_profile_card(profile_data: Dict[str, Any]) -> Optional[Path]:
        """
        Create profile card image
        
        Args:
            profile_data: Profile information
            
        Returns:
            Path to created image or None
        """
        try:
            width, height = 600, 800
            
            # Create background
            background = await ImageUtils.create_color_image(
                (width, height),
                (52, 73, 94)  # Dark blue-gray
            )
            
            draw = ImageDraw.Draw(background)
            
            # Try to load font
            try:
                font_path = "assets/fonts/kalpurush.ttf"
                title_font = ImageFont.truetype(font_path, 36)
                name_font = ImageFont.truetype(font_path, 48)
                info_font = ImageFont.truetype(font_path, 28)
                stat_font = ImageFont.truetype(font_path, 24)
            except:
                font = ImageFont.load_default()
                title_font = name_font = info_font = stat_font = font
                
            # Add title
            title = "প্রোফাইল কার্ড"
            title_width, _ = draw.textsize(title, title_font)
            draw.text(
                ((width - title_width) // 2, 50),
                title,
                font=title_font,
                fill=(46, 204, 113)
            )
            
            # Add user info
            user_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}"
            name_width, _ = draw.textsize(user_name, name_font)
            draw.text(
                ((width - name_width) // 2, 150),
                user_name.strip(),
                font=name_font,
                fill=(255, 255, 255)
            )
            
            # Add username
            username = profile_data.get("username", "")
            if username:
                username_text = f"@{username}"
                username_width, _ = draw.textsize(username_text, info_font)
                draw.text(
                    ((width - username_width) // 2, 220),
                    username_text,
                    font=info_font,
                    fill=(189, 195, 199)
                )
                
            # Add stats
            stats_y = 300
            stats = [
                ("মেসেজ", profile_data.get("message_count", 0)),
                ("রেপুটেশন", profile_data.get("reputation", 0)),
                ("র‍্যাংক", profile_data.get("rank", "নতুন")),
                ("ট্রাস্ট স্কোর", f"{profile_data.get('trust_score', 50)}%")
            ]
            
            for stat_name, stat_value in stats:
                stat_text = f"{stat_name}: {stat_value}"
                draw.text(
                    (100, stats_y),
                    stat_text,
                    font=stat_font,
                    fill=(236, 240, 241)
                )
                stats_y += 50
                
            # Add badges section
            badges = profile_data.get("badges", [])
            if badges:
                badges_y = 550
                draw.text(
                    (100, badges_y),
                    "ব্যাজসমূহ:",
                    font=info_font,
                    fill=(241, 196, 15)
                )
                
                badges_y += 50
                for badge in badges[:5]:  # Show first 5 badges
                    badge_text = f"• {badge.get('name', '')}"
                    draw.text(
                        (120, badges_y),
                        badge_text,
                        font=stat_font,
                        fill=(155, 89, 182)
                    )
                    badges_y += 35
                    
            # Save image
            timestamp = int(time.time())
            filename = f"profile_{profile_data.get('user_id', 'user')}_{timestamp}.png"
            filepath = Path("data/cache/images") / filename
            
            await FileUtils.ensure_directory(filepath.parent)
            background.save(filepath, "PNG", quality=95)
            
            return filepath
            
        except Exception as e:
            print(f"Error creating profile card: {e}")
            return None