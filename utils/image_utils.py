"""
Professional Image Processing System
For welcome images, collages, overlays, and graphics
"""

import os
import logging
from typing import List, Tuple, Optional, Union
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import requests
from io import BytesIO

from config import Config

logger = logging.getLogger(__name__)

class ImageUtils:
    """Professional image processing utilities"""
    
    def __init__(self):
        self.assets_dir = Config.ASSETS_DIR
        self.temp_dir = Config.TEMP_IMAGES
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Load fonts
        self._load_fonts()
        
        # Color schemes
        self.color_schemes = {
            "premium": {
                "primary": (148, 0, 211),  # Purple
                "secondary": (255, 105, 180),  # Pink
                "accent": (0, 191, 255),  # Sky Blue
                "text": (255, 255, 255),  # White
                "background": (25, 25, 35)  # Dark
            },
            "gradient": {
                "start": (131, 58, 180),  # Purple
                "end": (253, 29, 29),  # Red
                "middle": (252, 176, 69)  # Yellow
            },
            "modern": {
                "primary": (0, 150, 255),  # Blue
                "secondary": (0, 200, 83),  # Green
                "text": (240, 240, 240),  # Light Gray
                "background": (30, 30, 46)  # Dark Blue
            }
        }
    
    def _load_fonts(self):
        """Load fonts from assets"""
        try:
            # Main font
            font_path = Config.FONT_FILE
            if os.path.exists(font_path):
                self.main_font_large = ImageFont.truetype(font_path, 48)
                self.main_font_medium = ImageFont.truetype(font_path, 32)
                self.main_font_small = ImageFont.truetype(font_path, 24)
                self.main_font_xsmall = ImageFont.truetype(font_path, 18)
            else:
                logger.warning("Custom font not found, using default")
                self.main_font_large = ImageFont.load_default()
                self.main_font_medium = ImageFont.load_default()
                self.main_font_small = ImageFont.load_default()
                self.main_font_xsmall = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            self.main_font_large = ImageFont.load_default()
            self.main_font_medium = ImageFont.load_default()
            self.main_font_small = ImageFont.load_default()
            self.main_font_xsmall = ImageFont.load_default()
    
    def download_image(self, url: str) -> Optional[Image.Image]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def create_welcome_collage(self, 
                              profile_image: Union[str, Image.Image], 
                              group_image: Union[str, Image.Image],
                              user_info: Dict,
                              group_info: Dict) -> str:
        """
        Create professional welcome collage image
        """
        try:
            # Load or download images
            profile_img = self._load_image(profile_image, Config.DEFAULT_PROFILE)
            group_img = self._load_image(group_image, Config.DEFAULT_GROUP)
            
            # Resize images
            profile_img = self._resize_circular(profile_img, 200)
            group_img = self._resize_rounded(group_img, (150, 150), radius=20)
            
            # Create base image
            base_width = 800
            base_height = 600
            base = self._create_gradient_background(base_width, base_height)
            
            # Add overlay for text readability
            overlay = Image.new('RGBA', (base_width, base_height), (0, 0, 0, 128))
            base = Image.alpha_composite(base.convert('RGBA'), overlay)
            
            draw = ImageDraw.Draw(base)
            
            # Add profile image
            profile_x = base_width // 2 - 100
            profile_y = 50
            base.paste(profile_img, (profile_x, profile_y), profile_img)
            
            # Add group image
            group_x = base_width - 180
            group_y = 50
            base.paste(group_img, (group_x, group_y), group_img)
            
            # Add user name with gradient text
            user_name = user_info.get('first_name', 'User')
            self._draw_gradient_text(
                draw, 
                user_name, 
                (base_width // 2, 280), 
                self.main_font_large,
                self.color_schemes['gradient']['start'],
                self.color_schemes['gradient']['end']
            )
            
            # Add welcome text
            welcome_text = "গ্রুপে আপনাকে স্বাগতম! 🌸"
            draw.text(
                (base_width // 2, 330),
                welcome_text,
                font=self.main_font_medium,
                fill=self.color_schemes['premium']['secondary'],
                anchor="mm"
            )
            
            # Add user info box
            info_y = 380
            info_items = [
                f"🆔 ID: {user_info.get('user_id', 'N/A')}",
                f"⭐ র‍্যাংক: {user_info.get('rank', 'নতুন')}",
                f"💬 মেসেজ: {user_info.get('messages_count', 0)}",
                f"📅 যোগ: {user_info.get('join_date', datetime.now().strftime('%Y-%m-%d'))}"
            ]
            
            for i, item in enumerate(info_items):
                draw.text(
                    (100, info_y + i * 40),
                    item,
                    font=self.main_font_small,
                    fill=self.color_schemes['modern']['text']
                )
            
            # Add group info box
            group_info_y = 380
            group_items = [
                f"📋 গ্রুপ: {group_info.get('title', 'Unknown Group')}",
                f"👥 সদস্য: {group_info.get('member_count', 0)}",
                f"🏆 লেভেল: {group_info.get('level', 1)}",
                f"🔒 সিকিউরিটি: {group_info.get('security', 'High')}"
            ]
            
            for i, item in enumerate(group_items):
                draw.text(
                    (500, group_info_y + i * 40),
                    item,
                    font=self.main_font_small,
                    fill=self.color_schemes['modern']['text']
                )
            
            # Add decorative elements
            self._add_decorative_elements(base, draw)
            
            # Add footer
            footer_text = f"{Config.BOT_NAME} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            draw.text(
                (base_width // 2, base_height - 30),
                footer_text,
                font=self.main_font_xsmall,
                fill=self.color_schemes['premium']['accent'],
                anchor="mm"
            )
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.temp_dir, f"welcome_{timestamp}.jpg")
            base.save(output_path, "JPEG", quality=95)
            
            logger.info(f"Created welcome collage: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating welcome collage: {e}")
            return ""
    
    def create_profile_card(self, user_info: Dict) -> str:
        """
        Create professional profile card
        """
        try:
            width = 600
            height = 400
            
            # Create gradient background
            image = self._create_gradient_background(width, height, 
                                                     start_color=(30, 30, 46),
                                                     end_color=(15, 15, 25))
            
            draw = ImageDraw.Draw(image)
            
            # Add profile picture area
            profile_size = 120
            profile_x = 50
            profile_y = 50
            
            # Create circular profile placeholder
            profile_bg = Image.new('RGBA', (profile_size, profile_size), (0, 0, 0, 0))
            profile_draw = ImageDraw.Draw(profile_bg)
            profile_draw.ellipse([(0, 0), (profile_size, profile_size)], 
                                fill=self.color_schemes['premium']['primary'])
            
            # Add initial letter
            initial = user_info.get('first_name', 'U')[0].upper()
            profile_draw.text(
                (profile_size//2, profile_size//2),
                initial,
                font=self.main_font_large,
                fill=(255, 255, 255),
                anchor="mm"
            )
            
            image.paste(profile_bg, (profile_x, profile_y), profile_bg)
            
            # User info
            info_x = 200
            info_y = 60
            
            # Name with gradient
            name = user_info.get('first_name', 'User')
            if user_info.get('last_name'):
                name += f" {user_info['last_name']}"
            
            self._draw_gradient_text(
                draw,
                name,
                (info_x, info_y),
                self.main_font_large,
                self.color_schemes['gradient']['start'],
                self.color_schemes['gradient']['end']
            )
            
            # Username
            if user_info.get('username'):
                username = f"@{user_info['username']}"
                draw.text(
                    (info_x, info_y + 45),
                    username,
                    font=self.main_font_small,
                    fill=self.color_schemes['premium']['accent']
                )
            
            # User ID
            draw.text(
                (info_x, info_y + 75),
                f"🆔 ID: {user_info.get('user_id', 'N/A')}",
                font=self.main_font_small,
                fill=(200, 200, 200)
            )
            
            # Stats boxes
            stats_y = 180
            stats = [
                ("🏆 র‍্যাংক", user_info.get('rank', 'নতুন'), self.color_schemes['premium']['primary']),
                ("⭐ রিপুটেশন", str(user_info.get('reputation', 0)), self.color_schemes['premium']['secondary']),
                ("💬 মেসেজ", str(user_info.get('messages_count', 0)), self.color_schemes['modern']['primary']),
                ("📅 যোগদান", user_info.get('join_date', 'N/A')[:10], self.color_schemes['gradient']['middle'])
            ]
            
            for i, (label, value, color) in enumerate(stats):
                box_x = 50 + (i % 2) * 275
                box_y = stats_y + (i // 2) * 90
                
                # Draw stat box
                self._draw_rounded_rectangle(
                    draw,
                    (box_x, box_y, box_x + 250, box_y + 70),
                    radius=15,
                    fill=(color[0]//4, color[1]//4, color[2]//4, 100),
                    outline=color
                )
                
                # Draw label
                draw.text(
                    (box_x + 125, box_y + 20),
                    label,
                    font=self.main_font_small,
                    fill=(255, 255, 255),
                    anchor="mm"
                )
                
                # Draw value
                draw.text(
                    (box_x + 125, box_y + 45),
                    str(value),
                    font=self.main_font_medium,
                    fill=color,
                    anchor="mm"
                )
            
            # Add badges if available
            if user_info.get('badges'):
                badges_y = stats_y + 180
                badges_text = "🏅 ব্যাজ: " + ", ".join(user_info['badges'][:5])
                if len(user_info['badges']) > 5:
                    badges_text += f" +{len(user_info['badges'])-5} more"
                
                draw.text(
                    (50, badges_y),
                    badges_text,
                    font=self.main_font_small,
                    fill=self.color_schemes['premium']['accent']
                )
            
            # Footer
            footer_text = f"Generated by {Config.BOT_NAME} • {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            draw.text(
                (width // 2, height - 20),
                footer_text,
                font=self.main_font_xsmall,
                fill=(150, 150, 150),
                anchor="mm"
            )
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.temp_dir, f"profile_{user_info.get('user_id', 'unknown')}_{timestamp}.jpg")
            image.save(output_path, "JPEG", quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating profile card: {e}")
            return ""
    
    def create_group_stats_image(self, group_info: Dict) -> str:
        """
        Create group statistics image
        """
        try:
            width = 800
            height = 600
            
            # Create background
            image = self._create_gradient_background(width, height)
            draw = ImageDraw.Draw(image)
            
            # Group title
            title = group_info.get('title', 'Unknown Group')
            self._draw_shadow_text(
                draw,
                title,
                (width // 2, 50),
                self.main_font_large,
                self.color_schemes['premium']['secondary']
            )
            
            # Stats grid
            stats = [
                ("👥 মোট সদস্য", str(group_info.get('member_count', 0)), "members"),
                ("💬 মোট মেসেজ", str(group_info.get('total_messages', 0)), "messages"),
                ("🎉 ওয়েলকাম", str(group_info.get('welcome_count', 0)), "welcomes"),
                ("📊 একটিভিটি", f"{group_info.get('activity_score', 0)}%", "activity"),
                ("🛡️ সিকিউরিটি", group_info.get('security_level', 'Medium'), "security"),
                ("🏆 গ্রুপ লেভেল", str(group_info.get('level', 1)), "level"),
                ("📅 তৈরি হয়েছে", group_info.get('created_date', 'N/A'), "created"),
                ("🔄 শেষ আপডেট", group_info.get('last_activity', 'N/A'), "updated")
            ]
            
            for i, (label, value, _) in enumerate(stats):
                row = i // 4
                col = i % 4
                
                box_x = 50 + col * 175
                box_y = 150 + row * 120
                
                # Draw stat box
                self._draw_rounded_rectangle(
                    draw,
                    (box_x, box_y, box_x + 150, box_y + 100),
                    radius=10,
                    fill=(255, 255, 255, 30),
                    outline=self.color_schemes['premium']['accent']
                )
                
                # Draw label
                draw.text(
                    (box_x + 75, box_y + 25),
                    label,
                    font=self.main_font_small,
                    fill=(220, 220, 220),
                    anchor="mm"
                )
                
                # Draw value
                draw.text(
                    (box_x + 75, box_y + 60),
                    value,
                    font=self.main_font_medium,
                    fill=self.color_schemes['premium']['secondary'],
                    anchor="mm"
                )
            
            # Activity chart (simplified)
            self._draw_activity_chart(draw, group_info, width, height)
            
            # Footer
            footer_text = f"{Config.BOT_NAME} • Group Analytics • {datetime.now().strftime('%Y-%m-%d')}"
            draw.text(
                (width // 2, height - 30),
                footer_text,
                font=self.main_font_xsmall,
                fill=(150, 150, 150),
                anchor="mm"
            )
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.temp_dir, f"group_{group_info.get('id', 'unknown')}_{timestamp}.jpg")
            image.save(output_path, "JPEG", quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating group stats image: {e}")
            return ""
    
    # ============ HELPER METHODS ============
    
    def _load_image(self, image_source: Union[str, Image.Image], default_path: str) -> Image.Image:
        """Load image from various sources"""
        try:
            if isinstance(image_source, Image.Image):
                return image_source
            elif image_source.startswith(('http://', 'https://')):
                img = self.download_image(image_source)
                if img:
                    return img
            elif os.path.exists(image_source):
                return Image.open(image_source)
            
            # Use default image
            return Image.open(default_path)
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return Image.open(default_path)
    
    def _resize_circular(self, image: Image.Image, diameter: int) -> Image.Image:
        """Resize image to circular shape"""
        # Resize to square
        image = image.resize((diameter, diameter), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (diameter, diameter), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), (diameter, diameter)], fill=255)
        
        # Apply mask
        result = Image.new('RGBA', (diameter, diameter))
        result.paste(image, (0, 0), mask)
        
        # Add border
        border = Image.new('RGBA', (diameter + 10, diameter + 10), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse(
            [(0, 0), (diameter + 10, diameter + 10)],
            outline=self.color_schemes['premium']['secondary'],
            width=5
        )
        
        # Combine
        final = Image.new('RGBA', (diameter + 10, diameter + 10))
        final.paste(border, (0, 0), border)
        final.paste(result, (5, 5), result)
        
        return final
    
    def _resize_rounded(self, image: Image.Image, size: Tuple[int, int], radius: int = 20) -> Image.Image:
        """Resize image with rounded corners"""
        image = image.resize(size, Image.Resampling.LANCZOS)
        
        # Create rounded rectangle mask
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), size], radius=radius, fill=255)
        
        # Apply mask
        result = Image.new('RGBA', size)
        result.paste(image, (0, 0), mask)
        
        return result
    
    def _create_gradient_background(self, width: int, height: int, 
                                   start_color: Tuple[int, int, int] = None,
                                   end_color: Tuple[int, int, int] = None) -> Image.Image:
        """Create gradient background"""
        if start_color is None:
            start_color = self.color_schemes['gradient']['start']
        if end_color is None:
            end_color = self.color_schemes['gradient']['end']
        
        # Create base image
        base = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(base)
        
        # Draw gradient
        for y in range(height):
            # Calculate color at this position
            ratio = y / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add some noise for texture
        base = self._add_texture(base)
        
        return base
    
    def _add_texture(self, image: Image.Image) -> Image.Image:
        """Add subtle texture to image"""
        # Create noise overlay
        import random
        noise = Image.new('RGBA', image.size, (0, 0, 0, 0))
        noise_draw = ImageDraw.Draw(noise)
        
        for _ in range(1000):
            x = random.randint(0, image.width - 1)
            y = random.randint(0, image.height - 1)
            alpha = random.randint(5, 15)
            noise_draw.point((x, y), fill=(255, 255, 255, alpha))
        
        # Apply noise
        result = Image.alpha_composite(image.convert('RGBA'), noise)
        return result.convert('RGB')
    
    def _draw_gradient_text(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                           font: ImageFont.FreeTypeFont, start_color: Tuple[int, int, int],
                           end_color: Tuple[int, int, int]):
        """Draw text with gradient effect"""
        # Get text bounding box
        bbox = draw.textbbox(position, text, font=font, anchor="mm")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create temporary image for gradient text
        temp = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp)
        
        # Draw gradient on temp image
        for x in range(text_width):
            ratio = x / text_width
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            
            temp_draw.line([(x, 0), (x, text_height)], fill=(r, g, b, 255))
        
        # Create text mask
        mask = Image.new('L', (text_width, text_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.text((0, 0), text, font=font, fill=255)
        
        # Apply mask to gradient
        gradient_text = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        gradient_text.paste(temp, (0, 0), mask)
        
        # Paste onto main image
        main_image = draw.im
        x_pos = position[0] - text_width // 2
        y_pos = position[1] - text_height // 2
        main_image.paste(gradient_text, (x_pos, y_pos), gradient_text)
    
    def _draw_shadow_text(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                         font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        """Draw text with shadow effect"""
        # Draw shadow
        shadow_pos = (position[0] + 2, position[1] + 2)
        draw.text(shadow_pos, text, font=font, fill=(0, 0, 0, 128), anchor="mm")
        
        # Draw main text
        draw.text(position, text, font=font, fill=color, anchor="mm")
    
    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw, coordinates: Tuple[int, int, int, int],
                               radius: int = 10, fill: Tuple[int, int, int, int] = None,
                               outline: Tuple[int, int, int] = None, width: int = 2):
        """Draw rounded rectangle with optional transparency"""
        x1, y1, x2, y2 = coordinates
        
        if fill:
            # Draw filled rounded rectangle
            draw.rounded_rectangle(coordinates, radius=radius, fill=fill)
        
        if outline:
            # Draw outline
            draw.rounded_rectangle(coordinates, radius=radius, outline=outline, width=width)
    
    def _add_decorative_elements(self, image: Image.Image, draw: ImageDraw.Draw):
        """Add decorative elements to image"""
        width, height = image.size
        
        # Add corner decorations
        decor_color = self.color_schemes['premium']['accent']
        
        # Top-left corner
        draw.ellipse([(10, 10), (30, 30)], outline=decor_color, width=2)
        draw.ellipse([(20, 20), (40, 40)], outline=decor_color, width=2)
        
        # Top-right corner
        draw.ellipse([(width - 30, 10), (width - 10, 30)], outline=decor_color, width=2)
        draw.ellipse([(width - 40, 20), (width - 20, 40)], outline=decor_color, width=2)
        
        # Bottom-left corner
        draw.ellipse([(10, height - 30), (30, height - 10)], outline=decor_color, width=2)
        draw.ellipse([(20, height - 40), (40, height - 20)], outline=decor_color, width=2)
        
        # Bottom-right corner
        draw.ellipse([(width - 30, height - 30), (width - 10, height - 10)], outline=decor_color, width=2)
        draw.ellipse([(width - 40, height - 40), (width - 20, height - 20)], outline=decor_color, width=2)
    
    def _draw_activity_chart(self, draw: ImageDraw.Draw, group_info: Dict, width: int, height: int):
        """Draw simplified activity chart"""
        # This is a simplified version
        # In production, you'd use actual data
        
        chart_x = 50
        chart_y = height - 150
        chart_width = width - 100
        chart_height = 100
        
        # Draw chart background
        self._draw_rounded_rectangle(
            draw,
            (chart_x, chart_y, chart_x + chart_width, chart_y + chart_height),
            radius=10,
            fill=(255, 255, 255, 30)
        )
        
        # Draw chart title
        draw.text(
            (chart_x + chart_width // 2, chart_y - 20),
            "📊 সাপ্তাহিক একটিভিটি",
            font=self.main_font_small,
            fill=(220, 220, 220),
            anchor="mm"
        )
        
        # Draw sample data (in production, use real data)
        days = ["সোম", "মঙ্গল", "বুধ", "বৃহ", "শুক্র", "শনি", "রবি"]
        sample_data = [80, 65, 90, 75, 85, 60, 95]  # Sample percentages
        
        bar_width = chart_width // len(days) - 10
        
        for i, (day, value) in enumerate(zip(days, sample_data)):
            bar_x = chart_x + i * (bar_width + 10) + 5
            bar_height = (value / 100) * chart_height
            bar_y = chart_y + chart_height - bar_height
            
            # Draw bar
            color = self.color_schemes['premium']['primary']
            draw.rectangle(
                [bar_x, bar_y, bar_x + bar_width, chart_y + chart_height],
                fill=color + (150,)  # With alpha
            )
            
            # Draw day label
            draw.text(
                (bar_x + bar_width // 2, chart_y + chart_height + 15),
                day,
                font=self.main_font_xsmall,
                fill=(200, 200, 200),
                anchor="mm"
            )
            
            # Draw value
            draw.text(
                (bar_x + bar_width // 2, bar_y - 10),
                f"{value}%",
                font=self.main_font_xsmall,
                fill=color,
                anchor="mm"
            )
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Cleanup temporary image files"""
        try:
            import time
            current_time = time.time()
            cutoff = older_than_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if current_time - file_time > cutoff:
                        os.remove(filepath)
                        logger.debug(f"Cleaned up temp file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")