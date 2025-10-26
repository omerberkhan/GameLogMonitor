"""
Discord Webhook Integration
Sends death records to a Discord channel via webhook
"""

import requests
import json
from datetime import datetime, timezone
import threading
import queue
import time


class DiscordWebhook:
    def __init__(self, webhook_url=None):
        """
        Initialize Discord webhook sender

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url and webhook_url.strip())
        self.message_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        print(f"[Discord] Webhook initialized - enabled: {self.enabled}")

    def set_webhook_url(self, url):
        """Set the webhook URL"""
        self.webhook_url = url
        self.enabled = bool(url and url.strip())

    def start(self):
        """Start the webhook worker thread"""
        if self.enabled and not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            print("[Discord] Webhook sender started")

    def stop(self):
        """Stop the webhook worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[Discord] Webhook sender stopped")

    def send_death_record(self, death_data):
        """
        Queue a death record to be sent to Discord

        Args:
            death_data: Dictionary containing death information
        """
        if not self.enabled:
            print("[Discord] Webhook not enabled, skipping send")
            return

        self.message_queue.put(death_data)
        print(f"[Discord] Queued death record for {death_data.get('actor', 'Unknown')}")

    def _worker(self):
        """Worker thread that processes the message queue"""
        while self.running:
            try:
                # Get message from queue with timeout
                death_data = self.message_queue.get(timeout=1)

                # Send to Discord
                self._send_to_discord(death_data)

                # Rate limiting - Discord allows 30 requests per minute
                time.sleep(2)  # Wait 2 seconds between messages

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Discord] Error in worker thread: {e}")

    def _send_to_discord(self, death_data):
        """
        Send a formatted death record to Discord

        Args:
            death_data: Dictionary containing death information
        """
        if not self.webhook_url:
            return

        try:
            # Format the embed
            embed = self._create_embed(death_data)

            payload = {
                "embeds": [embed]
            }

            # Send to Discord
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                print(f"[Discord] Sent death record: {death_data.get('actor', 'Unknown')}")
            else:
                print(f"[Discord] Failed to send: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"[Discord] Network error sending webhook: {e}")
        except Exception as e:
            print(f"[Discord] Error sending webhook: {e}")

    def _create_embed(self, death_data):
        """
        Create a Discord embed from death data

        Args:
            death_data: Dictionary containing death information

        Returns:
            Dictionary representing Discord embed
        """
        # Parse timestamp
        timestamp_str = death_data.get('timestamp')
        if timestamp_str:
            try:
                # Parse ISO timestamp
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                dt = dt.replace(tzinfo=timezone.utc)
                iso_timestamp = dt.isoformat()
            except:
                iso_timestamp = datetime.now(timezone.utc).isoformat()
        else:
            iso_timestamp = datetime.now(timezone.utc).isoformat()

        # Get data
        actor = death_data.get('actor', 'Unknown')
        killer = death_data.get('killer', 'Unknown')
        weapon = death_data.get('weapon_display', death_data.get('weapon', 'Unknown'))
        damage = death_data.get('damage', 'Unknown')
        location = death_data.get('location_display', death_data.get('location', 'Unknown'))

        # Determine color based on killer
        if killer == actor:
            color = 0xFFA500  # Orange for suicide
        elif killer == 'Unknown':
            color = 0x808080  # Gray for unknown
        else:
            color = 0xFF0000  # Red for killed by someone else

        # Create description
        description = f"**{actor}** was killed"

        if killer != 'Unknown':
            if killer == actor:
                description = f"**{actor}** died"
            else:
                description += f" by **{killer}**"

        # Create embed
        embed = {
            "title": "☠️ Death Record",
            "description": description,
            "color": color,
            "timestamp": iso_timestamp,
            "fields": []
        }

        # Add weapon if available
        if weapon and weapon != 'Unknown':
            embed["fields"].append({
                "name": "🔫 Weapon",
                "value": weapon,
                "inline": True
            })

        # Add damage type
        if damage and damage != 'Unknown':
            embed["fields"].append({
                "name": "💥 Damage Type",
                "value": damage,
                "inline": True
            })

        # Add location if available
        if location and location != 'Unknown':
            embed["fields"].append({
                "name": "📍 Location",
                "value": location,
                "inline": False
            })

        return embed

    def send_test_message(self):
        """Send a test message to verify webhook is working"""
        if not self.webhook_url:
            return False, "No webhook URL configured"

        try:
            test_data = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "actor": "TestPlayer",
                "killer": "TestKiller",
                "weapon": "Test Weapon",
                "weapon_display": "Test Weapon",
                "damage": "Test Damage",
                "location": "Test Location",
                "location_display": "Test Location"
            }

            embed = self._create_embed(test_data)
            embed["title"] = "✅ Test Message"
            embed["description"] = "Discord webhook is configured correctly!"
            embed["color"] = 0x00FF00  # Green

            payload = {"embeds": [embed]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                return True, "Test message sent successfully!"
            else:
                return False, f"Failed: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

