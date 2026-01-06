"""
Scheduler - Manages scheduled tasks and events
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from enum import Enum
import json

class TaskType(Enum):
    """Task types"""
    REMINDER = "reminder"
    MESSAGE = "message"
    CLEANUP = "cleanup"
    BACKUP = "backup"
    REPORT = "report"
    CUSTOM = "custom"

@dataclass
class ScheduledTask:
    """Scheduled task data"""
    task_id: str
    task_type: TaskType
    execute_at: float  # Unix timestamp
    data: Dict[str, Any]
    callback: Optional[Callable] = None
    repeat_interval: Optional[int] = None  # Seconds, None for one-time
    created_at: float = None
    created_by: Optional[int] = None
    group_id: Optional[int] = None

class Scheduler:
    """Manages scheduled tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_scheduler")
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.task_queue = asyncio.PriorityQueue()
        self.worker_task = None
        
    async def start(self):
        """Start scheduler"""
        if self.running:
            return
            
        self.running = True
        self.logger.info("⏰ Starting scheduler...")
        
        # Load saved tasks
        await self._load_tasks()
        
        # Start worker
        self.worker_task = asyncio.create_task(self._worker())
        
        self.logger.info("✅ Scheduler started")
        
    async def stop(self):
        """Stop scheduler"""
        if not self.running:
            return
            
        self.running = False
        self.logger.info("🛑 Stopping scheduler...")
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
                
        # Save tasks
        await self._save_tasks()
        
        self.logger.info("✅ Scheduler stopped")
        
    async def _worker(self):
        """Worker that processes tasks"""
        self.logger.info("👷 Scheduler worker started")
        
        while self.running:
            try:
                # Check for due tasks every second
                current_time = time.time()
                
                for task_id, task in list(self.tasks.items()):
                    if task.execute_at <= current_time:
                        # Execute task
                        await self._execute_task(task)
                        
                        # Handle repetition
                        if task.repeat_interval:
                            # Reschedule
                            new_execute_at = current_time + task.repeat_interval
                            new_task = ScheduledTask(
                                task_id=task_id,
                                task_type=task.task_type,
                                execute_at=new_execute_at,
                                data=task.data,
                                callback=task.callback,
                                repeat_interval=task.repeat_interval,
                                created_at=task.created_at,
                                created_by=task.created_by,
                                group_id=task.group_id
                            )
                            self.tasks[task_id] = new_task
                        else:
                            # Remove one-time task
                            del self.tasks[task_id]
                            
                # Save tasks periodically
                if int(current_time) % 60 == 0:  # Every minute
                    await self._save_tasks()
                    
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler worker error: {e}")
                await asyncio.sleep(5)
                
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        self.logger.info(f"⚡ Executing task: {task.task_id} ({task.task_type.value})")
        
        try:
            # Execute based on task type
            if task.task_type == TaskType.REMINDER:
                await self._handle_reminder(task)
            elif task.task_type == TaskType.MESSAGE:
                await self._handle_message(task)
            elif task.task_type == TaskType.CLEANUP:
                await self._handle_cleanup(task)
            elif task.task_type == TaskType.BACKUP:
                await self._handle_backup(task)
            elif task.task_type == TaskType.REPORT:
                await self._handle_report(task)
            elif task.task_type == TaskType.CUSTOM and task.callback:
                await task.callback(task.data)
                
        except Exception as e:
            self.logger.error(f"❌ Task execution error: {e}")
            
    async def _handle_reminder(self, task: ScheduledTask):
        """Handle reminder task"""
        from core.engines.auto_reply_engine import AutoReplyEngine
        # This would send reminder to user/group
        pass
        
    async def _handle_message(self, task: ScheduledTask):
        """Handle scheduled message"""
        # Send scheduled message
        pass
        
    async def _handle_cleanup(self, task: ScheduledTask):
        """Handle cleanup task"""
        # Perform cleanup
        pass
        
    async def _handle_backup(self, task: ScheduledTask):
        """Handle backup task"""
        # Perform backup
        pass
        
    async def _handle_report(self, task: ScheduledTask):
        """Handle report task"""
        # Generate and send report
        pass
        
    async def schedule_task(self, task_type: TaskType, execute_in: int, 
                          data: Dict[str, Any], task_id: Optional[str] = None,
                          callback: Optional[Callable] = None,
                          repeat_interval: Optional[int] = None,
                          created_by: Optional[int] = None,
                          group_id: Optional[int] = None) -> str:
        """
        Schedule a new task
        
        Args:
            task_type: Type of task
            execute_in: Seconds from now to execute
            data: Task data
            task_id: Custom task ID (auto-generated if None)
            callback: Callback function for custom tasks
            repeat_interval: Repeat interval in seconds
            created_by: User who created task
            group_id: Group ID if group task
            
        Returns:
            Task ID
        """
        if not task_id:
            task_id = f"{task_type.value}_{int(time.time())}_{hash(str(data)) % 10000}"
            
        execute_at = time.time() + execute_in
        
        task = ScheduledTask(
            task_id=task_id,
            task_type=task_type,
            execute_at=execute_at,
            data=data,
            callback=callback,
            repeat_interval=repeat_interval,
            created_at=time.time(),
            created_by=created_by,
            group_id=group_id
        )
        
        self.tasks[task_id] = task
        self.logger.info(f"📅 Scheduled task: {task_id} in {execute_in}s")
        
        # Save tasks
        await self._save_tasks()
        
        return task_id
        
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.info(f"❌ Cancelled task: {task_id}")
            await self._save_tasks()
            return True
        return False
        
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
        
    def get_user_tasks(self, user_id: int) -> List[ScheduledTask]:
        """Get all tasks created by user"""
        return [task for task in self.tasks.values() 
                if task.created_by == user_id]
                
    def get_group_tasks(self, group_id: int) -> List[ScheduledTask]:
        """Get all tasks for group"""
        return [task for task in self.tasks.values() 
                if task.group_id == group_id]
                
    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks due for execution"""
        current_time = time.time()
        return [task for task in self.tasks.values() 
                if task.execute_at <= current_time]
                
    async def _load_tasks(self):
        """Load tasks from storage"""
        try:
            tasks_file = "data/scheduled_tasks.json"
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                
            for task_data in tasks_data:
                # Convert string task type to enum
                task_data['task_type'] = TaskType(task_data['task_type'])
                # Remove callback (can't serialize functions)
                if 'callback' in task_data:
                    del task_data['callback']
                    
                task = ScheduledTask(**task_data)
                # Only add if not expired
                if task.execute_at > time.time() or task.repeat_interval:
                    self.tasks[task.task_id] = task
                    
            self.logger.info(f"📂 Loaded {len(self.tasks)} scheduled tasks")
            
        except FileNotFoundError:
            self.logger.info("📂 No saved tasks found")
        except Exception as e:
            self.logger.error(f"❌ Error loading tasks: {e}")
            
    async def _save_tasks(self):
        """Save tasks to storage"""
        try:
            tasks_file = "data/scheduled_tasks.json"
            tasks_data = []
            
            for task in self.tasks.values():
                task_dict = {
                    'task_id': task.task_id,
                    'task_type': task.task_type.value,
                    'execute_at': task.execute_at,
                    'data': task.data,
                    'repeat_interval': task.repeat_interval,
                    'created_at': task.created_at,
                    'created_by': task.created_by,
                    'group_id': task.group_id
                }
                tasks_data.append(task_dict)
                
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(f"💾 Saved {len(tasks_data)} tasks")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving tasks: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        current_time = time.time()
        due_tasks = self.get_due_tasks()
        
        return {
            'total_tasks': len(self.tasks),
            'due_tasks': len(due_tasks),
            'task_types': {ttype.value: 0 for ttype in TaskType},
            'next_execution': min([t.execute_at for t in self.tasks.values()], default=0),
            'running': self.running
        }