"""
Collage Engine - Advanced image collage creation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random

from core.utils.image_utils import download_image, resize_image

class CollageEngine:
    """Advanced collage creation engine"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_collage")
        self.json_loader = json_loader
        self.collage_templates = {}
        self.collage_cache = {}
        
    async def initialize(self):
        """Initialize collage engine"""
        self.logger.info("🖼️ Initializing collage engine...")
        await self._load_collage_templates()
        
    async def _load_collage_templates(self):
        """Load collage templates"""
        templates_config = await self.json_loader.load("config/collage_templates.json")
        self.collage_templates = templates_config.get("templates", {})
        
        if not self.collage_templates:
            # Create default templates
            self.collage_templates = {
                "welcome_grid": {
                    "type": "grid",
                    "size": (1200, 800),
                    "background": "assets/bg.jpg",
                    "layout": {
                        "rows": 2,
                        "cols": 3,
                        "spacing": 10,
                        "padding": 20
                    },
                    "text": {
                        "title": "গ্রুপ সদস্যগণ",
                        "font_size": 36,
                        "font_color": "#FFFFFF"
                    }
                },
                "profile_mosaic": {
                    "type": "mosaic",
                    "size": (1000, 1000),
                    "background": "gradient",
                    "shape": "circle",
                    "overlay": True
                },
                "story_highlight": {
                    "type": "story",
                    "size": (1080, 1920),
                    "background": "blurred",
                    "layout": "vertical",
                    "effects": ["shadow", "border"]
                }
            }
            
        self.logger.info(f"📝 Loaded {len(self.collage_templates)} collage templates")
        
    async def create_collage(self, images: List[str], template_name: str = "welcome_grid",
                           title: str = "", subtitle: str = "") -> Optional[str]:
        """
        Create collage using template
        
        Args:
            images: List of image URLs or paths
            template_name: Template to use
            title: Collage title
            subtitle: Collage subtitle
            
        Returns:
            Path to collage image or None
        """
        try:
            if not images:
                self.logger.warning("⚠️ No images provided for collage")
                return None
                
            # Get template
            template = self.collage_templates.get(template_name, {})
            if not template:
                self.logger.warning(f"⚠️ Template not found: {template_name}")
                template = self.collage_templates.get("welcome_grid", {})
                
            # Download images
            downloaded_images = await self._download_images(images)
            if not downloaded_images:
                self.logger.error("❌ No images could be downloaded")
                return None
                
            # Create cache key
            cache_key = self._create_cache_key(images, template_name, title, subtitle)
            if cache_key in self.collage_cache:
                cached_path = self.collage_cache[cache_key]
                if Path(cached_path).exists():
                    self.logger.debug(f"🎨 Using cached collage: {cache_key}")
                    return cached_path
                    
            # Create collage based on template type
            collage_type = template.get("type", "grid")
            
            if collage_type == "grid":
                collage_image = await self._create_grid_collage(downloaded_images, template)
            elif collage_type == "mosaic":
                collage_image = await self._create_mosaic_collage(downloaded_images, template)
            elif collage_type == "story":
                collage_image = await self._create_story_collage(downloaded_images, template)
            elif collage_type == "circle":
                collage_image = await self._create_circle_collage(downloaded_images, template)
            elif collage_type == "heart":
                collage_image = await self._create_heart_collage(downloaded_images, template)
            else:
                collage_image = await self._create_grid_collage(downloaded_images, template)
                
            # Add title and subtitle if provided
            if title or subtitle:
                collage_image = await self._add_text_to_collage(collage_image, title, subtitle, template)
                
            # Apply effects
            collage_image = await self._apply_effects(collage_image, template)
            
            # Save collage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collage_{template_name}_{timestamp}.png"
            filepath = Path("data/cache/collages") / filename
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            collage_image.save(str(filepath), "PNG", quality=95)
            
            # Cache the collage
            self.collage_cache[cache_key] = str(filepath)
            
            # Cleanup old cache
            self._cleanup_collage_cache()
            
            self.logger.info(f"🎨 Created collage: {filename} with {len(downloaded_images)} images")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating collage: {e}")
            return None
            
    async def _download_images(self, image_urls: List[str]) -> List[Image.Image]:
        """Download and load images"""
        downloaded = []
        
        for url in image_urls[:12]:  # Limit to 12 images
            try:
                if url.startswith(('http://', 'https://')):
                    # Download from URL
                    image_data = await download_image(url)
                    if image_data:
                        img = Image.open(image_data)
                        downloaded.append(img)
                else:
                    # Load from local path
                    if Path(url).exists():
                        img = Image.open(url)
                        downloaded.append(img)
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load image {url}: {e}")
                continue
                
        return downloaded
        
    async def _create_grid_collage(self, images: List[Image.Image], 
                                 template: Dict) -> Image.Image:
        """Create grid collage"""
        # Get template parameters
        size = template.get("size", (1200, 800))
        layout = template.get("layout", {})
        rows = layout.get("rows", 2)
        cols = layout.get("cols", 3)
        spacing = layout.get("spacing", 10)
        padding = layout.get("padding", 20)
        
        # Create background
        bg_color = template.get("background_color", (41, 128, 185))
        if template.get("background") == "gradient":
            collage = self._create_gradient_background(size, bg_color)
        else:
            collage = Image.new('RGB', size, color=bg_color)
            
        # Calculate cell size
        content_width = size[0] - 2 * padding
        content_height = size[1] - 2 * padding
        cell_width = (content_width - (cols - 1) * spacing) // cols
        cell_height = (content_height - (rows - 1) * spacing) // rows
        
        # Place images
        for i, img in enumerate(images[:rows * cols]):
            row = i // cols
            col = i % cols
            
            # Calculate position
            x = padding + col * (cell_width + spacing)
            y = padding + row * (cell_height + spacing)
            
            # Resize image to fit cell
            img_resized = await resize_image(img, (cell_width, cell_height))
            
            # Apply shape if specified
            if template.get("shape") == "circle":
                img_resized = self._make_circular(img_resized)
            elif template.get("shape") == "rounded":
                img_resized = self._make_rounded(img_resized, radius=20)
                
            # Paste image
            collage.paste(img_resized, (x, y), img_resized if img_resized.mode == 'RGBA' else None)
            
        return collage
        
    async def _create_mosaic_collage(self, images: List[Image.Image], 
                                   template: Dict) -> Image.Image:
        """Create mosaic collage"""
        size = template.get("size", (1000, 1000))
        
        # Create base image
        mosaic = Image.new('RGB', size, (255, 255, 255))
        
        # Calculate grid based on number of images
        num_images = len(images)
        if num_images <= 4:
            grid_size = 2
        elif num_images <= 9:
            grid_size = 3
        elif num_images <= 16:
            grid_size = 4
        else:
            grid_size = 5
            
        cell_size = size[0] // grid_size
        
        # Place images in mosaic pattern
        for i, img in enumerate(images[:grid_size * grid_size]):
            row = i // grid_size
            col = i % grid_size
            
            # Resize image
            img_resized = await resize_image(img, (cell_size, cell_size))
            
            # Apply random rotation for artistic effect
            if random.random() > 0.7:
                angle = random.randint(-15, 15)
                img_resized = img_resized.rotate(angle, expand=True)
                img_resized = await resize_image(img_resized, (cell_size, cell_size))
                
            # Calculate position with slight randomness
            x_offset = random.randint(-10, 10) if random.random() > 0.5 else 0
            y_offset = random.randint(-10, 10) if random.random() > 0.5 else 0
            
            x = col * cell_size + x_offset
            y = row * cell_size + y_offset
            
            # Ensure within bounds
            x = max(0, min(x, size[0] - cell_size))
            y = max(0, min(y, size[1] - cell_size))
            
            # Paste image
            mosaic.paste(img_resized, (x, y))
            
        # Apply overlay if specified
        if template.get("overlay"):
            overlay = self._create_overlay(size, opacity=0.2)
            mosaic = Image.alpha_composite(
                mosaic.convert('RGBA'), 
                overlay
            )
            
        return mosaic.convert('RGB')
        
    async def _create_story_collage(self, images: List[Image.Image], 
                                  template: Dict) -> Image.Image:
        """Create story-style collage (vertical)"""
        size = template.get("size", (1080, 1920))
        
        # Create background
        if template.get("background") == "blurred" and images:
            # Use first image as blurred background
            bg_img = await resize_image(images[0], size)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(15))
            story = bg_img
        else:
            story = Image.new('RGB', size, (30, 30, 30))
            
        # Layout images vertically
        img_height = size[1] // len(images) if len(images) > 0 else size[1]
        img_height = min(img_height, 600)  # Max height per image
        
        for i, img in enumerate(images):
            # Resize image
            img_resized = await resize_image(img, (size[0] - 100, img_height - 50))
            
            # Apply effects
            if "shadow" in template.get("effects", []):
                img_resized = self._add_shadow(img_resized)
            if "border" in template.get("effects", []):
                img_resized = self._add_border(img_resized, color=(255, 255, 255), width=5)
                
            # Calculate position
            x = (size[0] - img_resized.width) // 2
            y = 100 + i * (img_height)
            
            # Paste image
            story.paste(img_resized, (x, y), img_resized if img_resized.mode == 'RGBA' else None)
            
        return story
        
    async def _create_circle_collage(self, images: List[Image.Image], 
                                   template: Dict) -> Image.Image:
        """Create circular arrangement collage"""
        size = template.get("size", (1000, 1000))
        
        # Create background
        collage = Image.new('RGB', size, (240, 240, 240))
        draw = ImageDraw.Draw(collage)
        
        # Calculate circle parameters
        center_x, center_y = size[0] // 2, size[1] // 2
        radius = min(size) // 2 - 100
        
        # Arrange images in circle
        num_images = len(images)
        for i, img in enumerate(images):
            # Calculate position on circle
            angle = 2 * math.pi * i / num_images
            img_x = center_x + int(radius * math.cos(angle)) - 75
            img_y = center_y + int(radius * math.sin(angle)) - 75
            
            # Resize image to circle
            img_resized = await resize_image(img, (150, 150))
            img_resized = self._make_circular(img_resized)
            
            # Paste image
            collage.paste(img_resized, (img_x, img_y), img_resized)
            
        # Draw connecting lines
        for i in range(num_images):
            angle1 = 2 * math.pi * i / num_images
            angle2 = 2 * math.pi * ((i + 1) % num_images) / num_images
            
            x1 = center_x + int(radius * math.cos(angle1))
            y1 = center_y + int(radius * math.sin(angle1))
            x2 = center_x + int(radius * math.cos(angle2))
            y2 = center_y + int(radius * math.sin(angle2))
            
            draw.line([(x1, y1), (x2, y2)], fill=(180, 180, 180), width=3)
            
        return collage
        
    async def _create_heart_collage(self, images: List[Image.Image], 
                                  template: Dict) -> Image.Image:
        """Create heart-shaped collage"""
        size = template.get("size", (1000, 1000))
        
        # Create background
        collage = Image.new('RGB', size, (255, 220, 220))
        
        # Heart coordinates (simplified)
        heart_positions = [
            (500, 300), (400, 350), (600, 350),
            (350, 400), (450, 400), (550, 400), (650, 400),
            (300, 450), (400, 450), (500, 450), (600, 450), (700, 450),
            (350, 500), (450, 500), (550, 500), (650, 500),
            (400, 550), (600, 550),
            (500, 600)
        ]
        
        # Place images in heart shape
        for i, (pos_x, pos_y) in enumerate(heart_positions[:len(images)]):
            if i < len(images):
                img = images[i]
                img_resized = await resize_image(img, (80, 80))
                img_resized = self._make_circular(img_resized)
                
                collage.paste(img_resized, (pos_x - 40, pos_y - 40), img_resized)
                
        return collage
        
    def _make_circular(self, image: Image.Image) -> Image.Image:
        """Convert image to circular shape"""
        # Create circular mask
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + image.size, fill=255)
        
        # Apply mask
        output = Image.new('RGBA', image.size)
        output.paste(image, (0, 0), mask)
        return output
        
    def _make_rounded(self, image: Image.Image, radius: int = 20) -> Image.Image:
        """Add rounded corners to image"""
        circle = Image.new('L', (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
        
        alpha = Image.new('L', image.size, 255)
        w, h = image.size
        
        # Apply rounded corners
        alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
        alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
        alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
        alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
        
        image.putalpha(alpha)
        return image
        
    def _create_gradient_background(self, size: Tuple[int, int], 
                                  base_color: Tuple[int, int, int]) -> Image.Image:
        """Create gradient background"""
        bg = Image.new('RGB', size, base_color)
        draw = ImageDraw.Draw(bg)
        
        # Draw gradient effect
        for y in range(size[1]):
            # Calculate color variation
            factor = y / size[1]
            r = int(base_color[0] * (1 - factor) + base_color[0] * 0.7 * factor)
            g = int(base_color[1] * (1 - factor) + base_color[1] * 0.7 * factor)
            b = int(base_color[2] * (1 - factor) + base_color[2] * 0.7 * factor)
            
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
            
        return bg
        
    def _add_shadow(self, image: Image.Image, offset: Tuple[int, int] = (5, 5),
                   shadow_color: Tuple[int, int, int] = (0, 0, 0, 100)) -> Image.Image:
        """Add shadow to image"""
        shadow = Image.new('RGBA', 
                          (image.width + abs(offset[0]), 
                           image.height + abs(offset[1])), 
                          (0, 0, 0, 0))
        
        shadow.paste((*shadow_color[:3], shadow_color[3] if len(shadow_color) > 3 else 100), 
                    [max(offset[0], 0), max(offset[1], 0), 
                     max(offset[0], 0) + image.width, 
                     max(offset[1], 0) + image.height])
        
        shadow = shadow.filter(ImageFilter.GaussianBlur(3))
        shadow.paste(image, (max(-offset[0], 0), max(-offset[1], 0)), image)
        
        return shadow
        
    def _add_border(self, image: Image.Image, color: Tuple[int, int, int] = (255, 255, 255),
                   width: int = 5) -> Image.Image:
        """Add border to image"""
        bordered = Image.new('RGBA', 
                            (image.width + width * 2, 
                             image.height + width * 2), 
                            color)
        bordered.paste(image, (width, width), image)
        return bordered
        
    def _create_overlay(self, size: Tuple[int, int], opacity: float = 0.2) -> Image.Image:
        """Create semi-transparent overlay"""
        overlay = Image.new('RGBA', size, (0, 0, 0, int(255 * opacity)))
        return overlay
        
    async def _add_text_to_collage(self, collage: Image.Image, title: str, 
                                 subtitle: str, template: Dict) -> Image.Image:
        """Add text to collage"""
        draw = ImageDraw.Draw(collage)
        
        # Get font settings
        font_settings = template.get("text", {})
        title_font_size = font_settings.get("title_font_size", 48)
        subtitle_font_size = font_settings.get("subtitle_font_size", 32)
        font_color = font_settings.get("font_color", "#FFFFFF")
        
        # Convert hex color to RGB
        if isinstance(font_color, str) and font_color.startswith('#'):
            font_color = tuple(int(font_color[i:i+2], 16) for i in (1, 3, 5))
            
        try:
            # Try to load font
            font_path = "assets/fonts/kalpurush.ttf"
            title_font = ImageFont.truetype(font_path, title_font_size)
            subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)
        except:
            # Use default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            
        # Add title
        if title:
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_x = (collage.width - title_width) // 2
            title_y = 50
            
            # Draw text with shadow
            shadow_offset = 2
            draw.text((title_x + shadow_offset, title_y + shadow_offset), 
                     title, font=title_font, fill=(0, 0, 0, 150))
            draw.text((title_x, title_y), title, font=title_font, fill=font_color)
            
        # Add subtitle
        if subtitle:
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
            
            subtitle_x = (collage.width - subtitle_width) // 2
            subtitle_y = collage.height - subtitle_height - 50
            
            draw.text((subtitle_x + 1, subtitle_y + 1), 
                     subtitle, font=subtitle_font, fill=(0, 0, 0, 150))
            draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=font_color)
            
        return collage
        
    async def _apply_effects(self, collage: Image.Image, template: Dict) -> Image.Image:
        """Apply effects to collage"""
        effects = template.get("effects", [])
        
        if "vignette" in effects:
            collage = self._apply_vignette(collage)
        if "noise" in effects:
            collage = self._apply_noise(collage)
        if "blur_edges" in effects:
            collage = self._apply_blur_edges(collage)
            
        return collage
        
    def _apply_vignette(self, image: Image.Image, intensity: float = 0.7) -> Image.Image:
        """Apply vignette effect"""
        width, height = image.size
        
        # Create vignette mask
        vignette = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(vignette)
        
        # Draw radial gradient
        center_x, center_y = width // 2, height // 2
        max_radius = max(center_x, center_y)
        
        for radius in range(max_radius, 0, -10):
            alpha = int(255 * (1 - intensity * (radius / max_radius)))
            draw.ellipse([center_x - radius, center_y - radius,
                         center_x + radius, center_y + radius],
                        fill=alpha)
            
        # Apply vignette
        image.putalpha(vignette)
        return image
        
    def _apply_noise(self, image: Image.Image, intensity: int = 10) -> Image.Image:
        """Apply noise/grain effect"""
        import random
        
        noise = Image.new('RGBA', image.size, (0, 0, 0, 0))
        pixels = noise.load()
        
        for x in range(image.width):
            for y in range(image.height):
                if random.random() < 0.1:  # 10% pixels get noise
                    value = random.randint(-intensity, intensity)
                    pixels[x, y] = (value, value, value, 30)
                    
        return Image.alpha_composite(image.convert('RGBA'), noise).convert('RGB')
        
    def _apply_blur_edges(self, image: Image.Image, blur_radius: int = 10) -> Image.Image:
        """Apply blur to edges"""
        # Create mask for edges
        mask = Image.new('L', image.size, 255)
        draw = ImageDraw.Draw(mask)
        
        # Clear center area
        center_width = image.width * 0.8
        center_height = image.height * 0.8
        center_x = (image.width - center_width) // 2
        center_y = (image.height - center_height) // 2
        
        draw.rectangle([center_x, center_y, 
                       center_x + center_width, 
                       center_y + center_height], fill=0)
        
        # Apply blur to masked areas
        blurred = image.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Composite with original
        result = Image.composite(image, blurred, mask)
        return result
        
    def _create_cache_key(self, images: List[str], template_name: str,
                         title: str, subtitle: str) -> str:
        """Create cache key for collage"""
        import hashlib
        
        key_data = {
            "images": images[:5],  # First 5 images for key
            "template": template_name,
            "title": title,
            "subtitle": subtitle
        }
        
        import json
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
        
    def _cleanup_collage_cache(self, max_files: int = 50):
        """Cleanup old collage files"""
        cache_dir = Path("data/cache/collages")
        if not cache_dir.exists():
            return
            
        # Get all collage files sorted by modification time
        collage_files = sorted(cache_dir.glob("*.png"), 
                             key=lambda x: x.stat().st_mtime, 
                             reverse=True)
                             
        # Remove old files
        if len(collage_files) > max_files:
            files_to_remove = collage_files[max_files:]
            for file in files_to_remove:
                try:
                    file.unlink()
                    # Remove from cache dict
                    keys_to_remove = [k for k, v in self.collage_cache.items() 
                                     if v == str(file)]
                    for key in keys_to_remove:
                        del self.collage_cache[key]
                except:
                    pass
                    
            self.logger.info(f"🧹 Cleaned up {len(files_to_remove)} old collage files")
            
    async def get_collage_stats(self) -> Dict[str, Any]:
        """Get collage engine statistics"""
        cache_dir = Path("data/cache/collages")
        total_files = len(list(cache_dir.glob("*.png"))) if cache_dir.exists() else 0
        
        return {
            "templates_loaded": len(self.collage_templates),
            "cache_size": len(self.collage_cache),
            "total_collage_files": total_files,
            "template_types": list(set(t.get("type", "grid") for t in self.collage_templates.values()))
        }
        
    async def create_template(self, template_name: str, template_config: Dict):
        """
        Create new collage template
        
        Args:
            template_name: Name of template
            template_config: Template configuration
        """
        self.collage_templates[template_name] = template_config
        
        # Save to config
        try:
            templates_config = await self.json_loader.load("config/collage_templates.json")
            templates_config["templates"] = self.collage_templates
            await self.json_loader.save("config/collage_templates.json", templates_config)
            
            self.logger.info(f"📝 Created new template: {template_name}")
        except Exception as e:
            self.logger.error(f"❌ Error saving template: {e}")