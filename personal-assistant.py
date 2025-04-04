import re
import os
import json
import datetime
from collections import UserDict
from datetime import datetime, timedelta
import difflib


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Ім'я не може бути порожнім")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректний номер телефону. Використовуйте формат +380XXXXXXXXX або 0XXXXXXXXX")
        super().__init__(value)

    def validate(self, value):
        # Перевірка для українських номерів телефону: +380XXXXXXXXX або 0XXXXXXXXX
        pattern = r"^(\+380\d{9}|0\d{9})$"
        return bool(re.match(pattern, value))


class Email(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректна електронна адреса")
        super().__init__(value)

    def validate(self, value):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, value))


class Address(Field):
    pass


class Birthday(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Некоректна дата народження. Використовуйте формат DD.MM.YYYY")
        super().__init__(value)

    def validate(self, value):
        pattern = r"^\d{2}\.\d{2}\.\d{4}$"
        if not re.match(pattern, value):
            return False
        
        try:
            day, month, year = map(int, value.split('.'))
            datetime(year, month, day)
            return True
        except ValueError:
            return False


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.email = None
        self.address = None
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))
        return f"Номер телефону {phone} додано для контакту {self.name}"

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return f"Номер телефону {phone} видалено для контакту {self.name}"
        return f"Номер телефону {phone} не знайдено для контакту {self.name}"

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                return f"Номер телефону змінено з {old_phone} на {new_phone} для контакту {self.name}"
        return f"Номер телефону {old_phone} не знайдено для контакту {self.name}"

    def add_email(self, email):
        self.email = Email(email)
        return f"Email {email} додано для контакту {self.name}"

    def add_address(self, address):
        self.address = Address(address)
        return f"Адресу додано для контакту {self.name}"

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
        return f"Дату народження додано для контакту {self.name}"

    def days_to_birthday(self):
        if not self.birthday:
            return None
        
        today = datetime.now().date()
        day, month, year = map(int, self.birthday.value.split('.'))
        
        # Встановлюємо дату народження в поточному році
        birthday_date = datetime(today.year, month, day).date()
        
        # Якщо день народження вже минув у цьому році, шукаємо наступний рік
        if birthday_date < today:
            birthday_date = datetime(today.year + 1, month, day).date()
        
        return (birthday_date - today).days

    def __str__(self):
        phones_str = ", ".join(str(p) for p in self.phones)
        email_str = f", Email: {self.email}" if self.email else ""
        address_str = f", Адреса: {self.address}" if self.address else ""
        birthday_str = f", День народження: {self.birthday}" if self.birthday else ""
        days_to_birth = f" (Днів до дня народження: {self.days_to_birthday()})" if self.birthday else ""
        
        return f"Контакт: {self.name}, Телефони: {phones_str}{email_str}{address_str}{birthday_str}{days_to_birth}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record
        return f"Контакт {record.name} додано до книги контактів"

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return f"Контакт {name} видалено з книги контактів"
        return f"Контакт {name} не знайдено в книзі контактів"

    def get_birthdays_per_period(self, days):
        upcoming_birthdays = []
        today = datetime.now().date()
        
        for record in self.data.values():
            if record.birthday:
                days_to_birth = record.days_to_birthday()
                if days_to_birth is not None and days_to_birth <= days:
                    day, month, year = map(int, record.birthday.value.split('.'))
                    birth_date = datetime(today.year, month, day).date()
                    if birth_date < today:
                        birth_date = datetime(today.year + 1, month, day).date()
                    upcoming_birthdays.append((record, days_to_birth, birth_date))
        
        # Сортуємо за кількістю днів до дня народження
        upcoming_birthdays.sort(key=lambda x: x[1])
        
        result = []
        for record, days_to_birth, birth_date in upcoming_birthdays:
            result.append(f"{record.name}: {birth_date.strftime('%d.%m.%Y')} (через {days_to_birth} днів)")
        
        return result

    def search_contacts(self, query):
        results = []
        query = query.lower()
        
        for record in self.data.values():
            name_match = query in record.name.value.lower()
            phone_match = any(query in phone.value for phone in record.phones)
            email_match = record.email and query in record.email.value.lower()
            address_match = record.address and query in record.address.value.lower()
            
            if name_match or phone_match or email_match or address_match:
                results.append(record)
        
        return results


class Note:
    def __init__(self, title, content):
        self.title = title
        self.content = content
        self.tags = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)
            return f"Тег '{tag}' додано до нотатки '{self.title}'"
        return f"Тег '{tag}' вже існує в нотатці '{self.title}'"

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            return f"Тег '{tag}' видалено з нотатки '{self.title}'"
        return f"Тег '{tag}' не знайдено в нотатці '{self.title}'"

    def __str__(self):
        tags_str = f" [Теги: {', '.join(self.tags)}]" if self.tags else ""
        return f"Заголовок: {self.title}{tags_str}\nДата створення: {self.created_at}\nЗміст: {self.content}"


class NoteBook:
    def __init__(self):
        self.notes = []

    def add_note(self, title, content):
        note = Note(title, content)
        self.notes.append(note)
        return f"Нотатку '{title}' додано"

    def find_note_by_title(self, title):
        for note in self.notes:
            if note.title.lower() == title.lower():
                return note
        return None

    def edit_note(self, title, new_content):
        note = self.find_note_by_title(title)
        if note:
            note.content = new_content
            return f"Нотатку '{title}' оновлено"
        return f"Нотатку '{title}' не знайдено"

    def delete_note(self, title):
        note = self.find_note_by_title(title)
        if note:
            self.notes.remove(note)
            return f"Нотатку '{title}' видалено"
        return f"Нотатку '{title}' не знайдено"

    def search_notes(self, query):
        results = []
        query = query.lower()
        
        for note in self.notes:
            if (query in note.title.lower() or 
                query in note.content.lower() or 
                any(query in tag.lower() for tag in note.tags)):
                results.append(note)
        
        return results

    def search_by_tag(self, tag):
        return [note for note in self.notes if tag.lower() in [t.lower() for t in note.tags]]


class PersonalAssistant:
    def __init__(self):
        self.address_book = AddressBook()
        self.note_book = NoteBook()
        self.data_folder = os.path.join(os.path.expanduser("~"), "personal_assistant")
        self.contacts_file = os.path.join(self.data_folder, "contacts.json")
        self.notes_file = os.path.join(self.data_folder, "notes.json")
        self.commands = {
            "додати контакт": self.add_contact,
            "показати контакт": self.show_contact,
            "показати всі контакти": self.show_all_contacts,
            "знайти контакт": self.search_contacts,
            "видалити контакт": self.delete_contact,
            "дні народження": self.birthdays_per_period,
            "додати телефон": self.add_phone_to_contact,
            "видалити телефон": self.remove_phone_from_contact,
            "додати email": self.add_email_to_contact,
            "додати адресу": self.add_address_to_contact,
            "додати день народження": self.add_birthday_to_contact,
            "додати нотатку": self.add_note,
            "показати нотатку": self.show_note,
            "показати всі нотатки": self.show_all_notes,
            "змінити нотатку": self.edit_note,
            "видалити нотатку": self.delete_note,
            "знайти нотатку": self.search_notes,
            "додати тег": self.add_tag_to_note,
            "видалити тег": self.remove_tag_from_note,
            "пошук за тегом": self.search_notes_by_tag,
            "допомога": self.show_help,
            "вихід": self.exit_program
        }
        self.load_data()

    def parse_input(self, user_input):
        if not user_input:
            return "", []
        
        cmd, *args = user_input.strip().split(' ', 1)
        cmd = cmd.lower()
        
        if args:
            args = args[0].split(', ')
        
        return cmd, args

    def guess_command(self, user_input):
        """Спроба визначити, яку команду хоче використати користувач."""
        user_input = user_input.lower()
        
        # Прямі ключові слова для швидкого визначення команди
        if "додати" in user_input and "контакт" in user_input:
            return "додати контакт"
        elif "показати" in user_input and "всі" in user_input and "контакт" in user_input:
            return "показати всі контакти"
        elif "показати" in user_input and "контакт" in user_input:
            return "показати контакт"
        elif "знайти" in user_input and "контакт" in user_input:
            return "знайти контакт"
        elif "видалити" in user_input and "контакт" in user_input:
            return "видалити контакт"
        elif "дн" in user_input and "народж" in user_input:
            return "дні народження"
        elif "додати" in user_input and "телефон" in user_input:
            return "додати телефон"
        elif "видалити" in user_input and "телефон" in user_input:
            return "видалити телефон"
        elif "додати" in user_input and "email" in user_input:
            return "додати email"
        elif "додати" in user_input and "адрес" in user_input:
            return "додати адресу"
        elif "додати" in user_input and ("народж" in user_input or "нар" in user_input):
            return "додати день народження"
        elif "додати" in user_input and "нотат" in user_input:
            return "додати нотатку"
        elif "показати" in user_input and "всі" in user_input and "нотат" in user_input:
            return "показати всі нотатки"
        elif "показати" in user_input and "нотат" in user_input:
            return "показати нотатку"
        elif ("змінити" in user_input or "редагувати" in user_input) and "нотат" in user_input:
            return "змінити нотатку"
        elif "видалити" in user_input and "нотат" in user_input:
            return "видалити нотатку"
        elif "знайти" in user_input and "нотат" in user_input:
            return "знайти нотатку"
        elif "додати" in user_input and "тег" in user_input:
            return "додати тег"
        elif "видалити" in user_input and "тег" in user_input:
            return "видалити тег"
        elif "пошук" in user_input and "тег" in user_input:
            return "пошук за тегом"
        elif "допомо" in user_input or "команд" in user_input:
            return "допомога"
        elif "вихід" in user_input or "exit" in user_input or "закрити" in user_input:
            return "вихід"
        
        # Якщо точне співпадіння не знайдено, використовуємо схожість рядків
        possible_commands = list(self.commands.keys())
        closest_match = difflib.get_close_matches(user_input, possible_commands, n=1, cutoff=0.4)
        
        if closest_match:
            return closest_match[0]
        
        return None

    def execute_command(self, cmd, args):
        if cmd in self.commands:
            return self.commands[cmd](*args)
        else:
            guessed_cmd = self.guess_command(cmd + (" " + args[0] if args else ""))
            if guessed_cmd:
                return f"Команду не знайдено. Можливо, ви мали на увазі '{guessed_cmd}'?"
            return "Команду не знайдено. Введіть 'допомога' для перегляду доступних команд."

    def add_contact(self, name, *_):
        if name in self.address_book.data:
            return f"Контакт {name} вже існує в книзі контактів"
        record = Record(name)
        return self.address_book.add_record(record)

    def show_contact(self, name, *_):
        record = self.address_book.find(name)
        if record:
            return str(record)
        return f"Контакт {name} не знайдено в книзі контактів"

    def show_all_contacts(self, *_):
        if not self.address_book.data:
            return "Книга контактів порожня"
        
        result = ["Книга контактів:"]
        for record in self.address_book.data.values():
            result.append(str(record))
        return "\n".join(result)

    def search_contacts(self, query, *_):
        results = self.address_book.search_contacts(query)
        if not results:
            return f"Контактів, що містять '{query}', не знайдено"
        
        result = [f"Знайдено {len(results)} контактів для запиту '{query}':"]
        for record in results:
            result.append(str(record))
        return "\n".join(result)

    def delete_contact(self, name, *_):
        return self.address_book.delete(name)

    def birthdays_per_period(self, days_str, *_):
        try:
            days = int(days_str)
            if days < 1:
                return "Кількість днів має бути додатним числом"
            
            birthdays = self.address_book.get_birthdays_per_period(days)
            if not birthdays:
                return f"Немає днів народження протягом наступних {days} днів"
            
            result = [f"Дні народження протягом наступних {days} днів:"]
            result.extend(birthdays)
            return "\n".join(result)
        except ValueError:
            return "Кількість днів має бути цілим числом"

    def add_phone_to_contact(self, name, phone, *_):
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        
        try:
            return record.add_phone(phone)
        except ValueError as e:
            return str(e)

    def remove_phone_from_contact(self, name, phone, *_):
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        
        return record.remove_phone(phone)

    def add_email_to_contact(self, name, email, *_):
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        
        try:
            return record.add_email(email)
        except ValueError as e:
            return str(e)

    def add_address_to_contact(self, name, *args):
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        
        address = ", ".join(args) if args else ""
        return record.add_address(address)

    def add_birthday_to_contact(self, name, birthday, *_):
        record = self.address_book.find(name)
        if not record:
            return f"Контакт {name} не знайдено в книзі контактів"
        
        try:
            return record.add_birthday(birthday)
        except ValueError as e:
            return str(e)

    def add_note(self, title, *args):
        content = ", ".join(args) if args else ""
        return self.note_book.add_note(title, content)

    def show_note(self, title, *_):
        note = self.note_book.find_note_by_title(title)
        if note:
            return str(note)
        return f"Нотатку '{title}' не знайдено"

    def show_all_notes(self, *_):
        if not self.note_book.notes:
            return "Книга нотаток порожня"
        
        result = ["Книга нотаток:"]
        for note in self.note_book.notes:
            result.append(str(note))
            result.append("-" * 40)
        return "\n".join(result)

    def edit_note(self, title, *args):
        content = ", ".join(args) if args else ""
        return self.note_book.edit_note(title, content)

    def delete_note(self, title, *_):
        return self.note_book.delete_note(title)

    def search_notes(self, query, *_):
        results = self.note_book.search_notes(query)
        if not results:
            return f"Нотаток, що містять '{query}', не знайдено"
        
        result = [f"Знайдено {len(results)} нотаток для запиту '{query}':"]
        for note in results:
            result.append(str(note))
            result.append("-" * 40)
        return "\n".join(result)

    def add_tag_to_note(self, title, tag, *_):
        note = self.note_book.find_note_by_title(title)
        if not note:
            return f"Нотатку '{title}' не знайдено"
        
        return note.add_tag(tag)

    def remove_tag_from_note(self, title, tag, *_):
        note = self.note_book.find_note_by_title(title)
        if not note:
            return f"Нотатку '{title}' не знайдено"
        
        return note.remove_tag(tag)

    def search_notes_by_tag(self, tag, *_):
        results = self.note_book.search_by_tag(tag)
        if not results:
            return f"Нотаток з тегом '{tag}' не знайдено"
        
        result = [f"Знайдено {len(results)} нотаток з тегом '{tag}':"]
        for note in results:
            result.append(str(note))
            result.append("-" * 40)
        return "\n".join(result)

    def show_help(self, *_):
        commands = [
            "додати контакт <ім'я> - Додати новий контакт",
            "показати контакт <ім'я> - Показати інформацію про контакт",
            "показати всі контакти - Показати всі контакти",
            "знайти контакт <запит> - Знайти контакт за запитом",
            "видалити контакт <ім'я> - Видалити контакт",
            "дні народження <кількість_днів> - Показати контакти з днями народження протягом вказаної кількості днів",
            "додати телефон <ім'я> <телефон> - Додати номер телефону для контакту",
            "видалити телефон <ім'я> <телефон> - Видалити номер телефону з контакту",
            "додати email <ім'я> <email> - Додати email для контакту",
            "додати адресу <ім'я> <адреса> - Додати адресу для контакту",
            "додати день народження <ім'я> <дата> - Додати день народження для контакту (формат: DD.MM.YYYY)",
            "додати нотатку <заголовок> <зміст> - Додати нову нотатку",
            "показати нотатку <заголовок> - Показати нотатку за заголовком",
            "показати всі нотатки - Показати всі нотатки",
            "змінити нотатку <заголовок> <новий_зміст> - Змінити зміст нотатки",
            "видалити нотатку <заголовок> - Видалити нотатку",
            "знайти нотатку <запит> - Знайти нотатку за запитом",
            "додати тег <заголовок> <тег> - Додати тег до нотатки",
            "видалити тег <заголовок> <тег> - Видалити тег з нотатки",
            "пошук за тегом <тег> - Знайти нотатки за тегом",
            "допомога - Показати доступні команди",
            "вихід - Вийти з програми"
        ]
        return "Доступні команди:\n" + "\n".join(commands)

    def exit_program(self, *_):
        self.save_data()
        return "До побачення!"

    def save_data(self):
        # Створюємо папку, якщо вона не існує
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Зберігаємо контакти
        contacts_data = {}
        for name, record in self.address_book.data.items():
            contacts_data[name] = {
                "phones": [phone.value for phone in record.phones],
                "email": record.email.value if record.email else None,
                "address": record.address.value if record.address else None,
                "birthday": record.birthday.value if record.birthday else None
            }
        
        with open(self.contacts_file, 'w', encoding='utf-8') as file:
            json.dump(contacts_data, file, ensure_ascii=False, indent=2)
        
        # Зберігаємо нотатки
        notes_data = []
        for note in self.note_book.notes:
            notes_data.append({
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "created_at": note.created_at
            })
        
        with open(self.notes_file, 'w', encoding='utf-8') as file:
            json.dump(notes_data, file, ensure_ascii=False, indent=2)

    def load_data(self):
        # Завантажуємо контакти
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as file:
                    contacts_data = json.load(file)
                
                for name, data in contacts_data.items():
                    record = Record(name)
                    
                    for phone in data["phones"]:
                        try:
                            record.add_phone(phone)
                        except ValueError:
                            continue
                    
                    if data["email"]:
                        try:
                            record.add_email(data["email"])
                        except ValueError:
                            pass
                    
                    if data["address"]:
                        record.add_address(data["address"])
                    
                    if data["birthday"]:
                        try:
                            record.add_birthday(data["birthday"])
                        except ValueError:
                            pass
                    
                    self.address_book.add_record(record)
            except (json.JSONDecodeError, KeyError):
                # Якщо є проблеми з файлом, ігноруємо їх
                pass
        
        # Завантажуємо нотатки
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as file:
                    notes_data = json.load(file)
                
                for data in notes_data:
                    note = Note(data["title"], data["content"])
                    note.tags = data["tags"]
                    note.created_at = data["created_at"]
                    self.note_book.notes.append(note)
            except (json.JSONDecodeError, KeyError):
                # Якщо є проблеми з файлом, ігноруємо їх
                pass


def main():
    assistant = PersonalAssistant()
    print("Вітаю! Я ваш персональний помічник. Введіть 'допомога' для перегляду доступних команд.")
    
    while True:
        user_input = input(">>> ")
        command, args = assistant.parse_input(user_input)
        
        if not command:
            continue
        
        result = assistant.execute_command(command.lower(), args)
        print(result)
        
        if command.lower() == "вихід":
            break


if __name__ == "__main__":
    main()
