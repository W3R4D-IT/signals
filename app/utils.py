def update_hit_field(message:dict):
    if(message['event'] != "updated"): 
        return message
    try:
        
        # Check if the message contains "sl_hit"
        if message.get("sl_hit") == "1":
            message["hit"] = "sl"

        # Check if the message contains "entry_hit"
        elif message.get("entry_hit") in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            message["hit"] = "entry"

        # Loop through possible tp hits from tp1 to tp8
        for i in range(1, 9):
            tp_key = f"tp{i}_hit"
            if message.get(tp_key) == "1":
                message["hit"] = f"tp{i}"
                break
        if message.get("hit"):    
            message["hit"] = message["hit"].upper()
    
    except Exception as ex:
        print(ex)
    
    return message
