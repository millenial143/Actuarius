import modules.agent as agent
import modules.database as db
import modules.whisper_stt as whisp
from pathlib import Path

# ================= НАСТРОЙКИ =================
# Путь к папке с wav файлами (измените на свой)
DATABASE_PATH = "../database"
REC_FOLDER_PATH = "/home/treadonme/ImportantSyncFolder/NotesBase/Recordings"
TXT_FOLDER_PATH = "/home/treadonme/ImportantSyncFolder/NotesBase/Texts"
OBSIDIAN_FOLDER_PATH = "/home/treadonme/ImportantSyncFolder/NotesBase/Obsidian"

# Размер модели (tiny, base, small, medium, large)
MODEL_SIZE = "small"

# Язык аудио (указание языка ускоряет работу и повышает точность)
LANGUAGE = "ru"
# =============================================

def main():
    Path(f"{OBSIDIAN_FOLDER_PATH}/Links").mkdir(parents=True, exist_ok=True)
    Path(f"{OBSIDIAN_FOLDER_PATH}/Notes").mkdir(parents=True, exist_ok=True)
    # Получаем файлы из папки и добавляем в базу имен файлов (как необработанные если их еще не было)
    db.sync_with_folder(DATABASE_PATH, REC_FOLDER_PATH, "wav")

    # print(db.list_unprocessed(DATABASE_PATH, "wav"))

    # транскрибируем необработанные файлы из папки
    if db.list_unprocessed(DATABASE_PATH, "wav"):
        processed_files = whisp.speech_to_text(REC_FOLDER_PATH, TXT_FOLDER_PATH, MODEL_SIZE, LANGUAGE, db.list_unprocessed(DATABASE_PATH, "wav"))
        if processed_files:
            for filename in processed_files:
                db.mark_processed(DATABASE_PATH, filename, "wav")

     # Получаем файлы из папки и добавляем в базу имен файлов (как необработанные если их еще не было)
    db.sync_with_folder(DATABASE_PATH, TXT_FOLDER_PATH, "txt")

    # ================= AGENT PART ===========

    for note in db.list_unprocessed(DATABASE_PATH, "txt"):
        with open(f"{TXT_FOLDER_PATH}/{note}", "r") as file:
            note_text = file.read()
            # 0. Исправление ошибок и структурирование текста
            note_text = agent.fix_note(note_text)

            # 1. Определение типа
            type = ""
            if note_text:
                type = agent.indentify_type(note_text)

                # 2. Определение тем
                #  тут потом будет обращение к базе тем
                themes = ["Шумеры", "Электромагнетизм", "Minecraft", "Комнатные растения", "Рефлексия", "Проекты", "Использование LLM", "Чайник Рассела"]
                themes += [f.name[:-3] for f in Path(f"{OBSIDIAN_FOLDER_PATH}/Links").iterdir() if f.is_file()]
                print(themes)
                if type :
                    themes = agent.indentify_themes(note_text, themes)
                    print(themes)
                    note_text = "#### Type: " + "#" + f"{type}\n\n" + note_text
                # 3. Генерация наименования заметки
                    note_name = agent.generate_name(note_text)
                    note_date = agent.indentify_date(note)
                    if type == "diary" and note_date and note_name:
                        note_name += f" {note_date}"
                    note_text = f"# {note_name}\n\n" + note_text

                # 4. Добавление ссылок и метаданных
                    note_text += "\n\n\n#### Links:\n"
                    if themes:
                        for theme in themes:
                            note_text += f"[[{theme}]]\n"
                            try:
                                with open(f"{OBSIDIAN_FOLDER_PATH}/Links/{theme}.md", 'x') as file:
                                    file.write("#link")
                                    print(f"Ссылка {theme} создана!")
                                    file.write(f"\n[[{note_name}]]")
                                    print(f"Ссылка {theme} дополнена!")

                            except FileExistsError:
                                print(f"Ссылка {theme} уже есть!")
                                with open(f"{OBSIDIAN_FOLDER_PATH}/Links/{theme}.md", 'w') as file:
                                    file.write(f"\n[[{note_name}]]")
                                    print(f"Ссылка {theme} дополнена!")

                    # тут еще надо добавить имя аудиофайла, txt файла, дату
                    note_text += f"\n\nAudio File name: {note[:-4]}.wav\n"
                    note_text += f"Text File name: {note}\n"
                    note_text += f"Date: {note_date}\n"

                # 5. Сохраняем файл
                    with open(f"{OBSIDIAN_FOLDER_PATH}/Notes/{note_name}.md", "w", encoding="utf-8") as f:
                        f.write(note_text)

                    db.mark_processed(DATABASE_PATH, note, "txt")

    # ========================================

if __name__ == "__main__":
    main()
