"""
Event and Trigger System
For handling special events, triggers, and automated responses
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import re
from enum import Enum

from config import Config
from utils.json_utils import JSONManager
from utils.logger_utils import setup_logger

logger = setup_logger("events")
json_manager = JSONManager()

class EventType(Enum):
    """Types of events"""
    MESSAGE = "message"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    USER_MENTION = "user_mention"
    KEYWORD = "keyword"
    COMMAND = "command"
    TIME_BASED = "time_based"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"
    CUSTOM = "custom"

class TriggerType(Enum):
    """Types of triggers"""
    EXACT_MATCH = "exact_match"
    CONTAINS = "contains"
    REGEX = "regex"
    COUNT = "count"
    TIME = "time"
    INTERVAL = "interval"
    CONDITION = "condition"

class ActionType(Enum):
    """Types of actions"""
    SEND_MESSAGE = "send_message"
    SEND_VOICE = "send_voice"
    SEND_IMAGE = "send_image"
    CHANGE_ROLE = "change_role"
    AWARD_POINTS = "award_points"
    AWARD_BADGE = "award_badge"
    RUN_COMMAND = "run_command"
    EXECUTE_FUNCTION = "execute_function"
    NOTIFY_ADMIN = "notify_admin"
    LOG_EVENT = "log_event"

class EventSystem:
    """Professional event and trigger system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.json_manager = json_manager
        self.events_file = "db/events.json"
        self.triggers = {}
        self.event_handlers = {}
        
        # Initialize events database
        self._init_events_db()
        
        # Register default event handlers
        self._register_default_handlers()
        
    def _init_events_db(self):
        """Initialize events database"""
        try:
            events_data = {
                "events": {},
                "triggers": {},
                "actions": {},
                "event_logs": [],
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            self._ensure_file(self.events_file, events_data)
            
        except Exception as e:
            logger.error(f"Error initializing events DB: {e}")
    
    def _ensure_file(self, file_path: str, default_data: Dict):
        """Ensure JSON file exists with default data"""
        import os
        import json
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Created events file: {file_path}")
                
        except Exception as e:
            logger.error(f"Error ensuring file {file_path}: {e}")
            raise
    
    def _read_events(self) -> Dict:
        """Read events from JSON file"""
        import json
        
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading events: {e}")
            return {"events": {}, "triggers": {}, "actions": {}, "event_logs": []}
    
    def _write_events(self, data: Dict):
        """Write events to JSON file"""
        import json
        
        try:
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"Error writing events: {e}")
            return False
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        # Message-based events
        self.register_handler(EventType.MESSAGE, self._handle_message_event)
        self.register_handler(EventType.KEYWORD, self._handle_keyword_event)
        self.register_handler(EventType.COMMAND, self._handle_command_event)
        self.register_handler(EventType.USER_MENTION, self._handle_mention_event)
        
        # User-based events
        self.register_handler(EventType.USER_JOIN, self._handle_user_join_event)
        self.register_handler(EventType.USER_LEAVE, self._handle_user_leave_event)
        
        # Achievement events
        self.register_handler(EventType.ACHIEVEMENT, self._handle_achievement_event)
        
        # System events
        self.register_handler(EventType.SYSTEM, self._handle_system_event)
        
        # Time-based events
        self.register_handler(EventType.TIME_BASED, self._handle_time_based_event)
        
        logger.info("Registered default event handlers")
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")
    
    async def trigger_event(self, event_type: EventType, data: Dict):
        """
        Trigger an event
        """
        try:
            event_id = f"{event_type.value}_{int(datetime.now().timestamp())}"
            
            event_data = {
                "id": event_id,
                "type": event_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "handled": False
            }
            
            # Log the event
            self._log_event(event_data)
            
            # Check for triggers
            triggered = await self._check_triggers(event_type, data)
            
            # Call event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event_data)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
            
            # Update event as handled
            event_data["handled"] = True
            event_data["triggered_actions"] = triggered
            self._update_event_log(event_id, event_data)
            
            logger.debug(f"Triggered event: {event_type.value}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error triggering event: {e}")
            return None
    
    async def create_trigger(self, name: str, event_type: EventType,
                           trigger_type: TriggerType, conditions: Dict,
                           actions: List[Dict], enabled: bool = True) -> str:
        """
        Create a new trigger
        """
        try:
            trigger_id = f"trigger_{int(datetime.now().timestamp())}"
            
            trigger_data = {
                "id": trigger_id,
                "name": name,
                "event_type": event_type.value,
                "trigger_type": trigger_type.value,
                "conditions": conditions,
                "actions": actions,
                "enabled": enabled,
                "created_at": datetime.now().isoformat(),
                "last_triggered": None,
                "trigger_count": 0
            }
            
            # Save to database
            data = self._read_events()
            data["triggers"][trigger_id] = trigger_data
            self._write_events(data)
            
            # Add to in-memory cache
            self.triggers[trigger_id] = trigger_data
            
            logger.info(f"Created trigger: {name}")
            return trigger_id
            
        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return ""
    
    async def _check_triggers(self, event_type: EventType, event_data: Dict) -> List[Dict]:
        """Check if any triggers match the event"""
        triggered = []
        
        try:
            data = self._read_events()
            
            for trigger_id, trigger in data.get("triggers", {}).items():
                if not trigger.get("enabled", True):
                    continue
                
                if trigger["event_type"] != event_type.value:
                    continue
                
                # Check trigger conditions
                if await self._evaluate_trigger(trigger, event_data):
                    # Execute actions
                    results = await self._execute_trigger_actions(trigger_id, trigger, event_data)
                    triggered.append({
                        "trigger_id": trigger_id,
                        "trigger_name": trigger["name"],
                        "actions_executed": results
                    })
                    
                    # Update trigger stats
                    trigger["last_triggered"] = datetime.now().isoformat()
                    trigger["trigger_count"] = trigger.get("trigger_count", 0) + 1
                    data["triggers"][trigger_id] = trigger
                    self._write_events(data)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error checking triggers: {e}")
            return []
    
    async def _evaluate_trigger(self, trigger: Dict, event_data: Dict) -> bool:
        """Evaluate if trigger conditions are met"""
        try:
            trigger_type = TriggerType(trigger["trigger_type"])
            conditions = trigger.get("conditions", {})
            
            if trigger_type == TriggerType.EXACT_MATCH:
                return await self._check_exact_match(conditions, event_data)
            
            elif trigger_type == TriggerType.CONTAINS:
                return await self._check_contains(conditions, event_data)
            
            elif trigger_type == TriggerType.REGEX:
                return await self._check_regex(conditions, event_data)
            
            elif trigger_type == TriggerType.COUNT:
                return await self._check_count(conditions, event_data)
            
            elif trigger_type == TriggerType.TIME:
                return await self._check_time(conditions, event_data)
            
            elif trigger_type == TriggerType.INTERVAL:
                return await self._check_interval(conditions, event_data)
            
            elif trigger_type == TriggerType.CONDITION:
                return await self._check_condition(conditions, event_data)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating trigger: {e}")
            return False
    
    async def _check_exact_match(self, conditions: Dict, event_data: Dict) -> bool:
        """Check exact match condition"""
        field = conditions.get("field")
        value = conditions.get("value")
        
        if not field or value is None:
            return False
        
        # Navigate nested fields
        data_value = event_data.get("data", {})
        for key in field.split("."):
            if isinstance(data_value, dict):
                data_value = data_value.get(key)
            else:
                return False
        
        return str(data_value) == str(value)
    
    async def _check_contains(self, conditions: Dict, event_data: Dict) -> bool:
        """Check contains condition"""
        field = conditions.get("field")
        value = conditions.get("value")
        
        if not field or value is None:
            return False
        
        # Navigate nested fields
        data_value = event_data.get("data", {})
        for key in field.split("."):
            if isinstance(data_value, dict):
                data_value = data_value.get(key)
            else:
                return False
        
        if not isinstance(data_value, str):
            data_value = str(data_value)
        
        return str(value).lower() in data_value.lower()
    
    async def _check_regex(self, conditions: Dict, event_data: Dict) -> bool:
        """Check regex condition"""
        field = conditions.get("field")
        pattern = conditions.get("pattern")
        
        if not field or not pattern:
            return False
        
        # Navigate nested fields
        data_value = event_data.get("data", {})
        for key in field.split("."):
            if isinstance(data_value, dict):
                data_value = data_value.get(key)
            else:
                return False
        
        if not isinstance(data_value, str):
            data_value = str(data_value)
        
        try:
            return bool(re.search(pattern, data_value, re.IGNORECASE))
        except re.error:
            return False
    
    async def _check_count(self, conditions: Dict, event_data: Dict) -> bool:
        """Check count condition"""
        field = conditions.get("field")
        operator = conditions.get("operator", ">=")
        value = conditions.get("value", 0)
        
        if not field:
            return False
        
        # Navigate nested fields
        data_value = event_data.get("data", {})
        for key in field.split("."):
            if isinstance(data_value, dict):
                data_value = data_value.get(key, 0)
            else:
                data_value = 0
        
        try:
            count = int(data_value)
        except (ValueError, TypeError):
            count = 0
        
        if operator == ">":
            return count > value
        elif operator == ">=":
            return count >= value
        elif operator == "==":
            return count == value
        elif operator == "<=":
            return count <= value
        elif operator == "<":
            return count < value
        elif operator == "!=":
            return count != value
        
        return False
    
    async def _check_time(self, conditions: Dict, event_data: Dict) -> bool:
        """Check time condition"""
        time_value = conditions.get("time")
        if not time_value:
            return False
        
        try:
            target_time = datetime.fromisoformat(time_value)
            current_time = datetime.now()
            
            # Check if current time is within tolerance
            tolerance = conditions.get("tolerance_minutes", 5)
            
            time_diff = abs((current_time - target_time).total_seconds())
            return time_diff <= tolerance * 60
            
        except Exception:
            return False
    
    async def _check_interval(self, conditions: Dict, event_data: Dict) -> bool:
        """Check interval condition"""
        interval_minutes = conditions.get("interval_minutes", 60)
        last_trigger = conditions.get("last_trigger")
        
        if not last_trigger:
            return True
        
        try:
            last_trigger_time = datetime.fromisoformat(last_trigger)
            current_time = datetime.now()
            
            time_diff = (current_time - last_trigger_time).total_seconds()
            return time_diff >= interval_minutes * 60
            
        except Exception:
            return True
    
    async def _check_condition(self, conditions: Dict, event_data: Dict) -> bool:
        """Check complex condition"""
        # This could be a complex condition with AND/OR logic
        # For simplicity, we'll check all conditions with AND logic
        checks = conditions.get("checks", [])
        
        if not checks:
            return False
        
        for check in checks:
            check_type = check.get("type")
            check_conditions = check.get("conditions", {})
            
            if check_type == "exact_match":
                if not await self._check_exact_match(check_conditions, event_data):
                    return False
            elif check_type == "contains":
                if not await self._check_contains(check_conditions, event_data):
                    return False
            elif check_type == "regex":
                if not await self._check_regex(check_conditions, event_data):
                    return False
            elif check_type == "count":
                if not await self._check_count(check_conditions, event_data):
                    return False
        
        return True
    
    async def _execute_trigger_actions(self, trigger_id: str, trigger: Dict, event_data: Dict) -> List[Dict]:
        """Execute trigger actions"""
        results = []
        
        try:
            actions = trigger.get("actions", [])
            
            for action in actions:
                action_type = ActionType(action.get("type"))
                action_data = action.get("data", {})
                
                try:
                    result = await self._execute_action(action_type, action_data, event_data)
                    results.append({
                        "action_type": action_type.value,
                        "success": True,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Error executing action {action_type}: {e}")
                    results.append({
                        "action_type": action_type.value,
                        "success": False,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing trigger actions: {e}")
            return []
    
    async def _execute_action(self, action_type: ActionType, action_data: Dict, event_data: Dict) -> Any:
        """Execute a single action"""
        try:
            if action_type == ActionType.SEND_MESSAGE:
                return await self._action_send_message(action_data, event_data)
            
            elif action_type == ActionType.SEND_VOICE:
                return await self._action_send_voice(action_data, event_data)
            
            elif action_type == ActionType.SEND_IMAGE:
                return await self._action_send_image(action_data, event_data)
            
            elif action_type == ActionType.CHANGE_ROLE:
                return await self._action_change_role(action_data, event_data)
            
            elif action_type == ActionType.AWARD_POINTS:
                return await self._action_award_points(action_data, event_data)
            
            elif action_type == ActionType.AWARD_BADGE:
                return await self._action_award_badge(action_data, event_data)
            
            elif action_type == ActionType.RUN_COMMAND:
                return await self._action_run_command(action_data, event_data)
            
            elif action_type == ActionType.EXECUTE_FUNCTION:
                return await self._action_execute_function(action_data, event_data)
            
            elif action_type == ActionType.NOTIFY_ADMIN:
                return await self._action_notify_admin(action_data, event_data)
            
            elif action_type == ActionType.LOG_EVENT:
                return await self._action_log_event(action_data, event_data)
            
            else:
                raise ValueError(f"Unknown action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error in action execution: {e}")
            raise
    
    async def _action_send_message(self, action_data: Dict, event_data: Dict) -> bool:
        """Send message action"""
        try:
            chat_id = action_data.get("chat_id")
            message = action_data.get("message")
            
            if not chat_id or not message:
                return False
            
            # Replace variables in message
            message = self._replace_variables(message, event_data)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def _action_send_voice(self, action_data: Dict, event_data: Dict) -> bool:
        """Send voice message action"""
        try:
            chat_id = action_data.get("chat_id")
            text = action_data.get("text")
            
            if not chat_id or not text:
                return False
            
            # Replace variables in text
            text = self._replace_variables(text, event_data)
            
            # Generate voice
            from utils.voice_utils import VoiceUtils
            voice_utils = VoiceUtils()
            voice_path = voice_utils.text_to_speech(text)
            
            if voice_path:
                from aiogram.types import FSInputFile
                await self.bot.send_voice(
                    chat_id=chat_id,
                    voice=FSInputFile(voice_path)
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending voice: {e}")
            return False
    
    async def _action_send_image(self, action_data: Dict, event_data: Dict) -> bool:
        """Send image action"""
        try:
            chat_id = action_data.get("chat_id")
            image_url = action_data.get("image_url")
            caption = action_data.get("caption", "")
            
            if not chat_id or not image_url:
                return False
            
            # Replace variables in caption
            caption = self._replace_variables(caption, event_data)
            
            await self.bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=caption
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            return False
    
    async def _action_change_role(self, action_data: Dict, event_data: Dict) -> bool:
        """Change user role action"""
        try:
            user_id = action_data.get("user_id")
            role = action_data.get("role")
            
            if not user_id or not role:
                return False
            
            # Update user role in database
            user_data = self.json_manager.get_user(user_id)
            if user_data:
                user_data["role"] = role
                self.json_manager.update_user(user_id, user_data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error changing role: {e}")
            return False
    
    async def _action_award_points(self, action_data: Dict, event_data: Dict) -> bool:
        """Award points action"""
        try:
            user_id = action_data.get("user_id")
            points = action_data.get("points", 0)
            
            if not user_id or points == 0:
                return False
            
            # Update user reputation
            user_data = self.json_manager.get_user(user_id)
            if user_data:
                current_reputation = user_data.get("reputation", 0)
                user_data["reputation"] = current_reputation + points
                self.json_manager.update_user(user_id, user_data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            return False
    
    async def _action_award_badge(self, action_data: Dict, event_data: Dict) -> bool:
        """Award badge action"""
        try:
            user_id = action_data.get("user_id")
            badge_id = action_data.get("badge_id")
            
            if not user_id or not badge_id:
                return False
            
            # Award badge
            from features.badges import BadgeSystem
            badge_system = BadgeSystem()
            return badge_system._award_badge(user_id, badge_id)
            
        except Exception as e:
            logger.error(f"Error awarding badge: {e}")
            return False
    
    async def _action_run_command(self, action_data: Dict, event_data: Dict) -> bool:
        """Run command action"""
        try:
            command = action_data.get("command")
            
            if not command:
                return False
            
            # This would need integration with command system
            # For now, just log it
            logger.info(f"Would run command: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return False
    
    async def _action_execute_function(self, action_data: Dict, event_data: Dict) -> Any:
        """Execute function action"""
        try:
            function_name = action_data.get("function")
            args = action_data.get("args", [])
            
            if not function_name:
                return None
            
            # This is a placeholder - in production, you'd have a registry of functions
            # or use some other mechanism to call functions by name
            
            logger.info(f"Would execute function: {function_name} with args {args}")
            return None
            
        except Exception as e:
            logger.error(f"Error executing function: {e}")
            return None
    
    async def _action_notify_admin(self, action_data: Dict, event_data: Dict) -> bool:
        """Notify admin action"""
        try:
            message = action_data.get("message", "Event triggered")
            
            # Replace variables
            message = self._replace_variables(message, event_data)
            
            # Notify all admins
            for admin_id in Config.ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 **ইভেন্ট নোটিফিকেশন:**\n\n{message}"
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")
            return False
    
    async def _action_log_event(self, action_data: Dict, event_data: Dict) -> bool:
        """Log event action"""
        try:
            log_message = action_data.get("message", "Event logged")
            
            # Replace variables
            log_message = self._replace_variables(log_message, event_data)
            
            logger.info(f"Event log: {log_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False
    
    def _replace_variables(self, text: str, event_data: Dict) -> str:
        """Replace variables in text with actual values"""
        try:
            variables = {
                "{user_id}": str(event_data.get("data", {}).get("user_id", "")),
                "{user_name}": str(event_data.get("data", {}).get("user_name", "")),
                "{chat_id}": str(event_data.get("data", {}).get("chat_id", "")),
                "{chat_title}": str(event_data.get("data", {}).get("chat_title", "")),
                "{message}": str(event_data.get("data", {}).get("message", "")),
                "{timestamp}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "{date}": datetime.now().strftime("%Y-%m-%d"),
                "{time}": datetime.now().strftime("%H:%M:%S")
            }
            
            for var, value in variables.items():
                text = text.replace(var, value)
            
            return text
            
        except Exception as e:
            logger.error(f"Error replacing variables: {e}")
            return text
    
    def _log_event(self, event_data: Dict):
        """Log an event"""
        try:
            data = self._read_events()
            
            # Keep only last 1000 events
            event_logs = data.get("event_logs", [])
            event_logs.append(event_data)
            
            if len(event_logs) > 1000:
                event_logs = event_logs[-1000:]
            
            data["event_logs"] = event_logs
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            self._write_events(data)
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def _update_event_log(self, event_id: str, updated_data: Dict):
        """Update event log entry"""
        try:
            data = self._read_events()
            
            for i, event in enumerate(data.get("event_logs", [])):
                if event.get("id") == event_id:
                    data["event_logs"][i] = updated_data
                    break
            
            self._write_events(data)
            
        except Exception as e:
            logger.error(f"Error updating event log: {e}")
    
    # ============ EVENT HANDLERS ============
    
    async def _handle_message_event(self, event_data: Dict):
        """Handle message events"""
        try:
            data = event_data.get("data", {})
            message = data.get("message", "")
            user_id = data.get("user_id")
            chat_id = data.get("chat_id")
            
            # Check for keywords
            if "hello" in message.lower() or "hi" in message.lower():
                await self.trigger_event(EventType.KEYWORD, {
                    "keyword": "hello",
                    "message": message,
                    "user_id": user_id,
                    "chat_id": chat_id
                })
            
            # Check for mentions
            if "@" in message:
                await self.trigger_event(EventType.USER_MENTION, {
                    "mentioned_users": self._extract_mentions(message),
                    "message": message,
                    "user_id": user_id,
                    "chat_id": chat_id
                })
            
        except Exception as e:
            logger.error(f"Error handling message event: {e}")
    
    async def _handle_keyword_event(self, event_data: Dict):
        """Handle keyword events"""
        # This could trigger auto-replies, etc.
        pass
    
    async def _handle_command_event(self, event_data: Dict):
        """Handle command events"""
        # Commands are handled elsewhere
        pass
    
    async def _handle_mention_event(self, event_data: Dict):
        """Handle user mention events"""
        try:
            data = event_data.get("data", {})
            mentioned_users = data.get("mentioned_users", [])
            
            # Check if bot was mentioned
            if str(Config.BOT_ID) in mentioned_users or f"@{Config.BOT_USERNAME}" in mentioned_users:
                # Bot was mentioned - could trigger special response
                pass
            
        except Exception as e:
            logger.error(f"Error handling mention event: {e}")
    
    async def _handle_user_join_event(self, event_data: Dict):
        """Handle user join events"""
        try:
            data = event_data.get("data", {})
            user_id = data.get("user_id")
            chat_id = data.get("chat_id")
            
            # Check if this is user's first join
            user_data = self.json_manager.get_user(user_id)
            if user_data:
                join_count = user_data.get("join_count", 0)
                if join_count == 0:
                    # First join - trigger achievement
                    await self.trigger_event(EventType.ACHIEVEMENT, {
                        "achievement": "first_join",
                        "user_id": user_id,
                        "chat_id": chat_id
                    })
            
        except Exception as e:
            logger.error(f"Error handling user join event: {e}")
    
    async def _handle_user_leave_event(self, event_data: Dict):
        """Handle user leave events"""
        # Could trigger farewell messages, analytics updates, etc.
        pass
    
    async def _handle_achievement_event(self, event_data: Dict):
        """Handle achievement events"""
        try:
            data = event_data.get("data", {})
            achievement = data.get("achievement")
            user_id = data.get("user_id")
            
            # Award badge for achievement
            from features.badges import BadgeSystem
            badge_system = BadgeSystem()
            
            if achievement == "first_join":
                badge_system._award_badge(user_id, "first_join")
            
        except Exception as e:
            logger.error(f"Error handling achievement event: {e}")
    
    async def _handle_system_event(self, event_data: Dict):
        """Handle system events"""
        # System events like bot start, shutdown, errors, etc.
        pass
    
    async def _handle_time_based_event(self, event_data: Dict):
        """Handle time-based events"""
        # Events triggered by time (daily, weekly, etc.)
        pass
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        mentions = []
        
        # Extract @mentions
        mention_pattern = r'@(\w+)'
        mentions.extend(re.findall(mention_pattern, text))
        
        # Extract user IDs (if any)
        id_pattern = r'user_id:(\d+)'
        mentions.extend(re.findall(id_pattern, text))
        
        return mentions
    
    def get_event_stats(self) -> Dict:
        """Get event system statistics"""
        try:
            data = self._read_events()
            
            stats = {
                "total_events": len(data.get("event_logs", [])),
                "total_triggers": len(data.get("triggers", {})),
                "events_by_type": {},
                "recent_events": data.get("event_logs", [])[-10:],
                "active_triggers": 0
            }
            
            # Count events by type
            for event in data.get("event_logs", []):
                event_type = event.get("type", "unknown")
                stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Count active triggers
            for trigger in data.get("triggers", {}).values():
                if trigger.get("enabled", True):
                    stats["active_triggers"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting event stats: {e}")
            return {}
    
    def get_trigger_details(self, trigger_id: str) -> Optional[Dict]:
        """Get details of a specific trigger"""
        try:
            data = self._read_events()
            return data.get("triggers", {}).get(trigger_id)
        except Exception as e:
            logger.error(f"Error getting trigger details: {e}")
            return None
    
    def update_trigger(self, trigger_id: str, updates: Dict) -> bool:
        """Update a trigger"""
        try:
            data = self._read_events()
            
            if trigger_id in data.get("triggers", {}):
                trigger = data["triggers"][trigger_id]
                trigger.update(updates)
                trigger["updated_at"] = datetime.now().isoformat()
                data["triggers"][trigger_id] = trigger
                
                # Update in-memory cache
                if trigger_id in self.triggers:
                    self.triggers[trigger_id] = trigger
                
                self._write_events(data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating trigger: {e}")
            return False
    
    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a trigger"""
        try:
            data = self._read_events()
            
            if trigger_id in data.get("triggers", {}):
                del data["triggers"][trigger_id]
                
                # Remove from in-memory cache
                if trigger_id in self.triggers:
                    del self.triggers[trigger_id]
                
                self._write_events(data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting trigger: {e}")
            return False
    
    def create_predefined_trigger(self, trigger_name: str) -> Optional[str]:
        """Create a predefined trigger"""
        predefined_triggers = {
            "welcome_new_user": {
                "name": "নতুন ইউজার স্বাগতম",
                "event_type": EventType.USER_JOIN.value,
                "trigger_type": TriggerType.EXACT_MATCH.value,
                "conditions": {
                    "field": "data.is_first_join",
                    "value": True
                },
                "actions": [
                    {
                        "type": ActionType.SEND_MESSAGE.value,
                        "data": {
                            "chat_id": "{chat_id}",
                            "message": "🎉 আসসালামু আলাইকুম {user_name}! গ্রুপে আপনাকে স্বাগতম।"
                        }
                    },
                    {
                        "type": ActionType.AWARD_BADGE.value,
                        "data": {
                            "user_id": "{user_id}",
                            "badge_id": "first_join"
                        }
                    }
                ]
            },
            "message_count_milestone": {
                "name": "মেসেজ মাইলস্টোন",
                "event_type": EventType.MESSAGE.value,
                "trigger_type": TriggerType.COUNT.value,
                "conditions": {
                    "field": "data.user_total_messages",
                    "operator": "==",
                    "value": 100
                },
                "actions": [
                    {
                        "type": ActionType.SEND_MESSAGE.value,
                        "data": {
                            "chat_id": "{chat_id}",
                            "message": "🎊 অভিনন্দন {user_name}! আপনি ১০০টি মেসেজ পাঠিয়েছেন।"
                        }
                    },
                    {
                        "type": ActionType.AWARD_BADGE.value,
                        "data": {
                            "user_id": "{user_id}",
                            "badge_id": "chatty"
                        }
                    }
                ]
            },
            "daily_greeting": {
                "name": "দৈনিক শুভেচ্ছা",
                "event_type": EventType.TIME_BASED.value,
                "trigger_type": TriggerType.TIME.value,
                "conditions": {
                    "time": datetime.now().replace(hour=9, minute=0, second=0).isoformat(),
                    "tolerance_minutes": 5
                },
                "actions": [
                    {
                        "type": ActionType.SEND_MESSAGE.value,
                        "data": {
                            "chat_id": "all",  # Special value for all chats
                            "message": "🌅 সকাল বেলা শুভেচ্ছা! ভালো একটি দিন হোক সবার।"
                        }
                    }
                ]
            }
        }
        
        if trigger_name in predefined_triggers:
            trigger_config = predefined_triggers[trigger_name]
            return self.create_trigger(
                name=trigger_config["name"],
                event_type=EventType(trigger_config["event_type"]),
                trigger_type=TriggerType(trigger_config["trigger_type"]),
                conditions=trigger_config["conditions"],
                actions=trigger_config["actions"]
            )
        
        return None