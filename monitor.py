"""
Monitoring script for bot health and performance
"""

import json
import os
import psutil
import time
from datetime import datetime
import requests

def check_bot_health():
    """Check bot health status"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "issues": [],
        "metrics": {}
    }
    
    try:
        # Check if bot process is running
        bot_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline or 'run.py' in cmdline:
                        bot_running = True
                        health_status["metrics"]["bot_pid"] = proc.info['pid']
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        health_status["metrics"]["bot_running"] = bot_running
        
        if not bot_running:
            health_status["status"] = "unhealthy"
            health_status["issues"].append("Bot process not running")
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        health_status["metrics"]["disk_usage_percent"] = disk_usage.percent
        health_status["metrics"]["disk_free_gb"] = disk_usage.free / (1024**3)
        
        if disk_usage.percent > 90:
            health_status["status"] = "warning"
            health_status["issues"].append("Disk space running low")
        
        # Check memory usage
        memory = psutil.virtual_memory()
        health_status["metrics"]["memory_usage_percent"] = memory.percent
        
        if memory.percent > 85:
            health_status["status"] = "warning"
            health_status["issues"].append("High memory usage")
        
        # Check CPU usage
        try:
           cpu = psutil.cpu_percent()
        except PermissionError:
           cpu = None

        if cpu is None:
            logger.warning("⚠️ CPU metrics unavailable (Termux restricted)")
    
        # Check database files
        db_files = [
            "db/users.json",
            "db/groups.json",
            "db/system.json",
            "db/logs.json"
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                size_mb = os.path.getsize(db_file) / (1024*1024)
                health_status["metrics"][f"db_{db_file.split('/')[-1]}_size_mb"] = size_mb
            else:
                health_status["status"] = "warning"
                health_status["issues"].append(f"Database file missing: {db_file}")
        
        # Check log files
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = os.listdir(log_dir)
            health_status["metrics"]["log_files_count"] = len(log_files)
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "error"
        health_status["issues"].append(f"Monitoring error: {str(e)}")
        return health_status

def send_alert(health_status):
    """Send alert if bot is unhealthy"""
    if health_status["status"] in ["unhealthy", "error"]:
        # Send Telegram alert to admins
        message = f"⚠️ **বট হেলথ অ্যালার্ট**\n\n"
        message += f"স্ট্যাটাস: {health_status['status']}\n"
        message += f"সময়: {health_status['timestamp']}\n\n"
        
        if health_status["issues"]:
            message += "**ইস্যুসমূহ:**\n"
            for issue in health_status["issues"]:
                message += f"• {issue}\n"
        
        # Here you would send the message via Telegram
        print(f"ALERT: {message}")

def main():
    """Main monitoring loop"""
    print("🔍 Starting bot monitor...")
    
    while True:
        try:
            # Check health
            health_status = check_bot_health()
            
            # Print status
            print(f"\n[{health_status['timestamp']}] Status: {health_status['status']}")
            
            if health_status["issues"]:
                print("Issues detected:")
                for issue in health_status["issues"]:
                    print(f"  - {issue}")
            
            # Send alert if needed
            send_alert(health_status)
            
            # Save to log file
            log_file = "logs/health_monitor.log"
            with open(log_file, 'a') as f:
                f.write(json.dumps(health_status) + '\n')
            
            # Wait before next check
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
