import os
import json
import datetime

def save_log(log_folder, chat_log):
    filename = os.path.join(log_folder, f"chat_log_latest.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(chat_log, f, indent=2, ensure_ascii=False)
