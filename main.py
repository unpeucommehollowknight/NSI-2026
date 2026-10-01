import arcade
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# =========================================================
# CONFIG
# =========================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TITLE = "Mon RPG 2D - Inventaire"

# Palette dark fantasy
BG = (7, 9, 12)
BG2 = (13, 16, 21)
PANEL = (24, 24, 24)
PANEL_DARK = (12, 13, 16)
PANEL_LIGHT = (35, 34, 32)

GOLD_DARK = (88, 63, 35)
GOLD = (184, 135, 61)
GOLD_LIGHT = (230, 181, 88)

RED = (150, 42, 48)
RED_LIGHT = (220, 68, 70)

TEXT = (225, 218, 201)
TEXT_DARK = (140, 136, 126)

GREEN = (80, 165, 95)
BLUE = (80, 125, 185)
PURPLE = (145, 85, 175)

# =========================================================
# OBJETS
# =========================================================

ITEMS = [
    {
        "name": "Épée basique",
        "type": "Arme",
        "icon": "sword",
        "attack": 17,
        "defense": 0,
        "crit": 4,
        "weight": 5.2,
    },
    {
        "name": "Épée en or ",
        "type": "Arme",
        "icon": None,
        "attack": 10,
        "defense": 0,
        "crit": 9,
        "weight": 2.1,
    },
    {
        "name": "Bouclier ",
        "type": "Équipement",
        "icon": "shield",
        "attack": 0,
        "defense": 12,
        "crit": 0,
        "weight": 7.0,
    },
    {
            "name": "Bouclier en émeuraude ",
            "type": "Équipement",
            "icon": "shield",
            "attack": 0,
            "defense": 30,
            "crit": 0,
            "weight": 7.0,
        },
    {
        "name": "Clé ",
        "type": "Équipement",
        "icon": "ring",
        "attack": 0,
        "defense": 0,
        "crit": 0,
        "weight": 0.2,
    },
    {
        "name": "Potion de soin",
        "type": "Objet",
        "icon": "potion",
        "attack": 0,
        "defense": 0,
        "crit": 0,
        "weight": 0.5,
        "description": "Restaure des points de vie."
    },
    {
        "name": "Potion de mana",
        "type": "Objet",
        "icon": "mana",
        "attack": 0,
        "defense": 0,
        "crit": 0,
        "weight": 0.5,
        "description": "Restaure des points de mana."
    },
]

SKILLS = [
    ("Frappe rapide", 25, 10, 2),
    ("Lame fantôme", 40, 25, 6),
    ("Soin", 0, 30, 10),
    ("Explosion obscure", 65, 50, 15),
]


class Game(arcade.Window):

    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            TITLE,
            fullscreen=True
        )

        self.background_color = BG

        self.player_x = self.width * 0.32
        self.player_y = self.height * 0.48
        self.speed = 5
        self.keys = set()

        self.inventory_open = True
        self.category = "Arme"

        self.hover_item = None
        self.selected_item = None
        self.equipped_weapon = None

        self.mouse_x = 0
        self.mouse_y = 0

        # Image de l'épée (facultative pour le moment).
        # Tu pourras mettre ton image dans weapons/sword.png plus tard.
        sword_path = BASE_DIR / "weapons" / "sword.png"
        self.sword_sprite = None
        if sword_path.exists():
            self.sword_sprite = arcade.Sprite(str(sword_path), scale=0.48)

    # =====================================================
    # STATS
    # =====================================================

    def get_stats(self):
        attack = 25
        defense = 18
        crit = 5

        if self.equipped_weapon:
            attack += self.equipped_weapon["attack"]
            defense += self.equipped_weapon["defense"]
            crit += self.equipped_weapon["crit"]

        return attack, defense, crit

    # =====================================================
    # OUTILS
    # =====================================================

    def box(self, left, right, bottom, top, color):
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top, color
        )

    def outline(self, left, right, bottom, top, color, width=2):
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top, color, width
        )

    def text(self, value, x, y, size=12, color=TEXT,
             anchor_x="left", anchor_y="center"):
        arcade.draw_text(
            value, x, y, color, size,
            anchor_x=anchor_x,
            anchor_y=anchor_y
        )

    def diamond(self, x, y, size=12):
        arcade.draw_polygon_filled(
            [
                (x, y + size),
                (x + size, y),
                (x, y - size),
                (x - size, y)
            ],
            RED
        )
        arcade.draw_polygon_outline(
            [
                (x, y + size),
                (x + size, y),
                (x, y - size),
                (x - size, y)
            ],
            GOLD_LIGHT,
            2
        )

    def decorative_frame(self, left, right, bottom, top):
        # Fond
        self.box(left, right, bottom, top, PANEL)

        # Double cadre
        self.outline(left, right, bottom, top, GOLD_DARK, 6)
        self.outline(
            left + 7, right - 7,
            bottom + 7, top - 7,
            GOLD, 2
        )

        # Coins
        s = 18
        for x, y in [
            (left + 5, bottom + 5),
            (left + 5, top - 5),
            (right - 5, bottom + 5),
            (right - 5, top - 5)
        ]:
            self.diamond(x, y, s)

    # =====================================================
    # UPDATE
    # =====================================================

    def on_update(self, delta_time):
        if self.inventory_open:
            return

        if arcade.key.W in self.keys:
            self.player_y += self.speed
        if arcade.key.S in self.keys:
            self.player_y -= self.speed
        if arcade.key.A in self.keys:
            self.player_x -= self.speed
        if arcade.key.D in self.keys:
            self.player_x += self.speed

    # =====================================================
    # DRAW
    # =====================================================

    def on_draw(self):
        self.clear()
        self.draw_background()

        if self.inventory_open:
            self.draw_inventory()
        else:
            self.draw_game()

    def draw_background(self):
        self.box(0, self.width, 0, self.height, BG)

        # Lignes discrètes façon texture pixel
        for x in range(0, self.width, 48):
            arcade.draw_line(
                x, 0, x + 180, self.height,
                BG2, 1
            )

    def draw_game(self):
        self.box(
            0, self.width, 0, self.height,
            (24, 38, 29)
        )

        arcade.draw_circle_filled(
            self.player_x,
            self.player_y + 25,
            20,
            (190, 190, 195)
        )

        self.box(
            self.player_x - 23,
            self.player_x + 23,
            self.player_y - 35,
            self.player_y + 20,
            (85, 88, 95)
        )

        self.text(
            "TAB / I : INVENTAIRE",
            20, self.height - 30,
            14, TEXT
        )

    # =====================================================
    # INVENTAIRE
    # =====================================================

    def draw_inventory(self):

        left = self.width * 0.06
        right = self.width * 0.94
        top = self.height * 0.92
        bottom = self.height * 0.08

        upper_bottom = self.height * 0.50
        grid_bottom = self.height * 0.18

        # Grand cadre principal
        self.decorative_frame(left, right, bottom, top)

        # Ligne centrale décorative
        arcade.draw_line(
            left + 15, upper_bottom,
            right - 15, upper_bottom,
            GOLD_DARK, 5
        )
        arcade.draw_line(
            left + 25, upper_bottom,
            right - 25, upper_bottom,
            GOLD, 1
        )
        self.diamond(
            (left + right) / 2,
            upper_bottom,
            14
        )

        # -------------------------------------------------
        # ZONE ÉQUIPEMENT
        # -------------------------------------------------

        self.text(
            "ÉQUIPEMENT",
            left + 35,
            top - 35,
            18,
            GOLD_LIGHT
        )

        # Slots à gauche
        slot_size = 58
        sx = left + 28
        sy = top - 100

        for i in range(4):
            y = sy - i * 72
            self.draw_slot(
                sx, y - slot_size,
                sx + slot_size, y
            )

        # Grande zone personnage
        char_left = left + 115
        char_right = left + 355
        char_bottom = upper_bottom + 30
        char_top = top - 75

        self.box(
            char_left, char_right,
            char_bottom, char_top,
            PANEL_DARK
        )
        self.outline(
            char_left, char_right,
            char_bottom, char_top,
            GOLD, 2
        )

        # Symbole central
        cx = (char_left + char_right) / 2
        cy = (char_bottom + char_top) / 2

        arcade.draw_circle_outline(
            cx, cy + 30, 62,
            GOLD_DARK, 2
        )

        arcade.draw_circle_filled(
            cx, cy + 45, 20,
            (170, 170, 175)
        )

        self.box(
            cx - 25, cx + 25,
            cy - 55, cy + 25,
            (75, 78, 85)
        )

        # Arme équipée
        if self.equipped_weapon and self.sword_sprite:
            self.sword_sprite.center_x = cx + 48
            self.sword_sprite.center_y = cy
            self.sword_sprite.scale = 0.42
            arcade.draw_sprite(self.sword_sprite)

        # -------------------------------------------------
        # ZONE CRAFT / APERÇU
        # -------------------------------------------------

        craft_left = left + 400
        craft_right = right - 35

        self.text(
            "ÉQUIPEMENT / OBJET",
            craft_left,
            top - 35,
            18,
            GOLD_LIGHT
        )

        # 4 gros slots
        for i in range(4):
            row = i // 2
            col = i % 2

            x = craft_left + 40 + col * 95
            y = top - 115 - row * 95

            self.draw_slot(
                x, y - 70,
                x + 70, y,
            )

        # Flèche
        arcade.draw_line(
            craft_left + 245,
            top - 155,
            craft_left + 305,
            top - 155,
            GOLD_LIGHT,
            5
        )
        arcade.draw_triangle_filled(
            craft_left + 320,
            top - 155,
            craft_left + 295,
            top - 140,
            craft_left + 295,
            top - 170,
            GOLD_LIGHT
        )

        # Résultat
        self.draw_slot(
            craft_left + 345,
            top - 190,
            craft_left + 425,
            top - 110
        )

        # -------------------------------------------------
        # INVENTAIRE
        # -------------------------------------------------

        inv_left = left + 25
        inv_right = right - 25

        self.text(
            "INVENTAIRE",
            inv_left,
            upper_bottom - 30,
            17,
            GOLD_LIGHT
        )

        # Onglets
        tabs = ["Arme", "Équipement", "Objet"]
        tx = inv_left + 130

        for tab in tabs:
            active = tab == self.category

            self.box(
                tx, tx + 105,
                upper_bottom - 55,
                upper_bottom - 28,
                (50, 39, 25) if active else PANEL_DARK
            )

            self.outline(
                tx, tx + 105,
                upper_bottom - 55,
                upper_bottom - 28,
                GOLD if active else GOLD_DARK,
                2
            )

            self.text(
                tab.upper(),
                tx + 52,
                upper_bottom - 42,
                10,
                GOLD_LIGHT if active else TEXT_DARK,
                anchor_x="center"
            )

            tx += 115

        # Grille
        items = [
            item for item in ITEMS
            if item["type"] == self.category
        ]

        slot = 58
        gap = 8
        cols = 8

        grid_width = cols * slot + (cols - 1) * gap
        start_x = (
            (left + right) / 2
            - grid_width / 2
        )
        start_y = upper_bottom - 78

        for i, item in enumerate(items):

            col = i % cols
            row = i // cols

            x = start_x + col * (slot + gap)
            y = start_y - row * (slot + gap)

            hovered = self.hover_item == item
            selected = self.selected_item == item

            self.draw_slot(
                x, y - slot,
                x + slot, y,
                hovered or selected
            )

            self.draw_item_icon(item, x, y)

        # -------------------------------------------------
        # BARRE RAPIDE
        # -------------------------------------------------

        hotbar_y = bottom + 35

        self.text(
            "BARRE RAPIDE",
            left + 25,
            hotbar_y + 65,
            12,
            TEXT_DARK
        )

        for i in range(9):
            x = left + 150 + i * 65
            self.draw_slot(
                x,
                hotbar_y,
                x + 55,
                hotbar_y + 55
            )

        # -------------------------------------------------
        # TOOLTIP
        # -------------------------------------------------

        if self.hover_item:
            self.draw_item_tooltip(
                self.hover_item,
                self.mouse_x,
                self.mouse_y
            )

    # =====================================================
    # SLOTS
    # =====================================================

    def draw_slot(self, left, bottom, right, top, active=False):

        self.box(
            left, right,
            bottom, top,
            PANEL_LIGHT if active else PANEL_DARK
        )

        self.outline(
            left, right,
            bottom, top,
            GOLD_LIGHT if active else GOLD_DARK,
            3
        )

        # petits coins
        c = 7
        for x, y in [
            (left + 3, bottom + 3),
            (left + 3, top - 3),
            (right - 3, bottom + 3),
            (right - 3, top - 3)
        ]:
            arcade.draw_line(
                x - c, y,
                x + c, y,
                GOLD_DARK,
                2
            )

    def draw_item_icon(self, item, x, y):

        if item["icon"] == "sword":
            if self.sword_sprite:
                self.sword_sprite.center_x = x + 29
                self.sword_sprite.center_y = y - 29
                self.sword_sprite.scale = 0.48
                arcade.draw_sprite(self.sword_sprite)
            else:
                # Icône temporaire en attendant ton image.
                arcade.draw_line(x + 17, y - 41, x + 41, y - 17, GOLD_LIGHT, 5)
                arcade.draw_line(x + 14, y - 44, x + 22, y - 36, GOLD, 4)

        elif item["icon"] == "shield":
            arcade.draw_circle_filled(
                x + 29, y - 29,
                18, BLUE
            )
            arcade.draw_circle_outline(
                x + 29, y - 29,
                18, GOLD, 2
            )

        elif item["icon"] == "ring":
            arcade.draw_circle_outline(
                x + 29, y - 29,
                13, GOLD_LIGHT, 4
            )

        elif item["icon"] == "potion":
            self.box(
                x + 21, x + 37,
                y - 45, y - 23,
                RED
            )

        elif item["icon"] == "mana":
            self.box(
                x + 21, x + 37,
                y - 45, y - 23,
                BLUE
            )

        else:
            self.text(
                "?",
                x + 29, y - 29,
                18, GOLD_LIGHT,
                anchor_x="center"
            )

    # =====================================================
    # TOOLTIP
    # =====================================================

    def draw_item_tooltip(self, item, mouse_x, mouse_y):

        width = 270
        height = 170

        x = mouse_x + 18
        y = mouse_y - height

        if x + width > self.width:
            x = mouse_x - width - 18

        if y < 10:
            y = 10

        self.box(
            x, x + width,
            y, y + height,
            PANEL_DARK
        )

        self.outline(
            x, x + width,
            y, y + height,
            GOLD_LIGHT, 3
        )

        self.text(
            item["name"],
            x + 15,
            y + height - 25,
            15,
            GOLD_LIGHT
        )

        self.text(
            f"ATK    +{item['attack']}",
            x + 15,
            y + height - 55,
            11,
            RED_LIGHT
        )

        self.text(
            f"DEF    +{item['defense']}",
            x + 15,
            y + height - 77,
            11,
            BLUE
        )

        self.text(
            f"CRIT   +{item['crit']}%",
            x + 15,
            y + height - 99,
            11,
            PURPLE
        )

        self.text(
            f"POIDS  {item['weight']}",
            x + 15,
            y + height - 121,
            10,
            TEXT_DARK
        )

        self.text(
            "CLIC : sélectionner / équiper",
            x + 15,
            y + 15,
            9,
            TEXT_DARK
        )

    # =====================================================
    # SOURIS
    # =====================================================

    def on_mouse_motion(self, x, y, dx, dy):

        self.mouse_x = x
        self.mouse_y = y
        self.hover_item = None

        if not self.inventory_open:
            return

        left = self.width * 0.06
        right = self.width * 0.94
        upper_bottom = self.height * 0.50

        items = [
            item for item in ITEMS
            if item["type"] == self.category
        ]

        slot = 58
        gap = 8
        cols = 8

        grid_width = cols * slot + (cols - 1) * gap

        start_x = (
            (left + right) / 2
            - grid_width / 2
        )

        start_y = upper_bottom - 78

        for i, item in enumerate(items):

            col = i % cols
            row = i // cols

            sx = start_x + col * (slot + gap)
            sy = start_y - row * (slot + gap)

            if (
                sx <= x <= sx + slot
                and sy - slot <= y <= sy
            ):
                self.hover_item = item
                return

    # =====================================================
    # CLIC
    # =====================================================

    def on_mouse_press(self, x, y, button, modifiers):

        if not self.inventory_open:
            return

        # Cliquer sur un objet
        if self.hover_item:

            self.selected_item = self.hover_item

            # Une arme devient équipée
            if self.hover_item["type"] == "Arme":
                self.equipped_weapon = self.hover_item

    # =====================================================
    # CLAVIER
    # =====================================================

    def on_key_press(self, key, modifiers):

        if key == arcade.key.TAB or key == arcade.key.I:
            self.inventory_open = not self.inventory_open
            self.hover_item = None
            return

        if not self.inventory_open:
            self.keys.add(key)

    def on_key_release(self, key, modifiers):

        if key in self.keys:
            self.keys.remove(key)


# =========================================================
# LANCEMENT
# =========================================================

if __name__ == "__main__":
    game = Game()
    arcade.run()