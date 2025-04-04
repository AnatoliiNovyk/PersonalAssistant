# Персональний помічник вер. 1.2 (Personal Assistant ver. 1.2)

## Опис
"Персональний помічник" - це консольна програма, яка дозволяє зберігати та управляти контактами та нотатками. Програма розроблена на Python з використанням об'єктно-орієнтованого підходу.

## Функціональність

### Управління контактами
- Додавання нових контактів із іменами, адрес





⚠️ **Нове в цій версії:**


👉 ***додати тег контакту***

👉 ***видалити тег контакту***

👉 ***додати нотатку контакту***

👉 ***показати нотатки контакту***

👉 ***видалити нотатку контакту***

👉 ***пошук контакту за тегом***




## Персональний помічник вер. 1.1 (Personal Assistant ver. 1.1)

**Що було змінено:**

**`parse_input`:** Тепер ця функція знаходить найдовшу відповідну команду на початку введеного рядка (наприклад, "додати телефон") і повертає її разом з **усім** текстом, що йде після команди, як єдиний рядок аргументів (`args_str`).
**`execute_command`:** Ця функція тепер відповідає за розбір рядка аргументів (`args_str`) **залежно від команди**:
* Для команд типу `додати телефон`, `змінити телефон`, `додати email` тощо, вона розділяє рядок аргументів за пробілами на потрібну кількість частин.
* Для команд типу `показати контакт`, `знайти контакт`, `дні народження` тощо, вона використовує весь рядок аргументів як єдиний параметр.
* Для команд типу `додати нотатку`, `додати адресу` тощо, вона відокремлює перший аргумент (ім'я/заголовок), а решту передає як другий аргумент (обробники команд `add_note`, `add_address` вже вміють працювати з багатослівним змістом/адресою).
* Для команд без аргументів вона перевіряє, що рядок аргументів порожній.
**Обробка помилок:** Додано більш конкретні перевірки на наявність та коректність аргументів всередині `execute_command` перед викликом відповідного методу-обробника. Повідомлення про помилки `TypeError` стали більш детальними.
**Незначні покращення:** Додано сортування контактів та результатів пошуку за іменем/заголовком, покращено обробку днів народження, додано дату модифікації для нотаток, покращено завантаження/збереження даних.

Тепер ви можете вводити команди, розділяючи аргументи пробілами, наприклад:
`додати телефон Іван +380991234567`
`змінити телефон Іван +380991234567 0509876543`
`додати нотатку Моя нотатка Це текст моєї нотатки`


## Персональний помічник вер. 1.0 (Personal Assistant ver. 1.0)

**Основні зміни та доповнення:**

**Валідація в `edit_phone`:** Додано перевірку нового номера телефону перед його присвоєнням у методі `Record.edit_phone`.
**Покращене парсування команд (`parse_input`):** Тепер парсер намагається знайти найдовшу відповідну команду з початку рядка (наприклад, "додати контакт" буде розпізнано коректно, навіть якщо далі йде ім'я). Це робить введення команд більш гнучким.
**Покращена обробка помилок:**
* Додано більше перевірок на порожні аргументи у функціях-обробниках команд (`add_contact`, `show_contact`, `add_phone_to_contact` і т.д.).
* У `execute_command` додано обробку `TypeError` для випадків неправильної кількості аргументів та `ValueError` для помилок валідації даних.
* У `load_data` додано більше `try-except` блоків та перевірок `data.get()` для безпечнішого завантаження даних з файлів, а також вивід попереджень при некоректних даних у файлі замість повної зупинки завантаження.
* Додано обробку `KeyboardInterrupt` (Ctrl+C) та `EOFError` (Ctrl+D) у `main` для коректного збереження даних перед виходом.
**Нові команди:**
* `змінити телефон`: Додано окрему команду та метод `edit_phone_in_contact` для зміни номера телефону.
* `сортувати нотатки`: Додано команду та метод `sort_notes` (який викликає `note_book.sort_notes_by_tag`) для сортування нотаток за тегами.
* `зберегти`: Додано команду для примусового збереження даних у файл.
**Покращення `get_birthdays_per_period`:** Виправлено логіку визначення наступної дати народження та форматування виводу кількості днів.
**Покращення `NoteBook`:**
* Додано перевірку на унікальність заголовка при додаванні нотатки (`add_note`).
* Додано метод `sort_notes_by_tag` для сортування нотаток за тегами (алфавітно за тегами, потім нотатки без тегів).
**Покращення `show_help`:** Оновлено список команд та їх опис.
**Форматування та коментарі:** Додано більше коментарів та покращено форматування коду для кращої читабельності. Шлях до папки даних змінено на `personal_assistant_data` для уникнення потенційних конфліктів. Відступи у JSON файлах збільшено до 4 для кращої читабельності.
