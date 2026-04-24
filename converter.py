import json
from collections import defaultdict
from pathlib import Path

import questionary

def convert_sky_to_logitech_optimized(input_file, output_file):
    # 1. 定義按鍵映射表
    key_map = {
        "1Key0": {"name": "Y", "hid": "28"},
        "1Key1": {"name": "U", "hid": "24"},
        "1Key2": {"name": "I", "hid": "12"},
        "1Key3": {"name": "O", "hid": "18"},
        "1Key4": {"name": "P", "hid": "19"},
        "1Key5": {"name": "H", "hid": "11"},
        "1Key6": {"name": "J", "hid": "13"},
        "1Key7": {"name": "K", "hid": "14"},
        "1Key8": {"name": "L", "hid": "15"},
        "1Key9": {"name": ";", "hid": "51"},
        "1Key10": {"name": "N", "hid": "17"},
        "1Key11": {"name": "M", "hid": "16"},
        "1Key12": {"name": ",", "hid": "54"},
        "1Key13": {"name": ".", "hid": "55"},
        "1Key14": {"name": "/", "hid": "56"}
    }

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    song_data = data[0] if isinstance(data, list) else data
    notes = song_data.get("songNotes", [])
    
    # 2. 將相同時間點的音符群組化 (處理和弦)
    time_groups = defaultdict(list)
    for note in notes:
        time_groups[note["time"]].append(note["key"])
    
    # 排序時間點
    sorted_times = sorted(time_groups.keys())
    
    macro_events = []
    last_time = 0
    click_duration = 20  # 按下與抬起之間的固定延遲

    for current_time in sorted_times:
        keys_in_group = time_groups[current_time]
        
        # 計算與上一個音組結束點（抬起後）的等待時間
        wait_time = current_time - last_time
        if wait_time > 0:
            macro_events.append({"delay": {"durationMs": wait_time}})
        
        # --- 和弦處理開始 ---
        # A. 先按下音組中所有的鍵
        for key_code in keys_in_group:
            key_info = key_map.get(key_code)
            if key_info:
                macro_events.append({
                    "keyboard": {
                        "displayName": key_info["name"],
                        "hidUsage": key_info["hid"],
                        "isDown": True
                    }
                })
        
        # B. 預設延遲 (確保遊戲判定成功)
        macro_events.append({"delay": {"durationMs": click_duration}})
        
        # C. 再抬起音組中所有的鍵
        for key_code in keys_in_group:
            key_info = key_map.get(key_code)
            if key_info:
                macro_events.append({
                    "keyboard": {
                        "displayName": key_info["name"],
                        "hidUsage": key_info["hid"]
                    }
                })
        # --- 和弦處理結束 ---

        # 更新最後標記時間為目前音組「結束後」的時間點
        last_time = current_time + click_duration

    # 封裝格式
    logitech_macro = {
        "cards": [
            {
                "events": macro_events,
                "name": song_data.get("name", "Sky_Music_Grouped")
            }
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(logitech_macro, f, indent=2, ensure_ascii=False)

def main():
    base_dir = Path(__file__).resolve().parent
    txt_files = sorted(base_dir.glob('*.txt'))

    if not txt_files:
        print('目前資料夾內沒有找到 .txt 檔案。')
        return

    selected_files = questionary.checkbox(
        '選擇要轉換的 txt 檔案：',
        choices=[questionary.Choice(str(path.name), value=path) for path in txt_files],
        validate=lambda selected: True if selected else '請至少選擇一個檔案。',
    ).ask()

    if not selected_files:
        print('沒有選擇任何檔案，已取消。')
        return

    for input_path in selected_files:
        output_path = input_path.with_suffix('.json')
        convert_sky_to_logitech_optimized(str(input_path), str(output_path))
        print(f'已完成：{input_path.name} -> {output_path.name}')

    print('全部轉換完成！')


if __name__ == '__main__':
    main()