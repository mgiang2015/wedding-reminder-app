# 💍 Le & Zel — Wedding WhatsApp Sender

A minimal Flask web app to trigger bulk WhatsApp sends to your wedding guests from your phone.

## Structure

```
wedding-app/
├── app.py              # Flask server + all send logic
├── guests.csv          # Your guest list (commit this to the repo)
├── templates/
│   └── index.html      # Mobile-friendly button UI
├── requirements.txt
├── render.yaml
└── .env.example
```

## Setup

### 1. Add your guest list

Place your `guests.csv` in the project root. Required columns:

```
full_name,phone_number,guest_id
John Tan,+6591234567,001
Jane Lim,98765432,002
```

Phone numbers without `+` are automatically prefixed with `+65`.

### 2. Deploy to Render

1. Push the repo (including `guests.csv`) to GitHub
2. In Render: **New → Web Service** → connect your repo
3. Render will pick up `render.yaml` automatically
4. Go to **Environment** and set:
   - `TWILIO_ACCOUNT_SID` — from Twilio Console
   - `TWILIO_AUTH_TOKEN` — from Twilio Console
   - `TWILIO_FROM_NUMBER` — your approved WhatsApp sender (already defaulted)
5. Deploy

### 3. Use it

Open your Render URL on your phone. Tap a button, confirm, done.

- **Reminders** — 2 weeks / 1 week / 1 day / day-of
- **Check-in QR Code** — sends personalised QR with guest_id
- **After Wedding** — post-event message

The execution log shows live results for every guest.

## Updating the guest list

Edit `guests.csv` locally and push to GitHub. Render will redeploy automatically.
