TEXTS = {
    "choose_language": "Choose language",
    "welcome": "Welcome to DonatBot",
    "rules_btn": "Rules",
    "agree_btn": "I agree",
    "back_btn": "Back",
    "main_menu_btn": "Main menu",
    "rules": (
        "DonatBot Rules\n\n"
        "1. You send a donation to 5 addresses of the specified amount.\n"
        "2. You MUST include the word DONAT in the transaction comment.\n"
        "3. After all 5 donations are confirmed — your address is added to the system.\n"
        "4. As new participants join, you move up the queue.\n"
        "5. When you reach position 2 — new participants donate to you.\n"
        "6. All data is protected with end-to-end encryption (E2E encryption).\n"
        "7. Minimum donation amount: {amount} USDT\n"
        "8. Network: TON (USDT Jetton)\n\n"
        "⚠️ Violation of rules leads to exclusion from the system without refund.\n\n"
        "By continuing, you agree to the bot rules."
    ),
    "enter_wallet": "💳 Enter your TON wallet address (starts with EQ or UQ):",
    "invalid_wallet": "❌ Invalid address format. Enter TON address (starts with EQ or UQ).",
    "donate_instructions": (
        "💸 Send donations to the following addresses:\n\n"
        "Amount: {amount} USDT (TON network)\n"
        "Comment: <b>DONAT</b>\n\n"
        "{addresses}\n\n"
        "⚠️ You MUST include the word <b>DONAT</b> in the comment of each transaction!\n\n"
        "After sending all donations press the button ✅"
    ),
    "check_payment_btn": "✅ I sent all donations",
    "payment_pending": "⏳ Checking your blockchain transactions... Please wait.",
    "payment_success": (
        "🎉 All donations confirmed!\n\n"
        "Your address has been added to the system.\n"
        "Wait for new participants — you will move up!"
    ),
    "payment_failed": "❌ Confirmed {confirmed} of {required} donations. Check transactions and try again.",
    "already_in_queue": "✅ You are already participating in the system!",
    "queue_position": "📊 Your position: {position} of {total}",
    "graduated": (
        "🎊 Congratulations!\n\n"
        "You have completed the full system cycle.\n"
        "Want to participate again? Send /start"
    ),
    "set_amount_btn": "💰 Change donation amount",
    "set_wallet_btn": "👛 Change admin wallet",
    "set_ad_btn": "📢 Change advertisement",
    "broadcast_btn": "📣 Broadcast",
    "enter_amount": "💰 Enter new donation amount in USDT:",
    "amount_set": "✅ Donation amount updated: {amount} USDT",
    "enter_admin_wallet": "👛 Enter new admin TON wallet address (EQ... or UQ...):",
    "wallet_set": "✅ Wallet address updated.",
    "enter_ad": "📢 Enter advertisement text (or /skip to remove):",
    "ad_set": "✅ Advertisement updated.",
    "enter_broadcast": "📣 Enter broadcast message:",
    "broadcast_done": "✅ Broadcast complete. Sent: {sent}",
    "queue_view_btn": "📋 Queue",
    "queue_list": "📋 Current queue:\n\n{list}",
}
