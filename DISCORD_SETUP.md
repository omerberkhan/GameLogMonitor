# Discord Webhook Integration

Automatically post your kills to Discord!

## Setup Instructions

### Simple 2-Step Setup

1. Open **Game Log Monitor**
2. In the **Discord Integration** section, check **"Enable Discord Webhook (post only when I kill someone)"**

**That's it!** The webhook is pre-configured for your server. Just enable it and your kills will automatically post to Discord!

### Start Monitoring

Once enabled, **only your kills are posted to Discord in real-time**. When you kill another player, it will automatically post to Discord. Your own deaths are NOT posted.

---

## Features

### Real-Time Kill Notifications

When monitoring is active and Discord webhook is enabled, each time **you kill someone**, it's automatically posted to Discord with:

- 🎮 **Victim name** (who you killed)
- ⚔️ **Your name** (the killer)
- 🔫 **Weapon used** (with friendly name)
- 💥 **Damage type**
- 📍 **Location** (ship/zone name)
- 🕐 **Timestamp**

**Important:** Only posts when **you are the killer**. Your own deaths are not posted to Discord.

### Rich Embeds

Messages are formatted as Discord embeds with:
- **Color coding**:
  - 🔴 Red: Killed by another player
  - 🟠 Orange: Suicide/self-inflicted
  - ⚫ Gray: Unknown killer
- **Organized fields** for easy reading
- **Icons** for quick identification

---

## Rate Limiting

To comply with Discord's API limits:
- Messages are sent with a **2-second delay** between each
- Maximum 30 messages per minute
- This ensures reliable delivery without hitting Discord rate limits

---

## Example Discord Message

```
☠️ Death Record

EnemyPlayer was killed by Voisys

🔫 Weapon: Scourge Railgun
💥 Damage Type: Ballistic
📍 Location: Aegis Gladius

Today at 3:45 PM
```

**Note:** This message appears when **you (Voisys) killed EnemyPlayer**. If you died, no message is posted.

---

## Troubleshooting

### "Failed to send: 404"
- The Discord webhook may have been deleted on the Discord server
- Contact the server administrator to verify the webhook still exists

### "Network error"
- Check your internet connection
- Discord may be temporarily unavailable
- Restart the application and try again

### No messages appearing when I kill someone
- Verify the **"Enable Discord Webhook"** checkbox is checked in the main window
- **Check that your account name is detected** (should show at top: "Account: YourName")
  - If it shows "Account: Not detected", the app can't identify your kills
  - Make sure the game log contains your character login
- Check that monitoring is active (button should say "Stop Monitoring")
- Verify kill events are being detected (they should appear in the overlay)
- Check the console for debug messages showing: `[Discord] Posting kill: YourName killed VictimName`
  - If you see `[Debug] Skipping Discord - Killer: X, Victim: Y`, it means you weren't the killer
- **Remember:** Only YOUR kills are posted, not when you die

---

## Privacy & Security

ℹ️ **Security Information:**

1. **Webhook permissions**:
   - The webhook can only post to the pre-configured Discord channel
   - It cannot read messages or access other channels
   - It cannot perform admin actions

2. **What gets posted**:
   - Player names from game logs
   - Weapon and location information
   - Death timestamps
   - No personal information is collected or sent

---

## Advanced Configuration

### Settings Location

Discord settings are stored in:
```
%LOCALAPPDATA%\GameLogMonitor\settings.ini
```

Format:
```ini
[Discord]
enabled = True
```

### Webhook URL

The webhook URL is hardcoded in the application:
- Located in `game_log_monitor.py`
- Variable: `self.discord_webhook_url`
- Can only be changed by modifying the source code and rebuilding

### Customizing Messages

To customize the message format, edit `discord_webhook.py`:
- `_create_embed()` method controls the embed structure
- Colors can be changed (hex format: 0xRRGGBB)
- Field names and icons can be modified

---

## Disabling Discord Integration

To disable Discord posting:
1. Simply uncheck the **"Enable Discord Webhook"** checkbox in the main window
2. Settings are saved automatically

The webhook URL remains hardcoded in the application but will not send any messages when disabled.

---

## Questions?

For issues or feature requests, please check the main README.md or create an issue on GitHub.
