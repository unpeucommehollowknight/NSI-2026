import arcade
from pathlib import Path
import json
import random
import math 

from game_world import WorldMixin
from levels import TILE, SOLID_KINDS


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TITLE = "Mon RPG 2D - Inventaire"

BASE_DIR = Path(__file__).resolve().parent
SWORD_PATH = BASE_DIR / "weapons" / "epee.png"
SWORD_BAS_PATH = BASE_DIR / "weapons" / "epee_basique.png"
ARCLEG_PATH = BASE_DIR / "weapons" / "arc_legendaire.png"

SAVE_PATH = BASE_DIR / "save.json"

# Fallback utile si l'image système "epee_basique.png" n'existe pas.
# Dans ce cas, on réutilise l'épée principale pour éviter un crash au lancement.
if not SWORD_BAS_PATH.exists() and SWORD_PATH.exists():
    SWORD_BAS_PATH = SWORD_PATH


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
MELEE_COLOR = (235, 105, 65)
RANGED_COLOR = (65, 185, 215)
MANA_BLUE = (100, 175, 255)

FONT_TITLE = ("Garamond", "Georgia", "Palatino Linotype", "Times New Roman")
GAME_TITLE = "unpeucommehollowknight"
GAME_SUBTITLE = "en construction"

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_GAME_OVER = "game_over"


class Item:
    def __init__(self, name, item_type, icon, attack=0, defense=0, crit=0, weight=0, description="", item_id=None, kind=""):
        self.__name = name
        self.__type = item_type
        self.__icon = icon
        self.__id = item_id or {
            "Épée basique ": "epee_basique", "Épée en Or ": "epee_or",
            "Arc basique ": "arc_basique", "Arc légendaire": "arc_legendaire",
            "Bouclier en Ecaille de Dragon ": "bouclier_dragon",
            "Bouclier ancien": "bouclier_ancien", "Cle": "cle",
            "Potion de soin": "potion_soin", "Potion de mana": "potion_mana"
        }.get(name, name.strip().lower().replace(" ", "_"))
        self.__kind = kind or {
            "sword_bas": "melee", "sword": "melee", "arcbas": "ranged",
            "arcleg": "ranged", "shield": "shield", "object": "key",
            "potion": "heal", "mana": "mana"
        }.get(icon, "")
        self.__attack = attack
        self.__defense = defense
        self.__crit = crit
        self.__weight = weight
        self.__description = description

    # Accesseurs
    def get_id(self): return self.__id
    def get_kind(self): return self.__kind
    def get_name(self): return self.__name
    def get_type(self): return self.__type
    def get_icon(self): return self.__icon
    def get_attack(self): return self.__attack
    def get_defense(self): return self.__defense
    def get_crit(self): return self.__crit
    def get_weight(self): return self.__weight
    def get_description(self): return self.__description

    # 3+ mutateurs
    def set_name(self, value): self.__name = value
    def set_id(self, value): self.__id = value
    def set_kind(self, value): self.__kind = value
    def set_attack(self, value): self.__attack = value
    def set_defense(self, value): self.__defense = value
    def set_crit(self, value): self.__crit = value
    def set_weight(self, value): self.__weight = value

    def __eq__(self, other):
        return isinstance(other, Item) and self.__name == other.__name

    def __str__(self):
        return self.__name

    def to_dict(self):
        return {"id": self.__id, "name": self.__name, "type": self.__type,
                "icon": self.__icon, "kind": self.__kind,
                "attack": self.__attack, "defense": self.__defense, "crit": self.__crit,
                "weight": self.__weight, "description": self.__description}


# 20 vraies instances d'Item. Les 9 premières sont celles affichées dans l'inventaire.
ITEMS = [
    Item("Épée basique ", "Arme", "sword_bas", 5, 0, 1, 5.2, "Une ancienne épée utilisée par les escrimeurs."),
    Item("Épée en Or ", "Arme", "sword", 10, 0, 2, 5.2, "Une ancienne épée utilisée par les chevaliers."),
    Item("Arc basique ", "Arme", "arcbas", 4, 0, 5, 3.5, "Un arc légendaire forgé pour les guerriers les plus redoutables."),
    Item("Arc légendaire", "Arme", "arcleg", 20, 0, 12, 3.5, "Un arc légendaire forgé pour les guerriers les plus redoutables."),
    Item("Bouclier en Ecaille de Dragon ", "Équipement", "shield", 0, 40, 0, 7.0, "Un bouclier cree a partir d ecaille de dragon."),
    Item("Bouclier ancien", "Équipement", "shield", 0, 10, 0, 7.0, "Un vieux bouclier capable de résister aux coups."),
    Item("Cle", "Équipement", "object", 0, 0, 0, 0.2, "Cle qui permet d acceder a des zones "),
    Item("Potion de soin", "Objet", "potion", 0, 0, 0, 0.5, "Restaure des points de vie."),
    Item("Potion de mana", "Objet", "mana", 0, 0, 0, 0.5, "Restaure des points de mana."),
]
for n in range(11):
    ITEMS.append(Item(f"Objet catalogue {n + 1}", "Catalogue", "object"))


class Skill:
    def __init__(self, name, attack, defense, cost):
        self.__name = name
        self.__attack = attack
        self.__defense = defense
        self.__cost = cost

    def get_name(self): return self.__name
    def get_attack(self): return self.__attack
    def get_defense(self): return self.__defense
    def get_cost(self): return self.__cost
    def set_name(self, value): self.__name = value
    def set_attack(self, value): self.__attack = value
    def set_defense(self, value): self.__defense = value
    def set_cost(self, value): self.__cost = value

    def __eq__(self, other):
        return isinstance(other, Skill) and self.__name == other.__name


class Slot:
    def __init__(self, index, item=None):
        self.__index = index
        self.__item = item
        self.__active = False

    def get_index(self): return self.__index
    def get_item(self): return self.__item
    def is_active(self): return self.__active
    def set_index(self, value): self.__index = value
    def set_item(self, value): self.__item = value
    def set_active(self, value): self.__active = value

    def __bool__(self): return self.__item is not None


class Inventory:
    def __init__(self, items=None):
        self.__items = list(items) if items else []
        self.__category = "Arme"
        self.__selected = None

    def get_items(self): return self.__items
    def get_category(self): return self.__category
    def get_selected(self): return self.__selected
    def set_items(self, value): self.__items = list(value)
    def set_category(self, value): self.__category = value
    def set_selected(self, value): self.__selected = value
    def add_item(self, item): self.__items.append(item)

    def filtered_items(self):
        return [item for item in self.__items if item.get_type() == self.__category]

    def __len__(self): return len(self.__items)

    def to_dict(self):
        return {
            "items": [item.to_dict() for item in self.__items],
            "category": self.__category,
            "selected": self.__selected.to_dict() if self.__selected else None
        }


class Player:
    def __init__(self, inventory=None):
        self.__x = 0
        self.__y = 0
        self.__speed = 5
        self.__inventory = inventory if inventory else Inventory()
        self.__hp = 100
        self.__max_hp = 100
        self.__equipped_weapon = None
        self.__base_attack = 25
        self.__base_defense = 18
        self.__base_crit = 5
        self.__xp = 0
        self.__level = 1
        self.__xp_needed = 100
        self.__equipped_shield = None
        self.__mana = 50
        self.__max_mana = 50

        # Arbre de compétences
        self.__skill_points = 0
        self.__unlocked_skills = set()

    def get_hp(self): return self.__hp
    def get_max_hp(self): return self.__max_hp
    def get_xp(self): return self.__xp
    def get_level(self): return self.__level
    def get_xp_needed(self): return self.__xp_needed

    def get_skill_points(self):
        return self.__skill_points

    def has_skill(self, skill_name):
        return skill_name in self.__unlocked_skills

    def get_skill_status(self, skill_id):
        """Renvoie unlocked, locked, no_points ou available."""
        if skill_id in self.__unlocked_skills:
            return "unlocked"
        if skill_id not in SKILL_TREE:
            return "locked"
        if any(r not in self.__unlocked_skills for r in skill_requirements(skill_id)):
            return "locked"
        if self.__skill_points < SKILL_TREE[skill_id]["cost"]:
            return "no_points"
        return "available"

    def gain_xp(self, value):
        self.__xp += value

        while self.__xp >= self.__xp_needed:
            self.__xp -= self.__xp_needed
            self.__level += 1
            self.__xp_needed = int(self.__xp_needed * 1.5)

            self.__base_attack = round(self.__base_attack * 1.05)
            self.__base_defense = round(self.__base_defense * 1.05)
            self.__base_crit = round(self.__base_crit * 1.05)

            # Un point à chaque niveau, plus deux points tous les dix niveaux.
            self.__skill_points += 1
            if self.__level % 10 == 0:
                self.__skill_points += 2

            print("Niveau atteint :", self.__level)
            print("Points de compétence :", self.__skill_points)

    def unlock_skill(self, skill_name):
        if self.get_skill_status(skill_name) != "available":
            return False

        data = SKILL_TREE[skill_name]
        effects = data["effects"]
        self.__skill_points -= data["cost"]
        self.__unlocked_skills.add(skill_name)

        self.__base_attack += effects.get("attack", 0)
        self.__base_defense += effects.get("defense", 0)
        self.__base_crit += effects.get("crit", 0)

        hp = effects.get("hp", 0)
        self.__max_hp += hp
        self.__hp = min(self.__max_hp, self.__hp + hp)

        mana = effects.get("mana", 0)
        self.__max_mana += mana
        self.__mana = min(self.__max_mana, self.__mana + mana)
        return True

    # L'Inventaire est agrégé par Player.
    def get_x(self): return self.__x
    def get_y(self): return self.__y
    def get_speed(self): return self.__speed
    def get_inventory(self): return self.__inventory
    def get_equipped_weapon(self): return self.__equipped_weapon
    def set_x(self, value): self.__x = value
    def set_y(self, value): self.__y = value
    def set_speed(self, value): self.__speed = value
    def set_inventory(self, value): self.__inventory = value
    def set_equipped_weapon(self, value): self.__equipped_weapon = value

    def get_equipped_shield(self): return self.__equipped_shield
    def set_equipped_shield(self, v): self.__equipped_shield = v
    def get_mana(self): return self.__mana
    def get_max_mana(self): return self.__max_mana

    def use_mana(self, cost):
        if self.__mana >= cost:
            self.__mana -= cost
            return True
        return False

    def regen_mana(self, v): self.__mana = min(self.__max_mana, self.__mana + v)
    def heal(self, v): self.__hp = min(self.__max_hp, self.__hp + v)
    def revive(self): self.__hp = self.__max_hp

    def take_damage(self, raw):
        _, defense, _ = self.get_stats()
        dmg = max(1, int(raw * 100 / (100 + defense)))   # la défense réduit les dégâts
        self.__hp = max(0, self.__hp - dmg)
        return dmg

    def get_stats(self):
        attack, defense, crit = self.__base_attack, self.__base_defense, self.__base_crit
        for gear in (self.__equipped_weapon, self.__equipped_shield):
            if gear:
                attack += gear.get_attack()
                defense += gear.get_defense()
                crit += gear.get_crit()
        return attack, defense, crit

    def __str__(self): return f"Player ({self.__x}, {self.__y})"

    def to_dict(self):
        return {
            "x": self.__x,
            "y": self.__y,
            "speed": self.__speed,
            "hp": self.__hp,
            "max_hp": self.__max_hp,
            "mana": self.__mana,
            "max_mana": self.__max_mana,
            "level": self.__level,
            "xp": self.__xp,
            "xp_needed": self.__xp_needed,
            "base_attack": self.__base_attack,
            "base_defense": self.__base_defense,
            "base_crit": self.__base_crit,
            "skill_points": self.__skill_points,
            "unlocked_skills": list(self.__unlocked_skills),
            "equipped_weapon": self.__equipped_weapon.to_dict() if self.__equipped_weapon else None,
            "equipped_shield": self.__equipped_shield.to_dict() if self.__equipped_shield else None,
            "inventory": self.__inventory.to_dict()
        }

    def load_stats(self, data):
        """Restaure position, niveau, stats et ressources depuis le dict du save.json.
        data.get(clé, défaut) : si la clé n'existe pas (ancienne sauvegarde),
        on garde une valeur par défaut au lieu de planter."""
        self.__x = data.get("x", 0)
        self.__y = data.get("y", 0)
        self.__speed = data.get("speed", self.__speed)

        self.__level = data.get("level", 1)
        self.__xp = data.get("xp", 0)
        self.__xp_needed = data.get("xp_needed", 100)

        self.__max_hp = data.get("max_hp", self.__max_hp)
        self.__hp = max(1, min(self.__max_hp, data.get("hp", self.__max_hp)))

        self.__max_mana = data.get("max_mana", self.__max_mana)
        self.__mana = min(self.__max_mana, data.get("mana", self.__max_mana))

        self.__base_attack = data.get("base_attack", self.__base_attack)
        self.__base_defense = data.get("base_defense", self.__base_defense)
        self.__base_crit = data.get("base_crit", self.__base_crit)

        # Les bonus des compétences sont déjà compris dans les statistiques sauvegardées.
        self.__skill_points = data.get("skill_points", 0)
        self.__unlocked_skills = set(data.get("unlocked_skills", []))


class mobs:
    def __init__(self, hp, atk, speed, crit, col):
        self.hp = hp
        self.atk = atk
        self.speed = speed
        self.crit = crit
        self.color = col


# TODO

# Niveau 1 : Faibles
slime = mobs(50, 5, 2, 5, (180, 40, 40))
gobelin = mobs(80, 10, 4, 8, (100, 20, 20))
rat_geant = mobs(40, 8, 8, 10, (150, 50, 50))

# Niveau 2 : Normaux
squelette = mobs(150, 20, 5, 12, (120, 120, 120))
loup = mobs(120, 25, 10, 15, (100, 100, 100))
orc = mobs(250, 30, 3, 10, (150, 150, 150))

# Niveau 3 : Puissants
troll = mobs(500, 45, 4, 15, (200, 200, 200))
assassin = mobs(300, 60, 15, 25, (50, 50, 50))
golem = mobs(800, 50, 2, 5, (100, 100, 100))

# Niveau 4 : Élite
chevalier_noir = mobs(1200, 80, 8, 20, (50, 50, 50))
demon = mobs(1000, 100, 12, 30, (200, 0, 0))
dragonnet = mobs(1500, 120, 10, 25, (255, 165, 0))


# 20 instances de Skill, dont 4 utilisées par le jeu.
SKILLS = [
    Skill("Frappe rapide", 25, 10, 2),
    Skill("Lame fantôme", 40, 25, 6),
    Skill("Soin", 0, 30, 10),
    Skill("Explosion obscure", 65, 50, 15),
]
for n in range(16):
    SKILLS.append(Skill(f"Compétence catalogue {n + 1}", 0, 0, 0))


BRANCHES = {
    "FORCE":  {"label": "FORCE",  "color": (225, 85, 75),   "cx": 0.20},
    "MAGIE":  {"label": "MAGIE",  "color": (90, 135, 245),  "cx": 0.50},
    "SURVIE": {"label": "SURVIE", "color": (80, 200, 125),  "cx": 0.80},
}
BRANCH_ORDER = ("FORCE", "MAGIE", "SURVIE")


def _skill(name, branch, row, lane, cost, requires, flavor, **effects):
    return {
        "name": name, "branch": branch, "row": row, "lane": lane,
        "cost": cost, "requires": requires, "flavor": flavor,
        "effects": effects,
    }


SKILL_TREE = {
    # ---------------- FORCE ----------------
    "force_1": _skill("Puissance I", "FORCE", 0, 0, 2, None,
                      "Les premiers pas d'un véritable guerrier.", attack=10),
    "force_2": _skill("Puissance II", "FORCE", 1, 0, 3, "force_1",
                      "Chaque coup résonne plus fort que le précédent.", attack=15),
    "critique": _skill("Précision", "FORCE", 2, -1, 2, "force_2",
                       "Viser les failles de l'armure adverse.", crit=5),
    "rage": _skill("Rage guerrière", "FORCE", 2, 1, 2, "force_2",
                   "La colère guide ta lame.", attack=10),
    "oeil_faucon": _skill("Œil de faucon", "FORCE", 3, -1, 3, "critique",
                          "Rien n'échappe à ton regard.", crit=8),
    "fureur": _skill("Fureur", "FORCE", 3, 1, 3, "rage",
                     "Une tempête d'acier s'abat sur tes ennemis.", attack=15),
    "maitre_armes": _skill("Maître d'armes", "FORCE", 4, 0, 5, ("oeil_faucon", "fureur"),
                           "L'aboutissement de la voie du guerrier.", attack=20, crit=5),

    # ---------------- MAGIE ----------------
    "mana_1": _skill("Réserve magique", "MAGIE", 0, 0, 2, None,
                     "Une source d'énergie s'éveille en toi.", mana=25),
    "magie_1": _skill("Maîtrise magique", "MAGIE", 1, 0, 2, "mana_1",
                      "Tes sortilèges gagnent en puissance.", attack=10),
    "mana_2": _skill("Énergie supérieure", "MAGIE", 2, -1, 3, "magie_1",
                     "Ta réserve devient un véritable océan.", mana=25),
    "arcane": _skill("Savoir arcanique", "MAGIE", 2, 1, 2, "magie_1",
                     "Les anciens grimoires n'ont plus de secret.", attack=10, crit=3),
    "source": _skill("Source infinie", "MAGIE", 3, -1, 3, "mana_2",
                     "L'énergie coule en toi sans jamais tarir.", mana=40),
    "sorcellerie": _skill("Sorcellerie", "MAGIE", 3, 1, 3, "arcane",
                          "Plier le réel à ta volonté.", attack=15),
    "archimage": _skill("Archimage", "MAGIE", 4, 0, 5, ("source", "sorcellerie"),
                        "Le sommet de l'art magique.", attack=15, mana=50),

    # ---------------- SURVIE ----------------
    "vitalite": _skill("Vitalité", "SURVIE", 0, 0, 2, None,
                       "Ton corps s'endurcit face à la douleur.", hp=20),
    "armure": _skill("Armure renforcée", "SURVIE", 1, 0, 2, "vitalite",
                     "Un maillage plus serré protège ta chair.", defense=10),
    "forteresse": _skill("Forteresse", "SURVIE", 2, -1, 3, "armure",
                         "Rien ne perce ta garde.", defense=20),
    "constitution": _skill("Constitution", "SURVIE", 2, 1, 2, "armure",
                           "Une santé de fer.", hp=30),
    "rempart": _skill("Rempart", "SURVIE", 3, -1, 3, "forteresse",
                      "Tu deviens un mur infranchissable.", defense=20),
    "titan": _skill("Titan", "SURVIE", 3, 1, 3, "constitution",
                    "Une vigueur hors du commun.", hp=50),
    "immortel": _skill("Immortel", "SURVIE", 4, 0, 5, ("rempart", "titan"),
                       "Seule la légende peut t'abattre.", hp=60, defense=20),

    # ---------------- SORTS ----------------
        # SORTS DE COMBAT

    "sort_frappe": _skill(
        "Frappe rapide", "FORCE", 2, 0, 2, "force_2",
        "Une attaque magique rapide contre les ennemis.",
        spell="Frappe rapide"
    ),

    "sort_soin": _skill(
        "Soin", "SURVIE", 2, 0, 2, "armure",
        "Restaure une partie de tes points de vie.",
        spell="Soin"
    ),

    "sort_explosion": _skill(
        "Explosion obscure", "MAGIE", 4, 1, 4, "sorcellerie",
        "Libère une puissante explosion d'énergie obscure.",
        spell="Explosion obscure"
    ),

    "sort_lame": _skill(
    "Lame fantôme", "FORCE", 3, 0, 3, "sort_frappe",
    "Débloque la technique de la lame fantôme.",
    spell="Lame fantôme"
    ),
}

SKILL_MAX_ROW = max(d["row"] for d in SKILL_TREE.values())

# (clé d'effet, suffixe, libellé, étiquette courte, couleur)
SKILL_STATS = [
    ("attack", "", "attaque", "ATK", RED_LIGHT),
    ("defense", "", "défense", "DEF", BLUE),
    ("crit", "%", "coups critiques", "CRT", PURPLE),
    ("hp", "", "PV maximum", "PV", (225, 95, 95)),
    ("mana", "", "mana maximum", "MP", MANA_BLUE),
]


def skill_requirements(skill_id):
    """Renvoie toujours un tuple d'ids requis (vide si aucun)."""
    req = SKILL_TREE[skill_id]["requires"]
    if req is None:
        return ()
    if isinstance(req, str):
        return (req,)
    return tuple(req)


def skill_effect_lines(data):
    lines = []
    for key, suffix, label, _tag, color in SKILL_STATS:
        value = data["effects"].get(key, 0)
        if value:
            lines.append((f"+{value}{suffix} {label}", color))
    return lines


def skill_main_tag(data):
    for key, _suffix, _label, tag, _color in SKILL_STATS:
        if data["effects"].get(key, 0):
            return tag

    if data["effects"].get("spell"):
        return "SORT"

    return "?"


# 20 slots réels : la grille et la barre rapide peuvent les utiliser.
SLOTS = [Slot(i) for i in range(20)]

# 20 inventaires : un actif et 19 profils de réserve.
INVENTORIES = [Inventory(ITEMS[:9])] + [Inventory() for _ in range(19)]

# 20 joueurs : un actif et 19 profils de réserve.
PLAYERS = [Player(INVENTORIES[0])] + [Player(INVENTORIES[i]) for i in range(1, 20)]


class Game(WorldMixin, arcade.Window):
    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            TITLE,
            fullscreen=True,
            vsync=True
        )

        self._text_cache = {}      # cache des textes (voir méthode text)

        # Le jeu démarre sur le menu principal
        self.state = STATE_MENU
        self.menu_selection = 0
        self.menu_options = ["Nouvelle partie", "Charger la partie", "Quitter"]
        self.menu_message = ""      # message d'erreur affiché dans le menu

        # --- Animation des menus ---
        self.ui_time = 0.0            # temps total (pour les pulsations)
        self.state_time = 0.0         # temps écoulé depuis le dernier changement d'écran
        self._ui_prev_key = None      # sert à détecter un changement d'écran
        self.cursor_pos = 0.0         # position animée de la barre lumineuse
        self.particles = []
        self.init_particles()

        self.background_color = BG
        self.__window_title = TITLE
        self.__profile_name = "Partie principale"

        self.player = PLAYERS[0]
        self.inventory = self.player.get_inventory()
        self.player.set_x(0)
        self.player.set_y(0)

        # Objet à ramasser sur la carte
        self.objet_sol = ITEMS[3]  # Arc légendaire
        self.objet_sol_x = 300
        self.objet_sol_y = 200

        # Les monstres viennent maintenant du niveau (voir levels.py / world.py)

        self.facing = 1            # 1 = droite, -1 = gauche
        self.attack_cooldown = 0
        self.slash_timer = 0
        self.arrows = []

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.keys = set()
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_duration = 0.18
        self.dash_recharge = 3.0
        self.dash_speed = 1425.0

        # Saut : SPACE permet de sauter sur place ou dans la direction du déplacement.
        self.jump_timer = 0.0
        self.jump_duration = 0.45
        self.jump_height = 0.0
        self.jump_max_height = 85.0
        self.jump_dx = 0.0
        self.jump_dy = 0.0

        self.inventory_open = False
        self.category = "Arme"

        # Fenêtre de l'arbre de compétences
        self.skill_tree_open = False
        self.selected_skill = None

        self.pause_open = False
        self.pause_selection = 0
        self.settings_open = False

        # Statistiques de la partie
        self.play_time = 0.0
        self.death_count = 0
        self.mobs_killed = 0

        # Écran Game Over
        self.game_over_selection = 0

        self.pause_options = ["Reprendre", "Paramètres", "Menu principal", "Quitter"]

        self.hover_item = None
        self.selected_item = None
        self.equipped_weapon = None
        self.active_weapon_slot = None

        # Les 9 cases de la barre rapide
        self.hotbar = [None] * 9

        # Ressources affichées dans l'interface de jeu
        self.mana = 100
        self.max_mana = 100
        self.stamina = 100
        self.max_stamina = 100
        self.inventory.set_category(self.category)

        self.mouse_x = 0
        self.mouse_y = 0

        # Épée : on utilise directement l'image fournie.
        if not SWORD_PATH.exists():
            raise FileNotFoundError(
                f"Image introuvable : {SWORD_PATH}\n"
                "Vérifie que le dossier 'weapons' est bien à côté de main.py."
            )

        self.sword_sprite = arcade.Sprite(str(SWORD_PATH))

        # Si l'image basique manque, on utilise l'épée principale comme repli.
        sword_bas_path = SWORD_BAS_PATH
        if not sword_bas_path.exists():
            if SWORD_PATH.exists():
                sword_bas_path = SWORD_PATH
            else:
                raise FileNotFoundError(
                    f"Image introuvable : {SWORD_BAS_PATH}\n"
                    "Vérifie que le fichier epee_basique.png est dans le dossier 'weapons'."
                )

        self.sword_bas_sprite = arcade.Sprite(str(sword_bas_path))

        if not ARCLEG_PATH.exists():
            raise FileNotFoundError(
                f"Image introuvable : {ARCLEG_PATH}\n"
                "Vérifie que le dossier 'weapons' contient arc_legendaire.png."
            )
        self.arcleg_sprite = arcade.Sprite(str(ARCLEG_PATH))

        # Taille des armes dans la grille.
        self.inventory_sword_width = 58
        self.inventory_sword_bas_width = 58
        self.inventory_arcleg_width = 43

        # Taille de l'épée quand elle est équipée sur le personnage :
        # beaucoup plus grande que dans l'inventaire.
        self.character_sword_width = 175
        self.character_sword_bas_width = 175
        self.character_arcleg_width = 80
        self.set_minimum_size(900, 600)

        self.equipped_shield = None

        # Emplacements d'équipement 
        self.equipment_slots = ["weapon", "shield", "helmet", "armor"]
        self.equipment_labels = {
            "weapon": "ARME",
            "shield": "BOUCLIER",
            "helmet": "CASQUE",
            "armor": "ARMURE",
        }

        self.message = ""
        self.message_timer = 0

        self.init_world()           # monde side-scroller (game_world.py)

    # -----------------------------------------------------
    # OUTILS
    # -----------------------------------------------------
    def get_stats(self):
        return self.player.get_stats()

    def box(self, left, right, bottom, top, color):
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top, color
        )

    def outline(self, left, right, bottom, top, color, width=2):
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top, color, width
        )

    def text(self, value, x, y, size=12, color=TEXT, anchor_x="left", anchor_y="center", font=None, bold=False, italic=False):
        key = (value, size, color, anchor_x, anchor_y, font, bold, italic)
        t = self._text_cache.get(key)
        if t is None:
            if len(self._text_cache) > 600:      # évite que le cache grossisse sans fin
                self._text_cache.clear()
            extra = {"font_name": font} if font is not None else {}
            t = arcade.Text(str(value), x, y, color, size,
                            anchor_x=anchor_x, anchor_y=anchor_y,
                            bold=bold, italic=italic, **extra)
            self._text_cache[key] = t
        t.x = x
        t.y = y
        t.draw()

    def diamond(self, x, y, size=12):
        points = [
            (x, y + size),
            (x + size, y),
            (x, y - size),
            (x - size, y),
        ]

        arcade.draw_polygon_filled(points, RED)
        arcade.draw_polygon_outline(points, GOLD_LIGHT, 2)

    def decorative_frame(self, left, right, bottom, top):
        self.box(left, right, bottom, top, PANEL)

        self.outline(left, right, bottom, top, GOLD_DARK, 6)
        self.outline(
            left + 7,
            right - 7,
            bottom + 7,
            top - 7,
            GOLD,
            2,
        )

        s = 18
        for x, y in [
            (left + 5, bottom + 5),
            (left + 5, top - 5),
            (right - 5, bottom + 5),
            (right - 5, top - 5),
        ]:
            self.diamond(x, y, s)

    def get_equipped(self, slot_name):
        """Renvoie l'objet équipé dans un emplacement (ou None)."""
        if slot_name == "weapon":
            return self.equipped_weapon
        if slot_name == "shield":
            return self.equipped_shield
        return None   # casque / armure : pas encore d'objets

    def weapon_hotbar_index(self, item):
        if item.get_type() != "Arme":
            return None
        if item.get_icon() in ("sword", "sword_bas"):
            return 0
        if item.get_icon() in ("arcbas", "arcleg"):
            return 1
        return None

    def select_hotbar_weapon(self, index):
        item = self.hotbar[index]
        if item is None or self.weapon_hotbar_index(item) != index:
            self.show_message("Aucune arme dans cet emplacement")
            return
        self.equipped_weapon = item
        self.player.set_equipped_weapon(item)
        self.active_weapon_slot = index
        self.show_message(f"{item.get_name().strip()} sélectionnée")

    def start_dash(self):
        if self.state != STATE_GAME or self.dash_cooldown > 0:
            return
        stamina_cost = self.max_stamina * 0.25
        if self.stamina < stamina_cost:
            self.show_message("Pas assez d'endurance pour dasher")
            return
        self.stamina -= stamina_cost
        self.dash_timer = self.dash_duration
        self.dash_cooldown = self.dash_recharge
        self.body.knock_t = 0.0

    def equipment_slot_rects(self):
        """Position des 4 cases d'équipement : (nom, gauche, bas, droite, haut)."""
        left = self.width * 0.06
        top = self.height * 0.92
        upper_bottom = self.height * 0.50
        char_bottom = upper_bottom + 30
        char_top = top - 75

        gap_eq = 10
        size = min(58, (char_top - char_bottom - 3 * gap_eq) / 4)
        sx = left + 28

        rects = []
        for i, name in enumerate(self.equipment_slots):
            y_top = char_top - i * (size + gap_eq)
            rects.append((name, sx, y_top - size, sx + size, y_top))
        return rects

    # -----------------------------------------------------
    # EFFETS DE MENU
    # -----------------------------------------------------
    def init_particles(self, count=28):
        self.particles = []
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(0, self.width),
                "y": random.uniform(0, self.height),
                "speed": random.uniform(10, 38),
                "size": random.uniform(1.2, 3.0),
                "phase": random.uniform(0, 6.28),
                "gold": random.random() < 0.5,
            })

    def ui_update(self, dt):
        """Appelée à chaque image, même dans les menus."""
        self.ui_time += dt
        self.state_time += dt

        # Quelle option est sélectionnée sur l'écran actuel ?
        if self.state == STATE_MENU:
            target = self.menu_selection
        elif self.state == STATE_GAME_OVER:
            target = self.game_over_selection
        elif self.pause_open:
            target = self.pause_selection
        else:
            target = 0

        # Changement d'écran : on relance les animations
        key = (self.state, self.pause_open)
        if key != self._ui_prev_key:
            self._ui_prev_key = key
            self.state_time = 0.0
            self.cursor_pos = float(target)
        else:
            # la barre lumineuse glisse en douceur vers l'option choisie
            self.cursor_pos += (target - self.cursor_pos) * min(1.0, 14 * dt)

        # Particules : montent lentement en ondulant
        for p in self.particles:
            p["y"] += p["speed"] * dt
            p["x"] += math.sin(self.ui_time * 0.8 + p["phase"]) * 14 * dt
            if p["y"] > self.height + 10:
                p["y"] = -10
                p["x"] = random.uniform(0, self.width)

    def draw_particles(self, tint=None):
        for p in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.ui_time * 2.0 + p["phase"] * 3)
            alpha = int(50 + 170 * flicker)

            if tint is not None:
                base = tint
            elif p["gold"]:
                base = GOLD_LIGHT
            else:
                base = (190, 205, 230)       # lueur pâle façon Hollow Knight

            if p["gold"] or tint is not None:
                arcade.draw_circle_filled(p["x"], p["y"], p["size"] * 3, (*base, alpha // 7))
            arcade.draw_circle_filled(p["x"], p["y"], p["size"], (*base, alpha))

    def draw_vignette(self, strength=170):
        """Assombrit les bords de l'écran avec des cadres de plus en plus transparents."""
        w, h = self.width, self.height
        step = 50
        layers = 5
        for i in range(layers):
            alpha = int(strength * (1 - i / layers) ** 2)
            inset = i * step + step / 2
            self.outline(inset, w - inset, inset, h - inset, (0, 0, 0, alpha), step)

    def shadow_text(self, value, x, y, size, color, anchor_x="center",
                    font=FONT_TITLE, bold=False, italic=False):
        self.text(value, x + 2, y - 2, size, (0, 0, 0, 220),
                  anchor_x=anchor_x, font=font, bold=bold, italic=italic)
        self.text(value, x, y, size, color,
                  anchor_x=anchor_x, font=font, bold=bold, italic=italic)

    def ornament_diamond(self, x, y, size, fill=GOLD_LIGHT, edge=GOLD_DARK):
        points = [
            (x, y + size),
            (x + size, y),
            (x, y - size),
            (x - size, y),
        ]
        arcade.draw_polygon_filled(points, fill)
        arcade.draw_polygon_outline(points, edge, 1)

    def draw_fade_line(self, cx, y, half, color, alpha, inner=0, steps=8):
        """Ligne horizontale qui s'efface du centre vers les extrémités."""
        for i in range(steps):
            t0 = i / steps
            t1 = (i + 1) / steps
            a = int(alpha * (1 - t0) ** 1.5)
            x0 = inner + half * t0
            x1 = inner + half * t1
            arcade.draw_line(cx + x0, y, cx + x1, y, (*color, a), 1)
            arcade.draw_line(cx - x0, y, cx - x1, y, (*color, a), 1)

    def draw_divider(self, cx, y, half=230, color=GOLD, alpha=210):
        """Séparateur ornemental : filets qui s'effacent + trois losanges."""
        self.draw_fade_line(cx, y, half, color, alpha, inner=16)
        self.ornament_diamond(cx, y, 7)
        self.ornament_diamond(cx - 24, y, 3)
        self.ornament_diamond(cx + 24, y, 3)

    def draw_menu_panel(self, left, right, bottom, top):
        """Cadre sombre à double filet doré et losanges aux angles."""
        cx = (left + right) / 2
        self.box(left, right, bottom, top, (7, 8, 12, 225))
        self.outline(left, right, bottom, top, GOLD_DARK, 2)
        self.outline(left + 8, right - 8, bottom + 8, top - 8, (*GOLD, 110), 1)

        for x, y in ((left, bottom), (left, top), (right, bottom), (right, top)):
            self.ornament_diamond(x, y, 9, GOLD, GOLD_DARK)
        self.ornament_diamond(cx, top, 6)
        self.ornament_diamond(cx, bottom, 6)

    def draw_menu_options(self, options, selection, cx, start_y, spacing,
                          size=22, disabled=(), accent=(212, 160, 70),
                          sel_color=(246, 218, 150)):
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 3.0)
        bar_y = start_y - self.cursor_pos * spacing

        # Halo qui glisse d'une option à l'autre (couches très transparentes empilées)
        for k in range(4):
            half = 300 - k * 70
            self.box(cx - half, cx + half, bar_y - 24, bar_y + 24, (*accent, 6))

        # Filets fins au-dessus et en dessous
        self.draw_fade_line(cx, bar_y + 26, 230, accent, 150, steps=6)
        self.draw_fade_line(cx, bar_y - 26, 230, accent, 150, steps=6)

        # Losanges qui pulsent de part et d'autre
        off = 150 + 5 * pulse
        self.ornament_diamond(cx - off, bar_y, 6, accent)
        self.ornament_diamond(cx + off, bar_y, 6, accent)

        # Textes
        for i, option in enumerate(options):
            y = start_y - i * spacing
            is_sel = i == selection
            is_off = i in disabled

            if is_off:
                color = (110, 106, 100) if is_sel else (74, 72, 70)
            elif is_sel:
                color = sel_color
            else:
                color = (150, 146, 138)

            self.shadow_text(option, cx, y, size + (2 if is_sel else 0), color)

    def draw_menu_backdrop(self):
        w, h = self.width, self.height

        # 1) Dégradé vertical : abysse froide
        steps = 16
        band = h / steps
        top_c = (20, 26, 38)
        bot_c = (3, 4, 7)
        for i in range(steps):
            r = i / (steps - 1)
            color = (
                int(bot_c[0] + (top_c[0] - bot_c[0]) * r),
                int(bot_c[1] + (top_c[1] - bot_c[1]) * r),
                int(bot_c[2] + (top_c[2] - bot_c[2]) * r),
            )
            self.box(0, w, i * band, (i + 1) * band + 1, color)

        # 2) Halo doré en haut (l'Arbre-Monde au loin), qui respire
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 0.9)
        for k in range(4):
            r = 60 + k * 114
            arcade.draw_ellipse_filled(
                w / 2, h * 0.78, r * 2.2, r * 1.5,
                (230, 181, 88, int(3 + 2 * pulse)),
            )

        # 3) Piliers en ruine (silhouettes)
        for fx, pw, hf in ((0.10, 90, 0.88), (0.24, 54, 0.70),
                           (0.76, 54, 0.70), (0.90, 90, 0.88)):
            px = w * fx
            top_y = h * hf
            col = (6, 8, 12)
            self.box(px - pw / 2, px + pw / 2, 0, top_y, col)
            arcade.draw_triangle_filled(
                px - pw / 2, top_y,
                px + pw / 2, top_y,
                px, top_y + pw * 1.3,
                col,
            )
            arcade.draw_line(px - pw / 2, 0, px - pw / 2, top_y, (26, 32, 46), 1)
            arcade.draw_line(px + pw / 2, 0, px + pw / 2, top_y, (26, 32, 46), 1)

        # 4) Brume qui dérive lentement
        for k in range(3):
            mx = w / 2 + math.sin(self.ui_time * 0.15 + k * 2.1) * w * 0.25
            my = h * (0.18 + 0.12 * k)
            arcade.draw_ellipse_filled(mx, my, w * 0.9, 90 + 40 * k, (120, 135, 160, 9))

    # -----------------------------------------------------
    # COMBAT
    # -----------------------------------------------------
    def show_message(self, text, duration=1.5):
        self.message = text
        self.message_timer = duration

    def reset_monsters(self):
        """Remet les monstres à leur position de départ (feu de camp / mort)."""
        self.world_reset_mobs()

    def item_catalog(self):
        return ITEMS

    def clone_item(self, it):
        return Item(it.get_name(), it.get_type(), it.get_icon(), it.get_attack(), it.get_defense(),
                    it.get_crit(), it.get_weight(), it.get_description(),
                    item_id=it.get_id(), kind=it.get_kind())

    def use_item(self, item):
        icon = item.get_icon()
        if icon == "potion":
            self.player.heal(40)
        elif icon == "mana":
            self.player.regen_mana(30)
        else:
            return
        items = self.inventory.get_items()
        if item in items:
            items.remove(item)                   # potion consommée
        self.hotbar = [None if h == item else h for h in self.hotbar]
        self.show_message(f"{item.get_name().strip()} utilisée")

    def use_potion_by_icon(self, icon):
        for it in self.inventory.get_items():
            if it.get_icon() == icon:
                self.use_item(it)
                return
        self.show_message("Aucune potion !")

    def use_skill(self, index):
        skill_unlock_ids = {
            0: "sort_frappe",
            1: "sort_lame",
            2: "sort_soin",
            3: "sort_explosion",
        }
        unlock_id = skill_unlock_ids.get(index)
        if unlock_id and not self.player.has_skill(unlock_id):
            self.show_message("Sort verrouillé : débloque-le dans l'arbre !")
            return

        skill = SKILLS[index]
        if not self.player.use_mana(skill.get_cost()):
            self.show_message("Pas assez de mana")
            return
        if skill.get_name() == "Soin":
            self.player.heal(skill.get_defense())
            self.show_message("Soin +30 PV")
        else:
            for m in self.monsters:
                if not m.alive:
                    continue
                dx = m.x - self.player.get_x()
                dy = m.y - self.player.get_y()
                if (dx ** 2 + dy ** 2) ** 0.5 < 250:
                    self.damage_mob(m, skill.get_attack())
            self.show_message(skill.get_name())

    def compute_damage(self):
        attack, defense, crit = self.get_stats()
        damage = attack
        if random.randint(1, 100) <= crit:
            damage = int(damage * 1.3)
        return damage

    def attack(self):
        if self.attack_cooldown > 0:
            return
        if self.equipped_weapon is None:
            print("Équipe une arme dans l'inventaire (TAB) !")
            return
        if self.stamina < 10:
            print("Pas assez d'endurance !")
            return
        self.stamina = max(0, self.stamina - 10)

        icon = self.equipped_weapon.get_icon()
        px, py = self.player.get_x(), self.player.get_y()

        # ÉPÉE : coup au corps à corps devant le joueur
        if icon in ("sword", "sword_bas"):
            self.attack_cooldown = 0.4
            self.slash_timer = 0.15
            for m in self.monsters:
                if not m.alive:
                    continue
                dx = m.x - px
                dy = m.y - py
                if dx * self.facing > -30 - m.w / 2 and abs(dx) < 120 + m.w / 2 and abs(dy) < 60 + m.h / 2:
                    self.damage_mob(m, self.compute_damage())

        # ARC : tire une flèche vers la souris
        elif icon in ("arcbas", "arcleg"):
            self.attack_cooldown = 0.7

            # Convertit les coordonnées écran en coordonnées du monde
            mouse_world_x = self.cam_x + self.mouse_x - self.width / 2
            mouse_world_y = self.cam_y + self.mouse_y - self.height / 2

            dx = mouse_world_x - px
            dy = mouse_world_y - (py + 5)

            distance = max((dx**2 + dy**2)**0.5, 1)

            self.arrows.append({
                "x": px,
                "y": py + 5,
                "dir_x": dx / distance,
                "dir_y": dy / distance,
                "dist": 0,
                "damage": self.compute_damage(),
            })

    def damage_mob(self, m, damage):
        if not m.alive:
            return
        m.hp -= damage
        m.on_hit(1 if m.x >= self.player.get_x() else -1)
        if m.hp <= 0 and m.alive:
            m.hp = 0
            m.alive = False
            m.respawn_timer = m.respawn_time
            self.mobs_killed += 1
            self.player.gain_xp(int(m.xp * (1 if m.is_boss else self.rt.scale)))
            msg = self.rt.on_monster_killed(m)          # boss : herse, porte, phase 2...
            if msg:
                self.show_message(msg, 3.0)
                self.sync_progress()

    def update_combat(self, delta_time):
        self.attack_cooldown = max(0, self.attack_cooldown - delta_time)
        self.slash_timer = max(0, self.slash_timer - delta_time)

        # Réapparition des monstres
        for m in self.monsters:
            if not m.alive:
                m.respawn_timer -= delta_time
                if m.respawn_timer <= 0:
                    m.alive = True
                    m.hp = m.max_hp
                    m.x = m.start_x
                    m.y = m.start_y

        # Flèches
        for arrow in self.arrows[:]:
            move = 700 * delta_time
            arrow["x"] += arrow["dir_x"] * move
            arrow["y"] += arrow["dir_y"] * move
            arrow["dist"] += move

            touched = False
            for m in self.monsters:
                if (
                    m.alive
                    and abs(arrow["x"] - m.x) < 15 + m.w / 2
                    and abs(arrow["y"] - m.y) < 15 + m.h / 2
                ):
                    self.damage_mob(m, arrow["damage"])
                    touched = True
                    break

            if self.rt is not None and self.rt.level.kind_at(
                    int(arrow["x"] // TILE), int(arrow["y"] // TILE)) in SOLID_KINDS:
                touched = True                     # la flèche s'arrête dans les murs

            if touched or arrow["dist"] > 700:
                self.arrows.remove(arrow)

    def draw_combat_effects(self):
        px, py = self.player.get_x(), self.player.get_y()

        # Arc de cercle du coup d'épée
        if self.slash_timer > 0:
            start, end = (-45, 45) if self.facing == 1 else (135, 225)
            arcade.draw_arc_outline(px, py + 5, 220, 220,
                                    GOLD_LIGHT, start, end, 6)

        # Flèches
        for arrow in self.arrows:
            arcade.draw_line(
                arrow["x"] - arrow["dir_x"] * 20,
                arrow["y"] - arrow["dir_y"] * 20,
                arrow["x"] + arrow["dir_x"] * 20,
                arrow["y"] + arrow["dir_y"] * 20,
                GOLD_LIGHT,
                3,
            )

            arcade.draw_circle_filled(
                arrow["x"] + arrow["dir_x"] * 20,
                arrow["y"] + arrow["dir_y"] * 20,
                4,
                RED_LIGHT,
            )

    def on_update(self, delta_time):

        self.ui_update(delta_time)

        if self.state == STATE_MENU or self.state == STATE_GAME_OVER:
            return

        # Le temps augmente pendant la partie, mais pas dans les menus ou la pause.
        if not self.pause_open and not self.settings_open:
            self.play_time += delta_time

        if self.inventory_open:
            return

        if self.pause_open or self.settings_open:
            return

        # Déplacement, gravité, monstres, boss : voir game_world.py / world.py
        self.update_world(delta_time)

    def on_draw(self):
        self.clear()

        # MENU PRINCIPAL : on dessine uniquement lui
        if self.state == STATE_MENU:
            self.gui_camera.use()
            self.draw_main_menu()
            return

        self.draw_background()

        if not self.inventory_open:
            self.draw_game()

        self.gui_camera.use()

        # Interface de jeu uniquement pendant la partie : jamais sur l'inventaire
        # ni sur le menu pause, pour ne pas recouvrir ces écrans.
        if (
            not self.inventory_open
            and not self.pause_open
            and not self.skill_tree_open
            and self.state != STATE_GAME_OVER
        ):
            self.draw_hud()
            self.draw_world_ui()

        if self.inventory_open:
            self.draw_inventory()
        if self.pause_open:
            self.draw_pause_menu()
        if self.settings_open:
            self.draw_settings()
        if self.skill_tree_open:
            self.draw_skill_tree()
        if self.state == STATE_GAME_OVER:
            self.draw_game_over()

    def get_skill_node_positions(self):
        """Place les compétences selon leur branche, leur palier et leur couloir."""
        branch_x = {"FORCE": 245, "MAGIE": 640, "SURVIE": 1035}
        positions = {}
        for skill_id, data in SKILL_TREE.items():
            x = branch_x[data["branch"]] + data["lane"] * 58
            y = 555 - data["row"] * 100
            positions[skill_id] = (x, y)
        return positions

    def draw_skill_tree(self):
        """Affiche les trois branches complètes de compétences."""
        self.box(20, self.width - 20, 20, self.height - 20, (8, 10, 18, 248))
        self.outline(20, self.width - 20, 20, self.height - 20, (105, 88, 55), 3)
        self.text("ARBRE DE COMPÉTENCES", self.width / 2, self.height - 48,
                  24, (238, 202, 125), anchor_x="center", bold=True)
        self.text(f"Points disponibles : {self.player.get_skill_points()}",
                  self.width / 2, self.height - 78, 12, (220, 220, 230),
                  anchor_x="center")
        self.text("O ou ÉCHAP pour fermer", self.width - 45, self.height - 48,
                  10, (155, 160, 175), anchor_x="right")

        positions = self.get_skill_node_positions()
        branch_colors = {
            "FORCE": (220, 85, 75),
            "MAGIE": (85, 145, 235),
            "SURVIE": (85, 190, 125),
        }
        for branch, x in (("FORCE", 245), ("MAGIE", 640), ("SURVIE", 1035)):
            self.text(branch, x, 585, 14, branch_colors[branch],
                      anchor_x="center", bold=True)

        for skill_id, data in SKILL_TREE.items():
            x2, y2 = positions[skill_id]
            for required_id in skill_requirements(skill_id):
                if required_id not in positions:
                    continue
                x1, y1 = positions[required_id]
                line_color = branch_colors[data["branch"]] if self.player.has_skill(skill_id) else (65, 68, 80)
                arcade.draw_line(x1, y1, x2, y2, line_color, 3)

        for skill_id, data in SKILL_TREE.items():
            x, y = positions[skill_id]
            status = self.player.get_skill_status(skill_id)
            unlocked = status == "unlocked"
            selected = self.selected_skill == skill_id
            color = branch_colors[data["branch"]]
            if unlocked:
                fill, border = color, (245, 230, 185)
            elif selected:
                fill, border = (65, 68, 88), (245, 205, 115)
            else:
                fill, border = (28, 31, 43), (95, 100, 115)
            arcade.draw_circle_filled(x, y, 23, fill)
            arcade.draw_circle_outline(x, y, 26, border, 2)
            self.text("OK" if unlocked else str(data["cost"]), x, y - 4, 12,
                      (255, 255, 255), anchor_x="center", bold=True)
            self.text(data["name"], x, y - 34, 8, (225, 225, 235),
                      anchor_x="center")

        self.box(45, self.width - 45, 28, 105, (19, 22, 32, 252))
        self.outline(45, self.width - 45, 28, 105, (85, 91, 110), 2)
        if self.selected_skill is None:
            self.text("Clique sur une compétence pour voir ses détails.",
                      self.width / 2, 76, 12, (190, 195, 210),
                      anchor_x="center")
            self.text("Chaque niveau donne 1 point ; tous les 10 niveaux donnent 2 points bonus.",
                      self.width / 2, 50, 9, (145, 152, 170),
                      anchor_x="center")
            return

        data = SKILL_TREE[self.selected_skill]
        status = self.player.get_skill_status(self.selected_skill)
        effects = skill_effect_lines(data)
        self.text(data["name"], 65, 82, 13, (238, 202, 125), bold=True)
        self.text(data["flavor"], 65, 60, 9, (220, 220, 230))
        effect_text = " | ".join(line for line, _color in effects) or "Compétence spéciale"
        self.text(effect_text, 65, 42, 9, (180, 195, 220))

        if status == "unlocked":
            status_text, button_text, button_color = "Déjà débloquée", "DÉBLOQUÉE", (45, 75, 55)
        elif status == "locked":
            status_text, button_text, button_color = "Prérequis manquant", "VERROUILLÉE", (55, 55, 60)
        elif status == "no_points":
            status_text, button_text, button_color = "Pas assez de points", "PAS ASSEZ DE POINTS", (70, 45, 45)
        else:
            status_text, button_text, button_color = "Compétence disponible", "DÉBLOQUER", (45, 85, 60)

        self.text(f"Coût : {data['cost']} points", self.width - 390, 79,
                  9, (170, 180, 200))
        self.text(status_text, self.width - 390, 57, 9, (205, 210, 220))
        left, right = self.width - 230, self.width - 65
        self.box(left, right, 42, 88, button_color)
        self.outline(left, right, 42, 88, (190, 170, 115), 2)
        self.text(button_text, (left + right) / 2, 60, 8,
                  (255, 255, 245), anchor_x="center", bold=True)

    def draw_hud(self):
        """Interface affichée uniquement pendant le jeu."""
        # -------------------- PERSONNAGE EN HAUT À GAUCHE --------------------
        panel_left, panel_bottom = 18, self.height - 145
        panel_right, panel_top = 300, self.height - 18
        self.box(panel_left, panel_right, panel_bottom, panel_top, (13, 15, 21, 235))
        self.outline(panel_left, panel_right, panel_bottom, panel_top, GOLD_DARK, 2)

        # Petit portrait géométrique du personnage
        arcade.draw_circle_filled(52, self.height - 52, 17, (190, 190, 198))
        arcade.draw_circle_outline(52, self.height - 52, 18, GOLD_LIGHT, 2)
        self.box(39, 65, self.height - 105, self.height - 72, (83, 87, 98))
        self.outline(39, 65, self.height - 105, self.height - 72, (130, 132, 142), 1)

        self.text("HÉROS", 78, self.height - 38, 13, GOLD_LIGHT)
        self.text(f"Niveau {self.player.get_level()}", 78, self.height - 59, 12, TEXT)

        # Barre de vie réelle du joueur
        hp_ratio = max(0, min(1, self.player.get_hp() / max(1, self.player.get_max_hp())))
        self.text("PV", 78, self.height - 83, 10, TEXT_DARK)
        self.box(108, 280, self.height - 91, self.height - 77, (55, 18, 22))
        if hp_ratio > 0:
            self.box(108, 108 + 172 * hp_ratio, self.height - 91, self.height - 77, RED_LIGHT)
        self.outline(108, 280, self.height - 91, self.height - 77, GOLD_DARK, 1)
        self.text(f"{self.player.get_hp()} / {self.player.get_max_hp()}", 194, self.height - 84, 9, TEXT, anchor_x="center")

        # Barre d'expérience du personnage
        xp_ratio = max(0, min(1, self.player.get_xp() / max(1, self.player.get_xp_needed())))
        self.text("EXP", 78, self.height - 111, 10, TEXT_DARK)
        self.box(108, 280, self.height - 119, self.height - 105, (25, 20, 48))
        if xp_ratio > 0:
            self.box(108, 108 + 172 * xp_ratio, self.height - 119, self.height - 105, PURPLE)
        self.outline(108, 280, self.height - 119, self.height - 105, GOLD_DARK, 1)

        # -------------------- MANA ET ENDURANCE --------------------
        # Les deux jauges sont placées juste au-dessus du cadre inférieur.
        center_x = self.width / 2
        bar_width = 230
        bar_height = 12
        mana_left = center_x - 255
        stamina_left = center_x + 25
        bar_y = 132

        self.text("MANA", mana_left, bar_y + 20, 10, (100, 175, 255))
        self.box(mana_left, mana_left + bar_width, bar_y, bar_y + bar_height, (14, 25, 52))
        mana_ratio = max(0, min(1, self.player.get_mana() / max(1, self.player.get_max_mana())))
        if mana_ratio > 0:
            self.box(mana_left, mana_left + bar_width * mana_ratio, bar_y, bar_y + bar_height, (65, 135, 245))
        self.outline(mana_left, mana_left + bar_width, bar_y, bar_y + bar_height, GOLD_DARK, 1)
        self.text(f"{int(self.player.get_mana())}/{self.player.get_max_mana()}", mana_left + bar_width / 2, bar_y + 6, 8, TEXT, anchor_x="center")

        self.text("ENDURANCE", stamina_left, bar_y + 20, 10, (115, 220, 135))
        self.box(stamina_left, stamina_left + bar_width, bar_y, bar_y + bar_height, (15, 37, 23))
        stamina_ratio = max(0, min(1, self.stamina / max(1, self.max_stamina)))
        if stamina_ratio > 0:
            self.box(stamina_left, stamina_left + bar_width * stamina_ratio,
                     bar_y, bar_y + bar_height, (80, 200, 110))

        self.outline(stamina_left, stamina_left + bar_width, bar_y, bar_y + bar_height, GOLD_DARK, 1)
        self.text(
            f"{int(self.stamina)}/{self.max_stamina}",
            stamina_left + bar_width / 2,
            bar_y + 6,
            8,
            TEXT,
            anchor_x="center",
        )

        # -------------------- CADRE INFÉRIEUR : OBJETS + COMPÉTENCES --------------------
        frame_width = 760
        frame_height = 82
        frame_left = (self.width - frame_width) / 2
        frame_right = frame_left + frame_width
        frame_bottom = 18
        frame_top = frame_bottom + frame_height
        self.box(frame_left, frame_right, frame_bottom, frame_top, (12, 14, 20, 238))
        self.outline(frame_left, frame_right, frame_bottom, frame_top, GOLD, 2)
        self.text("ÉQUIPEMENT", frame_left + 12, frame_top - 12, 9, GOLD_LIGHT)

        # Neuf emplacements d'objets/armes (liés à la barre rapide de l'inventaire)
        slot_size = 43
        slot_gap = 5
        item_start_x = frame_left + 12
        slot_y = frame_bottom + 8
        for i in range(9):
            sx = item_start_x + i * (slot_size + slot_gap)
            self.box(sx, sx + slot_size, slot_y, slot_y + slot_size, (27, 29, 37))
            slot_color = MELEE_COLOR if i == 0 else RANGED_COLOR if i == 1 else GOLD_DARK
            self.outline(sx, sx + slot_size, slot_y, slot_y + slot_size,
                         slot_color, 4 if i < 2 else 1)
            self.text(str(i + 1), sx + 4, slot_y + slot_size - 5, 8,
                      slot_color if i < 2 else TEXT_DARK)

            item = self.hotbar[i]
            if item is not None:
                self.draw_item_icon(item, sx + 2, slot_y + slot_size - 2)

        # Quatre emplacements de compétences avec leurs touches de raccourci
        skills = [("T", "FRAPPE", (180, 65, 65)),
                  ("G", "LAME", (135, 75, 185)),
                  ("E", "SOIN", (70, 165, 105)),
                  ("R", "EXPLO", (65, 125, 210))]
        skill_size = 43
        skill_gap = 5
        skills_left = item_start_x + 9 * (slot_size + slot_gap) + 8
        for i, (key_name, skill_name, color) in enumerate(skills):
            sx = skills_left + i * (skill_size + skill_gap)
            self.box(sx, sx + skill_size, slot_y, slot_y + skill_size, (27, 29, 37))
            self.outline(sx, sx + skill_size, slot_y, slot_y + skill_size, color, 2)
            arcade.draw_circle_filled(sx + skill_size / 2, slot_y + 25, 10, color)
            self.text(key_name, sx + skill_size / 2, slot_y + 25, 10, TEXT, anchor_x="center")
            self.text(skill_name, sx + skill_size / 2, slot_y + 8, 6, TEXT, anchor_x="center")

        # -------------------- ORBES DE MANA ET D'EXP --------------------
        # Orbe de mana à gauche du cadre inférieur
        orb_y = frame_bottom + frame_height / 2
        mana_orb_x = frame_left - 42
        arcade.draw_circle_filled(mana_orb_x, orb_y, 25, (15, 30, 65))
        arcade.draw_circle_filled(mana_orb_x, orb_y, 19, (45, 105, 220))
        arcade.draw_circle_outline(mana_orb_x, orb_y, 26, (115, 175, 255), 3)
        arcade.draw_circle_filled(mana_orb_x - 6, orb_y + 7, 5, (165, 215, 255))
        self.text("MP", mana_orb_x, orb_y - 34, 9, (120, 180, 255), anchor_x="center")

        # Orbe d'EXP à droite
        exp_orb_x = frame_right + 42
        arcade.draw_circle_filled(exp_orb_x, orb_y, 25, (38, 18, 58))
        arcade.draw_circle_filled(exp_orb_x, orb_y, 19, (115, 55, 180))
        arcade.draw_circle_outline(exp_orb_x, orb_y, 26, (195, 135, 255), 3)
        arcade.draw_circle_filled(exp_orb_x - 6, orb_y + 7, 5, (225, 190, 255))
        self.text("EXP", exp_orb_x, orb_y - 34, 9, (205, 160, 255), anchor_x="center")

        # Informations de combat discrètes en haut à droite
        attack, defense, crit = self.get_stats()
        self.text(f"ATK {attack}   DEF {defense}   CRIT {crit}%", self.width - 18, self.height - 24, 12, TEXT, anchor_x="right")
        self.text("ZQSD : bouger  |  CLIC DROIT : attaquer  |  ESPACE : sauter  |  I : inventaire  |  ÉCHAP : pause",
                  self.width / 2, self.height - 22, 10, TEXT_DARK, anchor_x="center")

        if self.message_timer > 0:
            self.text(self.message, self.width / 2, self.height - 80, 20,
                      GOLD_LIGHT, anchor_x="center")

    # -----------------------------------------------------
    # GAME OVER
    # -----------------------------------------------------
    def draw_game_over(self):
        w, h = self.width, self.height
        cx, cy = w / 2, h / 2
        st = self.state_time
        red = (170, 40, 40)

        # Voile noir + teinte rouge qui monte lentement
        self.box(0, w, 0, h, (0, 0, 0, int(200 * min(1.0, st / 1.2))))
        self.box(0, w, 0, h, (90, 0, 0, int(55 * min(1.0, st / 2.5))))
        self.draw_vignette(230)
        self.draw_particles(tint=(200, 60, 50))

        # Bande sombre horizontale qui s'ouvre (comme dans Elden Ring)
        band_half = 95 * min(1.0, st / 0.8)
        for k in range(8):
            half = band_half + k * 8
            self.box(0, w, cy + 35 - half, cy + 35 + half, (0, 0, 0, 22))

        # "YOU DIED" apparaît en fondu (alpha par paliers pour limiter le cache de texte)
        a = int(255 * min(1.0, max(0.0, (st - 0.4) / 1.6)))
        a = (a // 32) * 32 + 31 if a > 0 else 0
        if a > 0:
            self.shadow_text("YOU DIED", cx, cy + 35, 66, (150, 28, 28, min(255, a)))
            self.draw_fade_line(cx, cy - 5, 260, red, min(255, a), inner=0)

        # Les choix apparaissent après l'animation
        if st > 1.6:
            self.draw_menu_options(
                ["CONTINUE", "MAIN MENU"],
                self.game_over_selection,
                cx, cy - 80, 50,
                size=20,
                accent=red,
                sel_color=(235, 120, 110),
            )

    def select_game_over_option(self):
        # CONTINUE
        if self.game_over_selection == 0:
            self.respawn_player()          # retour au dernier feu de camp

        # MAIN MENU
        elif self.game_over_selection == 1:
            self.state = STATE_MENU

            self.menu_selection = 0

            self.inventory_open = False
            self.pause_open = False

            self.keys.clear()

    # -----------------------------------------------------
    # MENUS
    # -----------------------------------------------------
    def draw_main_menu(self):
        w, h = self.width, self.height
        cx = w / 2

        self.draw_menu_backdrop()
        self.draw_particles()

        # Titre + séparateur + sous-titre
        title_y = h * 0.74
        self.shadow_text(GAME_TITLE, cx, title_y, 50, (236, 214, 160))
        self.draw_divider(cx, title_y - 46, half=260)
        self.shadow_text(GAME_SUBTITLE, cx, title_y - 76, 16, (120, 128, 145), italic=True)

        # Options (Charger grisé s'il n'y a pas de sauvegarde)
        start_y = h * 0.50
        spacing = 70
        disabled = set() if SAVE_PATH.exists() else {1}
        self.draw_menu_options(self.menu_options, self.menu_selection,
                               cx, start_y, spacing, size=22, disabled=disabled)

        # Message d'erreur
        if self.menu_message:
            self.text(self.menu_message, cx, start_y - len(self.menu_options) * spacing - 10,
                      15, RED_LIGHT, anchor_x="center", font=FONT_TITLE, italic=True)

        # Aide en bas
        self.text("HAUT / BAS : naviguer     |     ENTRÉE : valider",
                  cx, 30, 11, (95, 98, 108), anchor_x="center")

        # Bords sombres + fondu depuis le noir à l'arrivée sur l'écran
        self.draw_vignette(190)
        fade = 1 - min(1.0, self.state_time / 1.3)
        if fade > 0:
            self.box(0, w, 0, h, (0, 0, 0, int(255 * fade)))
            

    def select_menu_option(self):
        if self.menu_selection == 0:
            self.new_game()
        elif self.menu_selection == 1:
            if self.load_game():
                self.start_level(self.level_index, at_checkpoint=True)
            else:
                self.menu_message = "Aucune sauvegarde trouvée"
        elif self.menu_selection == 2:
            self.close()

    def start_level_1(self):
        """Lance le niveau 1 (les 4 niveaux sont décrits dans levels.py)."""
        self.start_level(1)

    def new_game(self):
        """Supprime l'ancienne sauvegarde et repart de zéro."""
        if SAVE_PATH.exists():
            SAVE_PATH.unlink()            # supprime le fichier save.json

        # Joueur et inventaire neufs (les 9 objets de départ)
        self.player = Player(Inventory(ITEMS[:9]))
        self.inventory = self.player.get_inventory()
        self.category = "Arme"
        self.inventory.set_category(self.category)

        self.equipped_weapon = None
        self.active_weapon_slot = None
        self.equipped_shield = None
        self.hotbar = [None] * 9
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.selected_item = None
        self.hover_item = None

        self.stamina = self.max_stamina
        self.arrows.clear()
        self.objet_sol = ITEMS[3]         # l'objet au sol réapparaît

        # Une nouvelle partie repart avec des statistiques à zéro.
        self.play_time = 0.0
        self.death_count = 0
        self.mobs_killed = 0

        self.world_new_game()
        self.start_level_1()

    def format_play_time(self):
        total_seconds = int(self.play_time)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d} h {minutes:02d} min {seconds:02d} s"

    def draw_settings(self):
        """Affiche les statistiques de la partie dans les paramètres."""
        w, h = self.width, self.height
        cx, cy = w / 2, h / 2

        self.box(0, w, 0, h, (0, 0, 0, 205))
        self.draw_vignette(190)

        panel_w, panel_h = 620, 440
        left = cx - panel_w / 2
        right = cx + panel_w / 2
        bottom = cy - panel_h / 2
        top = cy + panel_h / 2
        self.draw_menu_panel(left, right, bottom, top)

        self.shadow_text("STATISTIQUES DE LA PARTIE", cx, top - 65, 27, GOLD_LIGHT)
        self.draw_divider(cx, top - 105, half=220)

        stats = [
            ("TEMPS EN JEU", self.format_play_time()),
            ("NOMBRE DE MORTS", str(self.death_count)),
            ("MONSTRES ÉLIMINÉS", str(self.mobs_killed)),
        ]

        y = top - 175
        for label, value in stats:
            self.text(label, cx - 190, y, 15, TEXT_DARK, anchor_x="left")
            self.text(value, cx + 190, y, 19, GOLD_LIGHT, anchor_x="right", bold=True)
            y -= 75

        self.text("ECHAP : RETOUR AUX PARAMÈTRES DE PAUSE", cx, bottom + 35,
                  11, TEXT_DARK, anchor_x="center")

    def draw_pause_menu(self):
        w, h = self.width, self.height
        cx, cy = w / 2, h / 2

        # Voile qui s'assombrit progressivement + bords sombres + particules
        t = min(1.0, self.state_time / 0.35)
        self.box(0, w, 0, h, (0, 0, 0, int(185 * t)))
        self.draw_vignette(200)
        self.draw_particles()

        # Panneau central
        pw, ph = 460, 410
        left, right = cx - pw / 2, cx + pw / 2
        bottom, top = cy - ph / 2, cy + ph / 2
        self.draw_menu_panel(left, right, bottom, top)

        # Titre
        self.shadow_text("JEU EN PAUSE", cx, top - 62, 30, (246, 222, 160))
        self.draw_divider(cx, top - 98, half=170)

        # Options
        self.draw_menu_options(self.pause_options, self.pause_selection,
                               cx, top - 165, 66, size=21)

    # -----------------------------------------------------
    # INVENTAIRE
    # -----------------------------------------------------
    def draw_inventory(self):
        left = self.width * 0.06
        right = self.width * 0.94
        top = self.height * 0.92
        bottom = self.height * 0.08

        upper_bottom = self.height * 0.50

        self.decorative_frame(left, right, bottom, top)

        arcade.draw_line(
            left + 15,
            upper_bottom,
            right - 15,
            upper_bottom,
            GOLD_DARK,
            5,
        )

        arcade.draw_line(
            left + 25,
            upper_bottom,
            right - 25,
            upper_bottom,
            GOLD,
            1,
        )

        self.diamond(
            (left + right) / 2,
            upper_bottom,
            14,
        )

        self.text(
            "ÉQUIPEMENT",
            left + 35,
            top - 35,
            18,
            GOLD_LIGHT,
        )

        # Zone du personnage (définie avant les emplacements pour les aligner)
        char_left = left + 115
        char_right = left + 355
        char_bottom = upper_bottom + 30
        char_top = top - 75

        # Emplacements d'équipement à gauche, alignés sur la zone du personnage
        for name, sl, sb, sr, st in self.equipment_slot_rects():
            item = self.get_equipped(name)
            self.draw_slot(sl, sb, sr, st, item is not None)

            slot_cx = (sl + sr) / 2
            slot_cy = (sb + st) / 2

            if item is not None:
                self.draw_item_icon(item, slot_cx - 29, slot_cy + 29)
            else:
                self.text(self.equipment_labels[name], slot_cx, slot_cy,
                          6, TEXT_DARK, anchor_x="center")

        self.box(
            char_left,
            char_right,
            char_bottom,
            char_top,
            PANEL_DARK,
        )
        self.outline(
            char_left,
            char_right,
            char_bottom,
            char_top,
            GOLD,
            2,
        )

        cx = (char_left + char_right) / 2
        cy = (char_bottom + char_top) / 2

        arcade.draw_circle_outline(
            cx,
            cy + 30,
            62,
            GOLD_DARK,
            2,
        )

        arcade.draw_circle_filled(
            cx,
            cy + 45,
            20,
            (170, 170, 175),
        )

        self.box(
            cx - 25,
            cx + 25,
            cy - 55,
            cy + 25,
            (75, 78, 85),
        )

        # Arme équipée sur le personnage (dans l'inventaire)
        if self.equipped_weapon:
            icon = self.equipped_weapon.get_icon()

            if icon in ("sword", "sword_bas"):
                self.draw_sword(cx + 60, cy + 10, 120, icon == "sword_bas")

            elif icon == "arcleg":
                self.draw_arcleg(cx + 60, cy + 10, self.character_arcleg_width)

            elif icon == "arcbas":
                arcade.draw_arc_outline(
                    cx + 60, cy + 10, 55, 75, GOLD_LIGHT, 250, 70, 4
                )

        # STATISTIQUES (remplace la zone de craft)
        stats_left = left + 400
        stats_right = right - 35

        self.text("STATISTIQUES", stats_left, top - 35, 18, GOLD_LIGHT)

        weapon_name = (
            self.equipped_weapon.get_name().strip()
            if self.equipped_weapon else "Aucune"
        )
        self.text(f"Arme : {weapon_name}", stats_right, top - 35, 12,
                  TEXT_DARK, anchor_x="right")

        self.box(stats_left, stats_right, char_bottom, char_top, PANEL_DARK)
        self.outline(stats_left, stats_right, char_bottom, char_top, GOLD, 2)

        attack, defense, crit = self.get_stats()
        p = self.player
        weight = round(sum(i.get_weight() for i in self.inventory.get_items()), 1)
        level = p.get_level()

        rows_left = [
            ("NIVEAU", level, TEXT),
            ("PV", f"{p.get_hp()} / {p.get_max_hp()}", RED_LIGHT),
            ("XP", f"{p.get_xp()} / {p.get_xp_needed()}", GREEN),
            ("VITESSE", p.get_speed(), TEXT),
        ]
        rows_right = [
            ("ATTAQUE", attack, RED_LIGHT),
            ("DÉFENSE", defense, BLUE),
            ("CRITIQUE", f"{crit}%", PURPLE),
            ("POIDS", weight, TEXT_DARK),
        ]

        col_width = (stats_right - stats_left) / 2
        for col, rows in enumerate((rows_left, rows_right)):
            x = stats_left + 25 + col * col_width
            for i, (label, value, color) in enumerate(rows):
                y = char_top - 28 - i * 32
                self.text(label, x, y, 11, TEXT_DARK)
                self.text(str(value), x + 105, y, 13, color)

        # INVENTAIRE
        inv_left = left + 25

        self.text(
            "INVENTAIRE",
            inv_left,
            upper_bottom - 30,
            17,
            GOLD_LIGHT,
        )

        # Onglets.
        tabs = ["Arme", "Équipement", "Objet"]
        tx = inv_left + 130

        for tab in tabs:
            active = tab == self.category

            self.box(
                tx,
                tx + 105,
                upper_bottom - 55,
                upper_bottom - 28,
                (50, 39, 25) if active else PANEL_DARK,
            )

            self.outline(
                tx,
                tx + 105,
                upper_bottom - 55,
                upper_bottom - 28,
                GOLD if active else GOLD_DARK,
                2,
            )

            self.text(
                tab.upper(),
                tx + 52,
                upper_bottom - 42,
                10,
                GOLD_LIGHT if active else TEXT_DARK,
                anchor_x="center",
            )

            tx += 115

        # Grille.
        items = [
            item
            for item in self.inventory.get_items()
            if item.get_type() == self.inventory.get_category()
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
            equipped = item == self.equipped_weapon or item == self.equipped_shield

            self.draw_slot(
                x,
                y - slot,
                x + slot,
                y,
                hovered or selected or equipped,
            )

            self.draw_item_icon(item, x, y)

        # Barre rapide
        hotbar_y = bottom + 35

        self.text(
            "BARRE RAPIDE",
            left + 25,
            hotbar_y + 65,
            12,
            TEXT_DARK,
        )

        for i in range(9):
            x = left + 150 + i * 65

            # Dessine la case
            self.draw_slot(
                x,
                hotbar_y,
                x + 55,
                hotbar_y + 55,
                self.selected_item == self.hotbar[i]
                and self.hotbar[i] is not None,
            )
            if i < 2:
                slot_color = MELEE_COLOR if i == 0 else RANGED_COLOR
                self.outline(x, x + 55, hotbar_y, hotbar_y + 55,
                             slot_color, 5 if self.active_weapon_slot == i else 4)

            # Dessine l'objet placé dans la case
            item = self.hotbar[i]
            if item is not None:
                self.draw_item_icon(item, x, hotbar_y + 55)

        if self.hover_item:
            self.draw_item_tooltip(self.hover_item, self.mouse_x, self.mouse_y)

    # -----------------------------------------------------
    # CASES + ICONES
    # -----------------------------------------------------
    def draw_slot(
        self,
        left,
        bottom,
        right,
        top,
        active=False,
    ):
        self.box(
            left,
            right,
            bottom,
            top,
            PANEL_LIGHT if active else PANEL_DARK,
        )

        self.outline(
            left,
            right,
            bottom,
            top,
            GOLD_LIGHT if active else GOLD_DARK,
            3,
        )

        c = 7

        for x, y in [
            (left + 3, bottom + 3),
            (left + 3, top - 3),
            (right - 3, bottom + 3),
            (right - 3, top - 3),
        ]:
            arcade.draw_line(
                x - c,
                y,
                x + c,
                y,
                GOLD_DARK,
                2,
            )

    def draw_sword(self, center_x, center_y, target_width, basic=False):
        sprite = self.sword_bas_sprite if basic else self.sword_sprite
        texture_width = max(sprite.texture.width, 1)
        texture_height = max(sprite.texture.height, 1)

        target_height = target_width * texture_height / texture_width

        sprite.width = target_width
        sprite.height = target_height
        sprite.center_x = center_x
        sprite.center_y = center_y
        arcade.draw_sprite(sprite)

    def draw_arcleg(self, center_x, center_y, target_width):
        texture_width = max(self.arcleg_sprite.texture.width, 1)
        texture_height = max(self.arcleg_sprite.texture.height, 1)
        target_height = target_width * texture_height / texture_width
        self.arcleg_sprite.width = target_width
        self.arcleg_sprite.height = target_height
        self.arcleg_sprite.center_x = center_x
        self.arcleg_sprite.center_y = center_y
        self.arcleg_sprite.angle = 60
        arcade.draw_sprite(self.arcleg_sprite)

    def draw_shield(self, x, y):
        arcade.draw_circle_filled(x, y, 20, BLUE)
        arcade.draw_circle_outline(x, y, 20, GOLD, 3)
        arcade.draw_circle_filled(x, y, 6, GOLD_LIGHT)

    def draw_item_icon(self, item, x, y):
        center_x = x + 29
        center_y = y - 29

        if item.get_icon() in ("sword", "sword_bas"):
            self.draw_sword(
                center_x,
                center_y,
                self.inventory_sword_width,
                item.get_icon() == "sword_bas",
            )

        elif item.get_icon() == "arcleg":
            # L'arc utilise sa propre image et reste centré dans la case.
            self.draw_arcleg(
                center_x,
                center_y,
                self.inventory_arcleg_width,
            )

        elif item.get_icon() == "arcbas":
            arcade.draw_arc_outline(
                center_x + 5, center_y, 18, 70, GOLD_LIGHT, 250, 70, 3
            )
            arcade.draw_line(
                center_x - 8, center_y - 16,
                center_x + 8, center_y + 16,
                GOLD_LIGHT, 2
            )

        elif item.get_icon() == "shield":
            arcade.draw_circle_filled(
                center_x,
                center_y,
                18,
                BLUE,
            )
            arcade.draw_circle_outline(
                center_x,
                center_y,
                18,
                GOLD,
                2,
            )

        elif item.get_icon() == "ring":
            arcade.draw_circle_outline(
                center_x,
                center_y,
                13,
                GOLD_LIGHT,
                4,
            )

        elif item.get_icon() == "potion":
            self.box(
                x + 21,
                x + 37,
                y - 45,
                y - 23,
                RED,
            )

        elif item.get_icon() == "mana":
            self.box(
                x + 21,
                x + 37,
                y - 45,
                y - 23,
                BLUE,
            )

        else:
            self.text(
                "?",
                center_x,
                center_y,
                18,
                GOLD_LIGHT,
                anchor_x="center",
            )

    # -----------------------------------------------------
    # INFO DE L'OBJET
    # -----------------------------------------------------
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
            x,
            x + width,
            y,
            y + height,
            PANEL_DARK,
        )

        self.outline(
            x,
            x + width,
            y,
            y + height,
            GOLD_LIGHT,
            3,
        )

        self.text(
            item.get_name(),
            x + 15,
            y + height - 25,
            15,
            GOLD_LIGHT,
        )

        self.text(
            f"ATK    +{item.get_attack()}",
            x + 15,
            y + height - 55,
            11,
            RED_LIGHT,
        )

        self.text(
            f"DEF    +{item.get_defense()}",
            x + 15,
            y + height - 77,
            11,
            BLUE,
        )

        self.text(
            f"CRIT   +{item.get_crit()}%",
            x + 15,
            y + height - 99,
            11,
            PURPLE,
        )

        self.text(
            f"POIDS  {item.get_weight()}",
            x + 15,
            y + height - 121,
            10,
            TEXT_DARK,
        )

        self.text(
            "CLIC : sélectionner / équiper",
            x + 15,
            y + 15,
            9,
            TEXT_DARK,
        )

    # -----------------------------------------------------
    # SOURIS
    # -----------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):

        # GAME OVER : survol des boutons
        if self.state == STATE_GAME_OVER:
            cx = self.width / 2
            cy = self.height / 2

            if cx - 150 <= x <= cx + 150:
                if cy - 100 <= y <= cy - 60:
                    self.game_over_selection = 0
                elif cy - 150 <= y <= cy - 110:
                    self.game_over_selection = 1

            return

        if self.state == STATE_MENU:
            return

        self.mouse_x = x
        self.mouse_y = y
        self.hover_item = None

        if not self.inventory_open:
            return

        left = self.width * 0.06
        right = self.width * 0.94
        upper_bottom = self.height * 0.50

        # Vérification des onglets.
        inv_left = left + 25
        tx = inv_left + 130

        for tab in ["Arme", "Équipement", "Objet"]:
            if (
                tx <= x <= tx + 105
                and upper_bottom - 55 <= y <= upper_bottom - 28
            ):
                return
            tx += 115

        items = [
            item
            for item in self.inventory.get_items()
            if item.get_type() == self.inventory.get_category()
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

    def on_mouse_press(self, x, y, button, modifiers):

        # GAME OVER : clic sur les boutons
        if self.state == STATE_GAME_OVER:
            if button == arcade.MOUSE_BUTTON_LEFT:
                cx = self.width / 2
                cy = self.height / 2

                if cx - 150 <= x <= cx + 150:
                    if cy - 100 <= y <= cy - 60:
                        self.game_over_selection = 0
                        self.select_game_over_option()

                    elif cy - 150 <= y <= cy - 110:
                        self.game_over_selection = 1
                        self.select_game_over_option()

            return

        if self.state == STATE_MENU:
            return

        # Clics dans l'arbre de compétences
        if self.skill_tree_open:
            if button != arcade.MOUSE_BUTTON_LEFT:
                return

            button_left = self.width - 230
            button_right = self.width - 65
            if (
                self.selected_skill is not None
                and button_left <= x <= button_right
                and 42 <= y <= 88
            ):
                if self.player.unlock_skill(self.selected_skill):
                    self.show_message("Compétence débloquée !")
                else:
                    status = self.player.get_skill_status(self.selected_skill)
                    if status == "unlocked":
                        self.show_message("Compétence déjà débloquée")
                    elif status == "locked":
                        self.show_message("Prérequis manquant")
                    else:
                        self.show_message("Pas assez de points")
                return

            for skill_id, (sx, sy) in self.get_skill_node_positions().items():
                dx = x - sx
                dy = y - sy
                if dx ** 2 + dy ** 2 <= 29 ** 2:
                    self.selected_skill = skill_id
                    return
            return

        if not self.inventory_open:
            # Clic gauche : attaquer dans le monde du jeu
            if button == arcade.MOUSE_BUTTON_RIGHT and not self.pause_open:
                self.mouse_x = x
                self.mouse_y = y
                self.attack()
            return

        left = self.width * 0.06
        upper_bottom = self.height * 0.50
        hotbar_y = self.height * 0.08 + 35

        # Clic sur un emplacement d'équipement : on déséquipe
        for name, sl, sb, sr, st in self.equipment_slot_rects():
            if sl <= x <= sr and sb <= y <= st:
                item = self.get_equipped(name)
                if item is not None:
                    self.toggle_equip(item)
                return

        for i in range(9):
            slot_x = left + 150 + i * 65
            if slot_x <= x <= slot_x + 55 and hotbar_y <= y <= hotbar_y + 55:
                if button == arcade.MOUSE_BUTTON_RIGHT:
                    self.hotbar[i] = None
                    if self.active_weapon_slot == i:
                        self.equipped_weapon = None
                        self.player.set_equipped_weapon(None)
                        self.active_weapon_slot = None
                elif i >= 2 and self.selected_item is not None and self.selected_item.get_type() == "Objet":
                    self.hotbar[i] = self.selected_item
                    self.selected_item = None
                    self.inventory.set_selected(None)
                return

        tx = left + 25 + 130
        for tab in ["Arme", "Équipement", "Objet"]:
            if tx <= x <= tx + 105 and upper_bottom - 55 <= y <= upper_bottom - 28:
                self.category = tab
                self.inventory.set_category(tab)
                self.hover_item = None
                self.selected_item = None
                return
            tx += 115

        self.on_mouse_motion(x, y, 0, 0)
        item = self.hover_item
        if item is None:
            return
        if item.get_type() == "Arme":
            slot_index = self.weapon_hotbar_index(item)
            if slot_index is None:
                self.show_message("Type d'arme non pris en charge")
                return
            previous_item = self.hotbar[slot_index]
            self.hotbar[slot_index] = item
            if previous_item != item and self.active_weapon_slot == slot_index:
                self.equipped_weapon = None
                self.player.set_equipped_weapon(None)
                self.active_weapon_slot = None
            self.show_message(f"{item.get_name().strip()} assignée à la touche {slot_index + 1}")
        elif item.get_type() == "Équipement":
            self.toggle_equip(item)
        else:
            self.selected_item = item
            self.inventory.set_selected(item)

    def toggle_equip(self, item):
        if item.get_type() == "Arme":
            self.equipped_weapon = None if self.equipped_weapon == item else item
            self.player.set_equipped_weapon(self.equipped_weapon)
        elif item.get_defense() > 0:
            self.equipped_shield = None if self.equipped_shield == item else item
            self.player.set_equipped_shield(self.equipped_shield)
        else:
            self.show_message("Cet objet ne s'équipe pas")

    # -----------------------------------------------------
    # CLAVIER
    # -----------------------------------------------------
    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    def on_key_press(self, key, modifiers):

        # MENU PRINCIPAL
        if self.state == STATE_MENU:
            if key == arcade.key.UP:
                self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                self.menu_message = ""
            elif key == arcade.key.DOWN:
                self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                self.menu_message = ""
            elif key in (arcade.key.ENTER, arcade.key.RETURN):
                self.select_menu_option()
            return

        # GAME OVER
        if self.state == STATE_GAME_OVER:
            if key == arcade.key.UP:
                self.game_over_selection = (self.game_over_selection - 1) % 2
            elif key == arcade.key.DOWN:
                self.game_over_selection = (self.game_over_selection + 1) % 2
            elif key in (arcade.key.ENTER, arcade.key.RETURN):
                self.select_game_over_option()
            return

        # PARAMÈTRES / STATISTIQUES
        if self.settings_open:
            if key == arcade.key.ESCAPE:
                self.settings_open = False
                self.pause_open = True
                self.pause_selection = 1
            return

        # PAUSE
        if self.pause_open:

            if key == arcade.key.ESCAPE:
                self.pause_open = False
                return

            if key == arcade.key.UP:
                self.pause_selection -= 1

                if self.pause_selection < 0:
                    self.pause_selection = len(self.pause_options) - 1

                return

            if key == arcade.key.DOWN:
                self.pause_selection += 1

                if self.pause_selection >= len(self.pause_options):
                    self.pause_selection = 0

                return

            if key in (arcade.key.ENTER, arcade.key.RETURN):
                self.select_pause_option()
                return

            # Empêche ZQSD de faire bouger le personnage dans la pause
            return

        # FIN DU JEU / DIALOGUE AVEC UN PNJ
        if self.victory:
            if key in (arcade.key.ENTER, arcade.key.RETURN):
                self.victory = False
                self.state = STATE_MENU
                self.menu_selection = 0
                self.keys.clear()
            return
        if self.dialog is not None:
            if key in (arcade.key.F, arcade.key.ENTER, arcade.key.RETURN, arcade.key.SPACE):
                self.advance_dialog()
            elif key == arcade.key.ESCAPE:
                self.dialog = None
            return

        # ARBRE DE COMPÉTENCES
        if self.skill_tree_open:
            if key in (arcade.key.O, arcade.key.ESCAPE):
                self.skill_tree_open = False
                self.selected_skill = None
            return

        if key == arcade.key.O:
            if not self.inventory_open:
                self.skill_tree_open = True
                self.selected_skill = None
            return

        # INVENTAIRE
        if key == arcade.key.TAB or key == arcade.key.I:
            self.inventory_open = not self.inventory_open
            self.hover_item = None
            return

        if key == arcade.key.F5:
            self.save_game()
            self.show_message("Partie sauvegardée")
            return

        # ÉCHAP
        if key == arcade.key.ESCAPE:
            if self.inventory_open:
                self.inventory_open = False
                self.hover_item = None
            else:
                self.pause_open = True
                self.pause_selection = 0

            return

        # Touches de jeu et récupération d'objet
        if not self.inventory_open:

            if key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
                self.start_dash()
                return

            if key == arcade.key.F:                  # ramasser / parler / ouvrir / feu de camp / porte
                self.interact()

            if key in (arcade.key.SPACE, arcade.key.Z):      # saut (SPACE ou Z)
                self.body.jump_buf = 0.14

            if key == arcade.key.E:                  # sort : Soin
                self.use_skill(2)
            elif key == arcade.key.R:                # sort : Explosion obscure
                self.use_skill(3)
            elif key == arcade.key.H:                # potion de soin
                self.use_potion_by_icon("potion")
            elif key == arcade.key.M:                # potion de mana
                self.use_potion_by_icon("mana")
            elif arcade.key.KEY_1 <= key <= arcade.key.KEY_2:
                self.select_hotbar_weapon(key - arcade.key.KEY_1)
            elif arcade.key.KEY_3 <= key <= arcade.key.KEY_9:
                item = self.hotbar[key - arcade.key.KEY_1]
                if item is not None:
                    self.use_item(item)

            # Touches de déplacement (toujours enregistrées)
            self.keys.add(key)

    def on_close(self):
        # Sauvegarde auto si on ferme la fenêtre en pleine partie
        if self.state == STATE_GAME:
            self.save_game()
        super().on_close()

    def select_pause_option(self):

        if self.pause_selection == 0:
            # Reprendre
            self.pause_open = False

        elif self.pause_selection == 1:
            # Paramètres : affiche les statistiques de la partie.
            self.pause_open = False
            self.settings_open = True

        elif self.pause_selection == 2:
            self.save_game()              # sauvegarde auto avant de quitter
            self.pause_open = False
            self.state = STATE_MENU
            self.menu_message = ""

        elif self.pause_selection == 3:
            self.save_game()              # sauvegarde auto avant de quitter
            self.close()

    # -----------------------------------------------------
    # PROFILS / SAUVEGARDE
    # -----------------------------------------------------
    @classmethod
    def create_profile(cls):
        # Crée une instance légère pour satisfaire le nombre d'instances demandé,
        # sans lancer une fenêtre Arcade supplémentaire.
        profile = object.__new__(cls)
        profile._Game__window_title = TITLE
        profile._Game__profile_name = "Profil de démonstration"
        profile.profile_only = True
        return profile

    def save_game(self, filename=SAVE_PATH):
        data = self.player.to_dict()      # position, niveau, stats, inventaire, équipement

        # Ce qui appartient au jeu (pas au joueur)
        data["hotbar"] = [
            item.get_name() if item is not None else None
            for item in self.hotbar
        ]
        data["active_weapon_slot"] = self.active_weapon_slot
        data["stamina"] = self.stamina
        data["objet_sol_ramasse"] = self.objet_sol is None
        data["play_time"] = self.play_time
        data["death_count"] = self.death_count
        data["mobs_killed"] = self.mobs_killed
        data.update(self.world_save_data())      # niveau, feu de camp, boss vaincus, coffres

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Partie sauvegardée avec succès !")

    def load_game(self, filename=SAVE_PATH):
        """Renvoie True si le chargement a réussi, False sinon."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print("Aucun fichier de sauvegarde trouvé.")
            return False
        except json.JSONDecodeError:
            print("Fichier de sauvegarde illisible.")
            return False

        # 1) On recrée les objets de l'inventaire à partir des dictionnaires
        loaded_items = []
        for d in data["inventory"]["items"]:
            loaded_items.append(Item(
                name=d["name"],
                item_type=d["type"],
                icon=d["icon"],
                attack=d["attack"],
                defense=d["defense"],
                crit=d["crit"],
                weight=d["weight"],
                description=d.get("description", ""),
                item_id=d.get("id"),
                kind=d.get("kind", ""),
            ))

        def find(name):
            """Retrouve un objet de l'inventaire à partir de son nom."""
            for it in loaded_items:
                if it.get_name() == name:
                    return it
            return None

        # 2) Joueur neuf, puis on lui remet niveau, stats, position
        inventory = Inventory(loaded_items)
        inventory.set_category(data["inventory"].get("category", "Arme"))
        self.player = Player(inventory)
        self.player.load_stats(data)
        self.inventory = inventory
        self.category = inventory.get_category()

        # 3) Équipement : on reprend les objets de la liste chargée
        weapon = find(data["equipped_weapon"]["name"]) if data.get("equipped_weapon") else None
        shield = find(data["equipped_shield"]["name"]) if data.get("equipped_shield") else None
        self.equipped_weapon = weapon
        self.equipped_shield = shield
        self.player.set_equipped_weapon(weapon)
        self.player.set_equipped_shield(shield)

        # 4) Barre rapide (9 cases, sauvegardées par nom)
        saved_hotbar = data.get("hotbar", [])
        self.hotbar = [find(n) for n in (saved_hotbar + [None] * 9)[:9]]
        self.active_weapon_slot = data.get("active_weapon_slot")
        if self.active_weapon_slot not in (0, 1):
            self.active_weapon_slot = None
        equipped_slot = self.weapon_hotbar_index(weapon) if weapon is not None else None
        if equipped_slot is not None and self.hotbar[equipped_slot] is None:
            self.hotbar[equipped_slot] = weapon
        if (self.active_weapon_slot is None and equipped_slot is not None
                and self.hotbar[equipped_slot] == weapon):
            self.active_weapon_slot = equipped_slot

        # 5) Le reste
        self.stamina = data.get("stamina", self.max_stamina)
        self.objet_sol = None if data.get("objet_sol_ramasse") else ITEMS[3]
        self.play_time = data.get("play_time", 0.0)
        self.death_count = data.get("death_count", 0)
        self.mobs_killed = data.get("mobs_killed", 0)
        self.selected_item = None
        self.hover_item = None
        self.arrows.clear()
        self.world_load_data(data)

        print("Partie chargée avec succès !")
        return True


if __name__ == "__main__":
    game_profiles = [Game.create_profile() for _ in range(20)]
    game = Game()
    arcade.run()