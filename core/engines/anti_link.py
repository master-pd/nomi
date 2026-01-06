"""
Anti-Link System - Controls link posting in groups
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse

class AntiLink:
    """Anti-link protection system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_antilink")
        self.allowed_domains = set()
        self.blocked_domains = set()
        self.whitelist_users = set()
        self.blacklist_users = set()
        self.group_settings = {}
        
        # Default configuration
        self.config = {
            "enabled": True,
            "allow_all_links": False,
            "allow_specific_domains": True,
            "block_specific_domains": True,
            "require_admin_for_links": False,
            "action_on_violation": "delete",  # delete, warn, mute, ban
            "mute_duration": 300,
            "warning_threshold": 3,
            "scan_message_text": True,
            "scan_captions": True,
            "check_redirects": False
        }
        
        # Initialize default lists
        self._initialize_default_lists()
        
    def _initialize_default_lists(self):
        """Initialize default domain lists"""
        # Common allowed domains (safe)
        self.allowed_domains.update([
            "telegram.org",
            "github.com",
            "wikipedia.org",
            "youtube.com",
            "google.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "whatsapp.com",
            "discord.com",
            "reddit.com",
            "stackoverflow.com",
            "medium.com",
            "blogger.com",
            "wordpress.com"
        ])
        
        # Common blocked domains (spam/malware)
        self.blocked_domains.update([
            "bit.ly",
            "tinyurl.com",
            "goo.gl",
            "ow.ly",
            "adf.ly",
            "shorte.st",
            "bc.vc",
            "poketors.com",
            "ouo.io",
            "linkbucks.com"
        ])
        
    async def check_links(self, message: str, user_id: int, 
                        group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Check message for links
        
        Args:
            message: Message text
            user_id: User ID
            group_id: Group ID
            
        Returns:
            Link check result
        """
        if not self.config["enabled"]:
            return {"has_links": False, "allowed": True}
            
        # Check if user is whitelisted
        if user_id in self.whitelist_users:
            return {"has_links": False, "allowed": True}
            
        # Check if user is blacklisted
        if user_id in self.blacklist_users:
            return {
                "has_links": False,
                "allowed": False,
                "reason": "user_blacklisted",
                "action": "ban"
            }
            
        # Extract links from message
        links = self._extract_links(message)
        
        if not links:
            return {"has_links": False, "allowed": True}
            
        # Check each link
        violations = []
        allowed_links = []
        
        for link in links:
            check_result = await self._check_single_link(link, user_id, group_id)
            
            if check_result["allowed"]:
                allowed_links.append(link)
            else:
                violations.append({
                    "link": link,
                    "reason": check_result["reason"],
                    "domain": check_result.get("domain")
                })
                
        if violations:
            return {
                "has_links": True,
                "allowed": False,
                "violations": violations,
                "allowed_links": allowed_links,
                "action": self.config["action_on_violation"],
                "mute_duration": self.config["mute_duration"]
            }
        else:
            return {
                "has_links": True,
                "allowed": True,
                "links": allowed_links
            }
            
    def _extract_links(self, text: str) -> List[str]:
        """Extract links from text"""
        if not text:
            return []
            
        # Regex pattern for URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .\-?=&%+#]*'
        
        # Also match without protocol (common in messages)
        domain_pattern = r'(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:[/\w .\-?=&%+#]*)?'
        
        links = []
        
        # Find URLs with protocol
        urls = re.findall(url_pattern, text)
        links.extend(urls)
        
        # Find domains without protocol
        domains = re.findall(domain_pattern, text)
        for domain in domains:
            # Filter out words that look like domains but aren't
            if self._looks_like_domain(domain) and domain not in links:
                links.append(f"https://{domain}")
                
        return list(set(links))  # Remove duplicates
        
    def _looks_like_domain(self, text: str) -> bool:
        """Check if text looks like a domain"""
        # Common domain patterns
        domain_patterns = [
            r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$',
            r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/',
            r'^www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        ]
        
        for pattern in domain_patterns:
            if re.match(pattern, text):
                return True
                
        return False
        
    async def _check_single_link(self, link: str, user_id: int, 
                               group_id: Optional[int]) -> Dict[str, Any]:
        """Check a single link"""
        try:
            parsed_url = urlparse(link)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix for consistency
            if domain.startswith('www.'):
                domain = domain[4:]
                
            # Check if domain is blocked
            if domain in self.blocked_domains:
                return {
                    "allowed": False,
                    "reason": "blocked_domain",
                    "domain": domain
                }
                
            # Check if domain is allowed
            if domain in self.allowed_domains:
                return {
                    "allowed": True,
                    "domain": domain
                }
                
            # Check group-specific settings
            group_setting = self.group_settings.get(group_id, {})
            if group_setting.get("allow_all_links", False):
                return {"allowed": True, "domain": domain}
                
            # Check if specific domains are allowed for this group
            group_allowed = group_setting.get("allowed_domains", [])
            if domain in group_allowed:
                return {"allowed": True, "domain": domain}
                
            # Check if admin approval is required
            if self.config["require_admin_for_links"]:
                return {
                    "allowed": False,
                    "reason": "admin_approval_required",
                    "domain": domain
                }
                
            # Default: block unknown domains
            return {
                "allowed": False,
                "reason": "unknown_domain",
                "domain": domain
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error checking link {link}: {e}")
            return {"allowed": False, "reason": "parse_error"}
            
    async def add_allowed_domain(self, domain: str) -> bool:
        """
        Add domain to allowed list
        
        Args:
            domain: Domain to allow
            
        Returns:
            True if added
        """
        domain = domain.lower().strip()
        if not domain:
            return False
            
        self.allowed_domains.add(domain)
        self.logger.info(f"✅ Added allowed domain: {domain}")
        return True
        
    async def remove_allowed_domain(self, domain: str) -> bool:
        """
        Remove domain from allowed list
        
        Args:
            domain: Domain to remove
            
        Returns:
            True if removed
        """
        domain = domain.lower().strip()
        if domain in self.allowed_domains:
            self.allowed_domains.remove(domain)
            self.logger.info(f"🗑️ Removed allowed domain: {domain}")
            return True
        return False
        
    async def add_blocked_domain(self, domain: str) -> bool:
        """
        Add domain to blocked list
        
        Args:
            domain: Domain to block
            
        Returns:
            True if added
        """
        domain = domain.lower().strip()
        if not domain:
            return False
            
        self.blocked_domains.add(domain)
        self.logger.info(f"🚫 Added blocked domain: {domain}")
        return True
        
    async def remove_blocked_domain(self, domain: str) -> bool:
        """
        Remove domain from blocked list
        
        Args:
            domain: Domain to unblock
            
        Returns:
            True if removed
        """
        domain = domain.lower().strip()
        if domain in self.blocked_domains:
            self.blocked_domains.remove(domain)
            self.logger.info(f"✅ Removed blocked domain: {domain}")
            return True
        return False
        
    async def whitelist_user(self, user_id: int) -> bool:
        """
        Add user to whitelist
        
        Args:
            user_id: User ID
            
        Returns:
            True if added
        """
        self.whitelist_users.add(user_id)
        self.logger.info(f"✅ Whitelisted user: {user_id}")
        return True
        
    async def unwhitelist_user(self, user_id: int) -> bool:
        """
        Remove user from whitelist
        
        Args:
            user_id: User ID
            
        Returns:
            True if removed
        """
        if user_id in self.whitelist_users:
            self.whitelist_users.remove(user_id)
            self.logger.info(f"🗑️ Removed user from whitelist: {user_id}")
            return True
        return False
        
    async def blacklist_user(self, user_id: int) -> bool:
        """
        Add user to blacklist
        
        Args:
            user_id: User ID
            
        Returns:
            True if added
        """
        self.blacklist_users.add(user_id)
        self.logger.info(f"🚫 Blacklisted user: {user_id}")
        return True
        
    async def unblacklist_user(self, user_id: int) -> bool:
        """
        Remove user from blacklist
        
        Args:
            user_id: User ID
            
        Returns:
            True if removed
        """
        if user_id in self.blacklist_users:
            self.blacklist_users.remove(user_id)
            self.logger.info(f"✅ Removed user from blacklist: {user_id}")
            return True
        return False
        
    async def update_group_settings(self, group_id: int, settings: Dict[str, Any]) -> bool:
        """
        Update group-specific settings
        
        Args:
            group_id: Group ID
            settings: New settings
            
        Returns:
            True if updated
        """
        if group_id not in self.group_settings:
            self.group_settings[group_id] = {}
            
        self.group_settings[group_id].update(settings)
        self.logger.info(f"⚙️ Updated settings for group {group_id}")
        return True
        
    async def get_group_settings(self, group_id: int) -> Dict[str, Any]:
        """
        Get group-specific settings
        
        Args:
            group_id: Group ID
            
        Returns:
            Group settings
        """
        default_settings = {
            "enabled": self.config["enabled"],
            "allow_all_links": False,
            "allowed_domains": [],
            "blocked_domains": [],
            "require_admin": self.config["require_admin_for_links"]
        }
        
        group_settings = self.group_settings.get(group_id, {})
        return {**default_settings, **group_settings}
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get anti-link system statistics"""
        return {
            "allowed_domains_count": len(self.allowed_domains),
            "blocked_domains_count": len(self.blocked_domains),
            "whitelisted_users": len(self.whitelist_users),
            "blacklisted_users": len(self.blacklist_users),
            "groups_with_settings": len(self.group_settings),
            "config": self.config
        }
        
    async def export_domain_lists(self) -> Dict[str, List[str]]:
        """Export domain lists"""
        return {
            "allowed_domains": sorted(list(self.allowed_domains)),
            "blocked_domains": sorted(list(self.blocked_domains))
        }
        
    async def import_domain_lists(self, lists: Dict[str, List[str]]) -> bool:
        """
        Import domain lists
        
        Args:
            lists: Domain lists to import
            
        Returns:
            True if successful
        """
        try:
            if "allowed_domains" in lists:
                self.allowed_domains.update(lists["allowed_domains"])
                
            if "blocked_domains" in lists:
                self.blocked_domains.update(lists["blocked_domains"])
                
            self.logger.info(f"📥 Imported domain lists")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error importing domain lists: {e}")
            return False
            
    async def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Scan text for links (for testing/debugging)
        
        Args:
            text: Text to scan
            
        Returns:
            Scan results
        """
        links = self._extract_links(text)
        
        results = []
        for link in links:
            try:
                parsed = urlparse(link)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                    
                status = "unknown"
                if domain in self.allowed_domains:
                    status = "allowed"
                elif domain in self.blocked_domains:
                    status = "blocked"
                    
                results.append({
                    "link": link,
                    "domain": domain,
                    "status": status
                })
            except Exception as e:
                results.append({
                    "link": link,
                    "error": str(e)
                })
                
        return {
            "text": text,
            "links_found": len(links),
            "results": results
        }