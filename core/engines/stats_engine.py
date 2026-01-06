"""
Stats Engine - Handles statistics and analytics
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import statistics

class StatsEngine:
    """Engine for statistics and analytics"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_stats")
        self.json_loader = json_loader
        self.stats_data = {}
        self.realtime_stats = {}
        
    async def initialize(self):
        """Initialize stats engine"""
        self.logger.info("📊 Initializing stats engine...")
        await self._load_stats_data()
        
    async def _load_stats_data(self):
        """Load statistics data"""
        try:
            stats_file = Path("data/statistics.json")
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats_data = json.load(f)
                    
                self.logger.info(f"📂 Loaded statistics data")
        except Exception as e:
            self.logger.error(f"❌ Error loading stats: {e}")
            self.stats_data = {
                "daily_stats": {},
                "hourly_stats": {},
                "user_stats": {},
                "group_stats": {},
                "system_stats": {}
            }
            
    async def _save_stats_data(self):
        """Save statistics data"""
        try:
            stats_file = Path("data/statistics.json")
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving stats: {e}")
            
    async def record_message(self, user_id: int, group_id: Optional[int], 
                           message_type: str = "text", length: int = 0):
        """
        Record a message in statistics
        
        Args:
            user_id: User ID
            group_id: Group ID (None for private)
            message_type: Type of message
            length: Message length
        """
        current_time = datetime.now()
        date_key = current_time.strftime("%Y-%m-%d")
        hour_key = current_time.strftime("%Y-%m-%d %H:00")
        
        # Initialize data structures
        if "daily_stats" not in self.stats_data:
            self.stats_data["daily_stats"] = {}
        if "hourly_stats" not in self.stats_data:
            self.stats_data["hourly_stats"] = {}
        if "user_stats" not in self.stats_data:
            self.stats_data["user_stats"] = {}
        if "group_stats" not in self.stats_data:
            self.stats_data["group_stats"] = {}
            
        # Update daily stats
        if date_key not in self.stats_data["daily_stats"]:
            self.stats_data["daily_stats"][date_key] = {
                "total_messages": 0,
                "text_messages": 0,
                "voice_messages": 0,
                "photo_messages": 0,
                "total_users": set(),
                "total_groups": set(),
                "avg_message_length": 0,
                "message_lengths": []
            }
            
        daily = self.stats_data["daily_stats"][date_key]
        daily["total_messages"] += 1
        daily[f"{message_type}_messages"] = daily.get(f"{message_type}_messages", 0) + 1
        
        if length > 0:
            daily["message_lengths"].append(length)
            daily["avg_message_length"] = statistics.mean(daily["message_lengths"])
            
        if user_id not in daily["total_users"]:
            if isinstance(daily["total_users"], set):
                daily["total_users"].add(user_id)
            else:
                daily["total_users"] = set(daily["total_users"])
                daily["total_users"].add(user_id)
                
        if group_id and group_id not in daily["total_groups"]:
            if isinstance(daily["total_groups"], set):
                daily["total_groups"].add(group_id)
            else:
                daily["total_groups"] = set(daily["total_groups"])
                daily["total_groups"].add(group_id)
                
        # Convert sets to lists for JSON serialization
        daily["total_users"] = list(daily["total_users"])
        daily["total_groups"] = list(daily["total_groups"])
        
        # Update hourly stats
        if hour_key not in self.stats_data["hourly_stats"]:
            self.stats_data["hourly_stats"][hour_key] = {
                "messages": 0,
                "users": set(),
                "groups": set()
            }
            
        hourly = self.stats_data["hourly_stats"][hour_key]
        hourly["messages"] += 1
        hourly["users"].add(user_id)
        if group_id:
            hourly["groups"].add(group_id)
            
        # Convert sets to lists
        hourly["users"] = list(hourly["users"])
        hourly["groups"] = list(hourly["groups"])
        
        # Update user stats
        user_key = str(user_id)
        if user_key not in self.stats_data["user_stats"]:
            self.stats_data["user_stats"][user_key] = {
                "total_messages": 0,
                "daily_messages": {},
                "last_message": current_time.isoformat(),
                "message_types": {},
                "avg_message_length": 0,
                "message_lengths": []
            }
            
        user_stats = self.stats_data["user_stats"][user_key]
        user_stats["total_messages"] += 1
        user_stats["last_message"] = current_time.isoformat()
        user_stats["message_types"][message_type] = user_stats["message_types"].get(message_type, 0) + 1
        
        if length > 0:
            user_stats["message_lengths"].append(length)
            user_stats["avg_message_length"] = statistics.mean(user_stats["message_lengths"])
            
        # Update group stats
        if group_id:
            group_key = str(group_id)
            if group_key not in self.stats_data["group_stats"]:
                self.stats_data["group_stats"][group_key] = {
                    "total_messages": 0,
                    "daily_messages": {},
                    "active_users": set(),
                    "message_types": {},
                    "last_activity": current_time.isoformat()
                }
                
            group_stats = self.stats_data["group_stats"][group_key]
            group_stats["total_messages"] += 1
            group_stats["last_activity"] = current_time.isoformat()
            group_stats["active_users"].add(user_id)
            group_stats["message_types"][message_type] = group_stats["message_types"].get(message_type, 0) + 1
            
            # Convert set to list
            group_stats["active_users"] = list(group_stats["active_users"])
            
        # Update realtime stats
        self._update_realtime_stats()
        
        # Periodic save (every 10 messages)
        total_messages = sum(d["total_messages"] for d in self.stats_data["daily_stats"].values())
        if total_messages % 10 == 0:
            await self._save_stats_data()
            
    def _update_realtime_stats(self):
        """Update realtime statistics"""
        current_time = datetime.now()
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        
        if minute_key not in self.realtime_stats:
            self.realtime_stats[minute_key] = {
                "messages": 0,
                "users": set(),
                "groups": set(),
                "timestamp": current_time.timestamp()
            }
            
            # Cleanup old realtime stats (keep last 60 minutes)
            old_keys = []
            for key in self.realtime_stats.keys():
                try:
                    key_time = datetime.strptime(key, "%Y-%m-%d %H:%M")
                    if (current_time - key_time).total_seconds() > 3600:
                        old_keys.append(key)
                except:
                    old_keys.append(key)
                    
            for key in old_keys:
                del self.realtime_stats[key]
                
        realtime = self.realtime_stats[minute_key]
        realtime["messages"] += 1
        
    async def record_user_join(self, user_id: int, group_id: int):
        """
        Record user join
        
        Args:
            user_id: User ID
            group_id: Group ID
        """
        current_time = datetime.now()
        date_key = current_time.strftime("%Y-%m-%d")
        
        # Update daily stats
        if date_key in self.stats_data.get("daily_stats", {}):
            daily = self.stats_data["daily_stats"][date_key]
            daily["joins"] = daily.get("joins", 0) + 1
            
    async def record_user_leave(self, user_id: int, group_id: int):
        """
        Record user leave
        
        Args:
            user_id: User ID
            group_id: Group ID
        """
        current_time = datetime.now()
        date_key = current_time.strftime("%Y-%m-%d")
        
        # Update daily stats
        if date_key in self.stats_data.get("daily_stats", {}):
            daily = self.stats_data["daily_stats"][date_key]
            daily["leaves"] = daily.get("leaves", 0) + 1
            
    async def record_command(self, user_id: int, command: str, 
                           group_id: Optional[int] = None, success: bool = True):
        """
        Record command usage
        
        Args:
            user_id: User ID
            command: Command name
            group_id: Group ID
            success: Whether command succeeded
        """
        current_time = datetime.now()
        date_key = current_time.strftime("%Y-%m-%d")
        
        # Initialize command stats
        if "command_stats" not in self.stats_data:
            self.stats_data["command_stats"] = {}
            
        # Update command stats
        if command not in self.stats_data["command_stats"]:
            self.stats_data["command_stats"][command] = {
                "total_usage": 0,
                "successful": 0,
                "failed": 0,
                "daily_usage": {},
                "users": set(),
                "groups": set()
            }
            
        cmd_stats = self.stats_data["command_stats"][command]
        cmd_stats["total_usage"] += 1
        
        if success:
            cmd_stats["successful"] += 1
        else:
            cmd_stats["failed"] += 1
            
        cmd_stats["users"].add(user_id)
        if group_id:
            cmd_stats["groups"].add(group_id)
            
        # Update daily usage
        if date_key not in cmd_stats["daily_usage"]:
            cmd_stats["daily_usage"][date_key] = 0
        cmd_stats["daily_usage"][date_key] += 1
        
        # Convert sets to lists
        cmd_stats["users"] = list(cmd_stats["users"])
        cmd_stats["groups"] = list(cmd_stats["groups"])
        
    async def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily statistics
        
        Args:
            date: Date in YYYY-MM-DD format (None for today)
            
        Returns:
            Daily statistics
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        daily_stats = self.stats_data.get("daily_stats", {}).get(date, {})
        
        # Calculate additional metrics
        total_messages = daily_stats.get("total_messages", 0)
        total_users = len(daily_stats.get("total_users", []))
        total_groups = len(daily_stats.get("total_groups", []))
        
        return {
            "date": date,
            "total_messages": total_messages,
            "text_messages": daily_stats.get("text_messages", 0),
            "voice_messages": daily_stats.get("voice_messages", 0),
            "photo_messages": daily_stats.get("photo_messages", 0),
            "total_users": total_users,
            "total_groups": total_groups,
            "avg_message_length": daily_stats.get("avg_message_length", 0),
            "joins": daily_stats.get("joins", 0),
            "leaves": daily_stats.get("leaves", 0),
            "messages_per_user": total_messages / total_users if total_users > 0 else 0
        }
        
    async def get_hourly_stats(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get hourly statistics for a date
        
        Args:
            date: Date in YYYY-MM-DD format (None for today)
            
        Returns:
            List of hourly statistics
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        hourly_stats = []
        
        for hour_key, stats in self.stats_data.get("hourly_stats", {}).items():
            if hour_key.startswith(date):
                hour = hour_key.split(" ")[1]
                hourly_stats.append({
                    "hour": hour,
                    "messages": stats.get("messages", 0),
                    "users": len(stats.get("users", [])),
                    "groups": len(stats.get("groups", []))
                })
                
        # Sort by hour
        hourly_stats.sort(key=lambda x: x["hour"])
        return hourly_stats
        
    async def get_user_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            days: Number of days to include
            
        Returns:
            User statistics
        """
        user_key = str(user_id)
        user_stats = self.stats_data.get("user_stats", {}).get(user_key, {})
        
        # Calculate activity trend
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_activity = {}
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_activity[date] = user_stats.get("daily_messages", {}).get(date, 0)
            
        # Calculate most active hours
        hourly_activity = {}
        for hour_key, stats in self.stats_data.get("hourly_stats", {}).items():
            if user_id in stats.get("users", []):
                hour = hour_key.split(" ")[1]
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                
        return {
            "user_id": user_id,
            "total_messages": user_stats.get("total_messages", 0),
            "last_message": user_stats.get("last_message"),
            "message_types": user_stats.get("message_types", {}),
            "avg_message_length": user_stats.get("avg_message_length", 0),
            "daily_activity": daily_activity,
            "hourly_activity": dict(sorted(hourly_activity.items())),
            "activity_score": self._calculate_activity_score(user_stats)
        }
        
    async def get_group_stats(self, group_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get group statistics
        
        Args:
            group_id: Group ID
            days: Number of days to include
            
        Returns:
            Group statistics
        """
        group_key = str(group_id)
        group_stats = self.stats_data.get("group_stats", {}).get(group_key, {})
        
        # Calculate activity metrics
        end_date = datetime.now()
        
        daily_activity = {}
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_activity[date] = group_stats.get("daily_messages", {}).get(date, 0)
            
        # Get top users in group
        top_users = []
        for user_key, user_data in self.stats_data.get("user_stats", {}).items():
            # This would need message count per group, which we don't track currently
            # For now, return active users
            pass
            
        return {
            "group_id": group_id,
            "total_messages": group_stats.get("total_messages", 0),
            "last_activity": group_stats.get("last_activity"),
            "active_users": len(group_stats.get("active_users", [])),
            "message_types": group_stats.get("message_types", {}),
            "daily_activity": daily_activity,
            "activity_level": self._calculate_group_activity(group_stats)
        }
        
    async def get_command_stats(self, command: Optional[str] = None, 
                              days: int = 30) -> Dict[str, Any]:
        """
        Get command statistics
        
        Args:
            command: Command name (None for all commands)
            days: Number of days to include
            
        Returns:
            Command statistics
        """
        if command:
            cmd_stats = self.stats_data.get("command_stats", {}).get(command, {})
            
            # Calculate daily usage for specified days
            end_date = datetime.now()
            daily_usage = {}
            
            for i in range(days):
                date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_usage[date] = cmd_stats.get("daily_usage", {}).get(date, 0)
                
            return {
                "command": command,
                "total_usage": cmd_stats.get("total_usage", 0),
                "success_rate": cmd_stats.get("successful", 0) / cmd_stats.get("total_usage", 1) * 100,
                "unique_users": len(cmd_stats.get("users", [])),
                "unique_groups": len(cmd_stats.get("groups", [])),
                "daily_usage": daily_usage,
                "popularity_rank": await self._get_command_rank(command)
            }
        else:
            # Get all commands
            all_commands = {}
            for cmd, stats in self.stats_data.get("command_stats", {}).items():
                all_commands[cmd] = {
                    "total_usage": stats.get("total_usage", 0),
                    "success_rate": stats.get("successful", 0) / stats.get("total_usage", 1) * 100,
                    "unique_users": len(stats.get("users", [])),
                    "last_used": max(stats.get("daily_usage", {}).keys(), default=None)
                }
                
            return {
                "total_commands": len(all_commands),
                "total_usage": sum(c["total_usage"] for c in all_commands.values()),
                "commands": dict(sorted(all_commands.items(), 
                                      key=lambda x: x[1]["total_usage"], 
                                      reverse=True)[:20])  # Top 20
            }
            
    async def get_realtime_stats(self) -> Dict[str, Any]:
        """
        Get realtime statistics
        
        Returns:
            Realtime statistics
        """
        current_time = datetime.now()
        last_hour_stats = []
        
        # Calculate stats for last 60 minutes
        for i in range(60):
            minute_time = current_time - timedelta(minutes=i)
            minute_key = minute_time.strftime("%Y-%m-%d %H:%M")
            
            stats = self.realtime_stats.get(minute_key, {"messages": 0, "users": set(), "groups": set()})
            last_hour_stats.append({
                "time": minute_key,
                "messages": stats["messages"],
                "users": len(stats.get("users", set())),
                "groups": len(stats.get("groups", set()))
            })
            
        # Calculate current rate (messages per minute)
        current_rate = sum(s["messages"] for s in last_hour_stats[:5]) / 5 if len(last_hour_stats) >= 5 else 0
        
        # Calculate peak hour
        hourly_messages = {}
        for stats in last_hour_stats:
            hour = stats["time"][:13]  # Get hour part
            hourly_messages[hour] = hourly_messages.get(hour, 0) + stats["messages"]
            
        peak_hour = max(hourly_messages.items(), key=lambda x: x[1], default=(None, 0))
        
        return {
            "current_rate_messages_per_minute": current_rate,
            "last_hour_messages": sum(s["messages"] for s in last_hour_stats),
            "last_hour_users": len(set().union(*[s.get("users", set()) for s in last_hour_stats])),
            "last_hour_groups": len(set().union(*[s.get("groups", set()) for s in last_hour_stats])),
            "peak_hour": {
                "hour": peak_hour[0],
                "messages": peak_hour[1]
            },
            "recent_activity": last_hour_stats[:10]  # Last 10 minutes
        }
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide statistics
        
        Returns:
            System statistics
        """
        # Calculate overall totals
        total_messages = sum(d["total_messages"] for d in self.stats_data.get("daily_stats", {}).values())
        total_users = set()
        total_groups = set()
        
        for daily in self.stats_data.get("daily_stats", {}).values():
            total_users.update(daily.get("total_users", []))
            total_groups.update(daily.get("total_groups", []))
            
        # Calculate active users (last 7 days)
        active_users = set()
        end_date = datetime.now()
        
        for i in range(7):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.stats_data.get("daily_stats", {}):
                active_users.update(self.stats_data["daily_stats"][date].get("total_users", []))
                
        # Calculate message growth
        daily_growth = []
        dates = sorted(self.stats_data.get("daily_stats", {}).keys())[-30:]  # Last 30 days
        
        for date in dates:
            daily_growth.append({
                "date": date,
                "messages": self.stats_data["daily_stats"][date].get("total_messages", 0),
                "users": len(self.stats_data["daily_stats"][date].get("total_users", []))
            })
            
        return {
            "total_messages": total_messages,
            "total_users": len(total_users),
            "total_groups": len(total_groups),
            "active_users_7d": len(active_users),
            "avg_messages_per_day": total_messages / max(len(dates), 1),
            "avg_messages_per_user": total_messages / max(len(total_users), 1),
            "daily_growth": daily_growth,
            "most_active_day": max(self.stats_data.get("daily_stats", {}).items(), 
                                 key=lambda x: x[1].get("total_messages", 0), 
                                 default=(None, {})),
            "peak_hour": await self._get_peak_hour()
        }
        
    async def _get_peak_hour(self) -> Tuple[str, int]:
        """Get peak activity hour"""
        peak_hour = None
        peak_messages = 0
        
        for hour_key, stats in self.stats_data.get("hourly_stats", {}).items():
            messages = stats.get("messages", 0)
            if messages > peak_messages:
                peak_messages = messages
                peak_hour = hour_key
                
        return peak_hour, peak_messages
        
    async def _get_command_rank(self, command: str) -> int:
        """Get command popularity rank"""
        commands = self.stats_data.get("command_stats", {})
        if not commands or command not in commands:
            return 0
            
        sorted_commands = sorted(commands.items(), 
                               key=lambda x: x[1].get("total_usage", 0), 
                               reverse=True)
                               
        for rank, (cmd, _) in enumerate(sorted_commands, 1):
            if cmd == command:
                return rank
                
        return 0
        
    def _calculate_activity_score(self, user_stats: Dict[str, Any]) -> float:
        """Calculate user activity score"""
        score = 0
        
        # Message count contribution
        total_messages = user_stats.get("total_messages", 0)
        score += min(total_messages * 0.1, 30)  # Max 30 points
        
        # Recency contribution (last message within 24 hours)
        last_message = user_stats.get("last_message")
        if last_message:
            try:
                last_time = datetime.fromisoformat(last_message)
                if (datetime.now() - last_time).total_seconds() < 86400:
                    score += 20
            except:
                pass
                
        # Message diversity contribution
        message_types = user_stats.get("message_types", {})
        if len(message_types) > 1:
            score += min(len(message_types) * 5, 15)  # Max 15 points
            
        return min(score, 100)
        
    def _calculate_group_activity(self, group_stats: Dict[str, Any]) -> str:
        """Calculate group activity level"""
        total_messages = group_stats.get("total_messages", 0)
        active_users = len(group_stats.get("active_users", []))
        
        if total_messages == 0:
            return "inactive"
        elif total_messages < 100:
            return "low"
        elif total_messages < 500:
            return "medium"
        elif total_messages < 1000:
            return "high"
        else:
            return "very_high"
            
    async def generate_report(self, report_type: str = "daily", 
                            date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate statistics report
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            date: Reference date
            
        Returns:
            Report data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        if report_type == "daily":
            return await self._generate_daily_report(date)
        elif report_type == "weekly":
            return await self._generate_weekly_report(date)
        elif report_type == "monthly":
            return await self._generate_monthly_report(date)
        else:
            return {"error": "Invalid report type"}
            
    async def _generate_daily_report(self, date: str) -> Dict[str, Any]:
        """Generate daily report"""
        daily_stats = await self.get_daily_stats(date)
        hourly_stats = await self.get_hourly_stats(date)
        
        return {
            "report_type": "daily",
            "date": date,
            "summary": daily_stats,
            "hourly_breakdown": hourly_stats,
            "top_commands": await self._get_top_commands_for_date(date),
            "insights": self._generate_daily_insights(daily_stats, hourly_stats)
        }
        
    async def _generate_weekly_report(self, date: str) -> Dict[str, Any]:
        """Generate weekly report"""
        start_date = datetime.strptime(date, "%Y-%m-%d")
        
        weekly_data = []
        for i in range(7):
            current_date = (start_date - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_stats = await self.get_daily_stats(current_date)
            weekly_data.append({
                "date": current_date,
                **daily_stats
            })
            
        # Calculate weekly totals
        total_messages = sum(d["total_messages"] for d in weekly_data)
        avg_messages = total_messages / 7
        
        return {
            "report_type": "weekly",
            "week_start": (start_date - timedelta(days=6)).strftime("%Y-%m-%d"),
            "week_end": date,
            "total_messages": total_messages,
            "average_daily_messages": avg_messages,
            "daily_breakdown": weekly_data,
            "growth_rate": self._calculate_growth_rate(weekly_data),
            "weekly_insights": self._generate_weekly_insights(weekly_data)
        }
        
    async def _generate_monthly_report(self, date: str) -> Dict[str, Any]:
        """Generate monthly report"""
        # Similar to weekly but for 30 days
        pass
        
    async def _get_top_commands_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Get top commands for a date"""
        top_commands = []
        
        for command, stats in self.stats_data.get("command_stats", {}).items():
            usage = stats.get("daily_usage", {}).get(date, 0)
            if usage > 0:
                top_commands.append({
                    "command": command,
                    "usage": usage,
                    "success_rate": stats.get("successful", 0) / stats.get("total_usage", 1) * 100
                })
                
        top_commands.sort(key=lambda x: x["usage"], reverse=True)
        return top_commands[:10]
        
    def _generate_daily_insights(self, daily_stats: Dict[str, Any], 
                               hourly_stats: List[Dict[str, Any]]) -> List[str]:
        """Generate daily insights"""
        insights = []
        
        total_messages = daily_stats.get("total_messages", 0)
        peak_hour = max(hourly_stats, key=lambda x: x["messages"], default=None)
        
        if total_messages == 0:
            insights.append("No activity recorded today")
        else:
            if peak_hour:
                insights.append(f"Peak activity hour: {peak_hour['hour']} ({peak_hour['messages']} messages)")
                
            if daily_stats.get("avg_message_length", 0) > 50:
                insights.append("Users are sending longer messages than average")
            elif daily_stats.get("avg_message_length", 0) < 10:
                insights.append("Users are sending shorter messages than average")
                
        return insights
        
    def _generate_weekly_insights(self, weekly_data: List[Dict[str, Any]]) -> List[str]:
        """Generate weekly insights"""
        insights = []
        
        messages_by_day = [d["total_messages"] for d in weekly_data]
        avg_messages = statistics.mean(messages_by_day)
        
        if max(messages_by_day) > avg_messages * 1.5:
            max_day_index = messages_by_day.index(max(messages_by_day))
            max_day = weekly_data[max_day_index]["date"]
            insights.append(f"Highest activity on {max_day} with {max(messages_by_day)} messages")
            
        if statistics.stdev(messages_by_day) > avg_messages * 0.5:
            insights.append("Activity levels are highly variable throughout the week")
        else:
            insights.append("Activity levels are consistent throughout the week")
            
        return insights
        
    def _calculate_growth_rate(self, weekly_data: List[Dict[str, Any]]) -> float:
        """Calculate week-over-week growth rate"""
        if len(weekly_data) < 7:
            return 0
            
        first_day = weekly_data[0]["total_messages"]
        last_day = weekly_data[-1]["total_messages"]
        
        if first_day == 0:
            return 0
            
        return ((last_day - first_day) / first_day) * 100
        
    async def cleanup_old_stats(self, max_age_days: int = 90):
        """Cleanup old statistics"""
        current_time = datetime.now()
        old_dates = []
        
        for date_key in self.stats_data.get("daily_stats", {}).keys():
            try:
                date = datetime.strptime(date_key, "%Y-%m-%d")
                if (current_time - date).days > max_age_days:
                    old_dates.append(date_key)
            except:
                old_dates.append(date_key)
                
        # Remove old daily stats
        for date in old_dates:
            if date in self.stats_data.get("daily_stats", {}):
                del self.stats_data["daily_stats"][date]
                
        # Cleanup hourly stats
        old_hours = []
        for hour_key in self.stats_data.get("hourly_stats", {}).keys():
            try:
                hour_time = datetime.strptime(hour_key, "%Y-%m-%d %H:00")
                if (current_time - hour_time).days > 30:
                    old_hours.append(hour_key)
            except:
                old_hours.append(hour_key)
                
        for hour in old_hours:
            if hour in self.stats_data.get("hourly_stats", {}):
                del self.stats_data["hourly_stats"][hour]
                
        if old_dates or old_hours:
            await self._save_stats_data()
            self.logger.info(f"🧹 Cleaned up {len(old_dates)} old daily stats and {len(old_hours)} old hourly stats")
            
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get stats engine statistics"""
        daily_count = len(self.stats_data.get("daily_stats", {}))
        hourly_count = len(self.stats_data.get("hourly_stats", {}))
        user_count = len(self.stats_data.get("user_stats", {}))
        group_count = len(self.stats_data.get("group_stats", {}))
        command_count = len(self.stats_data.get("command_stats", {}))
        
        # Calculate data size
        import sys
        stats_size = sys.getsizeof(json.dumps(self.stats_data, ensure_ascii=False))
        
        return {
            "daily_records": daily_count,
            "hourly_records": hourly_count,
            "user_records": user_count,
            "group_records": group_count,
            "command_records": command_count,
            "realtime_records": len(self.realtime_stats),
            "total_records": daily_count + hourly_count + user_count + group_count + command_count,
            "data_size_mb": stats_size / (1024 * 1024),
            "last_updated": datetime.now().isoformat()
        }