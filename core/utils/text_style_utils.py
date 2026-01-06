"""
Text Style Utilities - Text styling and formatting
"""

from typing import List, Dict, Any

class TextStyleUtils:
    """Text styling and formatting utilities"""
    
    @staticmethod
    def apply_style(text: str, style: str = "bold") -> str:
        """Apply text style"""
        styles = {
            "bold": f"**{text}**",
            "italic": f"_{text}_",
            "underline": f"__{text}__",
            "strikethrough": f"~~{text}~~",
            "code": f"`{text}`",
            "pre": f"```{text}```",
            "spoiler": f"||{text}||"
        }
        
        return styles.get(style, text)
        
    @staticmethod
    def create_banner(text: str, 
                     width: int = 40,
                     border_char: str = "=") -> str:
        """Create text banner"""
        border = border_char * width
        centered = text.center(width)
        
        return f"{border}\n{centered}\n{border}"
        
    @staticmethod
    def create_table(headers: List[str], 
                    rows: List[List[str]],
                    padding: int = 2) -> str:
        """Create text table"""
        if not headers or not rows:
            return ""
            
        # Calculate column widths
        col_widths = []
        for i in range(len(headers)):
            column_data = [headers[i]] + [row[i] for row in rows if i < len(row)]
            max_width = max(len(str(item)) for item in column_data)
            col_widths.append(max_width + padding * 2)
            
        # Create separator
        separator = "+" + "+".join("-" * width for width in col_widths) + "+"
        
        # Create header row
        table = [separator]
        header_row = "|"
        for i, header in enumerate(headers):
            header_row += f" {header.center(col_widths[i] - 2)} |"
        table.append(header_row)
        table.append(separator)
        
        # Create data rows
        for row in rows:
            data_row = "|"
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    data_row += f" {str(cell).ljust(col_widths[i] - 2)} |"
                else:
                    data_row += f" {' '.ljust(col_widths[-1] - 2)} |"
            table.append(data_row)
            
        table.append(separator)
        return "\n".join(table)
        
    @staticmethod
    def progress_bar(current: int, 
                    total: int,
                    width: int = 20,
                    filled_char: str = "█",
                    empty_char: str = "░") -> str:
        """Create progress bar"""
        if total == 0:
            return empty_char * width
            
        progress = current / total
        filled_width = int(width * progress)
        
        bar = filled_char * filled_width + empty_char * (width - filled_width)
        percentage = int(progress * 100)
        
        return f"[{bar}] {percentage}%"
        
    @staticmethod
    def wrap_text(text: str, 
                 width: int = 80) -> str:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            if current_length + word_length + len(current_line) <= width:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return '\n'.join(lines)
        
    @staticmethod
    def justify_text(text: str,
                    width: int = 80) -> str:
        """Justify text to specified width"""
        lines = TextStyleUtils.wrap_text(text, width).split('\n')
        justified_lines = []
        
        for line in lines[:-1]:  # Don't justify last line
            words = line.split()
            if len(words) > 1:
                spaces_needed = width - len(line.replace(' ', ''))
                gaps = len(words) - 1
                
                if gaps > 0:
                    base_spaces = spaces_needed // gaps
                    extra_spaces = spaces_needed % gaps
                    
                    justified_line = words[0]
                    for i, word in enumerate(words[1:], 1):
                        spaces = base_spaces + (1 if i <= extra_spaces else 0)
                        justified_line += ' ' * spaces + word
                        
                    justified_lines.append(justified_line)
                else:
                    justified_lines.append(line)
            else:
                justified_lines.append(line)
                
        justified_lines.append(lines[-1])  # Add last line as is
        return '\n'.join(justified_lines)
        
    @staticmethod
    def create_bullet_list(items: List[str],
                          bullet_char: str = "•",
                          indent: int = 2) -> str:
        """Create bullet point list"""
        indent_spaces = ' ' * indent
        return '\n'.join(f"{indent_spaces}{bullet_char} {item}" for item in items)
        
    @staticmethod
    def create_numbered_list(items: List[str],
                            start: int = 1,
                            indent: int = 2) -> str:
        """Create numbered list"""
        indent_spaces = ' ' * indent
        lines = []
        
        for i, item in enumerate(items, start):
            lines.append(f"{indent_spaces}{i}. {item}")
            
        return '\n'.join(lines)
        
    @staticmethod
    def format_bytes(bytes_size: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
        
    @staticmethod
    def format_number(number: int) -> str:
        """Format number with commas"""
        return f"{number:,}"
        
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human readable"""
        if seconds < 60:
            return f"{seconds} সেকেন্ড"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} মিনিট"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ঘন্টা {minutes} মিনিট"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} দিন {hours} ঘন্টা"
            
    @staticmethod
    def create_quote(text: str,
                    author: str = "") -> str:
        """Create quoted text"""
        quote = f"\"{text}\""
        if author:
            quote += f"\n— {author}"
        return quote
        
    @staticmethod
    def create_header(text: str,
                     level: int = 1) -> str:
        """Create markdown style header"""
        if level < 1:
            level = 1
        elif level > 6:
            level = 6
            
        return f"{'#' * level} {text}"
        
    @staticmethod
    def create_footer(text: str,
                     width: int = 40,
                     border_char: str = "-") -> str:
        """Create footer"""
        border = border_char * width
        centered = text.center(width)
        return f"{border}\n{centered}"
        
    @staticmethod
    def add_padding(text: str,
                   padding: int = 1) -> str:
        """Add padding around text"""
        lines = text.split('\n')
        padded_lines = []
        
        for line in lines:
            padded_line = ' ' * padding + line + ' ' * padding
            padded_lines.append(padded_line)
            
        return '\n'.join(padded_lines)