import json
import os

from kivy.app import App
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

Builder.load_file("clicker.kv")
Window.size = (450, 900)


class Menu(Screen):
    def go_game(self, *args):
        self.manager.current = "g"

    def go_settings(self, *args):
        self.manager.current = "s"

    def go_exit(self, *args):
        app.stop()


class Game(Screen):
    score = NumericProperty(0)
    shop_popup = None
    shop_label = None
    buy_btn = None
    potion_2x_btn = None
    potion_4x_btn = None
    potion_8x_btn = None
    buff_label = None
    game_started = False
    buff_token = 0

    def on_enter(self, *args):
        if not self.game_started:
            self.game_started = True
            self.buff_label = self.ids.buff_label
            self.start_game()
        return super().on_enter(*args)

    def start_game(self):
        self.ids.block.new_block()

    def go_menu(self, *args):
        self.manager.current = "m"

    def open_shop(self, *args):
        content = BoxLayout(orientation="vertical", spacing=10, padding=15)

        self.shop_label = Label(
            text=f"Clicks: {app.click_currency}\nPermanent multiplier: x{app.click_multiplier}",
            font_size="18sp",
            size_hint=(1, 0.3)
        )
        content.add_widget(self.shop_label)

        self.buy_btn = Button(
            text=f"2x CLICK (permanent) — {app.double_click_price} clicks",
            font_size="14sp"
        )
        self.buy_btn.bind(on_release=self.buy_double_click)
        content.add_widget(self.buy_btn)

        self.potion_2x_btn = Button(
            text=f"2x Potion for 60 sec — {app.potion_2x_price} clicks",
            font_size="14sp"
        )
        self.potion_2x_btn.bind(on_release=lambda *a: self.buy_potion(2, 60, "potion_2x_price"))
        content.add_widget(self.potion_2x_btn)

        self.potion_4x_btn = Button(
            text=f"4x Potion for 30 sec — {app.potion_4x_price} clicks",
            font_size="14sp"
        )
        self.potion_4x_btn.bind(on_release=lambda *a: self.buy_potion(4, 30, "potion_4x_price"))
        content.add_widget(self.potion_4x_btn)

        self.potion_8x_btn = Button(
            text=f"8x Potion for 15 sec — {app.potion_8x_price} clicks",
            font_size="14sp"
        )
        self.potion_8x_btn.bind(on_release=lambda *a: self.buy_potion(8, 15, "potion_8x_price"))
        content.add_widget(self.potion_8x_btn)

        close_btn = Button(text="Close", font_size="16sp")
        content.add_widget(close_btn)

        self.shop_popup = Popup(
            title="Shop",
            content=content,
            size_hint=(0.85, 0.7)
        )
        close_btn.bind(on_release=self.shop_popup.dismiss)
        self.shop_popup.open()

    def buy_double_click(self, *args):
        if app.click_currency >= app.double_click_price:
            app.click_currency -= app.double_click_price
            app.click_multiplier *= 2
            app.double_click_price *= 2

            self.shop_label.text = (
                f"Purchased!\nClicks: {app.click_currency}\n"
                f"Permanent multiplier: x{app.click_multiplier}"
            )
            self.buy_btn.text = f"2x CLICK (permanent) — {app.double_click_price} clicks"
            app.save_progress()
        else:
            self.shop_label.text = (
                f"Not enough clicks!\nNeed {app.double_click_price}, you have {app.click_currency}"
            )

    def buy_potion(self, multiplier, duration, price_attr):
        price = getattr(app, price_attr)

        if app.click_currency < price:
            self.shop_label.text = f"Not enough clicks!\nNeed {price}, you have {app.click_currency}"
            return

        app.click_currency -= price
        setattr(app, price_attr, price * 2)

        if price_attr == "potion_2x_price":
            self.potion_2x_btn.text = f"2x Potion for 60 sec — {app.potion_2x_price} clicks"
        elif price_attr == "potion_4x_price":
            self.potion_4x_btn.text = f"4x Potion for 30 sec — {app.potion_4x_price} clicks"
        elif price_attr == "potion_8x_price":
            self.potion_8x_btn.text = f"8x Potion for 15 sec — {app.potion_8x_price} clicks"

        self.activate_temp_buff(multiplier, duration)
        self.shop_label.text = (
            f"Potion active!\nTemporary multiplier: x{multiplier}\nRemaining: {duration} sec"
        )
        app.save_progress()

    def activate_temp_buff(self, multiplier, duration):
        if app.temp_buff_event:
            app.temp_buff_event.cancel()

        self.buff_token += 1
        current_token = self.buff_token

        app.temp_multiplier = multiplier
        app.temp_buff_active = True
        self.update_buff_label(duration, current_token)

        app.temp_buff_event = Clock.schedule_once(self.end_temp_buff, duration)

    def end_temp_buff(self, *args):
        app.temp_multiplier = 1
        app.temp_buff_active = False
        app.temp_buff_event = None
        if self.buff_label:
            self.buff_label.text = ""

    def update_buff_label(self, seconds_left, token):

        if token != self.buff_token:
            return

        if self.buff_label:
            self.buff_label.text = f"Potion: x{app.temp_multiplier} ({int(seconds_left)} sec)"

        if seconds_left > 0 and app.temp_buff_active:
            Clock.schedule_once(lambda dt: self.update_buff_label(seconds_left - 1, token), 1)


class Settings(Screen):
    def go_menu(self, *args):
        self.manager.current = "m"


class Block(Image):
    block_current = None
    block_index = 0
    hp_current = 0
    hp_max = 0
    is_dead = False

    def new_block(self, *args):
        print(f"NEW BLOCK {self.block_current}")
        self.is_dead = False
        self.block_current = app.LEVELS[app.LEVEL][self.block_index]
        self.source = app.BLOCKS[self.block_current]["source"]
        self.hp_current = app.BLOCKS[self.block_current]["hp"]
        self.hp_max = self.hp_current
        self.opacity = 1

    def hit_feedback(self):
        damage_ratio = max(self.hp_current, 0) / self.hp_max
        Animation.cancel_all(self, "opacity")
        Animation(
            opacity=0.3 + 0.7 * damage_ratio,
            duration=0.1
        ).start(self)

    def destroy(self):
        if self.is_dead:
            return
        self.is_dead = True

        print("BLOCK IS DEAD INSIDE")

        Animation.cancel_all(self, "opacity")
        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=lambda *a: self.after_destroy())
        anim.start(self)

    def after_destroy(self):
        print("BLOCK GET HIT")

        self.block_index += 1
        app.root.get_screen("g").score += 1

        if self.block_index >= len(app.LEVELS[app.LEVEL]):
            if app.LEVEL + 1 < len(app.LEVELS):
                app.LEVEL += 1
                self.block_index = 0
                self.new_block()
            else:
                print("GAME COMPLETED — RESTARTING FROM LEVEL 1")
                app.LEVEL = 0
                self.block_index = 0
                self.new_block()
        else:
            self.new_block()

        app.save_progress()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.is_dead:
            return

        total_multiplier = app.click_multiplier * app.temp_multiplier
        app.click_currency += total_multiplier
        self.hp_current -= total_multiplier
        self.hit_feedback()

        if self.hp_current < 1:
            self.destroy()

        return super().on_touch_down(touch)


class MediumApp(App):
    LEVEL = 0

    click_currency = NumericProperty(0)
    click_multiplier = NumericProperty(1)
    double_click_price = NumericProperty(50)

    temp_multiplier = NumericProperty(1)
    temp_buff_active = False
    temp_buff_event = None

    potion_2x_price = NumericProperty(80)
    potion_4x_price = NumericProperty(100)
    potion_8x_price = NumericProperty(200)

    # === Все типы блоков ===
    BLOCKS = {
        "dirt": {"source": "assets/dirt.png", "hp": 10},
        "sand": {"source": "assets/sand.png", "hp": 15},
        "wood": {"source": "assets/wood.png", "hp": 20},
        "clay": {"source": "assets/clay.png", "hp": 28},
        "stone": {"source": "assets/stone.png", "hp": 35},
        "coal": {"source": "assets/coal.png", "hp": 45},
        "copper": {"source": "assets/copper.png", "hp": 60},
        "iron": {"source": "assets/iron.png", "hp": 80},
        "silver": {"source": "assets/silver.png", "hp": 100},
        "gold": {"source": "assets/gold.png", "hp": 125},
        "lapis": {"source": "assets/lapis.png", "hp": 150},
        "redstone": {"source": "assets/redstone.png", "hp": 180},
        "diamond": {"source": "assets/diamond.png", "hp": 220},
        "emerald": {"source": "assets/emerald.png", "hp": 260},
        "amethyst": {"source": "assets/amethyst.png", "hp": 310},
        "obsidian": {"source": "assets/obsidian.png", "hp": 370},
        "netherite": {"source": "assets/netherite.png", "hp": 440},
        "crystal": {"source": "assets/crystal.png", "hp": 520},
        "plasma": {"source": "assets/plasma.png", "hp": 620},
        "bedrock": {"source": "assets/bedrock.png", "hp": 740},
        "void": {"source": "assets/void.png", "hp": 880},
        "corrupted": {"source": "assets/corrupted.png", "hp": 1050},
    }

    # === Прогрессия уровней ===
    # Каждый новый тип блока сначала подмешивается к предыдущему,
    # затем идёт уровень из двух новых + один новый, и т.д.
    LEVELS = [
        ["dirt", "dirt", "wood"],
        ["dirt", "wood", "wood"],
        ["wood", "wood", "sand"],
        ["wood", "sand", "sand"],
        ["sand", "sand", "clay"],
        ["sand", "clay", "clay"],
        ["clay", "clay", "stone"],
        ["clay", "stone", "stone"],
        ["stone", "stone", "coal"],
        ["stone", "coal", "coal"],
        ["coal", "coal", "copper"],
        ["coal", "copper", "copper"],
        ["copper", "copper", "iron"],
        ["copper", "iron", "iron"],
        ["iron", "iron", "silver"],
        ["iron", "silver", "silver"],
        ["silver", "silver", "gold"],
        ["silver", "gold", "gold"],
        ["gold", "gold", "lapis"],
        ["gold", "lapis", "lapis"],
        ["lapis", "lapis", "redstone"],
        ["lapis", "redstone", "redstone"],
        ["redstone", "redstone", "diamond"],
        ["redstone", "diamond", "diamond"],
        ["diamond", "diamond", "emerald"],
        ["diamond", "emerald", "emerald"],
        ["emerald", "emerald", "amethyst"],
        ["emerald", "amethyst", "amethyst"],
        ["amethyst", "amethyst", "obsidian"],
        ["amethyst", "obsidian", "obsidian"],
        ["obsidian", "obsidian", "netherite"],
        ["obsidian", "netherite", "netherite"],
        ["netherite", "netherite", "crystal"],
        ["netherite", "crystal", "crystal"],
        ["crystal", "crystal", "plasma"],
        ["crystal", "plasma", "plasma"],
        ["plasma", "plasma", "bedrock"],
        ["plasma", "bedrock", "bedrock"],
        ["bedrock", "bedrock", "void"],
        ["bedrock", "void", "void"],
        ["void", "void", "corrupted"],
        ["corrupted", "corrupted", "corrupted"],
    ]

    SAVE_FILE = "save.json"

    def build(self):
        print("GAME IS RUNNING")
        sm = ScreenManager()
        sm.add_widget(Menu(name="m"))
        sm.add_widget(Game(name="g"))
        sm.add_widget(Settings(name="s"))
        return sm

    def on_start(self):
        # self.root уже существует и виден на экране — самое подходящее
        # место для загрузки сохранения (внутри build() self.root ещё None)
        self.load_progress()

    def on_stop(self):
        # вызывается при штатном закрытии окна (например, крестик на ПК)
        self.save_progress()

    def on_pause(self):
        # вызывается на Android при сворачивании приложения
        self.save_progress()
        return True  # разрешаем приложению уйти в паузу, а не закрыться

    def save_progress(self, *args):
        game_screen = self.root.get_screen("g")

        data = {
            "click_currency": self.click_currency,
            "click_multiplier": self.click_multiplier,
            "double_click_price": self.double_click_price,
            "potion_2x_price": self.potion_2x_price,
            "potion_4x_price": self.potion_4x_price,
            "potion_8x_price": self.potion_8x_price,
            "level": self.LEVEL,
            "score": game_screen.score,
            "block_index": game_screen.ids.block.block_index,
        }

        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("PROGRESS SAVED")
        except OSError as e:
            print(f"SAVE ERROR: {e}")

    def load_progress(self):
        if not os.path.exists(self.SAVE_FILE):
            print("NO SAVE FILE FOUND")
            return

        try:
            with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"LOAD ERROR: {e}")
            return

        self.click_currency = data.get("click_currency", 0)
        self.click_multiplier = data.get("click_multiplier", 1)
        self.double_click_price = data.get("double_click_price", 50)
        self.potion_2x_price = data.get("potion_2x_price", 80)
        self.potion_4x_price = data.get("potion_4x_price", 100)
        self.potion_8x_price = data.get("potion_8x_price", 200)
        self.LEVEL = data.get("level", 0)

        game_screen = self.root.get_screen("g")
        game_screen.score = data.get("score", 0)
        game_screen.ids.block.block_index = data.get("block_index", 0)

        print("PROGRESS LOADED")


app = MediumApp()
app.run()
