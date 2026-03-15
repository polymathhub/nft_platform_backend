import logging
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Dict, Set
logger = logging.getLogger(__name__)
class TelegramAdminSession:
    _sessions: Dict[int, dict] = {}
    SESSION_TIMEOUT_MINUTES = 30
    @classmethod
    def create_session(cls, chat_id: int, user_id: UUID, username: str) -> bool:
        cls._sessions[chat_id] = {
            "user_id": str(user_id),
            "username": username,
            "login_time": datetime.utcnow(),
        }
        logger.info(f"Admin session created for {username} (chat_id: {chat_id})")
        return True
    @classmethod
    def is_admin_logged_in(cls, chat_id: int) -> bool:
        if chat_id not in cls._sessions:
            return False
        session = cls._sessions[chat_id]
        login_time = session["login_time"]
        if datetime.utcnow() - login_time > timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES):
            del cls._sessions[chat_id]
            logger.info(f"Admin session expired for chat_id: {chat_id}")
            return False
        return True
    @classmethod
    def get_session(cls, chat_id: int) -> Optional[dict]:
        if cls.is_admin_logged_in(chat_id):
            return cls._sessions[chat_id]
        return None
    @classmethod
    def logout(cls, chat_id: int) -> bool:
        if chat_id in cls._sessions:
            username = cls._sessions[chat_id]["username"]
            del cls._sessions[chat_id]
            logger.info(f"Admin session ended for {username} (chat_id: {chat_id})")
            return True
        return False
    @classmethod
    def clear_all_sessions(cls):
        cls._sessions.clear()
class TelegramAdminService:
    @staticmethod
    def format_admin_dashboard() -> str:
        return (
            "<b>⚙️ ADMIN PANEL</b>\n\n"
            "Select an action to manage the platform:\n\n"
            "💰 <b>Commission Settings</b>\n"
            "   • View & Edit commission rate\n"
            "   • Manage commission wallets\n\n"
            "👥 <b>User Management</b>\n"
            "   • Make admin\n"
            "   • Remove admin\n"
            "   • Suspend/Activate users\n\n"
            "📊 <b>Platform Stats</b>\n"
            "   • View system statistics\n"
            "   • View audit logs\n"
            "   • View list of admins\n\n"
            "💾 <b>Backup & More</b>\n"
            "   • Export backup data\n"
            "   • Health check\n\n"
            "🚪 <b>Logout</b> - End admin session"
        )
    @staticmethod
    def format_commission_menu() -> str:
        return (
            "<b>💰 COMMISSION SETTINGS</b>\n\n"
            "Choose what to update:\n\n"
            "📈 <b>Commission Rate</b>\n"
            "   Current: View and change percentage (0-100%)\n\n"
            "🏪 <b>Commission Wallets</b>\n"
            "   Manage wallets for:\n"
            "   • TON (Mainnet)\n"
            "   • TRC20 (Tron)\n"
            "   • ERC20 (Ethereum/Polygon/etc)\n"
            "   • Solana\n"
        )
    @staticmethod
    def format_user_management_menu() -> str:
        return (
            "<b>👥 USER MANAGEMENT</b>\n\n"
            "Select user action:\n\n"
            "Add as Admin - Promote to admin role\n"
            "Remove Admin - Demote from admin role\n"
            "Suspend User - Block account access\n"
            "Activate User - Restore suspended account\n\n"
            "<i>After selecting, provide the user ID or username</i>"
        )
    @staticmethod
    def format_stats_menu() -> str:
        return (
            "<b>📊 PLATFORM STATISTICS & MONITORING</b>\n\n"
            "View:\n"
            "📈 System Stats - Users, NFTs, Listings, Orders, Wallets\n"
            "📋 Audit Logs - Action history from all admins\n"
            "👨‍💼 Admin List - All active administrators\n"
            "💚 Health Check - Database & system status"
        )
    @staticmethod
    def format_backup_menu() -> str:
        return (
            "<b>💾 BACKUP & UTILITIES</b>\n\n"
            "Available actions:\n"
            "📥 Export Backup - Download all platform data\n"
            "🔐 Change Password - Update admin password\n"
            "❓ Help - View command reference"
        )
