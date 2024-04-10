# ek-bot-dashboard

Parses a variety of data sources to build a little dashboard, showing interactions with the emojikitchen Twitter bot/account.

- Followers (updated once every 24 hours by cron job running the update script)
- Click counts/geostats on profile link (via Bitly API)
- Breakdown of successful/unsuccessful requests made to the bot (via logs stored elsewhere)

Runs as a plotly app from the commandline.