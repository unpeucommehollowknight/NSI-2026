import arcade
from pathlib import Path
import json
import random
import math
import copy
import textwrap


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
GOLD_CREAM = (246, 222, 160)
RED = (150, 42, 48)
RED_LIGHT = (220, 68, 70)
TEXT = (225, 218, 201)
TEXT_DARK = (140, 136, 126)
GREEN = (80, 165, 95)
BLUE = (80, 125, 185)
PURPLE = (145, 85, 175)
MANA_BLUE = (100, 175, 255)
STAMINA_GREEN = (115, 220, 135)

FONT_TITLE = ("Garamond", "Georgia", "Palatino Linotype", "Times New Roman")
GAME_TITLE = "unpeucommehollowknight"
GAME_SUBTITLE = "en construction"

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_GAME_OVER = "game_over"

INV_TABS = ["Arme", "Équipement", "Objet"]
KIND_LABELS = {
    "melee": "Corps à corps",
    "ranged": "Distance",
    "shield": "Bouclier",
    "heal": "Soin",
    "mana": "Mana",
    "key": "Clé",
}


class Item:
    def __init__(self, item_id, name, item_type, icon, kind="", attack=0,
                 defense=0, crit=0, weight=0, description=""):
        self.__id = item_id
        self.__name = name
        self.__type = item_type
        self.__icon = icon          # APPARENCE uniquement
        self.__kind = kind          # COMPORTEMENT : melee, ranged, heal, mana...
        self.__attack = attack
        self.__defense = defense
        self.__crit = crit
        self.__weight = weight
        self.__description = description

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
    def set_attack(self, value): self.__attack = value
    def set_defense(self, value): self.__defense = value
    def set_crit(self, value): self.__crit = value
    def set_weight(self, value): self.__weight = value

    def __eq__(self, other):
        return isinstance(other, Item) and self.__id == other.__id

    def to_dict(self):
        return {"id": self.__id, "name": self.__name, "type": self.__type,
                "icon": self.__icon, "kind": self.__kind,
                "attack": self.__attack, "defense": self.__defense,
                "crit": self.__crit, "weight": self.__weight,
                "description": self.__description}

    def __str__(self):
        return self.__name


# ---------------- CATALOGUE D'OBJETS ----------------
# Le "rangement" : un objet = une ligne. Rien n'est dans l'inventaire tant
# qu'on ne l'a pas sorti avec creer_objet().
CATALOGUE = {
    "epee_basique": Item("epee_basique", "Épée basique", "Arme", icon="sword_bas",
                         kind="melee", attack=5, crit=1, weight=5.2,
                         description="Une ancienne épée utilisée par les escrimeurs."),
    "epee_or": Item("epee_or", "Épée en Or", "Arme", icon="sword",
                    kind="melee", attack=10, crit=2, weight=5.2,
                    description="Une ancienne épée utilisée par les chevaliers."),
    "arc_basique": Item("arc_basique", "Arc basique", "Arme", icon="arcbas",
                        kind="ranged", attack=4, crit=5, weight=3.5,
                        description="Un arc simple mais fiable."),
    "arc_legendaire": Item("arc_legendaire", "Arc légendaire", "Arme", icon="arcleg",
                           kind="ranged", attack=20, crit=12, weight=3.5,
                           description="Un arc forgé pour les guerriers les plus redoutables."),
    "bouclier_dragon": Item("bouclier_dragon", "Bouclier en écaille de dragon", "Équipement",
                            icon="shield", kind="shield", defense=40, weight=7.0,
                            description="Un bouclier créé à partir d'écaille de dragon."),
    "bouclier_ancien": Item("bouclier_ancien", "Bouclier ancien", "Équipement",
                            icon="shield", kind="shield", defense=10, weight=7.0,
                            description="Un vieux bouclier capable de résister aux coups."),
    "cle": Item("cle", "Clé", "Équipement", icon="object", kind="key", weight=0.2,
                description="Clé qui permet d'accéder à des zones."),
    "potion_soin": Item("potion_soin", "Potion de soin", "Objet", icon="potion",
                        kind="heal", weight=0.5, description="Restaure des points de vie."),
    "potion_mana": Item("potion_mana", "Potion de mana", "Objet", icon="mana",
                        kind="mana", weight=0.5, description="Restaure des points de mana."),
}


def creer_objet(item_id):
    """Sort un objet du catalogue (une copie neuve, pour ne pas partager l'état)."""
    return copy.copy(CATALOGUE[item_id])


# Ce que le joueur possède au départ
INVENTAIRE_DEPART = ["epee_basique"]

OBJET_SOL_DEPART = "arc_legendaire"


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


# -----------------------------------------------------
# ARBRE DE COMPÉTENCES (données)
# -----------------------------------------------------
# Chaque compétence : branche, palier (row), couloir (lane : -1 / 0 / +1),
# coût, pré-requis (None, un id, ou un tuple d'ids : tous requis) et effets.
# La description affichée est générée automatiquement depuis les effets.

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
        """'unlocked', 'locked' (pré-requis manquant), 'no_points' ou 'available'."""
        if skill_id in self.__unlocked_skills:
            return "unlocked"
        if any(r not in self.__unlocked_skills for r in skill_requirements(skill_id)):
            return "locked"
        if self.__skill_points < SKILL_TREE[skill_id]["cost"]:
            return "no_points"
        return "available"

    def unlock_skill(self, skill_name):
        if skill_name not in SKILL_TREE:
            return False
        if self.get_skill_status(skill_name) != "available":
            return False

        data = SKILL_TREE[skill_name]
        fx = data["effects"]

        self.__skill_points -= data["cost"]
        self.__unlocked_skills.add(skill_name)

        self.__base_attack += fx.get("attack", 0)
        self.__base_defense += fx.get("defense", 0)
        self.__base_crit += fx.get("crit", 0)

        hp = fx.get("hp", 0)
        self.__max_hp += hp
        self.__hp = min(self.__max_hp, self.__hp + hp)

        mana = fx.get("mana", 0)
        self.__max_mana += mana
        self.__mana = min(self.__max_mana, self.__mana + mana)

        return True

    def gain_xp(self, value):
        self.__xp += value

        while self.__xp >= self.__xp_needed:
            self.__xp -= self.__xp_needed
            self.__level += 1
            self.__xp_needed = int(self.__xp_needed * 1.5)

            self.__base_attack = round(self.__base_attack * 1.05)
            self.__base_defense = round(self.__base_defense * 1.05)
            self.__base_crit = round(self.__base_crit * 1.05)

            # 1 point à chaque niveau
            self.__skill_points += 1

            # 2 points bonus tous les 10 niveaux
            if self.__level % 10 == 0:
                self.__skill_points += 2

            print("Niveau atteint :", self.__level)
            print("Points de compétence :", self.__skill_points)

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
        on garde une valeur par défaut au lieu de planter.

        Les stats sauvegardées (base_attack, max_hp, ...) contiennent déjà les bonus
        de l'arbre de compétences : on les restaure telles quelles."""
        self.__x = data.get("x", 0)
        self.__y = data.get("y", 0)
        self.__speed = data.get("speed", self.__speed)

        self.__level = data.get("level", 1)
        self.__xp = data.get("xp", 0)
        self.__xp_needed = data.get("xp_needed", 100)

        self.__max_hp = data.get("max_hp", self.__max_hp)
        self.__hp = max(1, min(self.__max_hp, data.get("hp", self.__max_hp)))

        self.__max_mana = data.get("max_mana", self.__max_mana)
        self.__mana = max(0, min(self.__max_mana, data.get("mana", self.__max_mana)))

        self.__base_attack = data.get("base_attack", self.__base_attack)
        self.__base_defense = data.get("base_defense", self.__base_defense)
        self.__base_crit = data.get("base_crit", self.__base_crit)

        # Arbre de compétences
        self.__skill_points = data.get("skill_points", 0)
        self.__unlocked_skills = {
            s for s in data.get("unlocked_skills", []) if s in SKILL_TREE
        }


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

# 20 slots réels : la grille et la barre rapide peuvent les utiliser.
SLOTS = [Slot(i) for i in range(20)]

# 20 inventaires : un actif et 19 profils de réserve.
INVENTORIES = [Inventory([creer_objet(i) for i in INVENTAIRE_DEPART])] + [Inventory() for _ in range(19)]

# 20 joueurs : un actif et 19 profils de réserve.
PLAYERS = [Player(INVENTORIES[0])] + [Player(INVENTORIES[i]) for i in range(1, 20)]


class Monster:

    def __init__(self, x, y, hp=150, speed=100,
                 damage=12, respawn_time=120,
                 variant="contamine"):

        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y

        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage

        self.variant = variant

        self.alive = True
        self.aggro = False  
        self.respawn_time = respawn_time
        self.respawn_timer = 0
        self.attack_cooldown = 0

        self.dir_timer = 0
        self.dx = 0
        self.dy = 0


class Game(arcade.Window):
    # Dimensions de l'arbre de compétences (défilement vertical)
    SKILL_ROW_H = 125
    SKILL_TOP_PAD = 115
    SKILL_BOTTOM_PAD = 95

    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            TITLE,
            fullscreen=False,
            vsync=True,
        )

        # Caches de rendu (textes, fonds et bords sombres pré-calculés)
        self._text_cache = {}
        self._shape_cache = {}

        # --- MAP NATIVE DE TEST (Matrice) ---
        self.wall_list = arcade.SpriteList()

        # 1 = Mur, 0 = Espace vide
        MAP_MATRIX = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1],
            [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

        TILE_SIZE = 64  # Taille d'affichage de chaque bloc

        for row_index, row in enumerate(MAP_MATRIX):
            for col_index, cell in enumerate(row):
                if cell == 1:
                    # Utilisation d'une texture de caisse intégrée à Arcade
                    wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", scale=0.5)

                    # Calcul des coordonnées x et y centrées
                    wall.center_x = col_index * TILE_SIZE + TILE_SIZE // 2
                    wall.center_y = (len(MAP_MATRIX) - 1 - row_index) * TILE_SIZE + TILE_SIZE // 2 + 100

                    self.wall_list.append(wall)

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
        self.objet_sol = creer_objet(OBJET_SOL_DEPART)
        self.objet_sol_x = 300
        self.objet_sol_y = 200

        # Liste des monstres : un Monster(x, y) par monstre
        self.monsters = [
            Monster(400, 200, hp=50, speed=75, damage=8),
            Monster(-300, 150, hp=50, speed=75, damage=8),
            Monster(600, -250, hp=180, speed=45, damage=20),
            Monster(800, 0, hp=450, speed=35, damage=40, respawn_time=30),
        ]

        self.facing = 1            # 1 = droite, -1 = gauche
        self.attack_cooldown = 0
        self.slash_timer = 0
        self.arrows = []

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Caméra fluide
        self.camera_x = self.player.get_x()
        self.camera_y = self.player.get_y()

        self.camera_follow_speed = 5.0
        self.camera_look_ahead = 85

        self.keys = set()

        # DASH horizontal
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_duration = 0.15
        self.dash_speed = 2000
        self.dash_dx = 0

        self.inventory_open = False
        self.category = "Arme"

        # --- Arbre de compétences ---
        self.skill_tree_open = False
        self.skill_from_inventory = False   # ouvert depuis l'inventaire ? (pour y revenir)
        self.selected_skill = None
        self.hover_skill = None
        self.skill_scroll = 0.0             # défilement affiché (pixels)
        self.skill_scroll_target = 0.0      # défilement visé (animation douce)
        self.skill_drag = None              # None / "bar" / "pan"
        self.skill_drag_offset = 0.0
        self.unlock_fx = None               # (id, temps restant) : flash au déblocage
        self.hover_skill_btn = False        # survol du bouton dans l'inventaire

        self.pause_open = False
        self.pause_selection = 0

        # Écran Game Over
        self.game_over_selection = 0

        self.pause_options = ["Reprendre", "Paramètres", "Menu principal", "Quitter"]

        self.hover_item = None
        self.selected_item = None
        self.equipped_weapon = None

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

    def text(
        self,
        value,
        x,
        y,
        size=12,
        color=TEXT,
        anchor_x="left",
        anchor_y="center",
        font=None,
        bold=False,
        italic=False,
    ):
        # arcade.draw_text recrée un objet texte à chaque appel (très lent).
        # On garde donc un objet arcade.Text par texte distinct et on ne fait
        # que le repositionner puis le dessiner.
        value = str(value)
        key = (value, size, tuple(color), anchor_x, anchor_y, font, bold, italic)
        label = self._text_cache.get(key)
        if label is None:
            if len(self._text_cache) > 1500:
                self._text_cache.clear()
            extra = {}
            if font is not None:
                extra["font_name"] = font
            label = arcade.Text(
                value,
                x,
                y,
                tuple(color),
                size,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                bold=bold,
                italic=italic,
                **extra,
            )
            self._text_cache[key] = label
        elif label.x != x or label.y != y:
            label.position = (x, y)
        label.draw()

    def diamond(self, x, y, size=12):
        points = [
            (x, y + size),
            (x + size, y),
            (x, y - size),
            (x - size, y),
        ]

        arcade.draw_polygon_filled(points, RED)
        arcade.draw_polygon_outline(points, GOLD_LIGHT, 2)

    def diamond_shape(self, x, y, size, fill=None, edge=None, edge_w=2):
        """Losange avec remplissage et/ou contour (couleurs optionnelles)."""
        points = [
            (x, y + size),
            (x + size, y),
            (x, y - size),
            (x - size, y),
        ]
        if fill is not None:
            arcade.draw_polygon_filled(points, fill)
        if edge is not None:
            arcade.draw_polygon_outline(points, edge, edge_w)

    def get_equipped(self, slot_name):
        """Renvoie l'objet équipé dans un emplacement (ou None)."""
        if slot_name == "weapon":
            return self.equipped_weapon
        if slot_name == "shield":
            return self.equipped_shield
        return None   # casque / armure : pas encore d'objets

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
    # EFFETS DE MENU (partagés avec HUD / inventaire / arbre)
    # -----------------------------------------------------
    def init_particles(self, count=55):
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

        # Messages temporaires (visibles aussi dans l'inventaire et l'arbre)
        self.message_timer = max(0, self.message_timer - dt)

        # Flash de déblocage d'une compétence
        if self.unlock_fx is not None:
            sid, t = self.unlock_fx
            t -= dt
            self.unlock_fx = (sid, t) if t > 0 else None

        # Défilement doux de l'arbre de compétences
        if self.skill_tree_open and self.skill_drag is None:
            max_scroll = self.skill_layout()["max_scroll"]
            self.skill_scroll_target = max(0.0, min(max_scroll, self.skill_scroll_target))
            self.skill_scroll += (self.skill_scroll_target - self.skill_scroll) * min(1.0, 14 * dt)
            if abs(self.skill_scroll_target - self.skill_scroll) < 0.2:
                self.skill_scroll = self.skill_scroll_target

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
        # Les particules sont regroupées par (couleur, transparence, taille) :
        # quelques appels draw_points au lieu d'un draw_circle par particule.
        groups = {}
        for p in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.ui_time * 2.0 + p["phase"] * 3)
            alpha = (int(50 + 170 * flicker) // 40) * 40 + 30      # 4-5 paliers

            if tint is not None:
                base = tint
            elif p["gold"]:
                base = GOLD_LIGHT
            else:
                base = (190, 205, 230)       # lueur pâle façon Hollow Knight

            size = 2 if p["size"] < 2.0 else 4
            groups.setdefault((base, min(255, alpha), size), []).append((p["x"], p["y"]))

        for (base, alpha, size), points in groups.items():
            arcade.draw_points(points, (*base, alpha), size)

    def cached_shapes(self, key, builder):
        """Construit une fois une ShapeElementList (dessin d'un seul bloc ensuite).
        Si la création échoue, renvoie None et l'appelant dessine à l'ancienne."""
        if key in self._shape_cache:
            return self._shape_cache[key]
        try:
            shapes = arcade.shape_list.ShapeElementList()
            builder(shapes)
        except Exception:
            shapes = None
        if len(self._shape_cache) > 40:
            self._shape_cache.clear()
        self._shape_cache[key] = shapes
        return shapes

    def draw_vignette(self, strength=170):
        """Assombrit les bords de l'écran avec des cadres de plus en plus transparents."""
        w, h = self.width, self.height
        step = 22
        layers = 12

        def build(shapes):
            from arcade.shape_list import create_rectangle_filled
            for i in range(layers):
                alpha = int(strength * (1 - i / layers) ** 2)
                inset = i * step
                # 4 bandes de largeur `step` qui forment le cadre de la couche i
                color = (0, 0, 0, alpha)
                shapes.append(create_rectangle_filled(w / 2, inset + step / 2, w - 2 * inset, step, color))
                shapes.append(create_rectangle_filled(w / 2, h - inset - step / 2, w - 2 * inset, step, color))
                side_h = h - 2 * inset - 2 * step
                if side_h > 0:
                    shapes.append(create_rectangle_filled(inset + step / 2, h / 2, step, side_h, color))
                    shapes.append(create_rectangle_filled(w - inset - step / 2, h / 2, step, side_h, color))

        shapes = self.cached_shapes(("vignette", w, h, strength), build)
        if shapes is not None:
            shapes.draw()
            return

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

    def draw_fade_line(self, cx, y, half, color, alpha, inner=0, steps=20):
        """Ligne horizontale qui s'efface du centre vers les extrémités."""
        steps = max(6, steps // 2)      # moitié moins de segments : rendu quasi identique
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

    def draw_panel_frame(self, left, right, bottom, top, corner=9, inner=8, mid=True):
        """Cadre à double filet doré et losanges aux angles (sans fond)."""
        cx = (left + right) / 2
        self.outline(left, right, bottom, top, GOLD_DARK, 2)
        self.outline(left + inner, right - inner, bottom + inner, top - inner, (*GOLD, 110), 1)

        for x, y in ((left, bottom), (left, top), (right, bottom), (right, top)):
            self.ornament_diamond(x, y, corner, GOLD, GOLD_DARK)
        if mid:
            self.ornament_diamond(cx, top, 6)
            self.ornament_diamond(cx, bottom, 6)

    def draw_menu_panel(self, left, right, bottom, top, alpha=225):
        """Cadre sombre à double filet doré et losanges aux angles."""
        self.box(left, right, bottom, top, (7, 8, 12, alpha))
        self.draw_panel_frame(left, right, bottom, top)

    def draw_inset(self, left, right, bottom, top, edge=GOLD_DARK):
        """Sous-panneau sombre (zone du personnage, statistiques, infobulles...)."""
        self.box(left, right, bottom, top, (10, 11, 15, 238))
        self.outline(left, right, bottom, top, edge, 2)
        self.outline(left + 4, right - 4, bottom + 4, top - 4, (*GOLD, 55), 1)
        for x, y in ((left, bottom), (left, top), (right, bottom), (right, top)):
            self.ornament_diamond(x, y, 4, GOLD, GOLD_DARK)

    def draw_bar(self, left, bottom, width, height, ratio, fill, back):
        """Jauge stylisée : fond sombre, reflet, filet doré, losanges aux extrémités."""
        ratio = max(0.0, min(1.0, ratio))
        self.box(left, left + width, bottom, bottom + height, back)
        if ratio > 0:
            fw = width * ratio
            self.box(left, left + fw, bottom, bottom + height, fill)
            light = tuple(min(255, c + 60) for c in fill[:3])
            self.box(left, left + fw, bottom + height * 0.55, bottom + height - 1, (*light, 110))
        self.outline(left, left + width, bottom, bottom + height, GOLD_DARK, 1)
        self.ornament_diamond(left, bottom + height / 2, 4, GOLD, GOLD_DARK)
        self.ornament_diamond(left + width, bottom + height / 2, 4, GOLD, GOLD_DARK)

    def draw_orb(self, cx, cy, radius, ratio, liquid, dark, label_value=None):
        """Orbe qui se vide / se remplit selon le ratio (tranches horizontales)."""
        arcade.draw_circle_filled(cx, cy, radius + 4, (6, 7, 10))
        arcade.draw_circle_filled(cx, cy, radius, dark)

        ratio = max(0.0, min(1.0, ratio))
        if ratio > 0:
            fill_h = 2 * radius * ratio
            bottom_y = cy - radius
            step = 2.0
            y = 0.0
            while y < fill_h:
                yy = bottom_y + y + step / 2
                dy = yy - cy
                half = math.sqrt(max(0.0, radius * radius - dy * dy))
                if half > 0:
                    self.box(cx - half, cx + half,
                             bottom_y + y, min(bottom_y + y + step, bottom_y + fill_h),
                             liquid)
                y += step

        arcade.draw_circle_filled(cx - radius * 0.38, cy + radius * 0.42, radius * 0.17, (255, 255, 255, 70))
        arcade.draw_circle_outline(cx, cy, radius + 2, GOLD, 2)
        arcade.draw_circle_outline(cx, cy, radius + 5, GOLD_DARK, 2)
        if label_value is not None:
            self.text(str(label_value), cx, cy, 9, TEXT, anchor_x="center", bold=True)

    def draw_toast(self, y):
        """Petit message temporaire dans le style des menus."""
        if self.message_timer <= 0 or not self.message:
            return
        cx = self.width / 2
        half = len(self.message) * 7.5 + 34
        self.box(cx - half, cx + half, y - 20, y + 20, (7, 8, 12, 238))
        self.outline(cx - half, cx + half, y - 20, y + 20, GOLD_DARK, 2)
        self.ornament_diamond(cx - half, y, 6, GOLD, GOLD_DARK)
        self.ornament_diamond(cx + half, y, 6, GOLD, GOLD_DARK)
        self.shadow_text(self.message, cx, y, 16, GOLD_CREAM)

    def draw_menu_options(self, options, selection, cx, start_y, spacing,
                          size=22, disabled=(), accent=(212, 160, 70),
                          sel_color=(246, 218, 150)):
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 3.0)
        bar_y = start_y - self.cursor_pos * spacing

        # Halo qui glisse d'une option à l'autre (couches très transparentes empilées)
        for k in range(10):
            half = 300 - k * 28
            self.box(cx - half, cx + half, bar_y - 24, bar_y + 24, (*accent, 6))

        # Filets fins au-dessus et en dessous
        self.draw_fade_line(cx, bar_y + 26, 230, accent, 150, steps=12)
        self.draw_fade_line(cx, bar_y - 26, 230, accent, 150, steps=12)

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

        # 1) Dégradé vertical : abysse froide (construit une seule fois)
        steps = 40
        band = h / steps
        top_c = (20, 26, 38)
        bot_c = (3, 4, 7)

        def band_color(i):
            r = i / (steps - 1)
            return (
                int(bot_c[0] + (top_c[0] - bot_c[0]) * r),
                int(bot_c[1] + (top_c[1] - bot_c[1]) * r),
                int(bot_c[2] + (top_c[2] - bot_c[2]) * r),
            )

        def build(shapes):
            from arcade.shape_list import create_rectangle_filled
            for i in range(steps):
                shapes.append(create_rectangle_filled(
                    w / 2, i * band + (band + 1) / 2, w, band + 1, band_color(i)))

        shapes = self.cached_shapes(("menu_gradient", w, h), build)
        if shapes is not None:
            shapes.draw()
        else:
            for i in range(steps):
                self.box(0, w, i * band, (i + 1) * band + 1, band_color(i))

        # 2) Halo doré en haut (l'Arbre-Monde au loin), qui respire
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 0.9)
        for k in range(0, 12, 2):          # 6 ellipses (alpha doublé) au lieu de 12
            r = 60 + k * 38
            arcade.draw_ellipse_filled(
                w / 2, h * 0.78, r * 2.2, r * 1.5,
                (230, 181, 88, int(6 + 4 * pulse)),
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
        """Remet tous les monstres vivants à leur position de départ."""
        for m in self.monsters:
            m.alive = True
            m.hp = m.max_hp
            m.x = m.start_x
            m.y = m.start_y
            m.attack_cooldown = 0
            m.respawn_timer = 0

    def use_item(self, item):
        kind = item.get_kind()
        if kind == "heal":
            self.player.heal(40)
        elif kind == "mana":
            self.player.regen_mana(30)
        else:
            return
        items = self.inventory.get_items()
        if item in items:
            items.remove(item)                   # potion consommée
        self.hotbar = [None if h == item else h for h in self.hotbar]
        self.show_message(f"{item.get_name().strip()} utilisée")

    def use_potion_by_kind(self, kind):
        for it in self.inventory.get_items():
            if it.get_kind() == kind:
                self.use_item(it)
                return
        self.show_message("Aucune potion !")

    def use_skill(self, index):

        # Vérification du déblocage dans l'arbre
        sort_requis = {
            0: "sort_frappe",
            1: "sort_lame",
            2: "sort_soin",
            3: "sort_explosion"
        }

        competence = sort_requis.get(index)

        if competence is not None:
            if not self.player.has_skill(competence):
                self.show_message(
                    "Sort verrouillé : débloque-le dans l'arbre !"
                )
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

        kind = self.equipped_weapon.get_kind()
        px, py = self.player.get_x(), self.player.get_y()

        # ÉPÉE : coup au corps à corps devant le joueur
        if kind == "melee":
            self.attack_cooldown = 0.4
            self.slash_timer = 0.15
            for m in self.monsters:
                if not m.alive:
                    continue
                dx = m.x - px
                dy = m.y - py
                if dx * self.facing > -30 and abs(dx) < 120 and abs(dy) < 60:
                    self.damage_mob(m, self.compute_damage())

        # ARC : tire une flèche vers la souris
        elif kind == "ranged":
            self.attack_cooldown = 0.7

            # Convertit les coordonnées écran en coordonnées du monde
            mouse_world_x = px + self.mouse_x - self.width / 2
            mouse_world_y = py + self.mouse_y - self.height / 2

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
        m.aggro = True

        m.hp -= damage
        if m.hp <= 0:
            m.hp = 0
            m.alive = False
            m.respawn_timer = m.respawn_time
            self.player.gain_xp(40)

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
                    m.aggro = False

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
                    and abs(arrow["x"] - m.x) < 30
                    and abs(arrow["y"] - m.y) < 45
                ):
                    self.damage_mob(m, arrow["damage"])
                    touched = True
                    break

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

    def draw_mob(self):
        for m in self.monsters:
            if not m.alive:
                continue

            # Corps du mob (slime vert)
            arcade.draw_ellipse_filled(m.x, m.y - 5, 56, 44, (70, 190, 90))
            arcade.draw_ellipse_outline(m.x, m.y - 5, 56, 44, (30, 110, 50), 3)
            arcade.draw_circle_filled(m.x - 12, m.y + 5, 5, (170, 240, 180))
            arcade.draw_circle_filled(m.x - 9, m.y - 2, 5, (255, 255, 255))
            arcade.draw_circle_filled(m.x + 9, m.y - 2, 5, (255, 255, 255))
            arcade.draw_circle_filled(m.x - 9, m.y - 2, 2, (0, 0, 0))
            arcade.draw_circle_filled(m.x + 9, m.y - 2, 2, (0, 0, 0))

            # Barre de vie
            ratio = max(0, m.hp / m.max_hp)
            percent = int(round(ratio * 100))

            bar_w = 40
            bar_left = m.x - bar_w / 2
            bar_bottom = m.y + 30
            bar_top = bar_bottom + 5

            self.box(bar_left, bar_left + bar_w, bar_bottom, bar_top, (40, 10, 10))
            if ratio > 0.5:
                color = GREEN
            elif ratio > 0.25:
                color = GOLD_LIGHT
            else:
                color = RED_LIGHT
            self.box(bar_left, bar_left + bar_w * ratio, bar_bottom, bar_top, color)
            self.outline(bar_left, bar_left + bar_w, bar_bottom, bar_top, GOLD_DARK, 1)

            self.text(f"{percent}%", m.x, bar_top + 8, 8, TEXT, anchor_x="center")

    def on_update(self, delta_time):

        self.ui_update(delta_time)

        if self.state == STATE_MENU or self.state == STATE_GAME_OVER:
            return

        if self.inventory_open:
            return

        if self.skill_tree_open:
            return

        if self.pause_open:
            return

        # Recharge du dash
        self.dash_cooldown = max(
            0, self.dash_cooldown - delta_time
        )

        # Détection du sprint avec CTRL
        touches_deplacement = (
            arcade.key.Z in self.keys
            or arcade.key.Q in self.keys
            or arcade.key.S in self.keys
            or arcade.key.D in self.keys
        )

        sprinting = (
            (arcade.key.LCTRL in self.keys or arcade.key.RCTRL in self.keys)
            and touches_deplacement
            and self.stamina > 0
        )

        vitesse = self.player.get_speed()

        if sprinting:
            vitesse *= 1.7
            self.stamina = max(0, self.stamina - 25 * delta_time)

        # Déplacement pendant le dash
        if self.dash_timer > 0:
            self.dash_timer = max(
                0, self.dash_timer - delta_time
            )

            distance = self.dash_speed * delta_time

            self.player.set_x(
                self.player.get_x() + self.dash_dx * distance
            )

        else:
            # Déplacement normal ou sprint
            if arcade.key.Z in self.keys:
                self.player.set_y(
                    self.player.get_y() + vitesse
                )
            if arcade.key.S in self.keys:
                self.player.set_y(
                    self.player.get_y() - vitesse
                )
            if arcade.key.Q in self.keys:
                self.player.set_x(
                    self.player.get_x() - vitesse
                )
            if arcade.key.D in self.keys:
                self.player.set_x(
                    self.player.get_x() + vitesse
                )
        # Empêche le personnage de sortir de l'écran.
                # Limites du monde
        self.player.set_x(max(-1960, min(1960, self.player.get_x())))
        self.player.set_y(max(-1950, min(1920, self.player.get_y())))

        if arcade.key.Q in self.keys:
            self.facing = -1
        if arcade.key.D in self.keys:
            self.facing = 1

        # --- CAMÉRA FLUIDE ---
        target_x = (
            self.player.get_x()
            + self.facing * self.camera_look_ahead
        )

        target_y = self.player.get_y() + 20

        # Interpolation indépendante du nombre d'images par seconde
        smooth = 1 - math.exp(-self.camera_follow_speed * delta_time)

        self.camera_x += (target_x - self.camera_x) * smooth
        self.camera_y += (target_y - self.camera_y) * smooth

        # Régénération de l'endurance hors sprint
        if not sprinting:
            self.stamina = min(
                self.max_stamina,
                self.stamina + 8 * delta_time
            )

        self.update_combat(delta_time)
        self.player.regen_mana(3 * delta_time)

        player_x = self.player.get_x()
        player_y = self.player.get_y()

        for m in self.monsters:
            m.attack_cooldown = max(0, m.attack_cooldown - delta_time)

            if not m.alive:
                continue

            distance_x = player_x - m.x
            distance_y = player_y - m.y
            distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

            # --- IA DES MONSTRES ---
        if m.aggro:
            # Le monstre poursuit le joueur
            if distance > 35:
                m.x += (distance_x / distance) * m.speed * delta_time
                m.y += (distance_y / distance) * m.speed * delta_time

            # Recalcul de la distance après le déplacement
            distance_x = player_x - m.x
            distance_y = player_y - m.y
            distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

            # Le monstre attaque au contact
            if distance < 45 and m.attack_cooldown <= 0:
                dealt = self.player.take_damage(m.damage)
                m.attack_cooldown = 1.0
                self.show_message(f"-{dealt} PV")

                if self.player.get_hp() <= 0:
                    self.state = STATE_GAME_OVER
                    self.game_over_selection = 0
                    self.keys.clear()
                    self.inventory_open = False
                    self.pause_open = False
                    self.message = ""
                    self.message_timer = 0
                    return

        # Limites du monde
        m.x = max(-1900, min(1900, m.x))
        m.y = max(-1900, min(1900, m.y))

    def on_draw(self):
        self.clear()

        # MENU PRINCIPAL : on dessine uniquement lui
        if self.state == STATE_MENU:
            self.gui_camera.use()
            self.draw_main_menu()
            return

        if self.inventory_open or self.skill_tree_open:
            # Le fond n'est visible que derrière l'inventaire : en jeu, le sol
            # (draw_game) le recouvre entièrement, donc inutile de le dessiner.
            self.draw_background()
        else:
            self.draw_game()

        self.gui_camera.use()

        # Interface de jeu uniquement pendant la partie : jamais sur l'inventaire,
        # le menu pause ou l'arbre de compétences, pour ne pas recouvrir ces écrans.
        if (
            not self.inventory_open
            and not self.pause_open
            and not self.skill_tree_open
            and self.state != STATE_GAME_OVER
        ):
            self.draw_hud()

        if self.inventory_open:
            self.draw_inventory()
        if self.pause_open:
            self.draw_pause_menu()
        if self.state == STATE_GAME_OVER:
            self.draw_game_over()
        if self.skill_tree_open:
            self.draw_skill_tree()

    def draw_background(self):
        # Dégradé vertical du haut vers le bas
        top_color = (35, 45, 65)
        bottom_color = (7, 9, 12)

        w, h = self.width, self.height
        steps = 40
        height = h / steps

        def band_color(i):
            ratio = i / (steps - 1)
            return (
                int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio),
                int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio),
                int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio),
            )

        def build(shapes):
            from arcade.shape_list import create_rectangle_filled, create_line
            for i in range(steps):
                shapes.append(create_rectangle_filled(
                    w / 2, i * height + (height + 1) / 2, w, height + 1, band_color(i)))
            # Quelques lignes très discrètes par-dessus
            for x in range(0, int(SCREEN_WIDTH), 80):
                shapes.append(create_line(x, 0, x + 250, SCREEN_HEIGHT, (25, 30, 42), 1))

        # Dégradé + lignes construits une seule fois, puis dessinés d'un bloc
        shapes = self.cached_shapes(("background", w, h), build)
        if shapes is not None:
            shapes.draw()
            return

        for i in range(steps):
            self.box(0, w, i * height, (i + 1) * height + 1, band_color(i))
        for x in range(0, int(SCREEN_WIDTH), 80):
            arcade.draw_line(x, 0, x + 250, SCREEN_HEIGHT, (25, 30, 42), 1)

    def draw_game(self):
        self.camera.position = (
            self.camera_x,
            self.camera_y
        )

        self.camera.use()

        # TOUT LE MONDE DU JEU ICI
        self.box(
            -2000,
            2000,
            -2000,
            2000,
            (24, 38, 29),
        )

        # Personnage
        arcade.draw_circle_filled(
            self.player.get_x(),
            self.player.get_y() + 25,
            20,
            (190, 190, 195),
        )

        self.box(
            self.player.get_x() - 23,
            self.player.get_x() + 23,
            self.player.get_y() - 35,
            self.player.get_y() + 20,
            (85, 88, 95),
        )

        # Objet posé au sol
        if self.objet_sol is not None:
            arcade.draw_circle_filled(
                self.objet_sol_x,
                self.objet_sol_y,
                12,
                GOLD_LIGHT,
            )

            self.text(
                self.objet_sol.get_name(),
                self.objet_sol_x,
                self.objet_sol_y + 25,
                12,
                TEXT,
                anchor_x="center",
            )

            dx = self.player.get_x() - self.objet_sol_x
            dy = self.player.get_y() - self.objet_sol_y
            if (dx ** 2 + dy ** 2) ** 0.5 < 50:
                self.text("F : ramasser", self.objet_sol_x, self.objet_sol_y + 48,
                          13, GOLD_LIGHT, anchor_x="center")

        self.draw_mob()
        self.draw_combat_effects()

        # Arme équipée sur le personnage
        if self.equipped_weapon:
            icon = self.equipped_weapon.get_icon()

            if icon in ("sword", "sword_bas"):
                self.draw_sword(
                    self.player.get_x() + 75,
                    self.player.get_y() + 5,
                    self.character_sword_width,
                    icon == "sword_bas",
                )

            elif icon == "arcleg":
                self.draw_arcleg(
                    self.player.get_x() + 75,
                    self.player.get_y() + 5,
                    self.character_arcleg_width,
                )

            elif icon == "arcbas":
                px = self.player.get_x() + 75
                py = self.player.get_y() + 5
                arcade.draw_arc_outline(
                    px, py, 55, 75, GOLD_LIGHT, 250, 70, 4
                )

        # Bouclier équipé (côté gauche du personnage)
        if self.equipped_shield:
            self.draw_shield(self.player.get_x() - 38, self.player.get_y() + 5)

    # -----------------------------------------------------
    # HUD
    # -----------------------------------------------------
    def draw_hud(self):
        """Interface affichée uniquement pendant le jeu (même style que les menus)."""
        w, h = self.width, self.height
        p = self.player
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 3.0)

        # -------------------- PERSONNAGE EN HAUT À GAUCHE --------------------
        pl, pr, pb, pt = 18, 318, h - 125, h - 18
        self.box(pl, pr, pb, pt, (7, 8, 12, 232))
        self.draw_panel_frame(pl, pr, pb, pt, corner=6, inner=5, mid=False)

        # Médaillon en losange avec un petit portrait géométrique
        mx, my = 62, h - 72
        self.diamond_shape(mx, my, 36, (14, 16, 22), GOLD_DARK, 2)
        self.diamond_shape(mx, my, 30, None, (*GOLD, 120), 1)
        arcade.draw_circle_filled(mx, my + 6, 11, (190, 190, 198))
        self.box(mx - 11, mx + 11, my - 24, my - 6, (83, 87, 98))

        self.shadow_text("HÉROS", 114, h - 38, 17, GOLD_CREAM, anchor_x="left")
        self.shadow_text(f"Niv. {p.get_level()}", 304, h - 38, 13, TEXT, anchor_x="right")
        arcade.draw_line(114, h - 52, 304, h - 52, (*GOLD, 90), 1)

        # Barre de vie
        hp_ratio = p.get_hp() / max(1, p.get_max_hp())
        self.text("PV", 114, h - 70, 10, TEXT_DARK)
        self.draw_bar(142, h - 77, 160, 14, hp_ratio, RED_LIGHT, (55, 18, 22))
        self.text(f"{p.get_hp()} / {p.get_max_hp()}", 222, h - 70, 9, TEXT, anchor_x="center")

        # Barre d'expérience
        xp_ratio = p.get_xp() / max(1, p.get_xp_needed())
        self.text("EXP", 114, h - 98, 10, TEXT_DARK)
        self.draw_bar(142, h - 103, 160, 10, xp_ratio, PURPLE, (25, 20, 48))

        # Rappel : points de compétence à dépenser
        if p.get_skill_points() > 0:
            self.ornament_diamond(28, h - 140, 4 + 2 * pulse, GOLD_LIGHT)
            self.text(f"O : arbre de compétences  (+{p.get_skill_points()})",
                      42, h - 140, 11, GOLD_LIGHT, font=FONT_TITLE)

        # -------------------- STATS EN HAUT À DROITE --------------------
        attack, defense, crit = self.get_stats()
        sl, sr, sb, st = w - 318, w - 18, h - 62, h - 18
        self.box(sl, sr, sb, st, (7, 8, 12, 232))
        self.draw_panel_frame(sl, sr, sb, st, corner=6, inner=5, mid=False)
        for i, (label, value, color) in enumerate((
            ("ATTAQUE", attack, RED_LIGHT),
            ("DÉFENSE", defense, BLUE),
            ("CRITIQUE", f"{crit}%", PURPLE),
        )):
            colx = sl + 50 + i * 100
            self.text(label, colx, st - 14, 8, TEXT_DARK, anchor_x="center")
            self.shadow_text(str(value), colx, st - 31, 15, color)

        # Aide discrète sous les stats
        self.text("ZQSD : bouger  ·  SHIFT : dash  ·  CTRL : sprint",
                  w - 18, h - 78, 9, TEXT_DARK, anchor_x="right")
        self.text("CLIC / ESPACE : attaquer  ·  I : inventaire  ·  O : compétences  ·  ÉCHAP : pause",
                  w - 18, h - 92, 9, TEXT_DARK, anchor_x="right")

        # -------------------- MANA ET ENDURANCE --------------------
        center_x = w / 2
        bar_width = 230
        bar_height = 12
        mana_left = center_x - 255
        stamina_left = center_x + 25
        bar_y = 118

        self.text("MANA", mana_left, bar_y + 20, 10, MANA_BLUE, font=FONT_TITLE)
        self.draw_bar(mana_left, bar_y, bar_width, bar_height,
                      p.get_mana() / max(1, p.get_max_mana()),
                      (65, 135, 245), (14, 25, 52))
        self.text(f"{int(p.get_mana())}/{p.get_max_mana()}",
                  mana_left + bar_width / 2, bar_y + 6, 8, TEXT, anchor_x="center")

        self.text("ENDURANCE", stamina_left, bar_y + 20, 10, STAMINA_GREEN, font=FONT_TITLE)
        self.draw_bar(stamina_left, bar_y, bar_width, bar_height,
                      self.stamina / max(1, self.max_stamina),
                      (80, 200, 110), (15, 37, 23))
        self.text(f"{int(self.stamina)}/{self.max_stamina}",
                  stamina_left + bar_width / 2, bar_y + 6, 8, TEXT, anchor_x="center")

        # -------------------- CADRE INFÉRIEUR : OBJETS + COMPÉTENCES --------------------
        frame_width = 660
        frame_height = 82
        frame_left = (w - frame_width) / 2
        frame_right = frame_left + frame_width
        frame_bottom = 18
        frame_top = frame_bottom + frame_height
        self.box(frame_left, frame_right, frame_bottom, frame_top, (7, 8, 12, 238))
        self.draw_panel_frame(frame_left, frame_right, frame_bottom, frame_top,
                              corner=6, inner=4, mid=True)

        slot_size = 43
        slot_gap = 5
        item_start_x = frame_left + 14
        slot_y = frame_bottom + 9
        self.text("BARRE RAPIDE", item_start_x, frame_top - 12, 9, GOLD_LIGHT, font=FONT_TITLE)

        for i in range(9):
            sx = item_start_x + i * (slot_size + slot_gap)
            self.box(sx, sx + slot_size, slot_y, slot_y + slot_size, (14, 15, 20))
            self.outline(sx, sx + slot_size, slot_y, slot_y + slot_size, GOLD_DARK, 1)
            self.outline(sx + 3, sx + slot_size - 3, slot_y + 3, slot_y + slot_size - 3, (*GOLD, 40), 1)
            self.text(str(i + 1), sx + 4, slot_y + slot_size - 6, 8, TEXT_DARK)

            item = self.hotbar[i]
            if item is not None:
                self.draw_item_icon(item, sx, slot_y + slot_size, slot_size)

        # Quatre emplacements de compétences avec leurs touches de raccourci
        skills = [("T", "FRAPPE", (180, 65, 65)),
                  ("G", "LAME", (135, 75, 185)),
                  ("E", "SOIN", (70, 165, 105)),
                  ("R", "EXPLO", (65, 125, 210))]
        skill_size = 43
        skill_gap = 5
        skills_left = item_start_x + 9 * (slot_size + slot_gap) + 10
        self.text("COMPÉTENCES", skills_left, frame_top - 12, 9, GOLD_LIGHT, font=FONT_TITLE)
        for i, (key_name, skill_name, color) in enumerate(skills):
            sx = skills_left + i * (skill_size + skill_gap)
            self.box(sx, sx + skill_size, slot_y, slot_y + skill_size, (14, 15, 20))
            self.outline(sx, sx + skill_size, slot_y, slot_y + skill_size, color, 2)
            self.ornament_diamond(sx + skill_size / 2, slot_y + 26, 12, color, GOLD_DARK)
            self.text(key_name, sx + skill_size / 2, slot_y + 26, 10, TEXT,
                      anchor_x="center", bold=True)
            self.text(skill_name, sx + skill_size / 2, slot_y + 8, 6, TEXT, anchor_x="center")

        # -------------------- ORBES DE MANA ET D'EXP (réagissent aux valeurs) --------------------
        orb_y = frame_bottom + frame_height / 2
        mana_orb_x = frame_left - 46
        self.draw_orb(mana_orb_x, orb_y, 26,
                      p.get_mana() / max(1, p.get_max_mana()),
                      (60, 125, 235), (12, 22, 48), int(p.get_mana()))
        self.text("MP", mana_orb_x, orb_y - 42, 9, MANA_BLUE, anchor_x="center", font=FONT_TITLE)

        exp_orb_x = frame_right + 46
        self.draw_orb(exp_orb_x, orb_y, 26, xp_ratio,
                      (130, 60, 200), (30, 14, 46), p.get_level())
        self.text("EXP", exp_orb_x, orb_y - 42, 9, (205, 160, 255), anchor_x="center", font=FONT_TITLE)

        # Messages
        self.draw_toast(h - 112)

    # -----------------------------------------------------
    # ARBRE DE COMPÉTENCES : OUVERTURE / FERMETURE / GÉOMÉTRIE
    # -----------------------------------------------------
    def open_skill_tree(self, from_inventory=False):
        self.skill_tree_open = True
        self.skill_from_inventory = from_inventory
        if from_inventory:
            self.inventory_open = False
        self.selected_skill = None
        self.hover_skill = None
        self.skill_scroll = 0.0
        self.skill_scroll_target = 0.0
        self.skill_drag = None
        self.hover_item = None
        self.keys.clear()

    def close_skill_tree(self, return_to_inventory=True):
        self.skill_tree_open = False
        self.selected_skill = None
        self.hover_skill = None
        self.skill_drag = None
        if self.skill_from_inventory and return_to_inventory:
            self.inventory_open = True
        self.skill_from_inventory = False

    def skill_layout(self):
        """Toutes les zones de l'écran de l'arbre (utilisées pour dessiner ET pour les clics)."""
        w, h = self.width, self.height
        L = {}
        L["left"], L["right"] = 70, w - 70
        L["bottom"], L["top"] = 40, h - 40
        L["view_top"] = L["top"] - 128
        L["info_bottom"] = L["bottom"] + 22
        L["info_top"] = L["info_bottom"] + 104
        L["view_bottom"] = L["info_top"] + 14
        L["view_left"] = L["left"] + 28
        L["view_right"] = L["right"] - 44
        L["view_h"] = L["view_top"] - L["view_bottom"]
        L["content_h"] = (self.SKILL_TOP_PAD
                          + SKILL_MAX_ROW * self.SKILL_ROW_H
                          + self.SKILL_BOTTOM_PAD)
        L["max_scroll"] = max(0.0, L["content_h"] - L["view_h"])
        return L

    def skill_node_pos(self, skill_id, L=None):
        L = L or self.skill_layout()
        d = SKILL_TREE[skill_id]
        b = BRANCHES[d["branch"]]
        vw = L["view_right"] - L["view_left"]
        cx = L["view_left"] + vw * b["cx"]
        lane_gap = min(95, vw * 0.085)
        x = cx + d["lane"] * lane_gap
        y = (L["view_top"] - self.SKILL_TOP_PAD
             - d["row"] * self.SKILL_ROW_H + self.skill_scroll)
        return x, y

    def skill_node_at(self, x, y, L=None):
        L = L or self.skill_layout()
        if not (L["view_bottom"] <= y <= L["view_top"]
                and L["view_left"] - 20 <= x <= L["view_right"] + 20):
            return None
        for sid in SKILL_TREE:
            nx, ny = self.skill_node_pos(sid, L)
            if abs(x - nx) + abs(y - ny) <= 36:
                return sid
        return None

    def skill_close_rect(self, L):
        return (L["right"] - 165, L["right"] - 32, L["top"] - 52, L["top"] - 20)

    def skill_unlock_rect(self, L):
        ir = L["right"] - 30
        return (ir - 210, ir - 24, L["info_bottom"] + 14, L["info_bottom"] + 50)

    def skill_scrollbar(self, L):
        """(gauche, droite, bas piste, haut piste, bas curseur, haut curseur) ou None."""
        if L["max_scroll"] <= 0:
            return None
        track_b = L["view_bottom"] + 6
        track_t = L["view_top"] - 6
        track_h = track_t - track_b
        thumb_h = max(36.0, track_h * L["view_h"] / L["content_h"])
        ratio = self.skill_scroll / L["max_scroll"]
        thumb_top = track_t - (track_h - thumb_h) * ratio
        bar_l = L["right"] - 34
        return (bar_l, bar_l + 8, track_b, track_t, thumb_top - thumb_h, thumb_top)

    def skill_scroll_from_bar_y(self, y, L, sb):
        track_b, track_t = sb[2], sb[3]
        thumb_h = sb[5] - sb[4]
        usable = track_t - track_b - thumb_h
        if usable <= 0:
            return 0.0
        center_top = track_t - thumb_h / 2
        ratio = (center_top - (y - self.skill_drag_offset)) / usable
        return max(0.0, min(1.0, ratio)) * L["max_scroll"]

    def skill_set_scroll(self, value):
        value = max(0.0, min(self.skill_layout()["max_scroll"], value))
        self.skill_scroll = value
        self.skill_scroll_target = value

    def scroll_skill_by(self, delta):
        max_scroll = self.skill_layout()["max_scroll"]
        self.skill_scroll_target = max(0.0, min(max_scroll, self.skill_scroll_target + delta))

    def try_unlock_skill(self):
        sid = self.selected_skill
        if sid is None:
            return
        status = self.player.get_skill_status(sid)
        if status == "unlocked":
            self.show_message("Compétence déjà débloquée")
        elif status == "locked":
            self.show_message("Compétence précédente nécessaire")
        elif status == "no_points":
            self.show_message("Pas assez de points")
        elif self.player.unlock_skill(sid):
            self.unlock_fx = (sid, 0.8)
            self.show_message("Compétence débloquée !")

    # -----------------------------------------------------
    # DESSIN DE L'ARBRE
    # -----------------------------------------------------
    def draw_skill_tree(self):
        w, h = self.width, self.height
        L = self.skill_layout()
        pl, pr, pb, pt = L["left"], L["right"], L["bottom"], L["top"]
        vt, vb, vl, vr = L["view_top"], L["view_bottom"], L["view_left"], L["view_right"]
        cx = (pl + pr) / 2
        vw = vr - vl
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 3.0)
        solid = (7, 8, 12, 255)
        p = self.player

        # Fond : voile + bords sombres, panneau opaque, particules dedans
        self.box(0, w, 0, h, (0, 0, 0, 190))
        self.draw_vignette(210)
        self.box(pl, pr, pb, pt, solid)
        self.draw_particles()

        positions = {sid: self.skill_node_pos(sid, L) for sid in SKILL_TREE}

        # ---------- Titres de branches (défilent avec le contenu) ----------
        for bid in BRANCH_ORDER:
            b = BRANCHES[bid]
            bx = vl + vw * b["cx"]
            y_head = vt - 34 + self.skill_scroll
            if vb - 40 < y_head < vt + 40:
                ids = [s for s, d in SKILL_TREE.items() if d["branch"] == bid]
                got = sum(1 for s in ids if p.has_skill(s))
                self.shadow_text(b["label"], bx, y_head, 18, b["color"], bold=True)
                self.text(f"{got} / {len(ids)}", bx, y_head - 20, 10, TEXT_DARK, anchor_x="center")
                self.draw_fade_line(bx, y_head - 34, 110, b["color"], 150, steps=10)

        # ---------- Liaisons ----------
        for sid in SKILL_TREE:
            x2, y2 = positions[sid]
            color = BRANCHES[SKILL_TREE[sid]["branch"]]["color"]
            for req in skill_requirements(sid):
                x1, y1 = positions[req]
                if p.has_skill(req) and p.has_skill(sid):
                    arcade.draw_line(x1, y1, x2, y2, (*GOLD, 55), 9)
                    arcade.draw_line(x1, y1, x2, y2, GOLD_LIGHT, 3)
                elif p.has_skill(req):
                    arcade.draw_line(x1, y1, x2, y2, (*color, 210), 3)
                else:
                    arcade.draw_line(x1, y1, x2, y2, (62, 66, 82), 2)

        # ---------- Nœuds ----------
        for sid, data in SKILL_TREE.items():
            x, y = positions[sid]
            if y < vb - 70 or y > vt + 70:
                continue

            color = BRANCHES[data["branch"]]["color"]
            status = p.get_skill_status(sid)
            selected = self.selected_skill == sid
            hovered = self.hover_skill == sid

            if status == "unlocked":
                self.diamond_shape(x, y, 38 + 3 * pulse, (*color, 28))
                border, border_w = GOLD_LIGHT, 3
                inner = color
                tag_color = (255, 255, 255)
            elif status == "available":
                self.diamond_shape(x, y, 32 + 4 * pulse, None, (*color, 150), 2)
                border, border_w = color, 3
                inner = (48, 56, 76)
                tag_color = (205, 210, 225)
            elif status == "no_points":
                border, border_w = tuple(int(c * 0.55) for c in color), 3
                inner = (34, 38, 50)
                tag_color = (150, 155, 170)
            else:
                border, border_w = (62, 64, 76), 2
                inner = (22, 24, 32)
                tag_color = (95, 98, 110)

            self.diamond_shape(x, y, 30, (10, 11, 16), border, border_w)
            self.diamond_shape(x, y, 22, inner)

            if hovered and not selected:
                self.diamond_shape(x, y, 36, None, (*color, 200), 1)
            if selected:
                self.diamond_shape(x, y, 38, None, (255, 225, 140), 2)

            self.text(skill_main_tag(data), x, y, 9, tag_color, anchor_x="center", bold=True)

            # Flash de déblocage
            if self.unlock_fx is not None and self.unlock_fx[0] == sid:
                prog = 1 - self.unlock_fx[1] / 0.8
                self.diamond_shape(x, y, 30 + 60 * prog, None,
                                   (255, 230, 150, int(220 * (1 - prog))), 3)

            # Nom + coût / état
            self.text(data["name"], x, y - 46, 10, (230, 230, 240), anchor_x="center")
            if status == "unlocked":
                self.text("ACQUISE", x, y - 60, 8, GOLD_LIGHT, anchor_x="center")
            else:
                cost = data["cost"]
                afford = p.get_skill_points() >= cost
                self.text(f"{cost} pt{'s' if cost > 1 else ''}", x, y - 60, 9,
                          GOLD_LIGHT if afford else (150, 150, 160), anchor_x="center")

        # ---------- Caches opaques (haut et bas) : clippent le contenu qui déborde ----------
        self.box(pl, pr, vt, pt, solid)
        self.box(pl, pr, pb, vb, solid)

        # Fondu doux sur les bords de la zone défilante
        for i in range(10):
            a = int(235 * (1 - i / 10) ** 2)
            self.box(pl + 3, pr - 3, vt - (i + 1) * 3, vt - i * 3, (7, 8, 12, a))
            self.box(pl + 3, pr - 3, vb + i * 3, vb + (i + 1) * 3, (7, 8, 12, a))
        self.draw_fade_line(cx, vt, (pr - pl) / 2 - 30, GOLD, 150, inner=0, steps=14)
        self.draw_fade_line(cx, vb, (pr - pl) / 2 - 30, GOLD, 150, inner=0, steps=14)

        # Indicateurs de défilement
        if self.skill_scroll > 2:
            arcade.draw_triangle_filled(cx - 9, vt - 16, cx + 9, vt - 16, cx, vt - 5, GOLD)
        if self.skill_scroll < L["max_scroll"] - 2:
            arcade.draw_triangle_filled(cx - 9, vb + 16, cx + 9, vb + 16, cx, vb + 5, GOLD)

        # Barre de défilement
        sb = self.skill_scrollbar(L)
        if sb is not None:
            self.box(sb[0], sb[1], sb[2], sb[3], (20, 22, 30))
            self.outline(sb[0], sb[1], sb[2], sb[3], GOLD_DARK, 1)
            grabbed = self.skill_drag == "bar"
            over = sb[0] - 6 <= self.mouse_x <= sb[1] + 6 and sb[4] <= self.mouse_y <= sb[5]
            self.box(sb[0], sb[1], sb[4], sb[5], GOLD_LIGHT if (grabbed or over) else GOLD)
            self.outline(sb[0], sb[1], sb[4], sb[5], GOLD_DARK, 1)

        # ---------- En-tête ----------
        self.shadow_text("ARBRE DE COMPÉTENCES", cx, pt - 44, 28, GOLD_CREAM)
        self.draw_divider(cx, pt - 70, half=min(260, (pr - pl) / 2 - 40))
        sp = p.get_skill_points()
        self.text(f"Points de compétence : {sp}", cx, pt - 92, 13,
                  GOLD_LIGHT if sp > 0 else TEXT, anchor_x="center", font=FONT_TITLE)
        self.text("Molette / flèches : défiler   ·   Clic : choisir   ·   Entrée : débloquer",
                  cx, pt - 111, 10, TEXT_DARK, anchor_x="center")

        # Bouton fermer / retour
        cl, cr, cb, ct = self.skill_close_rect(L)
        over = cl <= self.mouse_x <= cr and cb <= self.mouse_y <= ct
        self.box(cl, cr, cb, ct, (60, 44, 22) if over else (14, 15, 20))
        self.outline(cl, cr, cb, ct, GOLD_LIGHT if over else GOLD_DARK, 2)
        self.shadow_text("RETOUR  [O]" if self.skill_from_inventory else "FERMER  [O]",
                         (cl + cr) / 2, (cb + ct) / 2, 12, GOLD_CREAM)

        # ---------- Panneau d'informations ----------
        il, ir, ib, it = pl + 30, pr - 30, L["info_bottom"], L["info_top"]
        self.draw_inset(il, ir, ib, it)

        shown = self.selected_skill or self.hover_skill
        if shown is None:
            self.text("Sélectionne une compétence pour voir ses détails",
                      (il + ir) / 2, (ib + it) / 2, 13, TEXT_DARK,
                      anchor_x="center", font=FONT_TITLE, italic=True)
        else:
            d = SKILL_TREE[shown]
            b = BRANCHES[d["branch"]]
            status = p.get_skill_status(shown)
            x0 = il + 28

            self.shadow_text(d["name"], x0, it - 26, 19, GOLD_CREAM, anchor_x="left")
            self.text(f'{b["label"]}  ·  Palier {d["row"] + 1}', x0, it - 48, 10, b["color"])
            ys = it - 68
            for line, color in skill_effect_lines(d):
                self.text(line, x0, ys, 12, color)
                ys -= 17

            # Description d'ambiance + pré-requis (colonne centrale, si la place le permet)
            x_b = il + 300
            avail = (ir - 216) - x_b
            chars = int(avail / 6.4)
            if chars >= 14:
                for i, line in enumerate(textwrap.wrap(d["flavor"], chars, max_lines=3,
                                                       placeholder="…")):
                    self.text(line, x_b, it - 30 - i * 17, 11, TEXT_DARK,
                              font=FONT_TITLE, italic=True)
                reqs = skill_requirements(shown)
                if reqs:
                    names = ", ".join(SKILL_TREE[r]["name"] for r in reqs)
                    self.text(f"Requiert : {names}", x_b, it - 90, 10,
                              (220, 130, 100) if status == "locked" else TEXT_DARK)

            # Colonne de droite : coût, état, bouton
            cost = d["cost"]
            self.text(f"Coût : {cost} point{'s' if cost > 1 else ''}", ir - 24, it - 26, 12,
                      GOLD_LIGHT if p.get_skill_points() >= cost else (220, 100, 100),
                      anchor_x="right")
            status_txt = {
                "unlocked": ("Compétence acquise", GREEN),
                "locked": ("Pré-requis manquant", (220, 130, 100)),
                "no_points": ("Points insuffisants", (220, 100, 100)),
                "available": ("Prête à être débloquée", (120, 210, 145)),
            }[status]
            self.text(status_txt[0], ir - 24, it - 46, 10, status_txt[1], anchor_x="right")

            if shown == self.selected_skill:
                ul, ur, ubt, ut = self.skill_unlock_rect(L)
                can = status == "available"
                hov = can and ul <= self.mouse_x <= ur and ubt <= self.mouse_y <= ut
                fill = (88, 64, 30) if hov else ((60, 44, 22) if can else (20, 21, 27))
                self.box(ul, ur, ubt, ut, fill)
                self.outline(ul, ur, ubt, ut, GOLD_LIGHT if can else GOLD_DARK, 2)
                label = "ACQUISE" if status == "unlocked" else "DÉBLOQUER"
                self.shadow_text(label, (ul + ur) / 2, (ubt + ut) / 2, 14,
                                 GOLD_CREAM if can else (110, 106, 100))

        # Cadre principal (par-dessus les caches) + message
        self.draw_panel_frame(pl, pr, pb, pt)
        self.draw_toast(vb + 34)

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
            self.player.revive()
            self.player.set_x(0)
            self.player.set_y(0)
            self.reset_monsters()

            # Les monstres ne frappent pas tout de suite après la réapparition
            for m in self.monsters:
                m.attack_cooldown = 2.0

            self.state = STATE_GAME
            self.inventory_open = False
            self.pause_open = False

            self.keys.clear()

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
                self.start_level_1()
            else:
                self.menu_message = "Aucune sauvegarde trouvée"
        elif self.menu_selection == 2:
            self.close()

    def start_level_1(self):
        """Lance le niveau 1 : remet le joueur à sa position de départ."""
        self.state = STATE_GAME
        self.inventory_open = False
        self.pause_open = False
        self.skill_tree_open = False
        self.skill_from_inventory = False
        self.keys.clear()
        self.reset_monsters()
        # Ici : charge la map / les plateformes / les mobs du level 1

    def new_game(self):
        """Supprime l'ancienne sauvegarde et repart de zéro."""
        if SAVE_PATH.exists():
            SAVE_PATH.unlink()            # supprime le fichier save.json

        # Joueur et inventaire neufs (les objets de départ)
        self.player = Player(Inventory([creer_objet(i) for i in INVENTAIRE_DEPART]))
        self.inventory = self.player.get_inventory()
        self.category = "Arme"
        self.inventory.set_category(self.category)

        self.equipped_weapon = None
        self.equipped_shield = None
        self.hotbar = [None] * 9
        self.selected_item = None
        self.hover_item = None
        self.selected_skill = None
        self.hover_skill = None

        self.stamina = self.max_stamina
        self.arrows.clear()
        self.objet_sol = creer_objet(OBJET_SOL_DEPART)

        self.start_level_1()

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
    def inv_layout(self):
        """Géométrie de l'inventaire (dessin + survol + clics utilisent la même)."""
        w, h = self.width, self.height
        L = {}
        L["left"], L["right"] = w * 0.06, w * 0.94
        L["top"], L["bottom"] = h * 0.92, h * 0.08
        ub = h * 0.50
        L["upper_bottom"] = ub

        inv_left = L["left"] + 25
        L["inv_left"] = inv_left

        tabs = []
        tx = inv_left + 150
        for tab in INV_TABS:
            tabs.append((tab, tx, ub - 55, tx + 105, ub - 28))
            tx += 115
        L["tabs"] = tabs

        # Bouton d'accès à l'arbre de compétences, à côté des onglets
        L["skill_btn"] = (tx + 10, ub - 55, tx + 10 + 160, ub - 28)

        L["slot"], L["gap"], L["cols"] = 58, 8, 8
        grid_w = L["cols"] * L["slot"] + (L["cols"] - 1) * L["gap"]
        L["grid_x"] = (L["left"] + L["right"]) / 2 - grid_w / 2
        L["grid_y"] = ub - 78

        L["hotbar_y"] = L["bottom"] + 35
        L["hotbar_x0"] = L["left"] + 150
        return L

    def inv_items(self):
        return [
            item
            for item in self.inventory.get_items()
            if item.get_type() == self.inventory.get_category()
        ]

    def draw_inventory(self):
        L = self.inv_layout()
        left, right, top, bottom = L["left"], L["right"], L["top"], L["bottom"]
        ub = L["upper_bottom"]
        mid = (left + right) / 2
        pulse = 0.5 + 0.5 * math.sin(self.ui_time * 3.0)

        # Fond : voile, particules, bords sombres, puis cadre principal
        self.box(0, self.width, 0, self.height, (0, 0, 0, 150))
        self.draw_particles()
        self.draw_vignette(190)
        self.draw_menu_panel(left, right, bottom, top, alpha=242)

        # Séparateur ornemental entre le haut et le bas
        self.draw_divider(mid, ub, half=(right - left) / 2 - 50)

        # Zone du personnage
        char_left = left + 115
        char_right = left + 355
        char_bottom = ub + 30
        char_top = top - 75

        # ---------------- ÉQUIPEMENT ----------------
        self.shadow_text("ÉQUIPEMENT", left + 35, top - 35, 22, GOLD_CREAM, anchor_x="left")
        arcade.draw_line(left + 35, top - 52, char_right, top - 52, (*GOLD, 90), 1)

        for name, sl, sb, sr, st in self.equipment_slot_rects():
            item = self.get_equipped(name)
            self.draw_slot(sl, sb, sr, st, item is not None)

            if item is not None:
                self.draw_item_icon(item, sl, st, sr - sl)
            else:
                self.text(self.equipment_labels[name], (sl + sr) / 2, (sb + st) / 2,
                          6, TEXT_DARK, anchor_x="center")

        self.draw_inset(char_left, char_right, char_bottom, char_top, GOLD)

        cx = (char_left + char_right) / 2
        cy = (char_bottom + char_top) / 2

        arcade.draw_circle_outline(cx, cy + 30, 62, GOLD_DARK, 2)
        arcade.draw_circle_filled(cx, cy + 45, 20, (170, 170, 175))
        self.box(cx - 25, cx + 25, cy - 55, cy + 25, (75, 78, 85))

        # Arme et bouclier équipés sur le personnage
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

        if self.equipped_shield:
            self.draw_shield(cx - 48, cy + 5)

        # ---------------- STATISTIQUES ----------------
        stats_left = left + 400
        stats_right = right - 35

        self.shadow_text("STATISTIQUES", stats_left, top - 35, 22, GOLD_CREAM, anchor_x="left")
        arcade.draw_line(stats_left, top - 52, stats_right, top - 52, (*GOLD, 90), 1)

        weapon_name = (
            self.equipped_weapon.get_name().strip()
            if self.equipped_weapon else "Aucune"
        )
        self.text(f"Arme : {weapon_name}", stats_right, top - 35, 12,
                  TEXT_DARK, anchor_x="right", font=FONT_TITLE, italic=True)

        self.draw_inset(stats_left, stats_right, char_bottom, char_top, GOLD)

        attack, defense, crit = self.get_stats()
        p = self.player
        weight = round(sum(i.get_weight() for i in self.inventory.get_items()), 1)

        rows_left = [
            ("NIVEAU", p.get_level(), TEXT),
            ("PV", f"{p.get_hp()} / {p.get_max_hp()}", RED_LIGHT),
            ("MANA", f"{int(p.get_mana())} / {p.get_max_mana()}", MANA_BLUE),
            ("XP", f"{p.get_xp()} / {p.get_xp_needed()}", GREEN),
            ("POINTS COMP.", p.get_skill_points(), GOLD_LIGHT),
        ]
        rows_right = [
            ("ATTAQUE", attack, RED_LIGHT),
            ("DÉFENSE", defense, BLUE),
            ("CRITIQUE", f"{crit}%", PURPLE),
            ("VITESSE", p.get_speed(), TEXT),
            ("POIDS", weight, TEXT_DARK),
        ]

        panel_h = char_top - char_bottom
        row_h = min(34, (panel_h - 30) / 5)
        col_width = (stats_right - stats_left) / 2
        for col, rows in enumerate((rows_left, rows_right)):
            x = stats_left + 25 + col * col_width
            for i, (label, value, color) in enumerate(rows):
                y = char_top - 26 - i * row_h
                self.text(label, x, y, 10, TEXT_DARK)
                self.text(str(value), x + 92, y, 13, color)
                arcade.draw_line(x - 4, y - row_h / 2, x + col_width - 45, y - row_h / 2,
                                 (*GOLD, 40), 1)

        # ---------------- INVENTAIRE ----------------
        inv_left = L["inv_left"]
        self.shadow_text("INVENTAIRE", inv_left, ub - 42, 19, GOLD_CREAM, anchor_x="left")

        # Onglets
        for tab, tl, tb, tr, tt in L["tabs"]:
            active = tab == self.category
            self.box(tl, tr, tb, tt, (50, 39, 25) if active else PANEL_DARK)
            self.outline(tl, tr, tb, tt, GOLD if active else GOLD_DARK, 2)
            if active:
                arcade.draw_line(tl + 8, tb + 2, tr - 8, tb + 2, GOLD_LIGHT, 2)
                self.ornament_diamond((tl + tr) / 2, tt + 1, 4, GOLD_LIGHT)
            self.text(tab.upper(), (tl + tr) / 2, (tb + tt) / 2, 10,
                      GOLD_LIGHT if active else TEXT_DARK, anchor_x="center",
                      font=FONT_TITLE, bold=active)

        # Bouton : arbre de compétences
        bl, bb, br, bt = L["skill_btn"]
        hov = self.hover_skill_btn
        sp = self.player.get_skill_points()
        self.box(bl, br, bb, bt, (74, 52, 24) if hov else (40, 30, 20))
        self.outline(bl, br, bb, bt, GOLD_LIGHT, 2)
        self.ornament_diamond(bl + 14, (bb + bt) / 2, 5, GOLD_LIGHT)
        self.text("COMPÉTENCES", (bl + br) / 2 + 8, (bb + bt) / 2, 10,
                  GOLD_CREAM, anchor_x="center", font=FONT_TITLE, bold=True)
        if sp > 0:
            bx, by = br - 4, bt + 2
            arcade.draw_circle_filled(bx, by, 10 + 1.5 * pulse, RED_LIGHT)
            arcade.draw_circle_outline(bx, by, 10 + 1.5 * pulse, GOLD_LIGHT, 2)
            self.text(str(sp), bx, by, 9, (255, 255, 255), anchor_x="center", bold=True)

        # Grille
        slot, gap, cols = L["slot"], L["gap"], L["cols"]
        for i, item in enumerate(self.inv_items()):
            col = i % cols
            row = i // cols

            x = L["grid_x"] + col * (slot + gap)
            y = L["grid_y"] - row * (slot + gap)

            hovered = self.hover_item == item
            selected = self.selected_item == item
            equipped = item == self.equipped_weapon or item == self.equipped_shield

            self.draw_slot(x, y - slot, x + slot, y, hovered or selected or equipped)
            self.draw_item_icon(item, x, y)

        # Barre rapide
        hotbar_y = L["hotbar_y"]
        self.shadow_text("BARRE RAPIDE", left + 25, hotbar_y + 27, 14, GOLD_CREAM, anchor_x="left")

        for i in range(9):
            x = L["hotbar_x0"] + i * 65
            item = self.hotbar[i]

            self.draw_slot(
                x, hotbar_y, x + 55, hotbar_y + 55,
                item is not None and self.selected_item == item,
            )
            self.text(str(i + 1), x + 6, hotbar_y + 48, 8, TEXT_DARK)

            if item is not None:
                self.draw_item_icon(item, x, hotbar_y + 55, 55)

        if self.hover_item:
            self.draw_item_tooltip(self.hover_item, self.mouse_x, self.mouse_y)

        self.draw_toast(self.height * 0.955)

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
        self.box(left, right, bottom, top, PANEL_LIGHT if active else PANEL_DARK)
        self.outline(left, right, bottom, top, GOLD_LIGHT if active else GOLD_DARK, 2)
        self.outline(left + 4, right - 4, bottom + 4, top - 4,
                     (*GOLD, 110 if active else 45), 1)

        if active:
            for x, y in ((left, bottom), (left, top), (right, bottom), (right, top)):
                self.ornament_diamond(x, y, 4, GOLD_LIGHT, GOLD_DARK)

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

    def draw_item_icon(self, item, x, y, size=58):
        """Dessine l'icône centrée dans une case de `size` pixels dont le coin
        haut-gauche est (x, y). Tout est mis à l'échelle (size / 58)."""
        k = size / 58
        cx = x + size / 2
        cy = y - size / 2
        icon = item.get_icon()

        if icon in ("sword", "sword_bas"):
            self.draw_sword(cx, cy, self.inventory_sword_width * k, icon == "sword_bas")

        elif icon == "arcleg":
            # L'arc utilise sa propre image et reste centré dans la case.
            self.draw_arcleg(cx, cy, self.inventory_arcleg_width * k)

        elif icon == "arcbas":
            arcade.draw_arc_outline(cx + 5 * k, cy, 18 * k, 70 * k, GOLD_LIGHT, 250, 70, 3)
            arcade.draw_line(cx - 8 * k, cy - 16 * k, cx + 8 * k, cy + 16 * k, GOLD_LIGHT, 2)

        elif icon == "shield":
            arcade.draw_circle_filled(cx, cy, 18 * k, BLUE)
            arcade.draw_circle_outline(cx, cy, 18 * k, GOLD, 2)
            arcade.draw_circle_filled(cx, cy, 5 * k, GOLD_LIGHT)

        elif icon == "ring":
            arcade.draw_circle_outline(cx, cy, 13 * k, GOLD_LIGHT, 4)

        elif icon in ("potion", "mana"):
            color = RED if icon == "potion" else BLUE
            self.box(cx - 9 * k, cx + 9 * k, cy - 14 * k, cy + 6 * k, color)
            self.box(cx - 4 * k, cx + 4 * k, cy + 6 * k, cy + 14 * k, (200, 200, 210))
            self.box(cx - 5 * k, cx + 5 * k, cy + 14 * k, cy + 17 * k, GOLD_DARK)

        elif icon == "object":
            # Petite clé
            arcade.draw_circle_outline(cx - 7 * k, cy + 5 * k, 6 * k, GOLD_LIGHT, 2)
            arcade.draw_line(cx - 3 * k, cy + 1 * k, cx + 11 * k, cy - 13 * k, GOLD_LIGHT, 3)
            arcade.draw_line(cx + 6 * k, cy - 8 * k, cx + 10 * k, cy - 4 * k, GOLD_LIGHT, 2)

        else:
            self.text("?", cx, cy, 18, GOLD_LIGHT, anchor_x="center")

    # -----------------------------------------------------
    # INFO DE L'OBJET
    # -----------------------------------------------------
    def draw_item_tooltip(self, item, mouse_x, mouse_y):
        width = 300

        desc = item.get_description()
        desc_lines = textwrap.wrap(desc, 40, max_lines=3, placeholder="…") if desc else []

        stats = []
        if item.get_attack():
            stats.append((f"ATK    +{item.get_attack()}", RED_LIGHT))
        if item.get_defense():
            stats.append((f"DEF    +{item.get_defense()}", BLUE))
        if item.get_crit():
            stats.append((f"CRIT   +{item.get_crit()}%", PURPLE))

        height = 78 + 22 * len(stats) + 24
        if desc_lines:
            height += 12 + 17 * len(desc_lines)
        height += 30

        x = mouse_x + 18
        y = mouse_y - height

        if x + width > self.width:
            x = mouse_x - width - 18

        if y < 10:
            y = 10

        self.draw_inset(x, x + width, y, y + height, GOLD_LIGHT)

        ty = y + height - 28
        self.shadow_text(item.get_name(), x + 16, ty, 15, GOLD_CREAM, anchor_x="left")
        ty -= 22
        kind = KIND_LABELS.get(item.get_kind(), item.get_kind())
        self.text(f"{item.get_type()}  ·  {kind}", x + 16, ty, 10, TEXT_DARK,
                  font=FONT_TITLE, italic=True)
        arcade.draw_line(x + 16, ty - 12, x + width - 16, ty - 12, (*GOLD, 90), 1)
        ty -= 32

        for line, color in stats:
            self.text(line, x + 16, ty, 11, color)
            ty -= 22

        self.text(f"POIDS  {item.get_weight()}", x + 16, ty, 10, TEXT_DARK)
        ty -= 24

        for line in desc_lines:
            self.text(line, x + 16, ty, 10, TEXT, font=FONT_TITLE, italic=True)
            ty -= 17

        self.text("CLIC : sélectionner / équiper", x + 16, y + 15, 9, TEXT_DARK)

    # -----------------------------------------------------
    # SOURIS
    # -----------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):

        self.mouse_x = x
        self.mouse_y = y

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

        # ARBRE DE COMPÉTENCES : survol des nœuds
        if self.skill_tree_open:
            self.hover_skill = self.skill_node_at(x, y)
            return

        self.hover_item = None
        self.hover_skill_btn = False

        if not self.inventory_open:
            return

        L = self.inv_layout()

        # Bouton de l'arbre de compétences
        bl, bb, br, bt = L["skill_btn"]
        if bl <= x <= br and bb <= y <= bt:
            self.hover_skill_btn = True
            return

        # Onglets
        for _tab, tl, tb, tr, tt in L["tabs"]:
            if tl <= x <= tr and tb <= y <= tt:
                return

        slot, gap, cols = L["slot"], L["gap"], L["cols"]
        for i, item in enumerate(self.inv_items()):
            col = i % cols
            row = i // cols

            sx = L["grid_x"] + col * (slot + gap)
            sy = L["grid_y"] - row * (slot + gap)

            if sx <= x <= sx + slot and sy - slot <= y <= sy:
                self.hover_item = item
                return

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x = x
        self.mouse_y = y

        if self.skill_tree_open and self.skill_drag is not None:
            L = self.skill_layout()
            if self.skill_drag == "bar":
                sb = self.skill_scrollbar(L)
                if sb is not None:
                    self.skill_set_scroll(self.skill_scroll_from_bar_y(y, L, sb))
            elif self.skill_drag == "pan":
                # Le contenu suit la souris : glisser vers le haut fait défiler vers le bas
                self.skill_set_scroll(self.skill_scroll + dy)
            return

        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        self.skill_drag = None

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.skill_tree_open:
            self.scroll_skill_by(-scroll_y * 70)

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

        # CLICS DANS L'ARBRE DE COMPÉTENCES
        if self.skill_tree_open:

            if button != arcade.MOUSE_BUTTON_LEFT:
                return

            L = self.skill_layout()

            # Bouton fermer / retour
            cl, cr, cb, ct = self.skill_close_rect(L)
            if cl <= x <= cr and cb <= y <= ct:
                self.close_skill_tree(True)
                return

            # Bouton débloquer
            ul, ur, ubt, ut = self.skill_unlock_rect(L)
            if (self.selected_skill is not None
                    and ul <= x <= ur and ubt <= y <= ut):
                self.try_unlock_skill()
                return

            # Barre de défilement
            sb = self.skill_scrollbar(L)
            if sb is not None and sb[0] - 8 <= x <= sb[1] + 8 and sb[2] <= y <= sb[3]:
                if sb[4] <= y <= sb[5]:
                    self.skill_drag_offset = y - (sb[4] + sb[5]) / 2
                else:
                    self.skill_drag_offset = 0.0
                self.skill_drag = "bar"
                self.skill_set_scroll(self.skill_scroll_from_bar_y(y, L, sb))
                return

            # Zone des compétences : sélection d'un nœud ou glisser pour défiler
            if (L["view_left"] - 10 <= x <= L["view_right"] + 10
                    and L["view_bottom"] <= y <= L["view_top"]):
                hit = self.skill_node_at(x, y, L)
                if hit is not None:
                    self.selected_skill = hit
                else:
                    self.skill_drag = "pan"
            return

        if not self.inventory_open:
            if button == arcade.MOUSE_BUTTON_LEFT and not self.pause_open:
                self.mouse_x = x
                self.mouse_y = y
                self.attack()
            return

        L = self.inv_layout()
        hotbar_y = L["hotbar_y"]

        # Clic sur un emplacement d'équipement : on déséquipe
        for name, sl, sb, sr, st in self.equipment_slot_rects():
            if sl <= x <= sr and sb <= y <= st:
                item = self.get_equipped(name)
                if item is not None:
                    self.toggle_equip(item)
                return

        # Barre rapide
        for i in range(9):
            slot_x = L["hotbar_x0"] + i * 65
            if slot_x <= x <= slot_x + 55 and hotbar_y <= y <= hotbar_y + 55:
                if button == arcade.MOUSE_BUTTON_RIGHT:
                    self.hotbar[i] = None
                elif self.selected_item is not None and self.selected_item.get_type() == "Objet":
                    self.hotbar[i] = self.selected_item
                    self.selected_item = None
                    self.inventory.set_selected(None)
                return

        # Bouton : arbre de compétences
        bl, bb, br, bt = L["skill_btn"]
        if button == arcade.MOUSE_BUTTON_LEFT and bl <= x <= br and bb <= y <= bt:
            self.open_skill_tree(from_inventory=True)
            return

        # Onglets
        for tab, tl, tb, tr, tt in L["tabs"]:
            if tl <= x <= tr and tb <= y <= tt:
                self.category = tab
                self.inventory.set_category(tab)
                self.hover_item = None
                self.selected_item = None
                return

        self.on_mouse_motion(x, y, 0, 0)
        item = self.hover_item
        if item is None:
            return
        if item.get_type() in ("Arme", "Équipement"):
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

        # ARBRE DE COMPÉTENCES
        if self.skill_tree_open:
            L = self.skill_layout()

            if key in (arcade.key.O, arcade.key.ESCAPE):
                self.close_skill_tree(True)
            elif key in (arcade.key.I, arcade.key.TAB):
                self.close_skill_tree(False)
            elif key in (arcade.key.UP, arcade.key.Z):
                self.scroll_skill_by(-70)
            elif key in (arcade.key.DOWN, arcade.key.S):
                self.scroll_skill_by(70)
            elif key == arcade.key.PAGEUP:
                self.scroll_skill_by(-L["view_h"] * 0.8)
            elif key == arcade.key.PAGEDOWN:
                self.scroll_skill_by(L["view_h"] * 0.8)
            elif key == arcade.key.HOME:
                self.skill_scroll_target = 0.0
            elif key == arcade.key.END:
                self.skill_scroll_target = L["max_scroll"]
            elif key in (arcade.key.ENTER, arcade.key.RETURN):
                self.try_unlock_skill()

            return

        if key == arcade.key.O:
            self.open_skill_tree(from_inventory=self.inventory_open)
            return

        # INVENTAIRE
        if key == arcade.key.TAB or key == arcade.key.I:
            self.inventory_open = not self.inventory_open
            self.hover_item = None
            self.keys.clear()
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

            # ESQUIVE avec SHIFT
            if key in (arcade.key.LSHIFT, arcade.key.RSHIFT):

                if self.dash_cooldown <= 0 and self.dash_timer <= 0:

                    # Priorité à la direction horizontale demandée
                    if arcade.key.Q in self.keys:
                        self.dash_dx = -1

                    elif arcade.key.D in self.keys:
                        self.dash_dx = 1

                    else:
                        # Sinon, direction dans laquelle regarde le personnage
                        self.dash_dx = self.facing

                    self.dash_timer = self.dash_duration
                    self.dash_cooldown = 4.0

            if key == arcade.key.F and self.objet_sol is not None:
                dx = self.player.get_x() - self.objet_sol_x
                dy = self.player.get_y() - self.objet_sol_y
                distance = (dx ** 2 + dy ** 2) ** 0.5

                if distance < 50:
                    self.player.get_inventory().add_item(self.objet_sol)
                    print("Objet récupéré :", self.objet_sol.get_name())
                    self.objet_sol = None
                else:
                    print("Tu es trop loin de l'objet !")

            if key == arcade.key.SPACE:
                self.attack()

            if key == arcade.key.T:                  # sort : Frappe rapide
                self.use_skill(0)
            elif key == arcade.key.G:                # sort : Lame fantôme
                self.use_skill(1)
            elif key == arcade.key.E:                # sort : Soin
                self.use_skill(2)
            elif key == arcade.key.R:                # sort : Explosion obscure
                self.use_skill(3)
            elif key == arcade.key.H:                # potion de soin
                self.use_potion_by_kind("heal")
            elif key == arcade.key.M:                # potion de mana
                self.use_potion_by_kind("mana")
            elif arcade.key.KEY_1 <= key <= arcade.key.KEY_9:   # barre rapide 1-9
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
            # Paramètres
            print("Paramètres")

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
            item.get_id() if item is not None else None
            for item in self.hotbar
        ]
        data["stamina"] = self.stamina
        data["objet_sol_ramasse"] = self.objet_sol is None

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
            if d.get("id") in CATALOGUE:
                loaded_items.append(creer_objet(d["id"]))

        def find(item_id):
            """Retrouve un objet de l'inventaire à partir de son id."""
            for it in loaded_items:
                if it.get_id() == item_id:
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
        weapon = find(data["equipped_weapon"]["id"]) if data.get("equipped_weapon") else None
        shield = find(data["equipped_shield"]["id"]) if data.get("equipped_shield") else None
        self.equipped_weapon = weapon
        self.equipped_shield = shield
        self.player.set_equipped_weapon(weapon)
        self.player.set_equipped_shield(shield)

        # 4) Barre rapide (9 cases, sauvegardées par nom)
        saved_hotbar = data.get("hotbar", [])
        self.hotbar = [find(n) for n in (saved_hotbar + [None] * 9)[:9]]

        # 5) Le reste
        self.stamina = data.get("stamina", self.max_stamina)
        self.objet_sol = None if data.get("objet_sol_ramasse") else creer_objet(OBJET_SOL_DEPART)
        self.selected_item = None
        self.hover_item = None
        self.selected_skill = None
        self.hover_skill = None
        self.arrows.clear()

        print("Partie chargée avec succès !")
        return True


if __name__ == "__main__":
    game_profiles = [Game.create_profile() for _ in range(20)]
    game = Game()
    arcade.run()