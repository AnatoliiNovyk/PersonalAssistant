import re
import pickle
from collections import UserDict
from datetime import datetime, timedelta
import difflib # Для додаткового функціоналу вгадування команд
import os # Для роботи з файловою системою

# --- Класи для Контактів ---

class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value):
        self._value = None # Ініціалізуємо внутрішнє значення як None
        self.value = value # Використовуємо сеттер для валідації

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # Тут можна додати загальну логіку валідації, якщо потрібно
        # Наприклад, перевірка на порожній рядок для обов'язкових полів
        # if not value:
        #     raise ValueError("Поле не може бути порожнім")
        self._value = value

    def __str__(self):
        return str(self.value) if self.value is not None else ""

class Name(Field):
    """Клас для зберігання імені контакту. Обов'язкове поле."""
    @Field.value.setter
    def value(self, value):
        if not value: # Ім'я не може бути порожнім
            raise ValueError("Ім'я контакту не може бути порожнім.")
        self._value = value

class Phone(Field):
    """Клас для зберігання номера телефону. Має валідацію формату."""
    @Field.value.setter
    def value(self, value):
        # Проста валідація: 10 цифр. Можна зробити гнучкішою.
        # Наприклад, для дозволу + та інших символів: r"^\+?\d[\d\s-()]{8,}\d$"
        if not isinstance(value, str) or not re.fullmatch(r"\d{10}", value):
            raise ValueError("Неправильний формат номеру телефону. Очікується 10 цифр.")
        self._value = value

class Email(Field):
    """Клас для зберігання email. Має валідацію формату."""
    @Field.value.setter
    def value(self, value):
         # Проста валідація формату email
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", value)):
            raise ValueError("Неправильний формат email.")
        self._value = value # Дозволяємо None

class Birthday(Field):
    """Клас для зберігання дня народження. Має валідацію формату."""
    @Field.value.setter
    def value(self, value):
        if value is None:
            self._value = None
            return
        try:
            # Очікуваний формат DD.MM.YYYY
            datetime.strptime(value, "%d.%m.%Y")
            self._value = value
        except (ValueError, TypeError):
            raise ValueError("Неправильний формат дня народження. Очікується DD.MM.YYYY.")

class Address(Field):
    """Клас для зберігання адреси."""
    # Можна додати специфічну валідацію для адреси
    pass


class Record:
    """Клас для зберігання інформації про контакт, включаючи ім'я та список телефонів."""
    def __init__(self, name, address=None, email=None, birthday=None):
        self.name = Name(name) # Ім'я обов'язкове
        self.phones = []
        # Використовуємо сеттери для валідації при ініціалізації
        self.address = None
        if address:
            self.set_address(address)
        self.email = None
        if email:
            self.set_email(email)
        self.birthday = None
        if birthday:
            self.set_birthday(birthday)

    def add_phone(self, phone_number):
        """Додає телефон до запису."""
        phone = Phone(phone_number) # Валідація відбувається при створенні Phone
        # Перевірка на дублікати перед додаванням
        if phone.value not in [p.value for p in self.phones]:
            self.phones.append(phone)
        else:
            print(f"Телефон {phone.value} вже існує для цього контакту.") # Або raise ValueError

    def remove_phone(self, phone_number):
        """Видаляє телефон із запису."""
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError(f"Телефон {phone_number} не знайдено.")

    def edit_phone(self, old_phone_number, new_phone_number):
        """Редагує існуючий телефон."""
        phone_to_edit = self.find_phone(old_phone_number)
        if not phone_to_edit:
            raise ValueError(f"Телефон {old_phone_number} не знайдено для редагування.")

        # Перевіряємо, чи новий номер вже існує (окрім старого)
        if new_phone_number != old_phone_number and new_phone_number in [p.value for p in self.phones]:
             raise ValueError(f"Телефон {new_phone_number} вже існує для цього контакту.")

        # Валідація нового номера відбувається при створенні Phone
        new_phone_obj = Phone(new_phone_number)
        index = self.phones.index(phone_to_edit)
        self.phones[index] = new_phone_obj


    def find_phone(self, phone_number):
        """Знаходить телефон у записі."""
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def set_address(self, address):
        """Встановлює або оновлює адресу."""
        self.address = Address(address)

    def set_email(self, email):
        """Встановлює або оновлює email."""
        # Створюємо об'єкт Email, щоб валідація відбулася в сеттері класу Email
        self.email = Email(email)

    def set_birthday(self, birthday):
        """Встановлює або оновлює день народження."""
         # Створюємо об'єкт Birthday для валідації
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        """Повертає кількість днів до наступного дня народження."""
        if not self.birthday or not self.birthday.value:
            return None

        today = datetime.today().date()
        try:
            bday = datetime.strptime(self.birthday.value, "%d.%m.%Y").date()
        except ValueError:
            return None # Помилка формату дати

        bday_this_year = bday.replace(year=today.year)

        if bday_this_year < today:
            # День народження вже був цього року, розглядаємо наступний рік
            bday_next_year = bday.replace(year=today.year + 1)
            delta = bday_next_year - today
        else:
            # День народження ще буде цього року
            delta = bday_this_year - today

        return delta.days

    def __str__(self):
        """Повертає рядкове представлення запису."""
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "Немає"
        address_str = str(self.address) if self.address else "Немає"
        email_str = str(self.email) if self.email else "Немає"
        birthday_str = str(self.birthday) if self.birthday else "Немає"
        days_left = self.days_to_birthday()
        birthday_info = f", День народження: {birthday_str}"
        if self.birthday and self.birthday.value: # Показуємо дні тільки якщо дата є
            if days_left is not None:
                birthday_info += f" (залишилось днів: {days_left})"
            else:
                # Це може статися, якщо дата некоректна, хоча валідатор мав би це зловити
                 birthday_info += " (некоректна дата)"
        else:
            birthday_info = "" # Не показуємо нічого про ДН, якщо його немає

        return (f"Ім'я: {self.name.value}, "
                f"Телефони: {phones_str}, "
                f"Адреса: {address_str}, "
                f"Email: {email_str}"
                f"{birthday_info}")

class AddressBook(UserDict):
    """Клас для зберігання та управління записами контактів."""
    def add_record(self, record: Record):
        """Додає запис до адресної книги."""
        if not isinstance(record, Record):
             raise TypeError("Можна додавати лише об'єкти типу Record")
        if record.name.value in self.data:
            raise ValueError(f"Контакт з ім'ям {record.name.value} вже існує.")
        self.data[record.name.value] = record

    def find(self, name):
        """Знаходить запис за ім'ям."""
        return self.data.get(name)

    def delete(self, name):
        """Видаляє запис за ім'ям."""
        if name in self.data:
            del self.data[name]
        else:
            # Повертаємо KeyError, щоб його обробив декоратор input_error
            raise KeyError(name)

    def find_by_criteria(self, query):
        """Шукає контакти за будь-яким полем (ім'я, телефон, email, адреса)."""
        results = []
        if not query: # Повертаємо порожній список, якщо запит порожній
            return results
        query_lower = query.lower()
        for record in self.data.values():
            # Перевірка імені
            if query_lower in record.name.value.lower():
                results.append(record)
                continue # Переходимо до наступного запису, якщо знайшли за іменем

            # Перевірка телефонів
            if any(query_lower in phone.value for phone in record.phones):
                 results.append(record)
                 continue

            # Перевірка email (з урахуванням, що email може бути None)
            if record.email and record.email.value and query_lower in record.email.value.lower():
                results.append(record)
                continue

            # Перевірка адреси (з урахуванням, що address може бути None)
            if record.address and record.address.value and query_lower in record.address.value.lower():
                results.append(record)
                continue
        return results


    def get_upcoming_birthdays(self, days):
        """Повертає список контактів, у яких день народження через задану кількість днів."""
        upcoming = []
        if not isinstance(days, int) or days < 0:
            raise ValueError("Кількість днів має бути невід'ємним цілим числом.")

        for record in self.data.values():
            days_left = record.days_to_birthday()
            # Перевіряємо, що days_left не None і знаходиться в потрібному діапазоні
            if days_left is not None and 0 <= days_left <= days:
                upcoming.append(record)
        # Сортуємо за кількістю днів до дня народження
        upcoming.sort(key=lambda x: x.days_to_birthday())
        return upcoming

# --- Класи для Нотаток ---

class Note:
    """Клас для представлення нотатки."""
    def __init__(self, text, tags=None):
        if not text or not isinstance(text, str): # Перевірка типу і на порожній рядок
            raise ValueError("Текст нотатки не може бути порожнім рядком.")
        self.text = text
        # Теги зберігаються як множина рядків для уникнення дублікатів і приведення до нижнього регістру
        self.tags = set(tag.strip().lower() for tag in tags if isinstance(tag, str) and tag.strip()) if tags else set()
        self.created_at = datetime.now() # Дата створення

    def add_tag(self, tag):
        """Додає тег до нотатки."""
        if isinstance(tag, str):
            tag_clean = tag.strip().lower()
            if tag_clean: # Не додаємо порожні теги
                self.tags.add(tag_clean)
        else:
            print("Помилка: Тег має бути рядком.") # Або raise TypeError

    def remove_tag(self, tag):
        """Видаляє тег з нотатки."""
        if isinstance(tag, str):
            tag_clean = tag.strip().lower()
            self.tags.discard(tag_clean) # discard не викликає помилку, якщо тег не знайдено
        else:
             print("Помилка: Тег має бути рядком.") # Або raise TypeError

    def edit_text(self, new_text):
         """Редагує текст нотатки."""
         if not new_text or not isinstance(new_text, str):
             raise ValueError("Текст нотатки не може бути порожнім рядком.")
         self.text = new_text

    def __str__(self):
        """Повертає рядкове представлення нотатки."""
        tags_str = ', '.join(sorted(list(self.tags))) if self.tags else "Немає тегів"
        created_str = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        # Додаємо індексацію (хоча індекс визначається в NotesManager)
        # Можна додати ID, якщо потрібно унікально ідентифікувати нотатку незалежно від списку
        return f"Створено: {created_str}\nТеги: [{tags_str}]\nТекст: {self.text}\n" + "-"*20

class NotesManager:
    """Клас для управління нотатками."""
    def __init__(self):
        self.notes = [] # Нотатки зберігаються у списку

    def add_note(self, note: Note):
        """Додає нотатку."""
        if not isinstance(note, Note):
            raise TypeError("Можна додавати лише об'єкти типу Note")
        self.notes.append(note)

    def find_notes(self, query):
        """Шукає нотатки за текстом або тегом."""
        results = []
        if not query or not isinstance(query, str):
            return results # Повертаємо порожній список для порожнього або некоректного запиту
        query_lower = query.lower()
        for i, note in enumerate(self.notes):
            found = False
            # Пошук у тексті
            if query_lower in note.text.lower():
                results.append((i, note)) # Зберігаємо індекс для редагування/видалення
                found = True

            # Пошук у тегах (якщо ще не знайдено за текстом)
            if not found and any(query_lower == tag for tag in note.tags): # Шукаємо точне співпадіння тегу
                 results.append((i, note))

        return results

    def edit_note_text(self, index, new_text):
        """Редагує текст нотатки за індексом."""
        if 0 <= index < len(self.notes):
            # Валідація нового тексту відбувається в методі edit_text класу Note
            self.notes[index].edit_text(new_text)
        else:
            raise IndexError("Неправильний індекс нотатки.")

    def add_note_tag(self, index, tag):
        """Додає тег до нотатки за індексом."""
        if 0 <= index < len(self.notes):
             # Валідація тегу відбувається в методі add_tag класу Note
            self.notes[index].add_tag(tag)
        else:
            raise IndexError("Неправильний індекс нотатки.")

    def remove_note_tag(self, index, tag):
        """Видаляє тег з нотатки за індексом."""
        if 0 <= index < len(self.notes):
            # Валідація тегу відбувається в методі remove_tag класу Note
            self.notes[index].remove_tag(tag)
        else:
            raise IndexError("Неправильний індекс нотатки.")

    def delete_note(self, index):
        """Видаляє нотатку за індексом."""
        if 0 <= index < len(self.notes):
            del self.notes[index]
        else:
            raise IndexError("Неправильний індекс нотатки.") # Залишаємо для обробки декоратором

    def sort_notes_by_tag(self, tag):
        """
        Повертає новий список нотаток, відсортований за наявністю вказаного тегу.
        Нотатки з цим тегом йдуть першими.
        """
        if not tag or not isinstance(tag, str):
            print("Помилка: Тег для сортування має бути непорожнім рядком.")
            return self.notes # Повертаємо оригінальний список у разі помилки

        tag_lower = tag.strip().lower()
        # Розділяємо нотатки на дві групи: ті, що містять тег, і ті, що ні
        notes_with_tag = [note for note in self.notes if tag_lower in note.tags]
        notes_without_tag = [note for note in self.notes if tag_lower not in note.tags]
        # Можна додати сортування всередині кожної групи, наприклад, за датою створення
        # notes_with_tag.sort(key=lambda n: n.created_at, reverse=True)
        # notes_without_tag.sort(key=lambda n: n.created_at, reverse=True)
        return notes_with_tag + notes_without_tag # Повертаємо новий об'єднаний список

    def get_all_notes(self):
         """Повертає копію списку всіх нотаток."""
         # Повертаємо копію, щоб зовнішній код не міг випадково змінити внутрішній список
         return list(self.notes)

# --- Збереження та Завантаження Даних ---

DATA_DIR = "personal_assistant_data" # Назва папки для даних
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.pkl")
NOTES_FILE = os.path.join(DATA_DIR, "notes.pkl")

def ensure_data_dir_exists():
    """Перевіряє існування папки для даних та створює її, якщо потрібно."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            print(f"Створено папку для даних: {DATA_DIR}")
        except OSError as e:
            print(f"Помилка створення папки {DATA_DIR}: {e}")
            # Можливо, варто завершити програму або працювати без збереження
            raise # Перевикидаємо помилку, щоб її було видно

def save_data(book: AddressBook, notes: NotesManager):
    """Зберігає адресну книгу та нотатки у файли."""
    try:
        ensure_data_dir_exists() # Переконуємось, що папка існує
    except OSError:
         print("Не вдалося створити папку для даних. Збереження неможливе.")
         return # Виходимо, якщо папку створити не вдалося

    try:
        # Зберігаємо словник даних з AddressBook
        with open(CONTACTS_FILE, "wb") as f:
            pickle.dump(book.data, f)
    except (IOError, pickle.PicklingError) as e:
        print(f"Помилка збереження контактів: {e}")

    try:
        # Зберігаємо список нотаток з NotesManager
        with open(NOTES_FILE, "wb") as f:
            pickle.dump(notes.notes, f)
    except (IOError, pickle.PicklingError) as e:
        print(f"Помилка збереження нотаток: {e}")


def load_data():
    """Завантажує адресну книгу та нотатки з файлів."""
    book = AddressBook()
    notes_manager = NotesManager()

    # Перевіряємо існування папки перед спробою читання файлів
    if not os.path.exists(DATA_DIR):
        print(f"Папка для даних ({DATA_DIR}) не знайдена. Створюється нова книга та нотатки.")
        return book, notes_manager

    # Завантаження контактів
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "rb") as f:
                # Завантажуємо словник і присвоюємо його атрибуту data
                book.data = pickle.load(f)
                # Додаткова перевірка типу завантажених даних
                if not isinstance(book.data, dict):
                    print(f"Помилка: Файл {CONTACTS_FILE} містить некоректні дані (не словник). Створюється нова адресна книга.")
                    book.data = {}
                else:
                     # Перевірка, чи значення є об'єктами Record (опціонально, може бути повільно)
                     for key, value in book.data.items():
                         if not isinstance(value, Record):
                              print(f"Попередження: Некоректний тип запису для ключа '{key}' у {CONTACTS_FILE}. Можливі проблеми.")
                              # Можна видалити некоректний запис: del book.data[key]
        except (IOError, pickle.UnpicklingError, EOFError, AttributeError, TypeError) as e:
            print(f"Помилка завантаження контактів з {CONTACTS_FILE}: {e}. Створюється нова адресна книга.")
            book = AddressBook() # Створюємо порожню книгу у разі помилки
        except Exception as e: # Ловимо інші можливі винятки
             print(f"Неочікувана помилка завантаження контактів: {e}. Створюється нова адресна книга.")
             book = AddressBook()

    # Завантаження нотаток
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "rb") as f:
                 # Завантажуємо список і присвоюємо його атрибуту notes
                notes_manager.notes = pickle.load(f)
                 # Додаткова перевірка типу завантажених даних
                if not isinstance(notes_manager.notes, list):
                     print(f"Помилка: Файл {NOTES_FILE} містить некоректні дані (не список). Створюється новий менеджер нотаток.")
                     notes_manager.notes = []
                else:
                     # Перевірка, чи елементи є об'єктами Note (опціонально)
                     for i, item in enumerate(notes_manager.notes):
                          if not isinstance(item, Note):
                              print(f"Попередження: Некоректний тип запису на позиції {i} у {NOTES_FILE}. Можливі проблеми.")
                              # Можна видалити некоректний запис: notes_manager.notes.pop(i)
        except (IOError, pickle.UnpicklingError, EOFError, AttributeError, TypeError) as e:
            print(f"Помилка завантаження нотаток з {NOTES_FILE}: {e}. Створюється новий менеджер нотаток.")
            notes_manager = NotesManager() # Створюємо порожній менеджер у разі помилки
        except Exception as e:
             print(f"Неочікувана помилка завантаження нотаток: {e}. Створюється новий менеджер нотаток.")
             notes_manager = NotesManager()

    return book, notes_manager

# --- Обробники Команд ---

def input_error(func):
    """Декоратор для обробки помилок введення та інших винятків під час виконання команди."""
    def inner(*args, **kwargs):
        try:
            # Перший аргумент args - це кортеж аргументів команди (args,),
            # другий - book або notes_manager
            return func(*args, **kwargs)
        except ValueError as e:
            # Помилки валідації даних (неправильний формат тощо)
            return f"Помилка даних: {e}"
        except KeyError as e:
             # Спроба доступу до неіснуючого контакту за ім'ям
            return f"Помилка: Контакт з ім'ям '{e}' не знайдено."
        except IndexError:
             # Неправильний індекс для нотатки
            return "Помилка: Неправильний індекс. Перевірте індекси у списку нотаток."
        except TypeError as e:
            # Неправильний тип аргументів для функції
            return f"Помилка типу аргументів: {e}"
        except AttributeError as e:
             # Спроба доступу до неіснуючого атрибута (може статися при помилках завантаження даних)
             return f"Помилка атрибуту: {e}. Можливо, дані пошкоджено."
        except Exception as e:
             # Інші, непередбачені помилки
            return f"Сталася непередбачена помилка: {e}"
    return inner

# --- Функції-обробники для Контактів ---

@input_error
def add_contact(args, book: AddressBook):
    """Додає новий контакт з інтерактивним введенням полів."""
    if not args:
        return "Введіть ім'я контакту після команди 'add_contact'."
    name = args[0]
    # Забороняємо додавання, якщо контакт вже існує (перевірка в add_record)
    # record = Record(name) # Валідація імені в класі Name

    # --- Інтерактивне введення інших полів ---
    phones_list = []
    while True:
        phone_input = input(f"Введіть номер телефону для {name} (10 цифр, Enter щоб завершити додавання телефонів): ").strip()
        if not phone_input:
            break
        try:
            # Створюємо об'єкт Phone для валідації
            phone_obj = Phone(phone_input)
            phones_list.append(phone_obj)
            print(f"Телефон {phone_obj.value} додано до списку.")
        except ValueError as e:
            print(f"Помилка: {e}. Спробуйте ще раз.")

    email = None
    while True:
        email_input = input(f"Введіть email для {name} (опціонально, Enter щоб пропустити): ").strip()
        if not email_input:
            break
        try:
            # Створюємо об'єкт Email для валідації
            email_obj = Email(email_input)
            email = email_obj # Зберігаємо валідний об'єкт
            break # Один email на контакт
        except ValueError as e:
            print(f"Помилка: {e}. Спробуйте ще раз.")

    birthday = None
    while True:
        birthday_input = input(f"Введіть день народження для {name} (ДД.ММ.РРРР, опціонально, Enter щоб пропустити): ").strip()
        if not birthday_input:
            break
        try:
             # Створюємо об'єкт Birthday для валідації
            birthday_obj = Birthday(birthday_input)
            birthday = birthday_obj # Зберігаємо валідний об'єкт
            break # Одна дата народження
        except ValueError as e:
            print(f"Помилка: {e}. Спробуйте ще раз.")

    address = None
    address_input = input(f"Введіть адресу для {name} (опціонально, Enter щоб пропустити): ").strip()
    if address_input:
        try:
            # Створюємо об'єкт Address (без суворої валідації за замовчуванням)
            address = Address(address_input)
        except ValueError as e: # Якщо в Address додати валідацію
             print(f"Помилка адреси: {e}") # Малоймовірно без валідації в Address

    # Створюємо запис з усіма зібраними даними
    # Передаємо рядкові значення, валідація відбудеться в __init__ та сеттерах Record
    record = Record(name,
                    address=address.value if address else None,
                    email=email.value if email else None,
                    birthday=birthday.value if birthday else None)
    # Додаємо телефони окремо
    for phone_obj in phones_list:
        record.phones.append(phone_obj) # Вже валідовані об'єкти Phone

    # Додаємо готовий запис до книги (перевірка на існування імені всередині)
    book.add_record(record)
    return f"Контакт {name} успішно додано."


@input_error
def edit_contact(args, book: AddressBook):
    """Редагує існуючий контакт (інтерактивно)."""
    if not args:
        return "Введіть ім'я контакту для редагування після команди 'edit_contact'."
    name = args[0]
    record = book.find(name)
    if not record:
        # Повертаємо помилку через raise, щоб її обробив декоратор
        raise KeyError(name)

    print(f"--- Редагування контакту: {name} ---")
    print(f"Поточні дані:\n{record}")
    print("\nЩо ви хочете змінити?")
    print("1 - Ім'я")
    print("2 - Додати телефон")
    print("3 - Редагувати телефон")
    print("4 - Видалити телефон")
    print("5 - Email")
    print("6 - День народження")
    print("7 - Адресу")
    print("0 - Скасувати")

    choice = input("Ваш вибір: ").strip()

    if choice == '1':
        new_name = input("Введіть нове ім'я: ").strip()
        if not new_name:
            return "Помилка: Нове ім'я не може бути порожнім."
        if new_name == name:
            return "Нове ім'я співпадає з поточним. Змін не внесено."
        if new_name in book:
            return f"Помилка: Контакт з ім'ям '{new_name}' вже існує."
        # Оновлюємо ім'я в записі та в словнику книги
        old_record = book.data.pop(name) # Видаляємо старий запис
        old_record.name = Name(new_name) # Оновлюємо ім'я в об'єкті Record (валідація в Name)
        book.data[new_name] = old_record # Додаємо запис з новим ключем
        return f"Ім'я контакту змінено з '{name}' на '{new_name}'."

    elif choice == '2':
        new_phone = input("Введіть номер телефону для додавання (10 цифр): ").strip()
        record.add_phone(new_phone) # Валідація та перевірка на дублікат всередині
        return f"Телефон {new_phone} додано до контакту {name}."

    elif choice == '3':
        if not record.phones:
            return "У контакта немає телефонів для редагування."
        print("Поточні телефони:", '; '.join(p.value for p in record.phones))
        old_phone = input("Введіть номер телефону, який хочете змінити: ").strip()
        new_phone = input("Введіть новий номер телефону (10 цифр): ").strip()
        record.edit_phone(old_phone, new_phone) # Валідація та обробка помилок всередині
        return f"Телефон для {name} змінено з {old_phone} на {new_phone}."

    elif choice == '4':
        if not record.phones:
            return "У контакта немає телефонів для видалення."
        print("Поточні телефони:", '; '.join(p.value for p in record.phones))
        phone_to_delete = input("Введіть номер телефону для видалення: ").strip()
        record.remove_phone(phone_to_delete) # Обробка помилки ValueError всередині
        return f"Телефон {phone_to_delete} видалено з контакту {name}."

    elif choice == '5':
        new_email = input(f"Введіть новий email (поточний: {record.email.value if record.email else 'Немає'}, Enter щоб видалити): ").strip()
        if not new_email:
             record.email = None # Видаляємо email
             return f"Email для {name} видалено."
        else:
            record.set_email(new_email) # Валідація в сеттері
            return f"Email для {name} оновлено на {new_email}."

    elif choice == '6':
        new_birthday = input(f"Введіть новий день народження (ДД.ММ.РРРР) (поточний: {record.birthday.value if record.birthday else 'Немає'}, Enter щоб видалити): ").strip()
        if not new_birthday:
            record.birthday = None # Видаляємо дату
            return f"День народження для {name} видалено."
        else:
            record.set_birthday(new_birthday) # Валідація в сеттері
            return f"День народження для {name} оновлено на {new_birthday}."

    elif choice == '7':
        new_address = input(f"Введіть нову адресу (поточна: {record.address.value if record.address else 'Немає'}, Enter щоб видалити): ").strip()
        if not new_address:
             record.address = None # Видаляємо адресу
             return f"Адресу для {name} видалено."
        else:
            record.set_address(new_address) # Валідація (якщо є) в сеттері
            return f"Адресу для {name} оновлено."
    elif choice == '0':
        return "Редагування скасовано."
    else:
        return "Невірний вибір."


@input_error
def delete_contact(args, book: AddressBook):
    """Видаляє контакт за ім'ям."""
    if not args:
        return "Введіть ім'я контакту для видалення після команди 'delete_contact'."
    name = args[0]
    book.delete(name) # Викличе KeyError, якщо контакту немає, обробиться декоратором
    return f"Контакт {name} успішно видалено."

@input_error
def find_contact(args, book: AddressBook):
    """Знаходить контакти за запитом (частина імені, телефону, email, адреси)."""
    if not args:
        return "Введіть запит для пошуку після команди 'find_contact'."
    query = " ".join(args)
    results = book.find_by_criteria(query)
    if not results:
        return f"Контакти за запитом '{query}' не знайдено."
    # Виводимо знайдені контакти
    output = f"Знайдено контактів ({len(results)}):\n" + "="*20 + "\n"
    output += "\n".join(str(record) for record in results)
    return output

@input_error
def show_all_contacts(args, book: AddressBook):
    """Показує всі контакти в адресній книзі."""
    if not book.data:
        return "Адресна книга порожня."
    output = "--- Всі контакти ---\n" + "="*20 + "\n"
    # Сортуємо контакти за іменем для зручності
    sorted_records = sorted(book.data.values(), key=lambda r: r.name.value)
    output += "\n".join(str(record) for record in sorted_records)
    return output

@input_error
def show_upcoming_birthdays(args, book: AddressBook):
    """Показує дні народження в найближчі N днів."""
    if not args:
        return "Введіть кількість днів після команди 'birthdays'."
    try:
        days = int(args[0])
    except ValueError:
        return "Кількість днів має бути цілим числом."
    if days < 0:
         return "Кількість днів не може бути від'ємною."

    upcoming = book.get_upcoming_birthdays(days)
    if not upcoming:
        return f"Немає днів народження в найближчі {days} днів."

    output = f"--- Дні народження в найближчі {days} днів ---\n" + "="*40 + "\n"
    # `get_upcoming_birthdays` вже сортує за датою
    output += "\n".join(f"{record.name.value}: {record.birthday.value} (залишилось днів: {record.days_to_birthday()})"
                        for record in upcoming)
    return output

# --- Функції-обробники для Нотаток ---

@input_error
def add_note(args, notes: NotesManager):
    """Додає нову нотатку з інтерактивним введенням."""
    # Аргументи args тут не використовуються, оскільки все вводиться інтерактивно
    text = input("Введіть текст нотатки: ").strip()
    # Валідація тексту відбувається в класі Note
    tags_input = input("Введіть теги через кому (опціонально): ").strip()
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else None

    # Створюємо нотатку (валідація тексту і тегів всередині)
    note = Note(text, tags)
    notes.add_note(note)
    return "Нотатку успішно додано."

@input_error
def find_notes(args, notes: NotesManager):
    """Шукає нотатки за текстом або тегом."""
    if not args:
        return "Введіть запит для пошуку нотаток після команди 'find_notes'."
    query = " ".join(args)
    results = notes.find_notes(query) # Повертає список кортежів (індекс, нотатка)
    if not results:
        return f"Нотатки за запитом '{query}' не знайдено."

    output = f"Знайдено нотаток ({len(results)}):\n" + "="*20 + "\n"
    # Виводимо результати з їхніми поточними індексами
    output += "\n".join(f"--- Індекс: {idx} ---\n{note}" for idx, note in results)
    return output

@input_error
def edit_note(args, notes: NotesManager):
    """Редагує текст або теги нотатки за індексом (інтерактивно)."""
    if not args:
        return "Введіть індекс нотатки для редагування після команди 'edit_note'."
    try:
        index = int(args[0])
        # Перевіряємо індекс одразу
        if not (0 <= index < len(notes.notes)):
             raise IndexError # Обробляється декоратором
    except ValueError:
        return "Індекс має бути цілим числом."

    note_to_edit = notes.notes[index]
    print(f"--- Редагування нотатки (Індекс: {index}) ---")
    print(f"Поточний стан:\n{note_to_edit}")
    print("Що ви хочете змінити?")
    print("1 - Текст")
    print("2 - Додати тег")
    print("3 - Видалити тег")
    print("0 - Скасувати")

    action = input("Ваш вибір: ").strip()

    if action == "1":
        new_text = input("Введіть новий текст нотатки: ").strip()
        notes.edit_note_text(index, new_text) # Валідація всередині
        return f"Текст нотатки {index} оновлено."
    elif action == "2":
        tag_to_add = input("Введіть тег для додавання: ").strip()
        notes.add_note_tag(index, tag_to_add) # Валідація всередині
        return f"Тег '{tag_to_add}' додано до нотатки {index}."
    elif action == "3":
        if not note_to_edit.tags:
            return "У нотатки немає тегів для видалення."
        print("Поточні теги:", ', '.join(sorted(list(note_to_edit.tags))))
        tag_to_remove = input("Введіть тег для видалення: ").strip()
        notes.remove_note_tag(index, tag_to_remove) # Обробка помилок всередині
        return f"Тег '{tag_to_remove}' видалено з нотатки {index} (якщо він існував)."
    elif action == '0':
        return "Редагування скасовано."
    else:
        return "Невірний вибір."


@input_error
def delete_note(args, notes: NotesManager):
    """Видаляє нотатку за індексом."""
    if not args:
        return "Введіть індекс нотатки для видалення після команди 'delete_note'."
    try:
        index = int(args[0])
        # Перевірка індексу перед викликом методу, щоб надати краще повідомлення
        if not (0 <= index < len(notes.notes)):
            # Повертаємо помилку через raise, щоб її обробив декоратор
             raise IndexError
    except ValueError:
        return "Індекс має бути цілим числом."

    # Видалення відбувається в методі NotesManager, який також може викликати IndexError
    notes.delete_note(index)
    return f"Нотатку з індексом {index} успішно видалено."

@input_error
def show_all_notes(args, notes: NotesManager):
    """Показує всі нотатки з індексами."""
    all_notes = notes.get_all_notes() # Отримуємо копію списку
    if not all_notes:
        return "Немає збережених нотаток."

    output = "--- Всі нотатки ---\n" + "="*20 + "\n"
    # Виводимо нотатки з їхніми поточними індексами
    output += "\n".join(f"--- Індекс: {i} ---\n{note}" for i, note in enumerate(all_notes))
    return output

@input_error
def sort_notes_by_tag(args, notes: NotesManager):
    """Сортує нотатки за тегом і показує результат."""
    if not args:
        return "Введіть тег для сортування після команди 'sort_notes'."
    tag = args[0]
    # Метод sort_notes_by_tag повертає новий відсортований список
    sorted_notes = notes.sort_notes_by_tag(tag)

    if not sorted_notes: # Може статися, якщо notes.notes порожній
        return "Немає нотаток для сортування."
    if sorted_notes == notes.notes and tag not in {t for n in notes.notes for t in n.tags}:
         # Якщо список не змінився і тегу немає, повідомляємо про це
         return f"Нотаток з тегом '{tag}' не знайдено. Порядок не змінено."

    output = f"--- Нотатки, відсортовані за тегом '{tag}' (з тегом перші) ---\n" + "="*50 + "\n"
    # Важливо: індекси тут будуть відповідати новому відсортованому списку,
    # а не оригінальним індексам в notes.notes. Це може бути незручно для редагування/видалення.
    # Краще виводити без індексів або з ID, якщо він є.
    # Для ясності, виведемо без індексів.
    output += "\n".join(str(note) for note in sorted_notes)
    return output


# --- Головна Логіка та Парсер Команд ---

def parse_input(user_input):
    """Розбирає введений рядок на команду та аргументи."""
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args

def find_closest_command(user_command, available_commands):
    """Знаходить найближчу команду (додатковий функціонал)."""
    if not user_command or not available_commands:
        return None
    # Використовуємо difflib для пошуку схожих команд
    matches = difflib.get_close_matches(user_command, available_commands, n=1, cutoff=0.6) # cutoff - поріг схожості
    return matches[0] if matches else None

def show_help(available_commands):
    """Показує список доступних команд та їх опис."""
    help_text = "Доступні команди:\n" + "="*20 + "\n"
    # Описи команд
    commands_description = {
        "add_contact": "add_contact <ім'я> - Додати новий контакт (інші поля запитаються інтерактивно)",
        "edit_contact": "edit_contact <ім'я> - Редагувати існуючий контакт (інтерактивно)",
        "delete_contact": "delete_contact <ім'я> - Видалити контакт за ім'ям",
        "find_contact": "find_contact <запит> - Знайти контакти за іменем, телефоном, email або адресою",
        "show_contacts": "show_contacts - Показати всі контакти (відсортовані за іменем)",
        "birthdays": "birthdays <кількість_днів> - Показати дні народження в найближчі N днів",
        "add_note": "add_note - Додати нову нотатку (текст і теги запитаються інтерактивно)",
        "find_notes": "find_notes <запит> - Знайти нотатки за текстом або тегом (показує індекси)",
        "edit_note": "edit_note <індекс> - Редагувати нотатку за її індексом (інтерактивно)",
        "delete_note": "delete_note <індекс> - Видалити нотатку за її індексом",
        "show_notes": "show_notes - Показати всі нотатки з їхніми поточними індексами",
        "sort_notes": "sort_notes <тег> - Показати нотатки, відсортовані за тегом (з тегом перші, без індексів)",
        "hello": "hello - Отримати привітання від бота",
        "help": "help - Показати цю довідку",
        "exit": "exit або close - Вийти з програми та зберегти дані",
        "close": "exit або close - Вийти з програми та зберегти дані",
    }

    # Виводимо команди в алфавітному порядку
    for cmd in sorted(available_commands):
         if cmd in commands_description:
             help_text += f"  - {commands_description[cmd]}\n"
         else:
             # Якщо команда є, але опису немає (малоймовірно)
             help_text += f"  - {cmd}\n"

    return help_text

def main():
    """Головна функція програми."""
    # Завантажуємо дані або створюємо нові об'єкти
    book, notes_manager = load_data()
    print("Ласкаво просимо до Персонального Помічника!")
    print("Введіть 'help' для списку доступних команд.")

    # Словник доступних команд та відповідних функцій-обробників
    # Використовуємо lambda, щоб передати book або notes_manager у відповідні функції
    commands = {
        # Контакти
        "add_contact": lambda args: add_contact(args, book),
        "edit_contact": lambda args: edit_contact(args, book),
        "delete_contact": lambda args: delete_contact(args, book),
        "find_contact": lambda args: find_contact(args, book),
        "show_contacts": lambda args: show_all_contacts(args, book),
        "birthdays": lambda args: show_upcoming_birthdays(args, book),
        # Нотатки
        "add_note": lambda args: add_note(args, notes_manager),
        "find_notes": lambda args: find_notes(args, notes_manager),
        "edit_note": lambda args: edit_note(args, notes_manager),
        "delete_note": lambda args: delete_note(args, notes_manager),
        "show_notes": lambda args: show_all_notes(args, notes_manager),
        "sort_notes": lambda args: sort_notes_by_tag(args, notes_manager),
        # Допомога та вихід
        "hello": lambda args: "Привіт! Чим я можу допомогти?",
        "help": lambda args: show_help(commands.keys()), # Передаємо ключі команд для показу в довідці
        "exit": lambda args: "exit", # Спеціальне значення для виходу з циклу
        "close": lambda args: "exit",
    }

    # Головний цикл обробки команд
    while True:
        try:
            user_input = input("Введіть команду > ").strip()
            if not user_input: # Пропускаємо порожнє введення
                continue

            command, args = parse_input(user_input)

            # Обробка команд виходу
            if command in ["exit", "close"]:
                print("До побачення! Зберігаю дані...")
                save_data(book, notes_manager) # Зберігаємо дані перед виходом
                break

            # Пошук та виконання команди
            if command in commands:
                result = commands[command](args) # Викликаємо відповідну lambda функцію
                print(result) # Друкуємо результат виконання команди
            else:
                # Спроба вгадати команду, якщо введено щось невідоме
                closest_command = find_closest_command(command, list(commands.keys()))
                if closest_command:
                    # Запитуємо користувача, чи він мав на увазі знайдену команду
                    suggestion = input(f"Невідома команда '{command}'. Можливо, ви мали на увазі '{closest_command}'? (y/n): ").lower()
                    if suggestion == 'y':
                        # Виконуємо запропоновану команду з тими ж аргументами
                        if closest_command in ["exit", "close"]: # Обробка виходу тут теж
                             print("До побачення! Зберігаю дані...")
                             save_data(book, notes_manager)
                             break
                        result = commands[closest_command](args)
                        print(result)
                    else:
                        print("Команду не виконано. Введіть 'help' для списку команд.")
                else:
                    # Якщо схожих команд не знайдено
                    print("Невідома команда. Введіть 'help' для списку команд.")

        except (KeyboardInterrupt): # Обробка Ctrl+C
             print("\nОтримано сигнал переривання. Зберігаю дані та виходжу...")
             save_data(book, notes_manager)
             break
        except Exception as e: # Загальний обробник непередбачених помилок на верхньому рівні
             print(f"\nСталася критична помилка: {e}")
             print("Спробую зберегти дані...")
             save_data(book, notes_manager)
             # Можна додати запис у лог або інші дії
             break # Завершуємо роботу після критичної помилки


if __name__ == "__main__":
    # Запускаємо головну функцію, якщо скрипт виконується безпосередньо
    main()
