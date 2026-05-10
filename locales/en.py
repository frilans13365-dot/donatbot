TEXTS = {
    "choose_language": "Choose language",
    "welcome": "Welcome to DonatBot! 🎉\n\nHere you can receive donations from other participants.\n\n💡 Tell your friends about this bot — the more participants, the faster you receive donations! 🚀{ad}",
    "rules_btn": "Rules",
    "my_position_btn": "📊 My position",
    "agree_btn": "I agree",
    "back_btn": "Back",
    "main_menu_btn": "Main menu",
    "rules": (
        "DonatBot Rules\n\n"
        "1. You send a donation to 5 addresses of the specified amount.\n"
        "2. You MUST include the word DONAT in the comment of each transaction.\n"
        "3. After sending, press the ✅ button — your payment is queued for automatic verification.\n"
        "4. Transactions are checked automatically every 30 seconds.\n"
        "5. After all 5 donations are confirmed — your address is added to the system at position 5.\n"
        "6. Every new participant donates to all 5 queue members including you.\n"
        "7. As new participants join, you move up the queue.\n"
        "8. When you reach position 1 — you graduate from the system, completing the full cycle.\n"
        "9. All data is protected with end-to-end encryption (E2E encryption).\n"
        "10. Minimum donation amount: {amount} TON\n"
        "11. Network: TON\n\n"
        "⚠️ Violation of rules leads to exclusion from the system without refund.\n\n"
        "By continuing, you agree to the bot rules."
    ),
    "enter_wallet": "💳 Enter your TON wallet address (starts with EQ or UQ):",
    "invalid_wallet": "❌ Invalid address format. Enter TON address (starts with EQ or UQ).",
    "donate_instructions": (
        "💸 Send donations to the following addresses:\n\n"
        "Amount: {amount} TON\n"
        "Comment: <b>DONAT</b>\n\n"
        "{addresses}\n\n"
        "⚠️ You MUST include the word <b>DONAT</b> in the comment of each transaction!\n\n"
        "After sending all donations press the button ✅"
    ),
    "check_payment_btn": "✅ I sent all donations",
    "payment_pending": "⏳ Checking your blockchain transactions... Please wait.",
    "payment_queued": (
        "⏳ Your payment has been queued for verification.\n\n"
        "We check transactions every 30 seconds.\n"
        "Once all donations are confirmed — you will receive a notification automatically.\n\n"
        "Maximum waiting time: 2 hours."
    ),
    "payment_success": (
        "🎉 All donations confirmed!\n\n"
        "Your address has been added to the system at position 5.\n"
        "Every new participant will donate to you!\n"
        "Tell your friends — the more participants, the faster you move up! 🚀"
    ),
    "payment_failed": "❌ Confirmed {confirmed} of {required} donations. Check transactions and try again.",
    "already_in_queue": "✅ You are already participating in the system!",
    "queue_position": "📊 Your position: {position} of {total}",
    "not_in_queue": "❌ You are not participating yet.\nPress Rules to get started.",
    "your_position": "👤 Your position: <b>{position}</b>",
    "graduated": (
        "🎊 Congratulations!\n\n"
        "You have completed the full system cycle!\n"
        "You received donations from all new participants while in the queue.\n\n"
        "Want to participate again? Send /start"
    ),
    "set_amount_btn": "💰 Change donation amount",
    "set_wallet_btn": "👛 Change admin wallet",
    "set_ad_btn": "📢 Change advertisement",
    "broadcast_btn": "📣 Broadcast",
    "enter_amount": "💰 Enter new donation amount in TON:",
    "amount_set": "✅ Donation amount updated: {amount} TON",
    "enter_admin_wallet": "👛 Enter new admin TON wallet address (EQ... or UQ...):",
    "wallet_set": "✅ Wallet address updated.",
    "enter_ad": "📢 Enter advertisement text (or /skip to remove):",
    "ad_set": "✅ Advertisement updated.",
    "enter_broadcast": "📣 Enter broadcast message:",
    "broadcast_done": "✅ Broadcast complete. Sent: {sent}",
    "queue_view_btn": "📋 Queue",
    "queue_list": "📋 Current queue:\n\n{list}",
}
