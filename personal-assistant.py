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
    pass

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
            datetime(year, month, day)
            if year > datetime.now().year:
                return False
            return True
        except ValueError:
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
        self.tags = [] # НОВЕ: Список тегів для контакту
        self.contact_notes = [] # НОВЕ: Список нотаток для контакту

    def add_phone(self, phone):
        """Додає номер телефону до контакту."""
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
        if not Phone.validate(new_phone):
             raise ValueError(f"Некоректний новий номер телефону: {new_phone}. Використовуйте формат +380XXXXXXXXX або 0XXXXXXXXX")
        if any(p.value == new_phone for p in self.phones if p.value != old_phone):
             return f"Номер телефону {new_phone} вже існує для іншого запису цього контакту."
        phone_found = False
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                phone_found = True
                break
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

    # --- НОВІ МЕТОДИ для тегів контакту ---
    def add_tag(self, tag):
        """Додає тег до контакту (унікальний, без урахування регістру)."""
        if not tag:
            return "Помилка: Тег не може бути порожнім."
        tag_lower = tag.lower()
        if tag_lower not in [t.lower() for t in self.tags]:
            self.tags.append(tag)
            self.tags.sort(key=str.lower) # Сортуємо для консистентності
            return f"Тег '{tag}' додано до контакту '{self.name}'"
        return f"Тег '{tag}' вже існує для контакту '{self.name}'"

    def remove_tag(self, tag_to_remove):
        """Видаляє тег з контакту (без урахування регістру)."""
        tag_to_remove_lower = tag_to_remove.lower()
        initial_length = len(self.tags)
        self.tags = [t for t in self.tags if t.lower() != tag_to_remove_lower]
        if len(self.tags) < initial_length:
            return f"Тег '{tag_to_remove}' видалено з контакту '{self.name}'"
        return f"Тег '{tag_to_remove}' не знайдено для контакту '{self.name}'"

    # --- НОВІ МЕТОДИ для нотаток контакту ---
    def add_contact_note(self, note_text):
        """Додає текстову нотатку до контакту."""
        if not note_text:
            return "Помилка: Текст нотатки не може бути порожнім."
        self.contact_notes.append(note_text)
        return f"Нотатку додано до контакту '{self.name}' (всього: {len(self.contact_notes)})."

    def remove_contact_note(self, index):
        """Видаляє нотатку за її індексом (починаючи з 1)."""
        if not isinstance(index, int) or index <= 0 or index > len(self.contact_notes):
            raise IndexError(f"Неправильний індекс нотатки: {index}. Введіть число від 1 до {len(self.contact_notes)}.")
        removed_note = self.contact_notes.pop(index - 1) # Видаляємо за індексом (0-based)
        return f"Нотатку #{index} ('{removed_note[:20]}...') видалено з контакту '{self.name}'."

    # --- Розрахунок днів до дня народження ---
    def days_to_birthday(self):
        """Розраховує кількість днів до наступного дня народження."""
        if not self.birthday: return None
        today = datetime.now().date()
        try:
            day, month, year = map(int, self.birthday.value.split('.'))
            birthday_this_year = datetime(today.year, month, day).date()
        except ValueError:
             if month == 2 and day == 29: birthday_this_year = datetime(today.year, 3, 1).date()
             else: return None
        if birthday_this_year < today:
            try: next_birthday = datetime(today.year + 1, month, day).date()
            except ValueError:
                 if month == 2 and day == 29: next_birthday = datetime(today.year + 1, 3, 1).date()
                 else: return None
        else:
            next_birthday = birthday_this_year
        return (next_birthday - today).days

    # --- Оновлений метод __str__ ---
    def __str__(self):
        """Повертає рядкове представлення контакту."""
        phones_str = ", ".join(str(p) for p in self.phones) if self.phones else "Немає"
        email_str = f", Email: {self.email}" if self.email else ""
        address_str = f", Адреса: {self.address}" if self.address else ""
        birthday_str = f", День народження: {self.birthday}" if self.birthday else ""
        days_to_birth_val = self.days_to_birthday()
        days_to_birth = ""
        if days_to_birth_val is not None:
             if days_to_birth_val == 0: days_to_birth = " (Сьогодні!)"
             elif days_to_birth_val == 1: days_to_birth = " (Завтра!)"
             else: days_to_birth = f" (Днів до ДН: {days_to_birth_val})"

        # НОВЕ: Додаємо теги та кількість нотаток
        tags_str = f", Теги: [{', '.join(self.tags)}]" if self.tags else ""
        notes_count_str = f" (Нотаток: {len(self.contact_notes)})" if self.contact_notes else ""

        return (f"Контакт: {self.name}{notes_count_str}\n"
                f"  Телефони: {phones_str}\n"
                f"  Email: {self.email if self.email else 'Немає'}\n"
                f"  Адреса: {self.address if self.address else 'Немає'}\n"
                f"  День народження: {self.birthday if self.birthday else 'Немає'}{days_to_birth}\n"
                f"  Теги: {', '.join(self.tags) if self.tags else 'Немає'}")


# --- Клас для адресної книги ---
class AddressBook(UserDict):
    """Клас для зберігання та управління записами контактів."""
    def add_record(self, record):
        """Додає запис до адресної книги."""
        self.data[record.name.value] = record

    def find(self, name):
        """Знаходить запис за ім'ям (без урахування регістру)."""
        for record_name in self.data:
            if record_name.lower() == name.lower():
                return self.data[record_name]
        return None

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
            return f"Контакт {key_to_delete} видалено."
        return f"Контакт {name} не знайдено."

    def get_birthdays_per_period(self, days):
        """Повертає список контактів з днями народження на період."""
        upcoming_birthdays = []
        today = datetime.now().date()
        for record in self.data.values():
            if record.birthday:
                days_to_birth = record.days_to_birthday()
                if days_to_birth is not None and 0 <= days_to_birth <= days:
                    try:
                        day, month, _ = map(int, record.birthday.value.split('.'))
                        birth_date_this_year = datetime(today.year, month, day).date()
                        birth_date_next = birth_date_this_year if birth_date_this_year >= today else datetime(today.year + 1, month, day).date()
                        upcoming_birthdays.append((record, days_to_birth, birth_date_next))
                    except ValueError: continue # Ігноруємо некоректні дати
        upcoming_birthdays.sort(key=lambda x: x[1])
        result = []
        for record, days_to_birth, birth_date in upcoming_birthdays:
            when_str = "Сьогодні" if days_to_birth == 0 else f"через {days_to_birth} дн."
            result.append(f"{record.name}: {birth_date.strftime('%d.%m.%Y')} ({when_str})")
        return result

    def search_contacts(self, query):
        """Шукає контакти за рядком запиту (ім'я, телефон, email, адреса, теги, нотатки контакту)."""
        results = []
        query_lower = query.lower()
        for record in self.data.values():
            match = False
            if query_lower in record.name.value.lower(): match = True
            if not match and any(query_lower in phone.value for phone in record.phones): match = True
            if not match and record.email and query_lower in record.email.value.lower(): match = True
            if not match and record.address and query_lower in record.address.value.lower(): match = True
            # НОВЕ: Пошук за тегами та нотатками контакту
            if not match and any(query_lower in tag.lower() for tag in record.tags): match = True
            if not match and any(query_lower in note.lower() for note in record.contact_notes): match = True

            if match:
                results.append(record)
        results.sort(key=lambda r: r.name.value.lower())
        return results

    # --- НОВИЙ МЕТОД для пошуку за тегом ---
    def search_by_tag(self, tag):
        """Шукає контакти за тегом (без урахування регістру)."""
        results = []
        tag_lower = tag.lower()
        for record in self.data.values():
            if any(tag_lower == t.lower() for t in record.tags):
                results.append(record)
        # Сортуємо результати за ім'ям
        results.sort(key=lambda r: r.name.value.lower())
        return results


# --- Клас для нотатки (без змін) ---
class Note:
    """Клас для представлення нотатки."""
    def __init__(self, title, content):
        if not title: raise ValueError("Заголовок нотатки не може бути порожнім.")
        self.title = title
        self.content = content
        self.tags = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified_at = self.created_at

    def add_tag(self, tag):
        if not tag: return "Помилка: Тег не може бути порожнім."
        tag_lower = tag.lower()
        if tag_lower not in [t.lower() for t in self.tags]:
            self.tags.append(tag)
            self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tags.sort(key=str.lower)
            return f"Тег '{tag}' додано до нотатки '{self.title}'"
        return f"Тег '{tag}' вже існує в нотатці '{self.title}'"

    def remove_tag(self, tag_to_remove):
        tag_to_remove_lower = tag_to_remove.lower()
        initial_length = len(self.tags)
        self.tags = [t for t in self.tags if t.lower() != tag_to_remove_lower]
        if len(self.tags) < initial_length:
            self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Тег '{tag_to_remove}' видалено з нотатки '{self.title}'"
        return f"Тег '{tag_to_remove}' не знайдено в нотатці '{self.title}'"

    def edit_content(self, new_content):
         self.content = new_content
         self.modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        tags_str = f" [Теги: {', '.join(self.tags)}]" if self.tags else ""
        modified_str = f"(Оновлено: {self.modified_at})" if self.modified_at != self.created_at else ""
        return (f"Заголовок: {self.title}{tags_str}\n"
                f"Створено: {self.created_at} {modified_str}\n"
                f"Зміст: {self.content}")

# --- Клас для книги нотаток (без змін) ---
class NoteBook:
    """Клас для зберігання та управління нотатками."""
    def __init__(self): self.notes = []
    def add_note(self, title, content):
        if self.find_note_by_title(title): return f"Нотатка з заголовком '{title}' вже існує."
        try: self.notes.append(Note(title, content)); return f"Нотатку '{title}' додано"
        except ValueError as e: return f"Помилка: {e}"
    def find_note_by_title(self, title):
        title_lower = title.lower()
        for note in self.notes:
            if note.title.lower() == title_lower: return note
        return None
    def edit_note(self, title, new_content):
        note = self.find_note_by_title(title)
        if note: note.edit_content(new_content); return f"Нотатку '{title}' оновлено"
        return f"Нотатку '{title}' не знайдено"
    def delete_note(self, title):
        note = self.find_note_by_title(title)
        if note: self.notes.remove(note); return f"Нотатку '{title}' видалено"
        return f"Нотатку '{title}' не знайдено"
    def search_notes(self, query):
        results = []; query_lower = query.lower()
        for note in self.notes:
            if (query_lower in note.title.lower() or query_lower in note.content.lower() or
                any(query_lower in tag.lower() for tag in note.tags)): results.append(note)
        results.sort(key=lambda n: n.title.lower()); return results
    def search_by_tag(self, tag):
        tag_lower = tag.lower(); results = [note for note in self.notes if tag_lower in [t.lower() for t in note.tags]]
        results.sort(key=lambda n: n.title.lower()); return results
    def sort_notes_by_tag(self):
        notes_by_tag = {}; notes_without_tags = []
        for note in self.notes:
            if note.tags:
                added_to_tag = False
                for tag in note.tags:
                    tag_lower = tag.lower()
                    if tag_lower not in notes_by_tag: notes_by_tag[tag_lower] = []
                    if note not in notes_by_tag[tag_lower]: notes_by_tag[tag_lower].append(note)
                    added_to_tag = True
                if not added_to_tag: notes_without_tags.append(note)
            else: notes_without_tags.append(note)
        sorted_tags = sorted(notes_by_tag.keys()); final_sorted_notes = []; processed_notes = set()
        for tag in sorted_tags:
            notes_by_tag[tag].sort(key=lambda n: n.title.lower())
            for note in notes_by_tag[tag]:
                if note not in processed_notes: final_sorted_notes.append(note); processed_notes.add(note)
        notes_without_tags.sort(key=lambda n: n.title.lower())
        for note in notes_without_tags:
             if note not in processed_notes: final_sorted_notes.append(note); processed_notes.add(note)
        self.notes = final_sorted_notes; return "Нотатки відсортовано за тегами."


# --- Головний клас додатка ---
class PersonalAssistant:
    """Клас персонального помічника, що об'єднує адресну книгу та нотатки."""
    def __init__(self):
        self.address_book = AddressBook()
        self.note_book = NoteBook()
        self.data_folder = os.path.join(os.path.expanduser("~"), "personal_assistant_data")
        self.contacts_file = os.path.join(self.data_folder, "contacts.json")
        self.notes_file = os.path.join(self.data_folder, "notes.json")
        # --- Оновлений словник команд ---
        self.commands = {
            # --- Контакти ---
            "додати контакт": self.add_contact,
            "показати контакт": self.show_contact,
            "показати всі контакти": self.show_all_contacts,
            "знайти контакт": self.search_contacts_command,
            "видалити контакт": self.delete_contact,
            "дні народження": self.birthdays_per_period,
            "додати телефон": self.add_phone_to_contact,
            "змінити телефон": self.edit_phone_in_contact,
            "видалити телефон": self.remove_phone_from_contact,
            "додати email": self.add_email_to_contact,
            "додати адресу": self.add_address_to_contact,
            "додати день народження": self.add_birthday_to_contact,
            # --- Теги та нотатки контакту (НОВЕ) ---
            "додати тег контакту": self.add_tag_to_contact,
            "видалити тег контакту": self.remove_tag_from_contact,
            "додати нотатку контакту": self.add_note_to_contact,
            "показати нотатки контакту": self.show_contact_notes,
            "видалити нотатку контакту": self.remove_note_from_contact,
            "пошук контакту за тегом": self.search_contacts_by_tag_command, # Також фільтр
            # --- Нотатки (загальні) ---
            "додати нотатку": self.add_note,
            "показати нотатку": self.show_note,
            "показати всі нотатки": self.show_all_notes,
            "змінити нотатку": self.edit_note,
            "видалити нотатку": self.delete_note,
            "знайти нотатку": self.search_notes_command,
            "додати тег": self.add_tag_to_note, # Тег до загальної нотатки
            "видалити тег": self.remove_tag_from_note, # Тег з загальної нотатки
            "пошук за тегом": self.search_notes_by_tag_command, # Пошук загальних нотаток
            "сортувати нотатки": self.sort_notes,
            # --- Загальні ---
            "допомога": self.show_help,
            "вихід": self.exit_program,
            "зберегти": self.save_data_command
        }
        self.load_data()

    def parse_input(self, user_input):
        """Розбирає введений рядок на команду та решту рядка аргументів."""
        if not user_input: return "", ""
        user_input_lower = user_input.lower()
        matched_command = None
        for command_key in self.commands:
            if user_input_lower.startswith(command_key):
                if len(user_input_lower) == len(command_key) or user_input_lower[len(command_key)].isspace():
                    if matched_command is None or len(command_key) > len(matched_command):
                        matched_command = command_key
        if matched_command:
            cmd = matched_command
            args_str = user_input[len(matched_command):].strip()
            return cmd, args_str
        else:
            parts = user_input.strip().split(' ', 1)
            cmd = parts[0].lower()
            args_str = parts[1].strip() if len(parts) > 1 else ""
            return cmd, args_str

    # --- Оновлений метод execute_command ---
    def execute_command(self, cmd, args_str):
        """Виконує команду, обробляючи рядок аргументів відповідно до команди."""
        if cmd in self.commands:
            handler = self.commands[cmd]
            processed_args = []
            try:
                # 1. Команди без аргументів
                if cmd in ["показати всі контакти", "показати всі нотатки",
                           "сортувати нотатки", "допомога", "вихід", "зберегти"]:
                    if args_str: raise ValueError(f"Команда '{cmd}' не приймає аргументів.")
                    processed_args = []

                # 2. Команди з одним обов'язковим аргументом
                elif cmd in ["показати контакт", "видалити контакт", "знайти контакт",
                             "показати нотатку", "видалити нотатку", "знайти нотатку",
                             "пошук за тегом", "дні народження",
                             "показати нотатки контакту", # НОВЕ
                             "пошук контакту за тегом"]: # НОВЕ
                    if not args_str: raise ValueError(f"Для команди '{cmd}' потрібен один аргумент.")
                    processed_args = [args_str]

                # 3. Команди з двома обов'язковими аргументами (розділені пробілом)
                elif cmd in ["додати телефон", "видалити телефон", "додати email",
                             "додати день народження", "додати тег", "видалити тег",
                             "додати тег контакту", "видалити тег контакту", # НОВЕ
                             "видалити нотатку контакту"]: # НОВЕ (name, index)
                    parts = [a.strip() for a in args_str.split(maxsplit=1)]
                    if len(parts) < 2 or not parts[0] or not parts[1]:
                        raise ValueError(f"Для команди '{cmd}' потрібно два аргументи.")
                    processed_args = parts

                # 4. Команда зміни телефону (3 аргументи)
                elif cmd == "змінити телефон":
                    parts = [a.strip() for a in args_str.split(maxsplit=2)]
                    if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
                        raise ValueError(f"Для команди '{cmd}' потрібно три аргументи (ім'я, старий, новий).")
                    processed_args = parts

                # 5. Команди з першим аргументом і необов'язковим другим/рештою
                elif cmd in ["додати контакт", "додати адресу", "додати нотатку", "змінити нотатку",
                             "додати нотатку контакту"]: # НОВЕ
                     parts = [a.strip() for a in args_str.split(maxsplit=1)]
                     if not parts or not parts[0]: raise ValueError(f"Для команди '{cmd}' потрібно вказати ім'я або заголовок.")
                     processed_args = parts # Буде [name/title] або [name/title, rest]

                else: # Непередбачена команда (помилка в логіці)
                     print(f"УВАГА: Невизначена логіка обробки аргументів для команди '{cmd}'.")
                     processed_args = [args_str] if args_str else []

                # --- Виклик обробника ---
                return handler(*processed_args)

            except TypeError as e:
                sig = inspect.signature(handler)
                print(f"Debug: Calling {cmd} with args: {processed_args}")
                print(f"Debug: TypeError details: {e}")
                return (f"Помилка: Неправильна кількість або тип аргументів для команди '{cmd}'.\n"
                        f"       Отримано: {processed_args}\n"
                        f"       Сигнатура функції: {handler.__name__}{sig}\n"
                        f"       Повідомлення: {e}")
            except ValueError as e: return f"Помилка: {e}"
            except IndexError as e: return f"Помилка індексу: {e}" # Для видалення нотатки контакту
            except Exception as e:
                print(f"Непередбачена помилка при виконанні команди '{cmd}' з аргументами '{args_str}':")
                traceback.print_exc()
                return f"Виникла непередбачена помилка: {e}. Дивіться деталі в консолі."
        else: # Команду не знайдено
            guessed_cmd = self.guess_command(cmd)
            full_input_for_guess = cmd + (f" {args_str}" if args_str else "")
            if not guessed_cmd: guessed_cmd = self.guess_command(full_input_for_guess)
            if guessed_cmd: return f"Команду '{full_input_for_guess}' не знайдено. Можливо, ви мали на увазі '{guessed_cmd}'?"
            return f"Команду '{cmd}' не знайдено. Введіть 'допомога'."


    # --- Методи-обробники команд ---
    def add_contact(self, name, phone=None):
        existing_record = self.address_book.find(name)
        if existing_record: return f"Контакт {existing_record.name.value} вже існує."
        record = Record(name); message = f"Контакт {name} додано."
        if phone:
            try: record.add_phone(phone); message += f" З номером телефону {phone}."
            except ValueError as e: self.address_book.add_record(record); return f"Контакт {name} додано, але помилка телефону: {e}"
        self.address_book.add_record(record); return message
    def show_contact(self, name):
        record = self.address_book.find(name)
        return str(record) if record else f"Контакт {name} не знайдено."
    def show_all_contacts(self):
        if not self.address_book.data: return "Книга контактів порожня"
        result = ["Книга контактів:"]
        for record_name in sorted(self.address_book.data.keys(), key=str.lower):
            result.append("-" * 40) # Додаємо роздільник перед кожним контактом
            result.append(str(self.address_book.data[record_name]))
        return "\n".join(result)
    def search_contacts_command(self, query):
        results = self.address_book.search_contacts(query)
        if not results: return f"Контактів, що містять '{query}', не знайдено"
        result = [f"Знайдено {len(results)} контактів для запиту '{query}':"]
        for record in results: result.append("-" * 40); result.append(str(record))
        return "\n".join(result)
    def delete_contact(self, name): return self.address_book.delete(name)
    def birthdays_per_period(self, days_str):
        try:
            days = int(days_str)
            if days < 0: return "Кількість днів не може бути від'ємною."
            birthdays = self.address_book.get_birthdays_per_period(days)
            if not birthdays: return f"Немає днів народження протягом {days} днів." if days != 0 else "Немає днів народження сьогодні."
            period_str = "Сьогодні:" if days == 0 else f"На {days} дн.:"
            return f"{period_str}\n" + "\n".join(birthdays)
        except ValueError: return "Кількість днів має бути цілим числом."
    def add_phone_to_contact(self, name, phone):
        record = self.address_book.find(name); return record.add_phone(phone) if record else f"Контакт {name} не знайдено."
    def edit_phone_in_contact(self, name, old_phone, new_phone):
         record = self.address_book.find(name); return record.edit_phone(old_phone, new_phone) if record else f"Контакт {name} не знайдено."
    def remove_phone_from_contact(self, name, phone):
        record = self.address_book.find(name); return record.remove_phone(phone) if record else f"Контакт {name} не знайдено."
    def add_email_to_contact(self, name, email):
        record = self.address_book.find(name); return record.add_email(email) if record else f"Контакт {name} не знайдено."
    def add_address_to_contact(self, name, address):
        record = self.address_book.find(name)
        if not record: return f"Контакт {name} не знайдено."
        if not address: return "Помилка: Адреса не може бути порожньою."
        return record.add_address(address)
    def add_birthday_to_contact(self, name, birthday):
        record = self.address_book.find(name); return record.add_birthday(birthday) if record else f"Контакт {name} не знайдено."

    # --- НОВІ ОБРОБНИКИ для тегів та нотаток контакту ---
    def add_tag_to_contact(self, name, tag):
        """Додає тег до вказаного контакту."""
        record = self.address_book.find(name)
        return record.add_tag(tag) if record else f"Контакт {name} не знайдено."

    def remove_tag_from_contact(self, name, tag):
        """Видаляє тег з вказаного контакту."""
        record = self.address_book.find(name)
        return record.remove_tag(tag) if record else f"Контакт {name} не знайдено."

    def add_note_to_contact(self, name, note_text):
        """Додає нотатку до вказаного контакту."""
        record = self.address_book.find(name)
        return record.add_contact_note(note_text) if record else f"Контакт {name} не знайдено."

    def show_contact_notes(self, name):
        """Показує всі нотатки для вказаного контакту."""
        record = self.address_book.find(name)
        if not record: return f"Контакт {name} не знайдено."
        if not record.contact_notes: return f"У контакта {name} немає нотаток."
        result = [f"Нотатки для контакту {name}:"]
        for i, note in enumerate(record.contact_notes):
            result.append(f"  {i+1}. {note}")
        return "\n".join(result)

    def remove_note_from_contact(self, name, index_str):
        """Видаляє нотатку контакту за її номером."""
        record = self.address_book.find(name)
        if not record: return f"Контакт {name} не знайдено."
        try:
            index = int(index_str)
            return record.remove_contact_note(index) # IndexError обробляється в execute_command
        except ValueError:
            return "Помилка: Індекс нотатки має бути цілим числом."

    def search_contacts_by_tag_command(self, tag):
        """Обробник команди для пошуку/фільтрації контактів за тегом."""
        results = self.address_book.search_by_tag(tag)
        if not results: return f"Контактів з тегом '{tag}' не знайдено."
        result = [f"Знайдено {len(results)} контактів з тегом '{tag}':"]
        for record in results: result.append("-" * 40); result.append(str(record))
        return "\n".join(result)

    # --- Обробники для загальних нотаток ---
    def add_note(self, title, content=''): return self.note_book.add_note(title, content)
    def show_note(self, title):
        note = self.note_book.find_note_by_title(title); return str(note) if note else f"Нотатку '{title}' не знайдено."
    def show_all_notes(self):
        if not self.note_book.notes: return "Книга нотаток порожня"
        result = ["Книга нотаток:"]; notes_to_show = sorted(self.note_book.notes, key=lambda n: n.title.lower())
        for note in notes_to_show: result.append("-" * 40); result.append(str(note))
        return "\n".join(result)
    def edit_note(self, title, new_content=''): return self.note_book.edit_note(title, new_content)
    def delete_note(self, title): return self.note_book.delete_note(title)
    def search_notes_command(self, query):
        results = self.note_book.search_notes(query)
        if not results: return f"Нотаток, що містять '{query}', не знайдено"
        result = [f"Знайдено {len(results)} нотаток для запиту '{query}':"]
        for note in results: result.append("-" * 40); result.append(str(note))
        return "\n".join(result)
    def add_tag_to_note(self, title, tag): # Тег до загальної нотатки
        note = self.note_book.find_note_by_title(title); return note.add_tag(tag) if note else f"Нотатку '{title}' не знайдено."
    def remove_tag_from_note(self, title, tag): # Тег з загальної нотатки
        note = self.note_book.find_note_by_title(title); return note.remove_tag(tag) if note else f"Нотатку '{title}' не знайдено."
    def search_notes_by_tag_command(self, tag): # Пошук загальних нотаток
        results = self.note_book.search_by_tag(tag)
        if not results: return f"Нотаток з тегом '{tag}' не знайдено."
        result = [f"Знайдено {len(results)} нотаток з тегом '{tag}':"]
        for note in results: result.append("-" * 40); result.append(str(note))
        return "\n".join(result)
    def sort_notes(self):
         if not self.note_book.notes: return "Книга нотаток порожня."
         return self.note_book.sort_notes_by_tag()

    # --- Загальні методи ---
    # --- Оновлений метод show_help ---
    def show_help(self):
        """Показує список доступних команд з описом."""
        commands_help = [
            "--- Контакти ---",
            "додати контакт <ім'я> [телефон]",
            "показати контакт <ім'я>",
            "показати всі контакти",
            "знайти контакт <запит> (шукає всюди, вкл. теги/нотатки контакту)",
            "видалити контакт <ім'я>",
            "дні народження <кількість_днів> (0 - сьогодні)",
            "додати телефон <ім'я> <телефон>",
            "змінити телефон <ім'я> <старий_тел> <новий_тел>",
            "видалити телефон <ім'я> <телефон>",
            "додати email <ім'я> <email>",
            "додати адресу <ім'я> <адреса>",
            "додати день народження <ім'я> <DD.MM.YYYY>",
            "",
            "--- Теги та Нотатки Контакту ---",
            "додати тег контакту <ім'я> <тег>",
            "видалити тег контакту <ім'я> <тег>",
            "пошук контакту за тегом <тег> (фільтр)",
            "додати нотатку контакту <ім'я> <текст нотатки>",
            "показати нотатки контакту <ім'я>",
            "видалити нотатку контакту <ім'я> <номер нотатки>",
            "",
            "--- Загальні Нотатки ---",
            "додати нотатку <заголовок> [зміст]",
            "показати нотатку <заголовок>",
            "показати всі нотатки",
            "змінити нотатку <заголовок> [новий_зміст]",
            "видалити нотатку <заголовок>",
            "знайти нотатку <запит>",
            "додати тег <заголовок> <тег>",
            "видалити тег <заголовок> <тег>",
            "пошук за тегом <тег>",
            "сортувати нотатки (за тегами)",
            "",
            "--- Загальні ---",
            "допомога",
            "зберегти",
            "вихід"
        ]
        return "Доступні команди:\n" + "\n".join(f"  {cmd}" for cmd in commands_help) # Додаємо відступ

    def save_data_command(self): self.save_data(); return "Дані успішно збережено."
    def exit_program(self): self.save_data(); return "До побачення!"

    # --- Оновлений метод save_data ---
    def save_data(self):
        """Зберігає контакти та нотатки у JSON файли."""
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            # Зберігаємо контакти
            contacts_to_save = {}
            for name, record in self.address_book.data.items():
                contacts_to_save[name] = {
                    "phones": [phone.value for phone in record.phones],
                    "email": record.email.value if record.email else None,
                    "address": record.address.value if record.address else None,
                    "birthday": record.birthday.value if record.birthday else None,
                    "tags": record.tags, # НОВЕ: Зберігаємо теги контакту
                    "contact_notes": record.contact_notes # НОВЕ: Зберігаємо нотатки контакту
                }
            with open(self.contacts_file, 'w', encoding='utf-8') as file:
                json.dump(contacts_to_save, file, ensure_ascii=False, indent=4)
            # Зберігаємо нотатки
            notes_to_save = []
            for note in self.note_book.notes:
                notes_to_save.append({
                    "title": note.title, "content": note.content, "tags": note.tags,
                    "created_at": note.created_at, "modified_at": note.modified_at
                })
            with open(self.notes_file, 'w', encoding='utf-8') as file:
                json.dump(notes_to_save, file, ensure_ascii=False, indent=4)
        except IOError as e: print(f"Помилка збереження даних: {e}")
        except Exception as e: print(f"Невідома помилка під час збереження даних: {e}")

    # --- Оновлений метод load_data ---
    def load_data(self):
        """Завантажує контакти та нотатки з JSON файлів."""
        # Завантажуємо контакти
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as file:
                    contacts_data = json.load(file)
                for name, data in contacts_data.items():
                    try:
                        record = Record(name)
                        for phone in data.get("phones", []):
                            try: record.add_phone(phone)
                            except ValueError: print(f"Попередження: Пропущено тел '{phone}' для '{name}'.")
                        if data.get("email"):
                            try: record.add_email(data["email"])
                            except ValueError: print(f"Попередження: Пропущено email '{data['email']}' для '{name}'.")
                        if data.get("address"): record.add_address(data["address"])
                        if data.get("birthday"):
                            try: record.add_birthday(data["birthday"])
                            except ValueError: print(f"Попередження: Пропущено ДН '{data['birthday']}' для '{name}'.")
                        # НОВЕ: Завантажуємо теги та нотатки контакту
                        record.tags = data.get("tags", [])
                        record.contact_notes = data.get("contact_notes", [])
                        record.tags.sort(key=str.lower) # Сортуємо теги після завантаження

                        self.address_book.data[record.name.value] = record
                    except ValueError as e: print(f"Помилка завантаження '{name}': {e}")
                    except KeyError as e: print(f"Помилка завантаження '{name}': відсутнє поле {e}.")
                    except Exception as e: print(f"Помилка обробки контакту '{name}': {e}")
            except json.JSONDecodeError: print(f"Помилка: Файл контактів ({self.contacts_file}) пошкоджено.")
            except IOError as e: print(f"Помилка читання файлу контактів: {e}")
            except Exception as e: print(f"Помилка завантаження контактів: {e}")

        # Завантажуємо нотатки
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as file:
                    notes_data = json.load(file)
                for data in notes_data:
                     try:
                         title = data.get("title")
                         if not title: print(f"Попередження: Пропущено нотатку без заголовка: {data}"); continue
                         note = Note(title, data.get("content", ""))
                         note.tags = data.get("tags", [])
                         note.created_at = data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                         note.modified_at = data.get("modified_at", note.created_at)
                         note.tags.sort(key=str.lower)
                         self.note_book.notes.append(note)
                     except ValueError as e: print(f"Помилка завантаження нотатки '{data.get('title', '')}': {e}")
                     except KeyError as e: print(f"Помилка завантаження нотатки: відсутнє поле {e}.")
                     except Exception as e: print(f"Помилка обробки нотатки {data}: {e}")
            except json.JSONDecodeError: print(f"Помилка: Файл нотаток ({self.notes_file}) пошкоджено.")
            except IOError as e: print(f"Помилка читання файлу нотаток: {e}")
            except Exception as e: print(f"Помилка завантаження нотаток: {e}")


# --- Головна функція запуску ---
def main():
    """Головна функція для запуску персонального помічника."""
    assistant = PersonalAssistant()
    print("Вітаю! Я ваш персональний помічник.")
    print("Введіть 'допомога' для перегляду доступних команд.")
    while True:
        try:
            user_input = input(">>> ").strip()
            if not user_input: continue
            command, args_string = assistant.parse_input(user_input)
            if command == "вихід": print(assistant.exit_program()); break
            result = assistant.execute_command(command, args_string)
            print(result)
        except KeyboardInterrupt: print("\nПереривання... Зберігаю дані."); assistant.save_data(); print("До побачення!"); break
        except EOFError: print("\nКінець вводу... Зберігаю дані."); assistant.save_data(); print("До побачення!"); break

if __name__ == "__main__":
    main()
