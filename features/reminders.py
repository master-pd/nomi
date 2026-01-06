"""
Reminder and Scheduling System
For scheduled messages, reminders, and automated tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from config import Config
from utils.json_utils import JSONManager
from utils.logger_utils import setup_logger

logger = setup_logger("reminders")
json_manager = JSONManager()

class ReminderSystem:
    """Professional reminder and scheduling system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduled_tasks = {}
        self.reminders_file = "db/reminders.json"
        
        # Initialize reminders database
        self._init_reminders_db()
        
    def _init_reminders_db(self):
        """Initialize reminders database"""
        try:
            reminders_data = {
                "reminders": {},
                "scheduled_messages": {},
                "recurring_tasks": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            self._ensure_file(self.reminders_file, reminders_data)
            
        except Exception as e:
            logger.error(f"Error initializing reminders DB: {e}")
    
    def _ensure_file(self, file_path: str, default_data: Dict):
        """Ensure JSON file exists with default data"""
        import os
        import json
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Created reminders file: {file_path}")
                
        except Exception as e:
            logger.error(f"Error ensuring file {file_path}: {e}")
            raise
    
    def _read_reminders(self) -> Dict:
        """Read reminders from JSON file"""
        import json
        
        try:
            with open(self.reminders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading reminders: {e}")
            return {"reminders": {}, "scheduled_messages": {}, "recurring_tasks": {}}
    
    def _write_reminders(self, data: Dict):
        """Write reminders to JSON file"""
        import json
        
        try:
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"Error writing reminders: {e}")
            return False
    
    async def start_scheduler(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("✅ Reminder scheduler started")
            
            # Load existing scheduled tasks
            await self._load_scheduled_tasks()
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("🛑 Reminder scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _load_scheduled_tasks(self):
        """Load existing scheduled tasks from database"""
        try:
            data = self._read_reminders()
            
            # Load scheduled messages
            for task_id, task_data in data.get("scheduled_messages", {}).items():
                if task_data.get("enabled", True):
                    await self._schedule_message_task(task_id, task_data)
            
            # Load recurring tasks
            for task_id, task_data in data.get("recurring_tasks", {}).items():
                if task_data.get("enabled", True):
                    await self._schedule_recurring_task(task_id, task_data)
            
            logger.info(f"Loaded {len(data.get('scheduled_messages', {}))} scheduled messages")
            logger.info(f"Loaded {len(data.get('recurring_tasks', {}))} recurring tasks")
            
        except Exception as e:
            logger.error(f"Error loading scheduled tasks: {e}")
    
    async def create_reminder(self, user_id: int, chat_id: int, 
                            message: str, remind_time: datetime) -> str:
        """
        Create a reminder for a user
        Returns reminder ID
        """
        try:
            reminder_id = f"reminder_{user_id}_{int(datetime.now().timestamp())}"
            
            reminder_data = {
                "id": reminder_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "message": message,
                "remind_time": remind_time.isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "recurring": False
            }
            
            # Save to database
            data = self._read_reminders()
            data["reminders"][reminder_id] = reminder_data
            self._write_reminders(data)
            
            # Schedule the reminder
            await self._schedule_reminder(reminder_id, reminder_data)
            
            logger.info(f"Created reminder {reminder_id} for user {user_id}")
            return reminder_id
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return ""
    
    async def create_recurring_reminder(self, user_id: int, chat_id: int,
                                      message: str, cron_expression: str) -> str:
        """
        Create a recurring reminder
        cron_expression format: "minute hour day month day_of_week"
        """
        try:
            reminder_id = f"recurring_{user_id}_{int(datetime.now().timestamp())}"
            
            reminder_data = {
                "id": reminder_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "message": message,
                "cron_expression": cron_expression,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "recurring": True,
                "last_triggered": None,
                "next_trigger": None
            }
            
            # Save to database
            data = self._read_reminders()
            data["reminders"][reminder_id] = reminder_data
            self._write_reminders(data)
            
            # Schedule recurring reminder
            await self._schedule_recurring_reminder(reminder_id, reminder_data)
            
            logger.info(f"Created recurring reminder {reminder_id} for user {user_id}")
            return reminder_id
            
        except Exception as e:
            logger.error(f"Error creating recurring reminder: {e}")
            return ""
    
    async def schedule_message(self, chat_id: int, message: str,
                             schedule_time: datetime, repeat: str = None) -> str:
        """
        Schedule a message to be sent at specific time
        repeat: 'daily', 'weekly', 'monthly', or None
        """
        try:
            task_id = f"msg_{chat_id}_{int(datetime.now().timestamp())}"
            
            task_data = {
                "id": task_id,
                "chat_id": chat_id,
                "message": message,
                "schedule_time": schedule_time.isoformat(),
                "repeat": repeat,
                "created_at": datetime.now().isoformat(),
                "enabled": True,
                "last_sent": None,
                "next_send": schedule_time.isoformat()
            }
            
            # Save to database
            data = self._read_reminders()
            data["scheduled_messages"][task_id] = task_data
            self._write_reminders(data)
            
            # Schedule the message
            await self._schedule_message_task(task_id, task_data)
            
            logger.info(f"Scheduled message {task_id} for chat {chat_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error scheduling message: {e}")
            return ""
    
    async def create_recurring_task(self, task_name: str, task_func: Callable,
                                  cron_expression: str, args: tuple = None) -> str:
        """
        Create a recurring system task
        """
        try:
            task_id = f"task_{task_name}_{int(datetime.now().timestamp())}"
            
            task_data = {
                "id": task_id,
                "name": task_name,
                "cron_expression": cron_expression,
                "created_at": datetime.now().isoformat(),
                "enabled": True,
                "last_run": None,
                "next_run": None
            }
            
            # Save to database
            data = self._read_reminders()
            data["recurring_tasks"][task_id] = task_data
            self._write_reminders(data)
            
            # Schedule the task
            await self._schedule_recurring_task(task_id, task_data, task_func, args)
            
            logger.info(f"Created recurring task {task_id}: {task_name}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating recurring task: {e}")
            return ""
    
    async def _schedule_reminder(self, reminder_id: str, reminder_data: Dict):
        """Schedule a reminder"""
        try:
            remind_time = datetime.fromisoformat(reminder_data["remind_time"])
            
            # Schedule the reminder
            job = self.scheduler.add_job(
                self._send_reminder,
                DateTrigger(run_date=remind_time),
                args=[reminder_id],
                id=reminder_id,
                name=f"reminder_{reminder_id}"
            )
            
            self.scheduled_tasks[reminder_id] = job
            logger.debug(f"Scheduled reminder {reminder_id} for {remind_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
    
    async def _schedule_recurring_reminder(self, reminder_id: str, reminder_data: Dict):
        """Schedule a recurring reminder"""
        try:
            cron_parts = reminder_data["cron_expression"].split()
            
            # Schedule recurring reminder
            job = self.scheduler.add_job(
                self._send_recurring_reminder,
                CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4]
                ),
                args=[reminder_id],
                id=reminder_id,
                name=f"recurring_reminder_{reminder_id}"
            )
            
            self.scheduled_tasks[reminder_id] = job
            
            # Update next trigger time
            data = self._read_reminders()
            if reminder_id in data["reminders"]:
                data["reminders"][reminder_id]["next_trigger"] = job.next_run_time.isoformat()
                self._write_reminders(data)
            
            logger.debug(f"Scheduled recurring reminder {reminder_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling recurring reminder: {e}")
    
    async def _schedule_message_task(self, task_id: str, task_data: Dict):
        """Schedule a message task"""
        try:
            schedule_time = datetime.fromisoformat(task_data["schedule_time"])
            repeat = task_data.get("repeat")
            
            if not repeat:
                # One-time message
                job = self.scheduler.add_job(
                    self._send_scheduled_message,
                    DateTrigger(run_date=schedule_time),
                    args=[task_id],
                    id=task_id,
                    name=f"scheduled_msg_{task_id}"
                )
            else:
                # Recurring message
                if repeat == "daily":
                    trigger = CronTrigger(hour=schedule_time.hour, minute=schedule_time.minute)
                elif repeat == "weekly":
                    trigger = CronTrigger(
                        day_of_week=schedule_time.weekday(),
                        hour=schedule_time.hour,
                        minute=schedule_time.minute
                    )
                elif repeat == "monthly":
                    trigger = CronTrigger(
                        day=schedule_time.day,
                        hour=schedule_time.hour,
                        minute=schedule_time.minute
                    )
                else:
                    logger.error(f"Unknown repeat interval: {repeat}")
                    return
                
                job = self.scheduler.add_job(
                    self._send_scheduled_message,
                    trigger,
                    args=[task_id],
                    id=task_id,
                    name=f"recurring_msg_{task_id}"
                )
            
            self.scheduled_tasks[task_id] = job
            
            # Update next send time
            data = self._read_reminders()
            if task_id in data["scheduled_messages"]:
                data["scheduled_messages"][task_id]["next_send"] = job.next_run_time.isoformat()
                self._write_reminders(data)
            
            logger.debug(f"Scheduled message task {task_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling message task: {e}")
    
    async def _schedule_recurring_task(self, task_id: str, task_data: Dict,
                                     task_func: Callable = None, args: tuple = None):
        """Schedule a recurring system task"""
        try:
            cron_parts = task_data["cron_expression"].split()
            
            if task_func:
                # External task function
                job = self.scheduler.add_job(
                    task_func,
                    CronTrigger(
                        minute=cron_parts[0],
                        hour=cron_parts[1],
                        day=cron_parts[2],
                        month=cron_parts[3],
                        day_of_week=cron_parts[4]
                    ),
                    args=args or (),
                    id=task_id,
                    name=f"system_task_{task_id}"
                )
            else:
                # Internal system task
                job = self.scheduler.add_job(
                    self._execute_system_task,
                    CronTrigger(
                        minute=cron_parts[0],
                        hour=cron_parts[1],
                        day=cron_parts[2],
                        month=cron_parts[3],
                        day_of_week=cron_parts[4]
                    ),
                    args=[task_id],
                    id=task_id,
                    name=f"system_task_{task_id}"
                )
            
            self.scheduled_tasks[task_id] = job
            
            # Update next run time
            data = self._read_reminders()
            if task_id in data["recurring_tasks"]:
                data["recurring_tasks"][task_id]["next_run"] = job.next_run_time.isoformat()
                self._write_reminders(data)
            
            logger.debug(f"Scheduled system task {task_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling system task: {e}")
    
    async def _send_reminder(self, reminder_id: str):
        """Send a reminder"""
        try:
            data = self._read_reminders()
            reminder_data = data["reminders"].get(reminder_id)
            
            if not reminder_data:
                logger.error(f"Reminder {reminder_id} not found")
                return
            
            user_id = reminder_data["user_id"]
            chat_id = reminder_data["chat_id"]
            message = reminder_data["message"]
            
            # Send reminder
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"⏰ **রিমাইন্ডার:**\n\n{message}"
                )
                
                # Update status
                reminder_data["status"] = "sent"
                reminder_data["sent_at"] = datetime.now().isoformat()
                data["reminders"][reminder_id] = reminder_data
                self._write_reminders(data)
                
                logger.info(f"Sent reminder {reminder_id} to user {user_id}")
                
            except Exception as e:
                logger.error(f"Error sending reminder {reminder_id}: {e}")
                reminder_data["status"] = "failed"
                reminder_data["error"] = str(e)
                data["reminders"][reminder_id] = reminder_data
                self._write_reminders(data)
            
            # Remove from scheduled tasks if not recurring
            if not reminder_data.get("recurring", False):
                if reminder_id in self.scheduled_tasks:
                    del self.scheduled_tasks[reminder_id]
                
                # Remove from database after sending
                if reminder_id in data["reminders"]:
                    del data["reminders"][reminder_id]
                    self._write_reminders(data)
            
        except Exception as e:
            logger.error(f"Error in _send_reminder: {e}")
    
    async def _send_recurring_reminder(self, reminder_id: str):
        """Send a recurring reminder"""
        try:
            data = self._read_reminders()
            reminder_data = data["reminders"].get(reminder_id)
            
            if not reminder_data:
                logger.error(f"Recurring reminder {reminder_id} not found")
                return
            
            user_id = reminder_data["user_id"]
            chat_id = reminder_data["chat_id"]
            message = reminder_data["message"]
            
            # Send reminder
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔄 **নিয়মিত রিমাইন্ডার:**\n\n{message}"
                )
                
                # Update last triggered time
                reminder_data["last_triggered"] = datetime.now().isoformat()
                
                # Update next trigger time
                job = self.scheduled_tasks.get(reminder_id)
                if job:
                    reminder_data["next_trigger"] = job.next_run_time.isoformat()
                
                data["reminders"][reminder_id] = reminder_data
                self._write_reminders(data)
                
                logger.debug(f"Sent recurring reminder {reminder_id} to user {user_id}")
                
            except Exception as e:
                logger.error(f"Error sending recurring reminder {reminder_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in _send_recurring_reminder: {e}")
    
    async def _send_scheduled_message(self, task_id: str):
        """Send a scheduled message"""
        try:
            data = self._read_reminders()
            task_data = data["scheduled_messages"].get(task_id)
            
            if not task_data or not task_data.get("enabled", True):
                logger.error(f"Scheduled message {task_id} not found or disabled")
                return
            
            chat_id = task_data["chat_id"]
            message = task_data["message"]
            
            # Send message
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
                
                # Update last sent time
                task_data["last_sent"] = datetime.now().isoformat()
                
                # Update next send time for recurring messages
                if task_data.get("repeat"):
                    job = self.scheduled_tasks.get(task_id)
                    if job:
                        task_data["next_send"] = job.next_run_time.isoformat()
                
                data["scheduled_messages"][task_id] = task_data
                self._write_reminders(data)
                
                logger.info(f"Sent scheduled message {task_id} to chat {chat_id}")
                
            except Exception as e:
                logger.error(f"Error sending scheduled message {task_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in _send_scheduled_message: {e}")
    
    async def _execute_system_task(self, task_id: str):
        """Execute a system task"""
        try:
            data = self._read_reminders()
            task_data = data["recurring_tasks"].get(task_id)
            
            if not task_data or not task_data.get("enabled", True):
                logger.error(f"System task {task_id} not found or disabled")
                return
            
            task_name = task_data["name"]
            
            # Execute different system tasks
            if task_name == "cleanup_temp_files":
                await self._cleanup_temp_files()
            elif task_name == "backup_database":
                await self._backup_database()
            elif task_name == "update_statistics":
                await self._update_statistics()
            elif task_name == "check_updates":
                await self._check_updates()
            else:
                logger.warning(f"Unknown system task: {task_name}")
                return
            
            # Update last run time
            task_data["last_run"] = datetime.now().isoformat()
            
            # Update next run time
            job = self.scheduled_tasks.get(task_id)
            if job:
                task_data["next_run"] = job.next_run_time.isoformat()
            
            data["recurring_tasks"][task_id] = task_data
            self._write_reminders(data)
            
            logger.info(f"Executed system task: {task_name}")
            
        except Exception as e:
            logger.error(f"Error executing system task: {e}")
    
    async def _cleanup_temp_files(self):
        """Cleanup temporary files"""
        import os
        import shutil
        import time
        
        try:
            current_time = time.time()
            
            # Cleanup image temp files
            temp_images = Config.TEMP_IMAGES
            if os.path.exists(temp_images):
                for filename in os.listdir(temp_images):
                    filepath = os.path.join(temp_images, filename)
                    if os.path.isfile(filepath):
                        file_time = os.path.getmtime(filepath)
                        if current_time - file_time > 24 * 3600:  # 24 hours
                            os.remove(filepath)
            
            # Cleanup voice temp files
            temp_voice = Config.TEMP_VOICE
            if os.path.exists(temp_voice):
                for filename in os.listdir(temp_voice):
                    filepath = os.path.join(temp_voice, filename)
                    if os.path.isfile(filepath):
                        file_time = os.path.getmtime(filepath)
                        if current_time - file_time > 24 * 3600:  # 24 hours
                            os.remove(filepath)
            
            logger.info("Cleaned up temporary files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    async def _backup_database(self):
        """Backup database"""
        try:
            from utils.json_utils import JSONManager
            json_manager = JSONManager()
            backup_path = json_manager.create_backup("auto_backup")
            
            if backup_path:
                logger.info(f"Created automatic backup: {backup_path}")
            else:
                logger.error("Failed to create automatic backup")
                
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
    
    async def _update_statistics(self):
        """Update system statistics"""
        try:
            from features.analytics import AnalyticsSystem
            analytics = AnalyticsSystem()
            stats = analytics.get_system_analytics("24h")
            
            # Update system stats in database
            json_manager.update_system_stats({
                "last_updated": datetime.now().isoformat(),
                "total_users": stats.get("overall", {}).get("total_users", 0),
                "total_groups": stats.get("overall", {}).get("total_groups", 0),
                "active_users": stats.get("overall", {}).get("active_users_24h", 0),
                "total_messages": stats.get("overall", {}).get("total_messages", 0)
            })
            
            logger.debug("Updated system statistics")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    async def _check_updates(self):
        """Check for bot updates"""
        try:
            import requests
            
            # Check GitHub for updates
            response = requests.get(
                "https://api.github.com/repos/username/your_crush_bot/releases/latest",
                timeout=10
            )
            
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release.get("tag_name", "")
                
                # Compare with current version
                current_version = "1.0.0"  # Should be from config
                
                if latest_version != current_version:
                    logger.info(f"Update available: {latest_version}")
                    # Notify admins about update
                    for admin_id in Config.ADMIN_IDS:
                        try:
                            await self.bot.send_message(
                                chat_id=admin_id,
                                text=f"🔄 **আপডেট উপলব্ধ:**\n\n"
                                     f"বর্তমান ভার্সন: {current_version}\n"
                                     f"নতুন ভার্সন: {latest_version}\n\n"
                                     f"ডাউনলোড লিঙ্ক: {latest_release.get('html_url')}"
                            )
                        except Exception as e:
                            logger.error(f"Error notifying admin {admin_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error checking updates: {e}")
    
    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """Get all reminders for a user"""
        try:
            data = self._read_reminders()
            user_reminders = []
            
            for reminder_id, reminder_data in data.get("reminders", {}).items():
                if reminder_data.get("user_id") == user_id:
                    user_reminders.append(reminder_data)
            
            return user_reminders
            
        except Exception as e:
            logger.error(f"Error getting user reminders: {e}")
            return []
    
    def get_chat_scheduled_messages(self, chat_id: int) -> List[Dict]:
        """Get scheduled messages for a chat"""
        try:
            data = self._read_reminders()
            chat_messages = []
            
            for task_id, task_data in data.get("scheduled_messages", {}).items():
                if task_data.get("chat_id") == chat_id:
                    chat_messages.append(task_data)
            
            return chat_messages
            
        except Exception as e:
            logger.error(f"Error getting chat scheduled messages: {e}")
            return []
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder"""
        try:
            # Remove from scheduler
            if reminder_id in self.scheduled_tasks:
                job = self.scheduled_tasks[reminder_id]
                job.remove()
                del self.scheduled_tasks[reminder_id]
            
            # Remove from database
            data = self._read_reminders()
            
            if reminder_id in data.get("reminders", {}):
                del data["reminders"][reminder_id]
                self._write_reminders(data)
                logger.info(f"Cancelled reminder {reminder_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling reminder: {e}")
            return False
    
    def cancel_scheduled_message(self, task_id: str) -> bool:
        """Cancel a scheduled message"""
        try:
            # Remove from scheduler
            if task_id in self.scheduled_tasks:
                job = self.scheduled_tasks[task_id]
                job.remove()
                del self.scheduled_tasks[task_id]
            
            # Remove from database
            data = self._read_reminders()
            
            if task_id in data.get("scheduled_messages", {}):
                del data["scheduled_messages"][task_id]
                self._write_reminders(data)
                logger.info(f"Cancelled scheduled message {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling scheduled message: {e}")
            return False
    
    def enable_task(self, task_id: str, enabled: bool) -> bool:
        """Enable or disable a task"""
        try:
            data = self._read_reminders()
            
            # Check all task types
            for task_type in ["reminders", "scheduled_messages", "recurring_tasks"]:
                if task_id in data.get(task_type, {}):
                    data[task_type][task_id]["enabled"] = enabled
                    
                    if not enabled and task_id in self.scheduled_tasks:
                        # Disable in scheduler
                        job = self.scheduled_tasks[task_id]
                        job.remove()
                        del self.scheduled_tasks[task_id]
                    
                    self._write_reminders(data)
                    logger.info(f"{'Enabled' if enabled else 'Disabled'} task {task_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enabling/disabling task: {e}")
            return False
    
    def get_scheduler_stats(self) -> Dict:
        """Get scheduler statistics"""
        try:
            data = self._read_reminders()
            
            stats = {
                "total_reminders": len(data.get("reminders", {})),
                "total_scheduled_messages": len(data.get("scheduled_messages", {})),
                "total_recurring_tasks": len(data.get("recurring_tasks", {})),
                "active_jobs": len(self.scheduled_tasks),
                "next_run_times": []
            }
            
            # Get next run times for active jobs
            for task_id, job in self.scheduled_tasks.items():
                if hasattr(job, 'next_run_time') and job.next_run_time:
                    stats["next_run_times"].append({
                        "task_id": task_id,
                        "next_run": job.next_run_time.isoformat()
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting scheduler stats: {e}")
            return {}