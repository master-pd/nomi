"""
File Utilities - File operations and management
"""

import os
import shutil
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import hashlib
import aiofiles
import aiofiles.os

class FileUtils:
    """File operations utility"""
    
    @staticmethod
    async def ensure_directory(directory: Union[str, Path]) -> bool:
        """Ensure directory exists, create if not"""
        try:
            path = Path(directory)
            await aiofiles.os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
            
    @staticmethod
    async def read_file(filepath: Union[str, Path], 
                       encoding: str = "utf-8") -> Optional[str]:
        """Read file content asynchronously"""
        try:
            async with aiofiles.open(filepath, 'r', encoding=encoding) as f:
                return await f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None
            
    @staticmethod
    async def write_file(filepath: Union[str, Path], 
                        content: str, 
                        encoding: str = "utf-8") -> bool:
        """Write content to file asynchronously"""
        try:
            # Ensure directory exists
            await FileUtils.ensure_directory(Path(filepath).parent)
            
            async with aiofiles.open(filepath, 'w', encoding=encoding) as f:
                await f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {filepath}: {e}")
            return False
            
    @staticmethod
    async def read_json(filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Read JSON file"""
        content = await FileUtils.read_file(filepath)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON {filepath}: {e}")
        return None
        
    @staticmethod
    async def write_json(filepath: Union[str, Path], 
                        data: Dict[str, Any],
                        indent: int = 2,
                        ensure_ascii: bool = False) -> bool:
        """Write data to JSON file"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
            return await FileUtils.write_file(filepath, content)
        except Exception as e:
            print(f"Error writing JSON {filepath}: {e}")
            return False
            
    @staticmethod
    async def read_pickle(filepath: Union[str, Path]) -> Any:
        """Read pickle file"""
        try:
            async with aiofiles.open(filepath, 'rb') as f:
                content = await f.read()
                return pickle.loads(content)
        except Exception as e:
            print(f"Error reading pickle {filepath}: {e}")
            return None
            
    @staticmethod
    async def write_pickle(filepath: Union[str, Path], data: Any) -> bool:
        """Write data to pickle file"""
        try:
            await FileUtils.ensure_directory(Path(filepath).parent)
            
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(pickle.dumps(data))
            return True
        except Exception as e:
            print(f"Error writing pickle {filepath}: {e}")
            return False
            
    @staticmethod
    async def list_files(directory: Union[str, Path], 
                        pattern: str = "*") -> List[Path]:
        """List files in directory matching pattern"""
        try:
            path = Path(directory)
            if not await aiofiles.os.path.exists(path):
                return []
                
            files = []
            for file_path in path.glob(pattern):
                if await aiofiles.os.path.isfile(file_path):
                    files.append(file_path)
            return files
        except Exception as e:
            print(f"Error listing files in {directory}: {e}")
            return []
            
    @staticmethod
    async def list_directories(directory: Union[str, Path]) -> List[Path]:
        """List subdirectories in directory"""
        try:
            path = Path(directory)
            if not await aiofiles.os.path.exists(path):
                return []
                
            dirs = []
            for item in path.iterdir():
                if await aiofiles.os.path.isdir(item):
                    dirs.append(item)
            return dirs
        except Exception as e:
            print(f"Error listing directories in {directory}: {e}")
            return []
            
    @staticmethod
    async def delete_file(filepath: Union[str, Path]) -> bool:
        """Delete file"""
        try:
            if await aiofiles.os.path.exists(filepath):
                await aiofiles.os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
        return False
        
    @staticmethod
    async def delete_directory(directory: Union[str, Path]) -> bool:
        """Delete directory recursively"""
        try:
            if await aiofiles.os.path.exists(directory):
                shutil.rmtree(directory)
                return True
        except Exception as e:
            print(f"Error deleting directory {directory}: {e}")
        return False
        
    @staticmethod
    async def copy_file(src: Union[str, Path], 
                       dst: Union[str, Path]) -> bool:
        """Copy file"""
        try:
            await FileUtils.ensure_directory(Path(dst).parent)
            
            # For large files, copy in chunks
            async with aiofiles.open(src, 'rb') as f_src:
                async with aiofiles.open(dst, 'wb') as f_dst:
                    while True:
                        chunk = await f_src.read(8192)
                        if not chunk:
                            break
                        await f_dst.write(chunk)
            return True
        except Exception as e:
            print(f"Error copying file {src} to {dst}: {e}")
            return False
            
    @staticmethod
    async def move_file(src: Union[str, Path], 
                       dst: Union[str, Path]) -> bool:
        """Move/rename file"""
        try:
            await FileUtils.ensure_directory(Path(dst).parent)
            await aiofiles.os.rename(src, dst)
            return True
        except Exception as e:
            print(f"Error moving file {src} to {dst}: {e}")
            return False
            
    @staticmethod
    async def get_file_size(filepath: Union[str, Path]) -> Optional[int]:
        """Get file size in bytes"""
        try:
            if await aiofiles.os.path.exists(filepath):
                stat = await aiofiles.os.stat(filepath)
                return stat.st_size
        except:
            pass
        return None
        
    @staticmethod
    async def get_file_hash(filepath: Union[str, Path], 
                          algorithm: str = "md5") -> Optional[str]:
        """Calculate file hash"""
        try:
            if not await aiofiles.os.path.exists(filepath):
                return None
                
            hash_func = hashlib.new(algorithm)
            
            async with aiofiles.open(filepath, 'rb') as f:
                while True:
                    chunk = await f.read(8192)
                    if not chunk:
                        break
                    hash_func.update(chunk)
                    
            return hash_func.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {filepath}: {e}")
            return None
            
    @staticmethod
    async def file_exists(filepath: Union[str, Path]) -> bool:
        """Check if file exists"""
        try:
            return await aiofiles.os.path.exists(filepath) and \
                   await aiofiles.os.path.isfile(filepath)
        except:
            return False
            
    @staticmethod
    async def directory_exists(directory: Union[str, Path]) -> bool:
        """Check if directory exists"""
        try:
            return await aiofiles.os.path.exists(directory) and \
                   await aiofiles.os.path.isdir(directory)
        except:
            return False
            
    @staticmethod
    async def get_file_info(filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            if not await FileUtils.file_exists(filepath):
                return None
                
            stat = await aiofiles.os.stat(filepath)
            path = Path(filepath)
            
            return {
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": True,
                "is_dir": False,
                "absolute_path": str(path.absolute())
            }
        except Exception as e:
            print(f"Error getting file info for {filepath}: {e}")
            return None
            
    @staticmethod
    async def get_directory_size(directory: Union[str, Path]) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = Path(root) / file
                    size = await FileUtils.get_file_size(filepath)
                    if size:
                        total_size += size
        except:
            pass
            
        return total_size
        
    @staticmethod
    async def find_files_by_extension(directory: Union[str, Path],
                                    extension: str) -> List[Path]:
        """Find files by extension"""
        if not extension.startswith('.'):
            extension = f'.{extension}'
            
        files = await FileUtils.list_files(directory, f"*{extension}")
        return files
        
    @staticmethod
    async def create_temp_file(content: str = "",
                             extension: str = ".tmp") -> Optional[Path]:
        """Create temporary file"""
        import tempfile
        
        try:
            # Create temp directory if not exists
            temp_dir = Path("temp")
            await FileUtils.ensure_directory(temp_dir)
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                dir=temp_dir,
                suffix=extension,
                delete=False,
                encoding='utf-8'
            )
            
            if content:
                temp_file.write(content)
            temp_file.close()
            
            return Path(temp_file.name)
        except Exception as e:
            print(f"Error creating temp file: {e}")
            return None
            
    @staticmethod
    async def cleanup_old_files(directory: Union[str, Path],
                              max_age_days: int = 7) -> int:
        """Cleanup files older than specified days"""
        import time
        from datetime import datetime, timedelta
        
        cutoff_time = time.time() - (max_age_days * 86400)
        deleted_count = 0
        
        files = await FileUtils.list_files(directory)
        for filepath in files:
            try:
                stat = await aiofiles.os.stat(filepath)
                if stat.st_mtime < cutoff_time:
                    if await FileUtils.delete_file(filepath):
                        deleted_count += 1
            except:
                pass
                
        return deleted_count
        
    @staticmethod
    async def compress_file(filepath: Union[str, Path],
                          output_path: Optional[Union[str, Path]] = None) -> bool:
        """Compress file using gzip"""
        import gzip
        
        try:
            input_path = Path(filepath)
            if output_path is None:
                output_path = input_path.with_suffix(input_path.suffix + '.gz')
                
            async with aiofiles.open(input_path, 'rb') as f_in:
                async with aiofiles.open(output_path, 'wb') as f_out:
                    async with aiofiles.open('/dev/null', 'wb') as _:  # For gzip context
                        with gzip.GzipFile(fileobj=f_out, mode='wb') as gz_out:
                            while True:
                                chunk = await f_in.read(8192)
                                if not chunk:
                                    break
                                gz_out.write(chunk)
                                
            return True
        except Exception as e:
            print(f"Error compressing file {filepath}: {e}")
            return False