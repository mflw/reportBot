# reportBot 0.2
Reporter for side Project with e-mail and chat notifications and alerts

Run: python main.py

Start parametres:

no params - default, email and chat notification

'chat' - chat message only

'mail' - email notification only

'alert' - alert to group chat if status is not ok

'it' - include diagnostic information in chat or debug report

'silent' - silentMode for chat: iOS users will not receive a notification, Android users will receive a notification with no sound

'dbg' - console out only (prints chat message)

'dbgmail' - console out only (prints email message)

'dbgchat' - chat report to bot owner

'help' - args list

example: "python main.py dbg it" - console out only, prints chat message, including diagnostic information

Logging:

Errors are logging in file report_log.log. Logs stored until next running.