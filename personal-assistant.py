import re
import os
import json
import datetime
from collections import UserDict
from datetime import datetime, timedelta
import difflib
import inspect # Додано для кращої діагностики помилок
import traceback # Додано для логування непередбачених помилок

# --- Базові класи полів ---
class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# --- Класи для конкретних полів ---
class Name(Field):
    """Клас для зберігання та валідації імені контакту."""
    def __init__(self, value):
        if not value:
            raise ValueError("Ім'я не може бути порожнім")
        super().__init__(value)

class Phone(Field):
    """Клас для зберігання та валідації номера телефону."""
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректний номер телефону. Використовуйте формат +380XXXXXXXXX або 0XXXXXXXXX")
        super().__init__(value)

    @staticmethod
    def validate(value):
        """Перевіряє валідність номера телефону (український формат)."""
        # Перевірка для українських номерів телефону: +380XXXXXXXXX або 0XXXXXXXXX
        pattern = r"^(\+380\d{9}|0\d{9})$"
        return bool(re.match(pattern, value))

class Email(Field):
    """Клас для зберігання та валідації електронної адреси."""
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректна електронна адреса")
        super().__init__(value)

    @staticmethod
    def validate(value):
        """Перевіряє валідність електронної адреси."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, value))

class Address(Field):
    """Клас для зберігання адреси."""
    pass # Додаткова валідація може бути додана за потреби

class Birthday(Field):
    """Клас для зберігання та валідації дати народження."""
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректна дата народження. Використовуйте формат DD.MM.YYYY")
        super().__init__(value)

    @staticmethod
    def validate(value):
        """Перевіряє валідність дати народження (формат DD.MM.YYYY)."""
        pattern = r"^\d{2}\.\d{2}\.\d{4}$"
        if not re.match(pattern, value):
            return False

        try:
            day, month, year = map(int, value.split('.'))
            # Перевірка коректності дати
            datetime(year, month, day)
            # Додаткова перевірка: рік не може бути майбутнім
            if year > datetime.now().year:
                return False
            return True
        except ValueError:
            # Виникає, якщо дата некоректна (наприклад, 31.02.2023)
            return False

# --- Клас для запису контакту ---
class Record:
    """Клас для представлення запису контакту в адресній книзі."""
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.email = None
        self.address = None
        self.birthday = None

    def add_phone(self, phone):
        """Додає номер телефону до контакту."""
        # Перевірка на дублікат
        if any(p.value == phone for p in self.phones):
            return f"Номер телефону {phone} вже існує для контакту {self.name}"
        self.phones.append(Phone(phone))
        return f"Номер телефону {phone} додано для контакту {self.name}"

    def remove_phone(self, phone_to_remove):
        """Видаляє номер телефону з контакту."""
        initial_length = len(self.phones)
        self.phones = [p for p in self.phones if p.value != phone_to_remove]
        if len(self.phones) < initial_length:
            return f"Номер телефону {phone_to_remove} видалено для контакту {self.name}"
        return f"Номер телефону {phone_to_remove} не знайдено для контакту {self.name}"

    def edit_phone(self, old_phone, new_phone):
        """Редагує існуючий номер телефону."""
        # Валідація нового номера перед зміною
        if not Phone.validate(new_phone):
             raise ValueError(f"Некоректний новий номер телефону: {new_phone}. Використовуйте формат +380XXXXXXXXX або 0XXXXXXXXX")

        # Перевірка, чи новий номер вже існує (крім старого)
        if any(p.value == new_phone for p in self.phones if p.value != old_phone):
             return f"Номер телефону {new_phone} вже існує для іншого запису цього контакту."

        phone_found = False
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                phone_found = True
                break # Зупиняємось після першого знайденого співпадіння

        if phone_found:
             return f"Номер телефону змінено з {old_phone} на {new_phone} для контакту {self.name}"
        else:
             return f"Номер телефону {old_phone} не знайдено для контакту {self.name}"


    def add_email(self, email):
        """Додає або оновлює email для контакту."""
        self.email = Email(email)
        return f"Email {email} додано/оновлено для контакту {self.name}"

    def add_address(self, address):
        """Додає або оновлює адресу для контакту."""
        self.address = Address(address)
        return f"Адресу додано/оновлено для контакту {self.name}"

    def add_birthday(self, birthday):
        """Додає або оновлює дату народження для контакту."""
        self.birthday = Birthday(birthday)
        return f"Дату народження додано/оновлено для контакту {self.name}"

    def days_to_birthday(self):
        """Розраховує кількість днів до наступного дня народження."""
        if not self.birthday:
            return None

        today = datetime.now().date()
        try:
            day, month, year = map(int, self.birthday.value.split('.'))
        except ValueError:
             return None

        try:
            birthday_this_year = datetime(today.year, month, day).date()
        except ValueError:
             # Обробка 29 лютого у не високосний рік
             if month == 2 and day == 29:
                 birthday_this_year = datetime(today.year, 3, 1).date() # Розглядаємо 1 березня
             else:
                 return None # Інша некоректна дата

        if birthday_this_year < today:
            # Якщо ДН вже минув цього року, розраховуємо для наступного року
            try:
                next_birthday = datetime(today.year + 1, month, day).date()
            except ValueError:
                 # Обробка 29 лютого для наступного року
                 if month == 2 and day == 29:
                      next_birthday = datetime(today.year + 1, 3, 1).date()
                 else:
                      return None
        else:
            next_birthday = birthday_this_year

        return (next_birthday - today).days

    def __str__(self):
        """Повертає рядкове представлення контакту."""
        phones_str = ", ".join(str(p) for p in self.phones) if self.phones else "Немає"
        email_str = f", Email: {self.email}" if self.email else ""
        address_str = f", Адреса: {self.address}" if self.address else ""
        birthday_str = f", День народження: {self.birthday}" if self.birthday else ""
        days_to_birth_val = self.days_to_birthday()
        days_to_birth = ""
        if days_to_birth_val is not None:
             if days_to_birth_val == 0:
                  days_to_birth = " (Сьогодні!)"
             elif days_to_birth_val == 1:
                  days_to_birth = " (Завтра!)"
             else:
                  days_to_birth = f" (Днів до дня народження: {days_to_birth_val})"


        return f"Контакт: {self.name}, Телефони: {phones_str}{email_str}{address_str}{birthday_str}{days_to_birth}"

# --- Клас для адресної книги ---
class AddressBook(UserDict):
    """Клас для зберігання та управління записами контактів."""
    def add_record(self, record):
        """Додає запис до адресної книги."""
        self.data[record.name.value] = record
        # Повідомлення тепер формується в обробнику команди

    def find(self, name):
        """Знаходить запис за ім'ям (без урахування регістру)."""
        # Шукаємо без урахування регістру
        for record_name in self.data:
            if record_name.lower() == name.lower():
                return self.data[record_name]
        return None # Повертаємо None, якщо не знайдено

    def delete(self, name):
        """Видаляє запис за ім'ям (без урахування регістру)."""
        name_lower = name.lower()
        key_to_delete = None
        for record_name in self.data:
            if record_name.lower() == name_lower:
                key_to_delete = record_name
                break

        if key_to_delete:
            del self.data[key_to_delete]
            return f"Контакт {key_to_delete} видалено з книги контактів" # Повертаємо оригінальне ім'я
        return f"Контакт {name} не знайдено в книзі контактів"


    def get_birthdays_per_period(self, days):
        """Повертає список контактів, у яких день народження протягом заданого періоду."""
        upcoming_birthdays = []
        today = datetime.now().date()

        for record in self.data.values():
            if record.birthday:
                days_to_birth = record.days_to_birthday()
                if days_to_birth is not None and 0 <= days_to_birth <= days:
                    try:
                        day, month, year = map(int, record.birthday.value.split('.'))
                        # Визначаємо дату наступного дня народження
                        birth_date_this_year = datetime(today.year, month, day).date()
                        if birth_date_this_year < today:
                             birth_date_next = datetime(today.year + 1, month, day).date()
                        else:
                             birth_date_next = birth_date_this_year
                        upcoming_birthdays.append((record, days_to_birth, birth_date_next))
                    except ValueError:
                        # Ігноруємо записи з некоректними датами народження
                        print(f"Попередження: Некоректна дата народження '{record.birthday.value}' для контакту '{record.name}' при розрахунку днів народження.")
                        continue

        # Сортуємо за кількістю днів до дня народження
        upcoming_birthdays.sort(key=lambda x: x[1])

        result = []
        for record, days_to_birth, birth_date in upcoming_birthdays:
            day_str = "день" if days_to_birth == 1 else "дні" if 1 < days_to_birth < 5 else "днів"
            when_str = "Сьогодні" if days_to_birth == 0 else f"через {days_to_birth} {day_str}"
            result.append(f"{record.name}: {birth_date.strftime('%d.%m.%Y')} ({when_str})")

        return result

    def search_contacts(self, query):
        """Шукає контакти за рядком запиту (ім'я, телефон, email, адреса)."""
        results = []
        query = query.lower()

        for record in self.data.values():
            name_match = query in record.name.value.lower()
            phone_match = any(query in phone.value for phone in record.phones)
            email_match = record.email and query in record.email.value.lower()
            address_match = record.address and query in record.address.value.lower()

            if name_match or phone_match or email_match or address_match:
                results.append(record)

        # Сортуємо результати за ім'ям
        results.sort(key=lambda r: r.name.value.lower())
        return results

# --- Клас для нотатки ---
class Note:
    """Клас для представлення нотатки."""
    def __init__(self, title, content):
        # Заголовки не можуть бути порожніми
        if not title:
             raise ValueError("Заголовок нотатки не може бути порожнім.")
        self.title = title
        self.content = content
        self.tags = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified_at = self.created_at # Додаємо дату модифікації

    def add_tag(self, tag):
        """Додає тег до нотатки (унікальний, без урахування регістру)."""
        if not tag: # Забороняємо порожні теги
             return "Помилка: Тег не може бути порожнім."
        tag_lower = tag.lower() # Зберігаємо та перевіряємо теги в нижньому регістрі
        if tag_lower not in [t.lower() for t in self.tags]:
            self.tags.append(tag) # Зберігаємо оригінальний регістр
            self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Оновлюємо дату модифікації
            # Сортуємо теги для консистентності
            self.tags.sort(key=str.lower)
            return f"Тег '{tag}' додано до нотатки '{self.title}'"
        return f"Тег '{tag}' вже існує в нотатці '{self.title}'"

    def remove_tag(self, tag_to_remove):
        """Видаляє тег з нотатки (без урахування регістру)."""
        tag_to_remove_lower = tag_to_remove.lower()
        initial_length = len(self.tags)
        # Видаляємо, ігноруючи регістр при пошуку
        self.tags = [t for t in self.tags if t.lower() != tag_to_remove_lower]
        if len(self.tags) < initial_length:
            self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Оновлюємо дату модифікації
            return f"Тег '{tag_to_remove}' видалено з нотатки '{self.title}'"
        return f"Тег '{tag_to_remove}' не знайдено в нотатці '{self.title}'"

    def edit_content(self, new_content):
         """Оновлює зміст нотатки та дату модифікації."""
         self.content = new_content
         self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        """Повертає рядкове представлення нотатки."""
        tags_str = f" [Теги: {', '.join(self.tags)}]" if self.tags else ""
        modified_str = f"(Оновлено: {self.modified_at})" if self.modified_at != self.created_at else ""
        return (f"Заголовок: {self.title}{tags_str}\n"
                f"Створено: {self.created_at} {modified_str}\n"
                f"Зміст: {self.content}")

# --- Клас для книги нотаток ---
class NoteBook:
    """Клас для зберігання та управління нотатками."""
    def __init__(self):
        self.notes = [] # Список об'єктів Note

    def add_note(self, title, content):
        """Додає нову нотатку."""
        # Перевірка, чи нотатка з таким заголовком вже існує (без урахування регістру)
        if self.find_note_by_title(title):
             return f"Нотатка з заголовком '{title}' вже існує. Використовуйте інший заголовок або команду 'змінити нотатку'."
        try:
            note = Note(title, content)
            self.notes.append(note)
            return f"Нотатку '{title}' додано"
        except ValueError as e: # Ловимо помилку з порожнім заголовком
            return f"Помилка: {e}"


    def find_note_by_title(self, title):
        """Знаходить нотатку за заголовком (без урахування регістру)."""
        title_lower = title.lower()
        for note in self.notes:
            if note.title.lower() == title_lower:
                return note
        return None

    def edit_note(self, title, new_content):
        """Редагує зміст існуючої нотатки."""
        note = self.find_note_by_title(title)
        if note:
            note.edit_content(new_content) # Використовуємо новий метод для оновлення
            return f"Нотатку '{title}' оновлено"
        return f"Нотатку '{title}' не знайдено"

    def delete_note(self, title):
        """Видаляє нотатку за заголовком."""
        note = self.find_note_by_title(title)
        if note:
            self.notes.remove(note)
            return f"Нотатку '{title}' видалено"
        return f"Нотатку '{title}' не знайдено"

    def search_notes(self, query):
        """Шукає нотатки за рядком запиту (заголовок, зміст, теги)."""
        results = []
        query = query.lower()

        for note in self.notes:
            if (query in note.title.lower() or
                query in note.content.lower() or
                any(query in tag.lower() for tag in note.tags)):
                results.append(note)

        # Сортуємо результати за заголовком
        results.sort(key=lambda n: n.title.lower())
        return results

    def search_by_tag(self, tag):
        """Шукає нотатки за тегом (без урахування регістру)."""
        tag_lower = tag.lower()
        results = [note for note in self.notes if tag_lower in [t.lower() for t in note.tags]]
        # Сортуємо результати за заголовком
        results.sort(key=lambda n: n.title.lower())
        return results


    def sort_notes_by_tag(self):
         """Сортує нотатки за тегами (алфавітно, потім без тегів)."""
         # Створюємо словник, де ключ - тег (lower case), значення - список нотаток
         notes_by_tag = {}
         notes_without_tags = []

         for note in self.notes:
             if note.tags:
                 # Додаємо нотатку до всіх її тегів
                 added_to_tag = False
                 for tag in note.tags:
                     tag_lower = tag.lower()
                     if tag_lower not in notes_by_tag:
                         notes_by_tag[tag_lower] = []
                     # Переконуємось, що нотатка додана лише раз до списку тегу
                     if note not in notes_by_tag[tag_lower]:
                          notes_by_tag[tag_lower].append(note)
                     added_to_tag = True
                 # Якщо у нотатки були теги, але всі вони порожні (не мало б бути),
                 # то додаємо її до списку без тегів
                 if not added_to_tag:
                      notes_without_tags.append(note)
             else:
                 notes_without_tags.append(note)

         # Сортуємо теги за алфавітом
         sorted_tags = sorted(notes_by_tag.keys())

         # Формуємо відсортований список нотаток
         final_sorted_notes = []
         processed_notes = set() # Для уникнення дублікатів

         # Додаємо нотатки з тегами
         for tag in sorted_tags:
             # Сортуємо нотатки всередині кожного тегу за заголовком
             notes_by_tag[tag].sort(key=lambda n: n.title.lower())
             for note in notes_by_tag[tag]:
                 if note not in processed_notes:
                     final_sorted_notes.append(note)
                     processed_notes.add(note)

         # Додаємо нотатки без тегів в кінець, сортовані за заголовком
         notes_without_tags.sort(key=lambda n: n.title.lower())
         for note in notes_without_tags:
              if note not in processed_notes: # Хоча тут дублікатів бути не повинно
                   final_sorted_notes.append(note)
                   processed_notes.add(note)


         self.notes = final_sorted_notes # Оновлюємо список нотаток відсортованим
         return "Нотатки відсортовано за тегами."


# --- Головний клас додатка ---
class PersonalAssistant:
    """Клас персонального помічника, що об'єднує адресну книгу та нотатки."""
    def __init__(self):
        self.address_book = AddressBook()
        self.note_book = NoteBook()
        # Визначаємо шлях до папки даних у домашній директорії користувача
        self.data_folder = os.path.join(os.path.expanduser("~"), "personal_assistant_data")
        self.contacts_file = os.path.join(self.data_folder, "contacts.json")
        self.notes_file = os.path.join(self.data_folder, "notes.json")
        # Словник доступних команд та відповідних методів
        self.commands = {
            # --- Контакти ---
            "додати контакт": self.add_contact,
            "показати контакт": self.show_contact,
            "показати всі контакти": self.show_all_contacts,
            "знайти контакт": self.search_contacts_command, # Перейменовано для ясності
            "видалити контакт": self.delete_contact,
            "дні народження": self.birthdays_per_period,
            "додати телефон": self.add_phone_to_contact,
            "змінити телефон": self.edit_phone_in_contact,
            "видалити телефон": self.remove_phone_from_contact,
            "додати email": self.add_email_to_contact,
            "додати адресу": self.add_address_to_contact,
            "додати день народження": self.add_birthday_to_contact,
            # --- Нотатки ---
            "додати нотатку": self.add_note,
            "показати нотатку": self.show_note,
            "показати всі нотатки": self.show_all_notes,
            "змінити нотатку": self.edit_note,
            "видалити нотатку": self.delete_note,
            "знайти нотатку": self.search_notes_command, # Перейменовано для ясності
            "додати тег": self.add_tag_to_note,
            "видалити тег": self.remove_tag_from_note,
            "пошук за тегом": self.search_notes_by_tag_command, # Перейменовано для ясності
            "сортувати нотатки": self.sort_notes,
            # --- Загальні ---
            "допомога": self.show_help,
            "вихід": self.exit_program,
            "зберегти": self.save_data_command
        }
        self.load_data() # Завантажуємо дані при старті

    # --- ОНОВЛЕНА ФУНКЦІЯ ---
    def parse_input(self, user_input):
        """Розбирає введений рядок на команду та решту рядка аргументів."""
        if not user_input:
            return "", "" # Повертаємо порожню команду та аргументи

        user_input_lower = user_input.lower()
        matched_command = None

        # Знаходимо найдовшу відповідну команду на початку рядка
        for command_key in self.commands:
            if user_input_lower.startswith(command_key):
                # Перевіряємо, чи наступний символ - це пробіл або кінець рядка
                # Це запобігає частковим співпадінням (напр., "додати" замість "додати контакт")
                if len(user_input_lower) == len(command_key) or user_input_lower[len(command_key)].isspace():
                    if matched_command is None or len(command_key) > len(matched_command):
                        matched_command = command_key

        if matched_command:
            cmd = matched_command
            # Визначаємо аргументи як рядок після команди
            args_str = user_input[len(matched_command):].strip()
            return cmd, args_str # Повертаємо команду і весь рядок аргументів
        else:
            # Якщо точна команда не знайдена, вважаємо перше слово командою, решту - аргументами
            # Це для випадків типу "show John" або невідомих команд
            parts = user_input.strip().split(' ', 1)
            cmd = parts[0].lower() # Беремо перше слово як команду
            args_str = parts[1].strip() if len(parts) > 1 else ""
            return cmd, args_str


    # --- ОНОВЛЕНА ФУНКЦІЯ ---
    def execute_command(self, cmd, args_str):
        """Виконує команду, обробляючи рядок аргументів відповідно до команди."""
        if cmd in self.commands:
            handler = self.commands[cmd]
            processed_args = [] # Список аргументів для передачі в обробник

            # --- Логіка обробки рядка аргументів `args_str` ---
            try:
                # 1. Команди без аргументів
                if cmd in ["показати всі контакти", "показати всі нотатки",
                           "сортувати нотатки", "допомога", "вихід", "зберегти"]:
                    if args_str:
                        raise ValueError(f"Команда '{cmd}' не приймає аргументів.")
                    processed_args = []

                # 2. Команди з одним обов'язковим аргументом
                elif cmd in ["показати контакт", "видалити контакт", "знайти контакт",
                             "показати нотатку", "видалити нотатку", "знайти нотатку",
                             "пошук за тегом", "дні народження"]:
                    if not args_str:
                        raise ValueError(f"Для команди '{cmd}' потрібен один аргумент (ім'я, заголовок, запит, кількість днів).")
                    processed_args = [args_str]

                # 3. Команди з двома обов'язковими аргументами (розділені пробілом, другий може бути складним)
                elif cmd in ["додати телефон", "видалити телефон", "додати email",
                             "додати день народження", "додати тег", "видалити тег"]:
                    parts = [a.strip() for a in args_str.split(maxsplit=1)]
                    if len(parts) < 2 or not parts[0] or not parts[1]: # Перевірка, що обидва аргументи не порожні
                        raise ValueError(f"Для команди '{cmd}' потрібно два аргументи (наприклад, ім'я/заголовок та значення).")
                    processed_args = parts

                # 4. Команда зміни телефону (3 аргументи, розділені пробілом)
                elif cmd == "змінити телефон":
                    parts = [a.strip() for a in args_str.split(maxsplit=2)]
                    if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
                        raise ValueError(f"Для команди '{cmd}' потрібно три аргументи (ім'я, старий телефон, новий телефон).")
                    processed_args = parts

                # 5. Команди з першим аргументом і необов'язковим другим/рештою
                elif cmd in ["додати контакт", "додати адресу", "додати нотатку", "змінити нотатку"]:
                     parts = [a.strip() for a in args_str.split(maxsplit=1)]
                     if not parts or not parts[0]: # Потрібен хоча б перший аргумент (ім'я/заголовок)
                          if cmd in ["додати контакт", "додати адресу"]:
                               raise ValueError(f"Для команди '{cmd}' потрібно вказати ім'я.")
                          else: # add_note, edit_note
                               raise ValueError(f"Для команди '{cmd}' потрібно вказати заголовок.")
                     processed_args = parts # Буде [name/title] або [name/title, rest]

                # Якщо логіка не визначена (помилка в коді)
                else:
                     print(f"УВАГА: Невизначена логіка обробки аргументів для команди '{cmd}'.")
                     processed_args = [args_str] if args_str else []

                # --- Виклик обробника ---
                return handler(*processed_args)

            except TypeError as e:
                # Покращена діагностика TypeError
                sig = inspect.signature(handler)
                print(f"Debug: Calling {cmd} with args: {processed_args}")
                print(f"Debug: TypeError details: {e}")
                return (f"Помилка: Неправильна кількість або тип аргументів для команди '{cmd}'.\n"
                        f"       Отримано: {processed_args}\n"
                        f"       Сигнатура функції: {handler.__name__}{sig}\n"
                        f"       Повідомлення: {e}")
            except ValueError as e:
                # Ловимо помилки валідації та помилки аргументів, створені вище
                return f"Помилка: {e}"
            except Exception as e:
                # Логування повного traceback для непередбачених помилок
                print(f"Непередбачена помилка при виконанні команди '{cmd}' з аргументами '{args_str}':")
                traceback.print_exc()
                return f"Виникла непередбачена помилка: {e}. Дивіться деталі в консолі."

        else: # Команду не знайдено у словнику self.commands
            guessed_cmd = self.guess_command(cmd) # cmd тут - це перше слово з parse_input
            full_input_for_guess = cmd + (f" {args_str}" if args_str else "")
            # Спробуємо вгадати за повним вводом, якщо перше слово не команда
            if not guessed_cmd:
                 guessed_cmd = self.guess_command(full_input_for_guess)

            if guessed_cmd:
                return f"Команду '{full_input_for_guess}' не знайдено. Можливо, ви мали на увазі '{guessed_cmd}'? Введіть 'допомога' для списку команд."
            return f"Команду '{cmd}' не знайдено. Введіть 'допомога' для перегляду доступних команд."


    # --- Методи для роботи з контактами ---
    def add_contact(self, name, phone=None): # Змінено сигнатуру для ясності
        """Додає новий контакт. Можна одразу додати телефон."""
        # Ім'я перевіряється в класі Name
        # Перевірка на існування (без урахування регістру)
        existing_record = self.address_book.find(name)
        if existing_record:
            return f"Контакт {existing_record.name.value} вже існує. Використовуйте команду 'додати телефон' або інші для оновлення даних."

        record = Record(name)
        message = f"Контакт {name} додано."
        if phone:
            try:
                record.add_phone(phone)
                message += f" З номером телефону {phone}."
            except ValueError as e:
                # Контакт все одно додаємо, але повідомляємо про помилку з телефоном
                self.address_book.add_record(record)
                return f"Контакт {name} додано, але виникла помилка при додаванні телефону: {e}"

        self.address_book.add_record(record)
        return message


    def show_contact(self, name):
        """Показує детальну інформацію про один контакт."""
        record = self.address_book.find(name) # Пошук без урахування регістру
        if record:
            return str(record)
        return f"Контакт {name} не знайдено в книзі контактів"

    def show_all_contacts(self):
        """Показує всі контакти в адресній книзі."""
        if not self.address_book.data:
            return "Книга контактів порожня"

        result = ["Книга контактів:"]
        # Сортуємо контакти за ім'ям для кращого вигляду
        for record_name in sorted(self.address_book.data.keys(), key=str.lower):
            result.append(str(self.address_book.data[record_name]))
        return "\n".join(result)

    # Перейменовано метод, щоб уникнути конфлікту імен з полем класу
    def search_contacts_command(self, query):
        """Обробник команди для пошуку контактів."""
        results = self.address_book.search_contacts(query)
        if not results:
            return f"Контактів, що містять '{query}', не знайдено"

        result = [f"Знайдено {len(results)} контактів для запиту '{query}':"]
        for record in results: # Результати вже відсортовані
            result.append(str(record))
        return "\n".join(result)

    def delete_contact(self, name):
        """Видаляє контакт за ім'ям."""
        return self.address_book.delete(name) # Видалення без урахування регістру

    def birthdays_per_period(self, days_str):
        """Показує дні народження на вказаний період."""
        try:
            days = int(days_str)
            if days < 0: # Дозволяємо 0 днів (сьогодні)
                return "Кількість днів не може бути від'ємною."

            birthdays = self.address_book.get_birthdays_per_period(days)
            if not birthdays:
                 if days == 0:
                      return "Немає днів народження сьогодні."
                 else:
                      return f"Немає днів народження протягом наступних {days} днів."

            period_str = "Сьогоднішні дні народження:" if days == 0 else f"Дні народження протягом наступних {days} днів:"
            result = [period_str]
            result.extend(birthdays)
            return "\n".join(result)
        except ValueError:
            return "Кількість днів має бути цілим числом."

    def add_phone_to_contact(self, name, phone):
        """Додає номер телефону до існуючого контакту."""
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        # ValueError обробляється в execute_command
        return record.add_phone(phone)


    def edit_phone_in_contact(self, name, old_phone, new_phone):
         """Змінює існуючий номер телефону контакту."""
         record = self.address_book.find(name)
         if not record:
             return f"Контакт {name} не знайдено."
         # ValueError обробляється в execute_command
         return record.edit_phone(old_phone, new_phone)


    def remove_phone_from_contact(self, name, phone):
        """Видаляє номер телефону з контакту."""
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        return record.remove_phone(phone)

    def add_email_to_contact(self, name, email):
        """Додає або оновлює email контакту."""
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        # ValueError обробляється в execute_command
        return record.add_email(email)

    def add_address_to_contact(self, name, address): # Змінено сигнатуру
        """Додає або оновлює адресу контакту."""
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        if not address: # Перевірка на порожню адресу
             return "Помилка: Адреса не може бути порожньою."
        return record.add_address(address)

    def add_birthday_to_contact(self, name, birthday):
        """Додає або оновлює дату народження контакту."""
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        # ValueError обробляється в execute_command
        return record.add_birthday(birthday)

    # --- Методи для роботи з нотатками ---
    def add_note(self, title, content=''): # Змінено сигнатуру, контент необов'язковий
        """Додає нову нотатку."""
        # ValueError (порожній заголовок) обробляється в execute_command/Note.__init__
        return self.note_book.add_note(title, content)

    def show_note(self, title):
        """Показує одну нотатку за заголовком."""
        note = self.note_book.find_note_by_title(title)
        if note:
            return str(note)
        return f"Нотатку '{title}' не знайдено"

    def show_all_notes(self):
        """Показує всі нотатки."""
        if not self.note_book.notes:
            return "Книга нотаток порожня"

        result = ["Книга нотаток:"]
        # Нотатки вже можуть бути відсортовані
        notes_to_show = sorted(self.note_book.notes, key=lambda n: n.title.lower()) # Сортуємо тут для показу
        for note in notes_to_show:
            result.append(str(note))
            result.append("-" * 40) # Роздільник між нотатками
        return "\n".join(result[:-1]) # Прибираємо останній роздільник

    def edit_note(self, title, new_content=''): # Змінено сигнатуру
        """Редагує зміст існуючої нотатки."""
        # Дозволяємо встановлювати порожній зміст при редагуванні
        return self.note_book.edit_note(title, new_content)

    def delete_note(self, title):
        """Видаляє нотатку за заголовком."""
        return self.note_book.delete_note(title)

    # Перейменовано метод
    def search_notes_command(self, query):
        """Обробник команди для пошуку нотаток."""
        results = self.note_book.search_notes(query)
        if not results:
            return f"Нотаток, що містять '{query}', не знайдено"

        result = [f"Знайдено {len(results)} нотаток для запиту '{query}':"]
        for note in results: # Результати вже відсортовані
            result.append(str(note))
            result.append("-" * 40)
        return "\n".join(result[:-1]) # Прибираємо останній роздільник

    def add_tag_to_note(self, title, tag):
        """Додає тег до нотатки."""
        note = self.note_book.find_note_by_title(title)
        if not note:
            return f"Нотатку '{title}' не знайдено"
        return note.add_tag(tag)

    def remove_tag_from_note(self, title, tag):
        """Видаляє тег з нотатки."""
        note = self.note_book.find_note_by_title(title)
        if not note:
            return f"Нотатку '{title}' не знайдено"
        return note.remove_tag(tag)

    # Перейменовано метод
    def search_notes_by_tag_command(self, tag):
        """Обробник команди для пошуку нотаток за тегом."""
        results = self.note_book.search_by_tag(tag)
        if not results:
            return f"Нотаток з тегом '{tag}' не знайдено"

        result = [f"Знайдено {len(results)} нотаток з тегом '{tag}':"]
        # Результати вже відсортовані
        for note in results:
            result.append(str(note))
            result.append("-" * 40)
        return "\n".join(result[:-1]) # Прибираємо останній роздільник

    def sort_notes(self):
         """Сортує нотатки за тегами."""
         if not self.note_book.notes:
              return "Книга нотаток порожня, немає що сортувати."
         return self.note_book.sort_notes_by_tag()

    # --- Загальні методи ---
    def show_help(self):
        """Показує список доступних команд з описом."""
        # Оновлено описи для відображення розділення аргументів пробілами
        commands_help = [
            "--- Контакти ---",
            "додати контакт <ім'я> [телефон] - Додати новий контакт (телефон необов'язковий)",
            "показати контакт <ім'я> - Показати інформацію про контакт",
            "показати всі контакти - Показати всі контакти",
            "знайти контакт <запит> - Знайти контакт за ім'ям, телефоном, email або адресою",
            "видалити контакт <ім'я> - Видалити контакт",
            "дні народження <кількість_днів> - Показати дні народження на найближчі дні (0 - сьогодні)",
            "додати телефон <ім'я> <телефон> - Додати номер телефону",
            "змінити телефон <ім'я> <старий_телефон> <новий_телефон> - Змінити номер телефону",
            "видалити телефон <ім'я> <телефон> - Видалити номер телефону",
            "додати email <ім'я> <email> - Додати/оновити email",
            "додати адресу <ім'я> <адреса> - Додати/оновити адресу (адреса може містити пробіли)",
            "додати день народження <ім'я> <дата> - Додати/оновити день народження (формат: DD.MM.YYYY)",
            "",
            "--- Нотатки ---",
            "додати нотатку <заголовок> [зміст] - Додати нову нотатку (зміст необов'язковий, може містити пробіли)",
            "показати нотатку <заголовок> - Показати нотатку за заголовком",
            "показати всі нотатки - Показати всі нотатки",
            "змінити нотатку <заголовок> [новий_зміст] - Змінити зміст нотатки (новий зміст необов'язковий)",
            "видалити нотатку <заголовок> - Видалити нотатку",
            "знайти нотатку <запит> - Знайти нотатку за заголовком, змістом або тегом",
            "додати тег <заголовок> <тег> - Додати тег до нотатки",
            "видалити тег <заголовок> <тег> - Видалити тег з нотатки",
            "пошук за тегом <тег> - Знайти нотатки за тегом",
            "сортувати нотатки - Сортувати нотатки за тегами (алфавітно)",
            "",
            "--- Загальні ---",
            "допомога - Показати цю довідку",
            "зберегти - Примусово зберегти дані у файл",
            "вихід - Зберегти дані та вийти з програми"
        ]
        return "Доступні команди:\n" + "\n".join(commands_help)

    def save_data_command(self):
         """Команда для явного збереження даних."""
         self.save_data()
         return "Дані успішно збережено."

    def exit_program(self):
        """Зберігає дані та завершує роботу програми."""
        self.save_data()
        return "До побачення!"

    def save_data(self):
        """Зберігає контакти та нотатки у JSON файли."""
        try:
            os.makedirs(self.data_folder, exist_ok=True)

            # --- Зберігаємо контакти ---
            contacts_to_save = {}
            for name, record in self.address_book.data.items():
                contacts_to_save[name] = {
                    "phones": [phone.value for phone in record.phones],
                    "email": record.email.value if record.email else None,
                    "address": record.address.value if record.address else None,
                    "birthday": record.birthday.value if record.birthday else None
                }
            with open(self.contacts_file, 'w', encoding='utf-8') as file:
                json.dump(contacts_to_save, file, ensure_ascii=False, indent=4)

            # --- Зберігаємо нотатки ---
            notes_to_save = []
            for note in self.note_book.notes:
                notes_to_save.append({
                    "title": note.title,
                    "content": note.content,
                    "tags": note.tags,
                    "created_at": note.created_at,
                    "modified_at": note.modified_at # Зберігаємо дату модифікації
                })
            with open(self.notes_file, 'w', encoding='utf-8') as file:
                json.dump(notes_to_save, file, ensure_ascii=False, indent=4)

        except IOError as e:
            print(f"Помилка збереження даних: Не вдалося записати у файл. {e}")
        except Exception as e:
            print(f"Невідома помилка під час збереження даних: {e}")


    def load_data(self):
        """Завантажує контакти та нотатки з JSON файлів."""
        # --- Завантажуємо контакти ---
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as file:
                    contacts_data = json.load(file)

                for name, data in contacts_data.items():
                    try:
                        record = Record(name) # Може викликати ValueError, якщо ім'я некоректне
                        # Додаємо дані безпечно
                        for phone in data.get("phones", []):
                            try: record.add_phone(phone)
                            except ValueError: print(f"Попередження: Пропущено невалідний телефон '{phone}' для контакту '{name}'.")
                        if data.get("email"):
                            try: record.add_email(data["email"])
                            except ValueError: print(f"Попередження: Пропущено невалідний email '{data['email']}' для контакту '{name}'.")
                        if data.get("address"):
                            record.add_address(data["address"])
                        if data.get("birthday"):
                            try: record.add_birthday(data["birthday"])
                            except ValueError: print(f"Попередження: Пропущено невалідну дату народження '{data['birthday']}' для контакту '{name}'.")

                        # Додаємо запис до книги (використовуємо оригінальне ім'я як ключ)
                        self.address_book.data[record.name.value] = record

                    except ValueError as e: # Помилка валідації при створенні Record або полів
                         print(f"Помилка завантаження контакту '{name}': {e}")
                    except KeyError as e: # Якщо структура JSON неправильна
                         print(f"Помилка завантаження контакту '{name}': відсутнє поле {e} у файлі.")
                    except Exception as e: # Інші можливі помилки
                         print(f"Невідома помилка при обробці контакту '{name}': {e}")


            except json.JSONDecodeError:
                print(f"Помилка: Файл контактів ({self.contacts_file}) пошкоджено. Створіть новий або відновіть з резервної копії.")
            except IOError as e:
                 print(f"Помилка читання файлу контактів: {e}")
            except Exception as e:
                 print(f"Невідома помилка під час завантаження контактів: {e}")


        # --- Завантажуємо нотатки ---
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as file:
                    notes_data = json.load(file)

                for data in notes_data:
                     try:
                         # Перевіряємо наявність обов'язкових полів
                         title = data.get("title")
                         content = data.get("content") # Може бути None, але Note це обробить
                         if not title: # Заголовок обов'язковий
                              print(f"Попередження: Пропущено завантаження нотатки через відсутність заголовка: {data}")
                              continue

                         note = Note(title, content if content is not None else "")
                         # Безпечно отримуємо теги та дати
                         note.tags = data.get("tags", [])
                         note.created_at = data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                         note.modified_at = data.get("modified_at", note.created_at) # Завантажуємо дату модифікації
                         # Сортуємо теги після завантаження
                         note.tags.sort(key=str.lower)
                         self.note_book.notes.append(note)

                     except ValueError as e: # Помилка валідації Note (порожній заголовок)
                          print(f"Помилка завантаження нотатки '{data.get('title', '')}': {e}")
                     except KeyError as e:
                          print(f"Помилка завантаження нотатки: відсутнє поле {e} у записі {data}")
                     except Exception as e:
                          print(f"Помилка обробки запису нотатки {data}: {e}")


            except json.JSONDecodeError:
                 print(f"Помилка: Файл нотаток ({self.notes_file}) пошкоджено. Створіть новий або відновіть з резервної копії.")
            except IOError as e:
                 print(f"Помилка читання файлу нотаток: {e}")
            except Exception as e:
                 print(f"Невідома помилка під час завантаження нотаток: {e}")


# --- Головна функція запуску ---
def main():
    """Головна функція для запуску персонального помічника."""
    assistant = PersonalAssistant()
    print("Вітаю! Я ваш персональний помічник.")
    print("Введіть 'допомога' для перегляду доступних команд.")

    while True:
        try:
            user_input = input(">>> ").strip()
            if not user_input: # Пропускаємо порожній ввід
                continue

            command, args_string = assistant.parse_input(user_input)

            # Перевіряємо, чи це команда виходу перед виконанням
            if command == "вихід":
                 result = assistant.exit_program()
                 print(result)
                 break # Виходимо з циклу

            # Виконуємо команду
            result = assistant.execute_command(command, args_string)
            print(result)

        except KeyboardInterrupt: # Обробка Ctrl+C
            print("\nОтримано сигнал переривання. Зберігаю дані...")
            assistant.save_data()
            print("До побачення!")
            break
        except EOFError: # Обробка Ctrl+D (кінець файлу)
             print("\nОтримано сигнал кінця файлу. Зберігаю дані...")
             assistant.save_data()
             print("До побачення!")
             break


if __name__ == "__main__":
    main()
