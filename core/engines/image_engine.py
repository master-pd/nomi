"""
Image Engine - Handles image processing and generation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests
from io import BytesIO

class ImageEngine:
    """Engine for image processing and generation"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_image")
        self.json_loader = json_loader
        self.image_cache = {}
        self.fonts = {}
        self.templates = {}
        
    async def initialize(self):
        """Initialize image engine"""
        self.logger.info("🖼️ Initializing image engine...")
        await self._load_fonts()
        await self._load_templates()
        
    async def _load_fonts(self):
        """Load available fonts"""
        fonts_dir = Path("assets/fonts")
        fonts_dir.mkdir(parents=True, exist_ok=True)
        
        # Default fonts
        default_fonts = {
            "kalpurush": "kalpurush.ttf",
            "siyamrupali": "siyamrupali.ttf",
            "noto_bangla": "NotoSansBengali-Regular.ttf"
        }
        
        for font_name, font_file in default_fonts.items():
            font_path = fonts_dir / font_file
            if not font_path.exists():
                # Try to download or use system font
                try:
                    # For now, use default if not found
                    self.fonts[font_name] = None
                except:
                    self.fonts[font_name] = None
            else:
                try:
                    self.fonts[font_name] = str(font_path)
                except:
                    self.fonts[font_name] = None
                    
        self.logger.info(f"📝 Loaded {len(self.fonts)} fonts")
        
    async def _load_templates(self):
        """Load image templates"""
        templates_dir = Path("assets/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load template configurations
        template_config = await self.json_loader.load("config/templates.json")
        self.templates = template_config.get("templates", {})
        
    async def create_welcome_image(self, user_data: Dict, group_data: Dict,
                                 template_name: str = "default") -> Optional[str]:
        """
        Create welcome image
        
        Args:
            user_data: User information
            group_data: Group information
            template_name: Template to use
            
        Returns:
            Path to image file or None
        """
        try:
            # Get template
            template = self.templates.get(template_name, {})
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"welcome_{user_data.get('id', 'user')}_{timestamp}.png"
            filepath = Path("data/cache/images") / filename
            
            # Create directory
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Create image
            image = await self._render_welcome_template(user_data, group_data, template)
            
            # Save image
            image.save(str(filepath), "PNG", quality=95)
            
            self.logger.info(f"🖼️ Created welcome image: {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating welcome image: {e}")
            return None
            
    async def _render_welcome_template(self, user_data: Dict, group_data: Dict,
                                     template: Dict) -> Image.Image:
        """Render welcome template"""
        # Get background
        bg_path = template.get("background", "assets/bg.jpg")
        try:
            background = Image.open(bg_path)
        except:
            # Create default background
            background = Image.new('RGB', (1200, 800), color=(41, 128, 185))
            
        # Create drawing context
        draw = ImageDraw.Draw(background)
        
        # Add user profile picture
        profile_url = user_data.get("profile_photo")
        if profile_url:
            await self._add_profile_picture(background, draw, profile_url)
            
        # Add text elements
        await self._add_text_elements(background, draw, user_data, group_data, template)
        
        # Add decorative elements
        await self._add_decorations(background, draw, template)
        
        return background
        
    async def _add_profile_picture(self, image: Image.Image, draw: ImageDraw.ImageDraw,
                                 profile_url: str):
        """Add user profile picture to image"""
        try:
            # Download profile picture
            response = requests.get(profile_url, timeout=10)
            profile_img = Image.open(BytesIO(response.content))
            
            # Resize to circle
            size = (200, 200)
            profile_img = profile_img.resize(size, Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0) + size, fill=255)
            
            # Apply mask
            profile_img.putalpha(mask)
            
            # Position on background
            position = (500, 150)  # Center
            image.paste(profile_img, position, profile_img)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not add profile picture: {e}")
            
    async def _add_text_elements(self, image: Image.Image, draw: ImageDraw.ImageDraw,
                               user_data: Dict, group_data: Dict, template: Dict):
        """Add text elements to image"""
        try:
            # Get font
            font_path = self.fonts.get("kalpurush")
            if font_path:
                title_font = ImageFont.truetype(font_path, 48)
                name_font = ImageFont.truetype(font_path, 64)
                info_font = ImageFont.truetype(font_path, 32)
            else:
                title_font = ImageFont.load_default()
                name_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                
            # Add title
            title = template.get("title", "স্বাগতম")
            draw.text((600, 50), title, font=title_font, fill=(255, 255, 255), 
                     anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
            
            # Add user name
            user_name = user_data.get("first_name", "অতিথি")
            draw.text((600, 400), user_name, font=name_font, fill=(255, 255, 255),
                     anchor="mm", stroke_width=3, stroke_fill=(41, 128, 185))
            
            # Add group info
            group_name = group_data.get("title", "গ্রুপ")
            group_info = f"{group_name} এ আপনাকে স্বাগতম"
            draw.text((600, 500), group_info, font=info_font, fill=(236, 240, 241),
                     anchor="mm")
            
            # Add member count
            member_count = group_data.get("member_count", 0)
            member_text = f"সদস্য সংখ্যা: {member_count}"
            draw.text((600, 550), member_text, font=info_font, fill=(236, 240, 241),
                     anchor="mm")
            
            # Add date
            date_text = datetime.now().strftime("%d %B %Y, %I:%M %p")
            draw.text((600, 600), date_text, font=info_font, fill=(189, 195, 199),
                     anchor="mm")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding text elements: {e}")
            
    async def _add_decorations(self, image: Image.Image, draw: ImageDraw.ImageDraw,
                             template: Dict):
        """Add decorative elements"""
        try:
            # Add borders
            draw.rectangle([(50, 50), (1150, 750)], outline=(255, 255, 255), width=5)
            
            # Add decorative lines
            for i in range(0, 1200, 50):
                draw.line([(i, 0), (i, 50)], fill=(255, 255, 255, 100), width=2)
                draw.line([(i, 750), (i, 800)], fill=(255, 255, 255, 100), width=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding decorations: {e}")
            
    async def create_collage(self, images: List[str], layout: str = "grid",
                           size: tuple = (1000, 1000)) -> Optional[str]:
        """
        Create image collage
        
        Args:
            images: List of image paths
            layout: Collage layout (grid, horizontal, vertical)
            size: Output image size
            
        Returns:
            Path to collage image or None
        """
        try:
            if not images:
                return None
                
            # Load images
            loaded_images = []
            for img_path in images[:9]:  # Max 9 images
                try:
                    img = Image.open(img_path)
                    loaded_images.append(img)
                except:
                    continue
                    
            if not loaded_images:
                return None
                
            # Create collage based on layout
            if layout == "grid":
                collage = await self._create_grid_collage(loaded_images, size)
            elif layout == "horizontal":
                collage = await self._create_horizontal_collage(loaded_images, size)
            else:  # vertical
                collage = await self._create_vertical_collage(loaded_images, size)
                
            # Save collage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collage_{timestamp}.png"
            filepath = Path("data/cache/collages") / filename
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            collage.save(str(filepath), "PNG", quality=95)
            
            self.logger.info(f"🖼️ Created collage: {filename} with {len(loaded_images)} images")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating collage: {e}")
            return None
            
    async def _create_grid_collage(self, images: List[Image.Image], size: tuple) -> Image.Image:
        """Create grid collage"""
        rows = cols = int(len(images) ** 0.5)
        if rows * cols < len(images):
            cols += 1
            
        collage = Image.new('RGB', size, color=(255, 255, 255))
        
        # Calculate cell size
        cell_width = size[0] // cols
        cell_height = size[1] // rows
        
        # Place images
        for i, img in enumerate(images):
            row = i // cols
            col = i % cols
            
            # Resize image to fit cell
            img_resized = img.resize((cell_width - 10, cell_height - 10), 
                                   Image.Resampling.LANCZOS)
            
            # Calculate position
            x = col * cell_width + 5
            y = row * cell_height + 5
            
            # Paste image
            collage.paste(img_resized, (x, y))
            
        return collage
        
    async def _create_horizontal_collage(self, images: List[Image.Image], size: tuple) -> Image.Image:
        """Create horizontal collage"""
        collage = Image.new('RGB', size, color=(255, 255, 255))
        
        # Calculate image sizes
        img_width = size[0] // len(images)
        img_height = size[1]
        
        # Place images
        for i, img in enumerate(images):
            # Resize image
            img_resized = img.resize((img_width - 5, img_height - 10),
                                   Image.Resampling.LANCZOS)
            
            # Calculate position
            x = i * img_width + 2
            y = 5
            
            # Paste image
            collage.paste(img_resized, (x, y))
            
        return collage
        
    async def _create_vertical_collage(self, images: List[Image.Image], size: tuple) -> Image.Image:
        """Create vertical collage"""
        collage = Image.new('RGB', size, color=(255, 255, 255))
        
        # Calculate image sizes
        img_width = size[0]
        img_height = size[1] // len(images)
        
        # Place images
        for i, img in enumerate(images):
            # Resize image
            img_resized = img.resize((img_width - 10, img_height - 5),
                                   Image.Resampling.LANCZOS)
            
            # Calculate position
            x = 5
            y = i * img_height + 2
            
            # Paste image
            collage.paste(img_resized, (x, y))
            
        return collage
        
    async def apply_filter(self, image_path: str, filter_name: str) -> Optional[str]:
        """
        Apply filter to image
        
        Args:
            image_path: Path to image
            filter_name: Filter to apply
            
        Returns:
            Path to filtered image or None
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Apply filter
            if filter_name == "blur":
                img = img.filter(ImageFilter.GaussianBlur(2))
            elif filter_name == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            elif filter_name == "grayscale":
                img = ImageEnhance.Color(img).enhance(0)
            elif filter_name == "sepia":
                # Apply sepia tone
                width, height = img.size
                for x in range(width):
                    for y in range(height):
                        r, g, b = img.getpixel((x, y))
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        img.putpixel((x, y), (tr, tg, tb))
            elif filter_name == "brighten":
                img = ImageEnhance.Brightness(img).enhance(1.5)
            else:
                return None
                
            # Save filtered image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filtered_{filter_name}_{timestamp}.png"
            filepath = Path("data/cache/filters") / filename
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(filepath), "PNG", quality=95)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error applying filter: {e}")
            return None
            
    async def get_image_stats(self) -> Dict[str, Any]:
        """Get image engine statistics"""
        cache_dirs = [
            Path("data/cache/images"),
            Path("data/cache/collages"),
            Path("data/cache/filters")
        ]
        
        stats = {
            "fonts_loaded": len(self.fonts),
            "templates_loaded": len(self.templates),
            "image_cache": len(self.image_cache)
        }
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                dir_name = cache_dir.name
                files = list(cache_dir.glob("*.*"))
                stats[f"{dir_name}_count"] = len(files)
                if files:
                    total_size = sum(f.stat().st_size for f in files)
                    stats[f"{dir_name}_size_mb"] = total_size / (1024 * 1024)
                    
        return stats
        
    def _cleanup_image_cache(self, max_age_hours: int = 24):
        """Cleanup old image files"""
        cache_dirs = [
            Path("data/cache/images"),
            Path("data/cache/collages"),
            Path("data/cache/filters")
        ]
        
        current_time = datetime.now()
        
        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue
                
            for file in cache_dir.glob("*.*"):
                try:
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        file.unlink()
                except:
                    pass