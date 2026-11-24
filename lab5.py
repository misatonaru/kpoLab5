import json
import random
from dataclasses import dataclass
from pathlib import Path

VERSION = "5.0"
STUDENT_NAME = "Student 5"

MENU_START = 1
MENU_LOAD = 2
MENU_SETTINGS = 3
MENU_ABOUT = 4
MENU_HORSE_BUILDER = 5
MENU_RATING = 6
MENU_EXIT = 7

SETTINGS_DIFFICULTY = 1
SETTINGS_DURATION = 2
SETTINGS_RESET = 3
SETTINGS_BACK = 4

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"
DEFAULTS_FILE = BASE_DIR / "default_settings.json"
DIFFICULTIES_FILE = BASE_DIR / "difficulties.txt"
MANUAL_SAVE_FILE = BASE_DIR / "save.json"
AUTO_SAVE_FILE = BASE_DIR / "autosave.json"
HORSES_FILE = BASE_DIR / "horse_templates.json"
PROFILE_FILE = BASE_DIR / "player_profile.json"

DEFAULT_SETTINGS = {"difficulty": "Средний", "duration": 5}
settings = {}
available_difficulties = set()

PASSIVE_BONUSES = {
    "Резвый": ("speed", 2),
    "Выносливый": ("stamina", 2),
    "Послушный": ("obedience", 2),
}


@dataclass
class Jockey:
    name: str = "Наездник"
    strength: int = 5
    technique: int = 5
    energy: int = 10

    def train(self, characteristic):
        if self.energy < 2:
            print("У наездника мало сил. нужно отдохнуть.")
            return

        if characteristic == "strength":
            self.strength = min(20, self.strength + 1)
            print("Сила наездника увеличена на 1.")
        elif characteristic == "technique":
            self.technique = min(20, self.technique + 1)
            print("Техника наездника увеличена на 1.")
        else:
            return

        self.energy -= 2


@dataclass
class Horse:
    name: str = "Искра"
    speed: int = 7
    stamina: int = 6
    obedience: int = 6
    energy: int = 10
    passive: str = "Резвый"

    def train(self, characteristic):
        if self.energy < 2:
            print("Лошадь устала. Сначала нужно дать ей отдохнуть.")
            return

        if characteristic not in {"speed", "stamina", "obedience"}:
            return

        current_value = getattr(self, characteristic)
        if current_value >= 20:
            print("Эта характеристика уже достигла максимума.")
            return

        setattr(self, characteristic, current_value + 1)
        self.energy -= 2
        print("Тренировка завершена. Характеристика лошади увеличена на 1.")

    def rest(self):
        self.energy = 10

    def bonus_for(self, characteristic):
        bonus_characteristic, bonus_value = PASSIVE_BONUSES.get(
            self.passive, (None, 0)
        )
        return bonus_value if characteristic == bonus_characteristic else 0


@dataclass
class GameState:
    jockey: Jockey
    horse: Horse
    current_day: int
    total_days: int
    difficulty: str
    rating: int = 0
    races: int = 0
    wins: int = 0


class Race:
    DIFFICULTY_TARGETS = {
        "Лёгкий": 10,
        "Средний": 13,
        "Сложный": 16,
    }

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.target = self.DIFFICULTY_TARGETS.get(difficulty, 13)

    def run(self, jockey, horse):
        if horse.energy < 2 or jockey.energy < 2:
            print("Для гонки нужно больше энергии. Отдохните")
            return None

        checks = [
            ("Стартовый рывок", "speed", "technique"),
            ("Прохождение поворотов", "obedience", "technique"),
            ("Финишный отрезок", "stamina", "strength"),
        ]

        successful_checks = 0
        print("\nГОНКА НАЧАЛАСЬ")

        for title, horse_stat, jockey_stat in checks:
            horse_value = getattr(horse, horse_stat)
            jockey_value = getattr(jockey, jockey_stat) // 2
            random_value = random.randint(1, 6)
            passive_value = horse.bonus_for(horse_stat)
            result = horse_value + jockey_value + random_value + passive_value

            print(
                f"{title}: результат {result}, сложность проверки {self.target}."
            )
            if result >= self.target:
                successful_checks += 1
                print("Проверка пройдена!")
            else:
                print("Проверка не пройдена.")

        horse.energy = max(0, horse.energy - 3)
        jockey.energy = max(0, jockey.energy - 2)

        won = successful_checks >= 2
        if won:
            print("\nПобеда! Ваша команда успешно завершила гонку.")
        else:
            print("\nWasted!")

        return won


def read_number(message):
    try:
        return int(input(message))
    except ValueError:
        print("Нужно ввести целое число.")
        return None


def write_json(file_path, data):
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def read_json(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def prepare_files():
    if not DEFAULTS_FILE.exists():
        write_json(DEFAULTS_FILE, DEFAULT_SETTINGS)
    if not DIFFICULTIES_FILE.exists():
        DIFFICULTIES_FILE.write_text("Лёгкий\nСредний\nСложный\n", encoding="utf-8")

    available_difficulties.clear()
    for line in DIFFICULTIES_FILE.read_text(encoding="utf-8").splitlines():
        difficulty = line.strip()
        if difficulty:
            available_difficulties.add(difficulty)
    if not available_difficulties:
        available_difficulties.update({"Лёгкий", "Средний", "Сложный"})

    if not SETTINGS_FILE.exists():
        write_json(SETTINGS_FILE, read_json(DEFAULTS_FILE))


def load_settings():
    global settings
    defaults = read_json(DEFAULTS_FILE)
    try:
        loaded = read_json(SETTINGS_FILE)
        difficulty = loaded.get("difficulty", defaults["difficulty"])
        duration = loaded.get("duration", defaults["duration"])
        if not isinstance(difficulty, str) or difficulty not in available_difficulties:
            difficulty = defaults["difficulty"]
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 1:
            duration = defaults["duration"]
        settings = {"difficulty": difficulty, "duration": duration}
    except (OSError, json.JSONDecodeError, AttributeError, KeyError):
        settings = defaults.copy()
        write_json(SETTINGS_FILE, settings)


def save_settings():
    write_json(SETTINGS_FILE, settings)


def state_to_dict(state):
    return {
        "jockey": state.jockey.__dict__,
        "horse": state.horse.__dict__,
        "current_day": state.current_day,
        "total_days": state.total_days,
        "difficulty": state.difficulty,
        "rating": state.rating,
        "races": state.races,
        "wins": state.wins,
    }


def state_from_dict(data):
    return GameState(
        jockey=Jockey(**data["jockey"]),
        horse=Horse(**data["horse"]),
        current_day=int(data["current_day"]),
        total_days=int(data["total_days"]),
        difficulty=str(data["difficulty"]),
        rating=int(data.get("rating", 0)),
        races=int(data.get("races", 0)),
        wins=int(data.get("wins", 0)),
    )


def save_game(state, automatic=False):
    file_path = AUTO_SAVE_FILE if automatic else MANUAL_SAVE_FILE
    try:
        write_json(file_path, state_to_dict(state))
        if automatic:
            print("Автосохранение выполнено.")
        else:
            print("Игра сохранена.")
    except OSError as error:
        print(f"Не удалось сохранить игру: {error}")


def load_game_file(automatic=False):
    file_path = AUTO_SAVE_FILE if automatic else MANUAL_SAVE_FILE
    try:
        data = read_json(file_path)
        state = state_from_dict(data)
        print("Сохранение успешно загружено.")
        save_profile(state)
        return state
    except FileNotFoundError:
        print("Файл сохранения пока не существует.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"Не удалось загрузить сохранение: {error}")
    return None


def show_main_menu():
    print("\nЛОШАДИ И ГОНКИ")
    print("1. Начать игру")
    print("2. Загрузить игру")
    print("3. Настройки")
    print("4. О программе")
    print("5. Конструктор лошадей")
    print("6. Рейтинг игрока")
    print("7. Выход")


def show_settings():
    choice = 0
    while choice != SETTINGS_BACK:
        print("\nНАСТРОЙКИ")
        print(f"1. Уровень сложности: {settings['difficulty']}")
        print(f"2. Продолжительность игры: {settings['duration']} игровых дней")
        print("3. Сброс настроек")
        print("4. Назад")
        choice = read_number("Выберите пункт: ")

        if choice == SETTINGS_DIFFICULTY:
            difficulties = sorted(available_difficulties)
            for number, difficulty in enumerate(difficulties, start=1):
                print(f"{number}. {difficulty}")
            selected = read_number("Выберите сложность: ")
            if selected is not None and 1 <= selected <= len(difficulties):
                settings["difficulty"] = difficulties[selected - 1]
                save_settings()
                print("Уровень сложности сохранён.")
            else:
                print("Такого уровня сложности нет.")
        elif choice == SETTINGS_DURATION:
            duration = read_number("Введите количество игровых дней (1–30): ")
            if duration is not None and 1 <= duration <= 30:
                settings["duration"] = duration
                save_settings()
                print("Продолжительность сохранена.")
            else:
                print("Введите число от 1 до 30.")
        elif choice == SETTINGS_RESET:
            settings.clear()
            settings.update(read_json(DEFAULTS_FILE))
            save_settings()
            print("Настройки сброшены.")
        elif choice == SETTINGS_BACK:
            print("Возвращаемся в главное меню.")
        else:
            print("Неизвестный пункт меню.")


def show_status(state):
    print("\nСОСТОЯНИЕ КОМАНДЫ")
    print(f"Наездник: {state.jockey.name}")
    print(f"Сила: {state.jockey.strength}; техника: {state.jockey.technique}; энергия: {state.jockey.energy}")
    print(f"Лошадь: {state.horse.name}")
    print(
        f"Скорость: {state.horse.speed}; выносливость: {state.horse.stamina}; "
        f"послушание: {state.horse.obedience}"
    )
    print(f"Энергия лошади: {state.horse.energy}")
    print(f"Пассивный бонус: {state.horse.passive}")
    print(f"Игровой день: {state.current_day} из {state.total_days}")
    print(f"Сложность: {state.difficulty}")
    print(f"Рейтинг игрока: {state.rating} ({get_rank_name(state.rating)})")
    print(f"Гонки: {state.races}; победы: {state.wins}")


def train_horse(state):
    print("\n1. Скорость")
    print("2. Выносливость")
    print("3. Послушание")
    choice = read_number("Какую характеристику тренировать? ")
    attributes = {1: "speed", 2: "stamina", 3: "obedience"}
    if choice in attributes:
        state.horse.train(attributes[choice])
    else:
        print("Такой характеристики нет.")


def train_jockey(state):
    print("\n1. Сила")
    print("2. Техника")
    choice = read_number("Какую характеристику тренировать? ")
    attributes = {1: "strength", 2: "technique"}
    if choice in attributes:
        state.jockey.train(attributes[choice])
    else:
        print("Такой характеристики нет.")


def play_game(state):
    for day_number in range(state.current_day, state.total_days + 1):
        state.current_day = day_number
        print(f"\nДЕНЬ {state.current_day}")
        print("За день можно выполнить не больше пяти действий.")

        for action_number in range(5):
            print("\n1. Тренировать лошадь")
            print("2. Тренировать наездника")
            print("3. Уход и отдых")
            print("4. Участвовать в гонке")
            print("5. Показать характеристики")
            print("6. Завершить день")
            print("7. Сохранить игру")
            print("8. Вернуться в главное меню")
            choice = read_number("Выберите действие: ")

            if choice == 1:
                train_horse(state)
            elif choice == 2:
                train_jockey(state)
            elif choice == 3:
                state.horse.rest()
                state.jockey.energy = 10
                print("Лошадь и наездник отдохнули. Энергия восстановлена.")
            elif choice == 4:
                won = Race(state.difficulty).run(state.jockey, state.horse)
                if won is not None:
                    state.races += 1
                    if won:
                        state.wins += 1
                        points = {"Лёгкий": 10, "Средний": 15, "Сложный": 20}.get(
                            state.difficulty, 15
                        )
                        print(f"За победу начислено {points} очков рейтинга.")
                    else:
                        points = 3
                        print(f"За участие начислено {points} очка рейтинга.")
                    state.rating += points
                    save_profile(state)
                save_game(state, automatic=True)
            elif choice == 5:
                show_status(state)
            elif choice == 6:
                break
            elif choice == 7:
                save_game(state)
            elif choice == 8:
                print("Возвращаемся в главное меню.")
                return
            else:
                print("Неизвестное действие.")

        state.current_day = day_number + 1
        state.horse.rest()
        state.jockey.energy = 10
        print("День завершён. Команда восстановила силы.")
        save_game(state, automatic=True)

    print("\nИгра завершена. Спасибо за участие!")


def load_profile():
    default_profile = {"rating": 0, "races": 0, "wins": 0}
    if not PROFILE_FILE.exists():
        write_json(PROFILE_FILE, default_profile)
        return default_profile.copy()

    try:
        profile = read_json(PROFILE_FILE)
        return {
            "rating": max(0, int(profile.get("rating", 0))),
            "races": max(0, int(profile.get("races", 0))),
            "wins": max(0, int(profile.get("wins", 0))),
        }
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
        write_json(PROFILE_FILE, default_profile)
        return default_profile.copy()


def save_profile(state):
    profile = {
        "rating": state.rating,
        "races": state.races,
        "wins": state.wins,
    }
    try:
        write_json(PROFILE_FILE, profile)
    except OSError as error:
        print(f"Не удалось сохранить рейтинг: {error}")


def get_rank_name(rating):
    if rating >= 150:
        return "Чемпион"
    if rating >= 75:
        return "Профессионал"
    if rating >= 30:
        return "Опытный наездник"
    return "Новичок"


def show_player_rating():
    profile = load_profile()
    print("\nРЕЙТИНГ ИГРОКА")
    print(f"Очки рейтинга: {profile['rating']}")
    print(f"Звание: {get_rank_name(profile['rating'])}")
    print(f"Всего гонок: {profile['races']}")
    print(f"Побед: {profile['wins']}")


def load_horse_templates():
    if not HORSES_FILE.exists():
        write_json(HORSES_FILE, [])

    try:
        horses = read_json(HORSES_FILE)
        if isinstance(horses, list):
            return [horse for horse in horses if isinstance(horse, dict)]
    except (OSError, json.JSONDecodeError):
        pass

    print("Файл созданных лошадей повреждён. Будет создан новый пустой список.")
    write_json(HORSES_FILE, [])
    return []


def show_stable():
    horses = load_horse_templates()
    print("\nВАША КОНЮШНЯ")
    if not horses:
        print("Пока нет созданных лошадей.")
        return

    for number, horse in enumerate(horses, start=1):
        print(
            f"{number}. {horse['name']} — скорость {horse['speed']}, "
            f"выносливость {horse['stamina']}, послушание {horse['obedience']}, "
            f"бонус: {horse['passive']}"
        )


def create_horse():
    print("\nСОЗДАНИЕ ЛОШАДИ")
    name = input("Введите имя лошади: ").strip()
    if not name:
        print("Имя не может быть пустым. Создание отменено.")
        return

    print("Распределите характеристики: каждое значение от 5 до 15, сумма не больше 30.")
    speed = read_number("Скорость (5–15): ")
    stamina = read_number("Выносливость (5–15): ")
    obedience = read_number("Послушание (5–15): ")

    values = (speed, stamina, obedience)
    if any(value is None or not 5 <= value <= 15 for value in values):
        print("Все характеристики должны быть числами от 5 до 15. Создание отменено.")
        return
    if sum(values) > 30:
        print("Сумма характеристик не должна превышать 30. Создание отменено.")
        return

    passive_names = list(PASSIVE_BONUSES)
    print("\nВыберите пассивный бонус:")
    characteristic_names = {
        "speed": "скорости",
        "stamina": "выносливости",
        "obedience": "послушанию",
    }
    for number, passive in enumerate(passive_names, start=1):
        characteristic, value = PASSIVE_BONUSES[passive]
        print(f"{number}. {passive} (+{value} к {characteristic_names[characteristic]})")
    selected = read_number("Номер бонуса: ")
    if selected is None or not 1 <= selected <= len(passive_names):
        print("Неверный номер. Создание лошади отменено.")
        return

    horse = {
        "name": name,
        "speed": speed,
        "stamina": stamina,
        "obedience": obedience,
        "energy": 10,
        "passive": passive_names[selected - 1],
    }
    horses = load_horse_templates()
    horses.append(horse)
    try:
        write_json(HORSES_FILE, horses)
        print(f"Лошадь «{name}» добавлена в конюшню.")
    except OSError as error:
        print(f"Не удалось сохранить лошадь: {error}")


def horse_constructor():
    choice = 0
    while choice != 3:
        print("\nКОНСТРУКТОР ЛОШАДЕЙ")
        print("1. Создать лошадь")
        print("2. Посмотреть конюшню")
        print("3. Назад")
        choice = read_number("Выберите пункт: ")

        if choice == 1:
            create_horse()
        elif choice == 2:
            show_stable()
        elif choice == 3:
            print("Возвращаемся в главное меню.")
        else:
            print("Неизвестный пункт меню.")


def choose_horse():
    horses = load_horse_templates()
    if not horses:
        print("Созданных лошадей пока нет. Для новой игры будет выбрана лошадь «Искра».")
        return Horse()

    print("\nВыберите лошадь для новой игры:")
    print("0. Стандартная лошадь — Искра")
    for number, horse in enumerate(horses, start=1):
        print(
            f"{number}. {horse['name']} "
            f"(скорость {horse['speed']}, выносливость {horse['stamina']}, "
            f"послушание {horse['obedience']}, бонус: {horse['passive']})"
        )

    selected = read_number("Ваш выбор: ")
    if selected == 0:
        return Horse()
    if selected is not None and 1 <= selected <= len(horses):
        try:
            return Horse(**horses[selected - 1])
        except TypeError:
            print("Данные выбранной лошади повреждены. Используем стандартную лошадь.")
    else:
        print("Неверный выбор. Используем стандартную лошадь.")
    return Horse()


def start_game():
    profile = load_profile()
    state = GameState(
        jockey=Jockey(),
        horse=choose_horse(),
        current_day=1,
        total_days=settings["duration"],
        difficulty=settings["difficulty"],
        rating=profile["rating"],
        races=profile["races"],
        wins=profile["wins"],
    )
    play_game(state)


def load_game():
    choice = 0
    while choice != 3:
        print("\nЗАГРУЗКА ИГРЫ")
        print("1. Загрузить обычное сохранение")
        print("2. Загрузить автосохранение")
        print("3. Назад")
        choice = read_number("Выберите вариант: ")

        if choice == 1:
            state = load_game_file(automatic=False)
            if state is not None:
                play_game(state)
                return
        elif choice == 2:
            state = load_game_file(automatic=True)
            if state is not None:
                play_game(state)
                return
        elif choice == 3:
            print("Возвращаемся в главное меню.")
        else:
            print("Неизвестный пункт меню.")


def show_about():
    print("\nО ПРОГРАММЕ")
    print("Игра: Лошади и гонки")
    print(f"Версия: {VERSION}")
    print(f"Автор: {STUDENT_NAME}")


def main():
    prepare_files()
    load_settings()
    load_profile()
    load_horse_templates()

    choice = 0
    while choice != MENU_EXIT:
        show_main_menu()
        choice = read_number("Выберите пункт меню: ")
        if choice == MENU_START:
            start_game()
        elif choice == MENU_LOAD:
            load_game()
        elif choice == MENU_SETTINGS:
            show_settings()
        elif choice == MENU_ABOUT:
            show_about()
        elif choice == MENU_HORSE_BUILDER:
            horse_constructor()
        elif choice == MENU_RATING:
            show_player_rating()
        elif choice == MENU_EXIT:
            print("BYE")
        else:
            print("Такого пункта меню нет.")


if __name__ == "__main__":
    main()
