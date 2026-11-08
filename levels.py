"""
levels.py : les 4 niveaux du jeu (maps, zones, mobs, boss, PNJ).

Aucune dépendance à arcade : tout est des données + un petit "constructeur" de map.
Repère : x vers la droite, y vers le HAUT (comme arcade). 1 tuile = TILE pixels.
Pour modifier un niveau, change simplement les appels dans build_levelN().
"""

TILE = 48

# Types de tuiles
AIR, SOLID, ONEWAY, SPIKE, LOCKED, GATE = 0, 1, 2, 3, 4, 5
SOLID_KINDS = (SOLID, LOCKED, GATE)

# ---------------------------------------------------------------------
# THÈMES VISUELS (une ambiance par zone)
# sky_top / sky_bottom : dégradé de fond ; wall / floor : couleurs des blocs
# far / near : silhouettes de parallaxe ; light : teinte des torches/bougies
# ---------------------------------------------------------------------
THEMES = {
    "oubliettes": dict(sky_top=(14, 22, 24), sky_bottom=(4, 7, 8), wall=(40, 52, 50), floor=(52, 66, 62),
                       far=(18, 28, 28), near=(24, 36, 36), light=(120, 200, 170), fog=(40, 90, 80)),
    "cellules": dict(sky_top=(26, 20, 18), sky_bottom=(7, 5, 5), wall=(62, 50, 44), floor=(78, 64, 54),
                     far=(34, 26, 22), near=(44, 34, 28), light=(240, 160, 70), fog=(90, 60, 40)),
    "armes": dict(sky_top=(28, 32, 44), sky_bottom=(7, 8, 12), wall=(68, 74, 88), floor=(88, 94, 110),
                  far=(30, 34, 48), near=(40, 46, 62), light=(255, 190, 90), fog=(60, 70, 100)),
    "cour": dict(sky_top=(24, 40, 70), sky_bottom=(10, 14, 26), wall=(78, 84, 92), floor=(70, 100, 72),
                 far=(20, 30, 50), near=(30, 44, 62), light=(255, 220, 140), fog=(50, 80, 120)),
    "chambres": dict(sky_top=(46, 24, 26), sky_bottom=(12, 6, 8), wall=(96, 62, 56), floor=(116, 78, 62),
                     far=(52, 26, 30), near=(70, 34, 38), light=(255, 170, 90), fog=(110, 50, 50)),
    "salle_manger": dict(sky_top=(58, 38, 22), sky_bottom=(14, 8, 6), wall=(112, 80, 54), floor=(132, 96, 62),
                         far=(64, 40, 24), near=(86, 54, 32), light=(255, 200, 100), fog=(120, 80, 40)),
    "biblio": dict(sky_top=(40, 30, 20), sky_bottom=(10, 7, 5), wall=(84, 60, 40), floor=(104, 76, 50),
                   far=(48, 34, 22), near=(64, 46, 30), light=(255, 210, 120), fog=(100, 70, 30)),
    "guerre": dict(sky_top=(52, 18, 20), sky_bottom=(12, 4, 6), wall=(86, 52, 54), floor=(108, 66, 66),
                   far=(58, 22, 26), near=(78, 30, 34), light=(255, 120, 80), fog=(130, 40, 40)),
    "chapelle": dict(sky_top=(34, 26, 62), sky_bottom=(8, 6, 16), wall=(70, 66, 96), floor=(88, 84, 116),
                     far=(36, 30, 70), near=(48, 40, 88), light=(190, 170, 255), fog=(90, 70, 150)),
    "trone": dict(sky_top=(44, 10, 18), sky_bottom=(8, 2, 5), wall=(74, 34, 44), floor=(98, 52, 62),
                  far=(52, 14, 24), near=(70, 20, 32), light=(255, 190, 70), fog=(140, 30, 40)),
}

# ---------------------------------------------------------------------
# MOBS : tous des slimes, avec des comportements et des éléments différents.
# ai : patrol (patrouille) / hop (saute) / fly (vole) / ranged (tire) / charge (fonce) / tank (lent)
# element : none / fire (brûlure) / ice (ralentit) / lightning (étourdit) / poison (poison)
# ---------------------------------------------------------------------
MOB_TYPES = {
    "gluant":   dict(label="Gluant",   hp=50,  dmg=8,  speed=70,  w=44, h=34, ai="patrol",  element="none",
                     body=(70, 190, 90),   edge=(30, 110, 50),  xp=30),
    "sauteur":  dict(label="Sauteur",  hp=45,  dmg=10, speed=110, w=40, h=34, ai="hop",     element="none",
                     body=(150, 200, 70),  edge=(80, 120, 30),  xp=35),
    "toxique":  dict(label="Toxique",  hp=70,  dmg=7,  speed=60,  w=46, h=36, ai="patrol",  element="poison",
                     body=(150, 70, 190),  edge=(80, 30, 120),  xp=45),
    "braise":   dict(label="Braise",   hp=80,  dmg=12, speed=55,  w=46, h=38, ai="ranged",  element="fire",
                     body=(230, 100, 40),  edge=(150, 40, 20),  xp=55),
    "givre":    dict(label="Givre",    hp=90,  dmg=11, speed=65,  w=46, h=38, ai="patrol",  element="ice",
                     body=(140, 210, 240), edge=(60, 130, 190), xp=55),
    "foudre":   dict(label="Foudre",   hp=75,  dmg=14, speed=90,  w=42, h=36, ai="charge",  element="lightning",
                     body=(240, 225, 80),  edge=(170, 140, 20), xp=65),
    "spectre":  dict(label="Spectre",  hp=60,  dmg=12, speed=85,  w=40, h=34, ai="fly",     element="ice",
                     body=(190, 190, 235), edge=(110, 110, 190), xp=60),
    "cuirasse": dict(label="Cuirassé", hp=220, dmg=22, speed=38,  w=58, h=48, ai="tank",    element="none",
                     body=(120, 130, 140), edge=(60, 66, 78),   xp=90),
}

# Multiplicateur de PV / dégâts / XP des mobs selon le niveau
LEVEL_SCALE = {1: 1.0, 2: 1.6, 3: 2.4, 4: 3.4}

# ---------------------------------------------------------------------
# BOSS : slimes agrandis avec un détail qui les rend reconnaissables.
# patterns1 / patterns2 : attaques de la phase 1 / 2 (phase 2 à 50 % de PV).
# ---------------------------------------------------------------------
BOSSES = {
    "capitaine": dict(name="Capitaine de la garde royale", hp=700, dmg=22, speed=80, w=120, h=96,
                      body=(110, 120, 150), edge=(50, 56, 80), element="none", xp=300, accent=(200, 40, 40),
                      patterns1=["charge", "slam"], patterns2=["charge", "slam", "summon"], summon="gluant"),
    "gouvernante": dict(name="La Gouvernante", hp=520, dmg=18, speed=70, w=104, h=86,
                        body=(150, 90, 170), edge=(80, 40, 100), element="poison", xp=220, accent=(235, 235, 235),
                        patterns1=["shoot", "rain"], patterns2=["shoot", "rain", "slam"], summon="toxique"),
    "cuisinier": dict(name="Le Cuisinier royal", hp=620, dmg=26, speed=75, w=124, h=100,
                      body=(235, 235, 225), edge=(150, 120, 90), element="fire", xp=240, accent=(230, 90, 40),
                      patterns1=["charge", "shoot"], patterns2=["charge", "shoot", "slam"], summon="braise"),
    "connetable": dict(name="Le Connétable", hp=1500, dmg=34, speed=90, w=140, h=112,
                       body=(80, 80, 96), edge=(30, 30, 44), element="lightning", xp=600, accent=(230, 190, 70),
                       patterns1=["charge", "shoot", "slam"], patterns2=["charge", "shoot", "slam", "summon", "rain"],
                       summon="foudre"),
    "roi": dict(name="Le Roi", hp=2000, dmg=44, speed=85, w=150, h=120,
                body=(160, 40, 60), edge=(70, 10, 24), element="fire", xp=900, accent=(255, 215, 80),
                patterns1=["charge", "slam", "shoot"], patterns2=["charge", "slam", "shoot", "rain"], summon="braise"),
    "reine": dict(name="La Reine", hp=1800, dmg=48, speed=95, w=136, h=116,
                  body=(90, 50, 160), edge=(30, 14, 70), element="ice", xp=1200, accent=(255, 215, 80),
                  patterns1=["shoot", "rain", "slam"], patterns2=["shoot", "rain", "slam", "summon", "charge"],
                  summon="spectre"),
}

# ---------------------------------------------------------------------
# PNJ : dialogues à remplir toi-même (pour l'instant des "...")
# ---------------------------------------------------------------------
NPCS = {
    "prisonnier": dict(name="Prisonnier", color=(150, 130, 110), lines=["...", "...", "..."]),
    "servante":   dict(name="Servante",   color=(200, 200, 210), lines=["...", "..."]),
    "erudit":     dict(name="Érudit",     color=(110, 130, 200), lines=["...", "...", "..."]),
    "mercenaire": dict(name="Mercenaire", color=(170, 90, 80),   lines=["...", "..."]),
    "pretre":     dict(name="Prêtre",     color=(220, 210, 240), lines=["...", "...", "..."]),
}

# Contenu des coffres (noms d'objets déjà présents dans ton inventaire)
CHEST_LOOT = {
    "soin":  ["Potion de soin", "Potion de soin"],
    "mana":  ["Potion de mana", "Potion de mana"],
    "mixte": ["Potion de soin", "Potion de mana", "Potion de soin"],
    "cle":   ["Cle"],
}


class Level:
    def __init__(self, index, name, w, h):
        self.index = index
        self.name = name
        self.w = w
        self.h = h
        self.grid = [[AIR] * w for _ in range(h)]       # grid[y][x]
        self.zones = []         # (x0, x1, id, nom affiché, thème)
        self.decor = []         # (kind, tx, ty)
        self.mobs = []          # (kind, tx, ty)
        self.bosses = []        # (id, tx, ty)
        self.npcs = []          # (id, tx, ty)
        self.bonfires = []      # (tx, ty)
        self.chests = []        # (tx, ty, loot)
        self.doors = []         # (tx, ty)  porte de sortie
        self.gates = []         # (tx, ty0, ty1) herses de l'arène du boss
        self.arena = None       # (x0, x1) en tuiles
        self.spawn = (3, 3)
        self.rects = []         # blocs fusionnés pour le dessin (calculés par finish())

    # ---- construction ----
    def fill(self, x0, y0, x1, y1, kind=SOLID):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                self.grid[y][x] = kind

    def clear(self, x0, y0, x1, y1):
        self.fill(x0, y0, x1, y1, AIR)

    def floor(self, x0, x1, top=3):
        self.fill(x0, 0, x1, top - 1)

    def ceil(self, x0, x1, bottom):
        self.fill(x0, bottom, x1, self.h - 1)

    def plat(self, x0, x1, y):
        self.fill(x0, y, x1, y, ONEWAY)

    def block(self, x0, y0, x1, y1):
        self.fill(x0, y0, x1, y1, SOLID)

    def stairs(self, x, y, n, direction=1):
        """Escalier de n marches (1 tuile de haut chacune) ; y = sol de départ."""
        for i in range(n):
            self.fill(x + i * direction, y, x + i * direction, y + i)

    def spikes(self, x0, x1, y):
        self.fill(x0, y, x1, y, SPIKE)

    def pit(self, x0, x1, top=3):
        """Fosse à pointes : le sol disparaît, des piques au fond."""
        self.clear(x0, 0, x1, top - 1)
        self.fill(x0, 0, x1, 0, SOLID)
        self.spikes(x0, x1, 1)

    def zone(self, x0, x1, zid, label, theme):
        self.zones.append((x0, x1, zid, label, theme))

    def deco(self, kind, tx, ty):
        self.decor.append((kind, tx, ty))

    def mob(self, kind, tx, ty):
        self.mobs.append((kind, tx, ty))

    def boss(self, bid, tx, ty):
        self.bosses.append((bid, tx, ty))

    def npc(self, nid, tx, ty):
        self.npcs.append((nid, tx, ty))

    def bonfire(self, tx, ty=3):
        self.bonfires.append((tx, ty))

    def chest(self, tx, ty, loot="soin"):
        self.chests.append((tx, ty, loot))

    def door(self, tx, ty=3):
        self.doors.append((tx, ty))

    def arena_zone(self, x0, x1, gate_top=12):
        """Arène de boss : une herse se ferme en x0 quand le joueur entre."""
        self.arena = (x0, x1)
        self.gates.append((x0, 3, gate_top))

    def lock(self, tx, y0, y1):
        """Porte verrouillée (il faut une Clé, touche F)."""
        self.fill(tx, y0, tx, y1, LOCKED)

    # ---- lecture ----
    def kind_at(self, tx, ty):
        if tx < 0 or tx >= self.w:
            return SOLID
        if ty < 0:
            return AIR
        if ty >= self.h:
            return SOLID
        return self.grid[ty][tx]

    def zone_at(self, tx):
        for z in self.zones:
            if z[0] <= tx < z[1]:
                return z
        return self.zones[-1]

    def theme_at(self, tx):
        return THEMES[self.zone_at(tx)[4]]

    def finish(self):
        """Fusionne les blocs en grands rectangles (dessin rapide)."""
        self.rects = merge_rects(self.grid, self.w, self.h)
        return self


def merge_rects(grid, w, h):
    """Découpe la grille en rectangles de même type (algorithme glouton)."""
    used = [[False] * w for _ in range(h)]
    rects = []
    for y in range(h):
        for x in range(w):
            k = grid[y][x]
            if k == AIR or used[y][x]:
                continue
            x2 = x
            while x2 + 1 < w and grid[y][x2 + 1] == k and not used[y][x2 + 1]:
                x2 += 1
            y2 = y
            while y2 + 1 < h:
                if all(grid[y2 + 1][xx] == k and not used[y2 + 1][xx] for xx in range(x, x2 + 1)):
                    y2 += 1
                else:
                    break
            for yy in range(y, y2 + 1):
                for xx in range(x, x2 + 1):
                    used[yy][xx] = True
            rects.append((x, y, x2, y2, k))
    return rects


def _frame(L, ceiling=20):
    """Murs gauche/droite et plafond communs à tous les niveaux."""
    L.fill(0, 0, 0, L.h - 1)
    L.fill(L.w - 1, 0, L.w - 1, L.h - 1)
    L.ceil(0, L.w - 1, ceiling)


# =====================================================================
# NIVEAU 1 : oubliettes -> cellules -> salle des armes (Capitaine)
# =====================================================================
def build_level1():
    L = Level(1, "Les Oubliettes", 170, 24)
    _frame(L, 20)
    L.zone(0, 58, "oubliettes", "Les Oubliettes", "oubliettes")
    L.zone(58, 112, "cellules", "Les Cellules", "cellules")
    L.zone(112, 170, "armes", "La Salle des Armes", "armes")
    L.floor(1, 169)
    L.spawn = (3, 3)

    # --- Oubliettes : cave basse, fosses et corniches ---
    L.ceil(1, 57, 15)
    L.ceil(26, 40, 13)
    L.pit(18, 21)
    L.pit(46, 49)
    L.plat(10, 14, 7)
    L.plat(23, 28, 8)
    L.stairs(32, 3, 3)                                  # escalier vers la corniche haute
    L.block(35, 3, 45, 5)                               # grande corniche (y=6 au-dessus)
    L.plat(37, 40, 9)
    L.chest(43, 6, "soin")
    L.block(52, 3, 53, 4)
    L.bonfire(5)
    for kind, x, y in [("gluant", 12, 3), ("gluant", 16, 3), ("sauteur", 25, 3), ("gluant", 30, 3),
                       ("toxique", 41, 6), ("sauteur", 44, 6), ("gluant", 55, 3), ("gluant", 12, 7)]:
        L.mob(kind, x, y)
    for x in (6, 24, 38, 54):
        L.deco("torch", x, 8)
    for x in (9, 15, 30, 44):
        L.deco("chain", x, 14)
    L.deco("bones", 20, 1)

    # --- Cellules : couloir au rez-de-chaussée + étage de cellules ---
    L.ceil(58, 111, 17)
    L.plat(62, 65, 5)                                   # on grimpe par des plateformes...
    L.plat(67, 70, 7)
    L.fill(72, 8, 100, 8)                               # ...jusqu'à l'étage des cellules
    L.stairs(106, 3, 6, -1)                             # escalier pour redescendre vers la salle des armes
    L.fill(76, 3, 76, 7)                                # cellule du bas (porte verrouillée)
    L.fill(90, 3, 90, 7)
    L.lock(76, 3, 5)
    L.chest(83, 3, "cle")                               # cellule fermée : une Clé
    L.chest(98, 9, "mixte")
    L.plat(74, 78, 12)
    L.npc("prisonnier", 84, 9)
    L.bonfire(60)
    L.bonfire(110)
    for kind, x, y in [("gluant", 66, 3), ("toxique", 72, 3), ("sauteur", 80, 9),
                       ("gluant", 74, 9), ("toxique", 88, 9), ("sauteur", 96, 9)]:
        L.mob(kind, x, y)
    for x in (64, 80, 94, 104):
        L.deco("torch", x, 6)
    for x in (68, 80, 86, 94):
        L.deco("bars", x, 9)

    # --- Salle des armes : couloir puis grande arène ---
    L.ceil(112, 169, 18)
    L.ceil(112, 128, 11)
    L.plat(140, 146, 8)
    L.plat(150, 156, 8)
    L.plat(135, 138, 12)
    L.arena_zone(130, 168, gate_top=10)
    L.bonfire(116)
    L.boss("capitaine", 154, 3)
    L.door(166, 3)
    for kind, x, y in [("sauteur", 118, 3), ("gluant", 122, 3), ("cuirasse", 126, 3)]:
        L.mob(kind, x, y)
    for x in (114, 120, 126, 134, 148, 160):
        L.deco("rack", x, 3)
    for x in (116, 124, 140, 152, 164):
        L.deco("torch", x, 8)
    L.deco("banner", 132, 14)
    L.deco("banner", 158, 14)
    return L.finish()


# =====================================================================
# NIVEAU 2 : cour intérieure -> chambres des nobles -> salle à manger
# =====================================================================
def build_level2():
    L = Level(2, "Le Château Intérieur", 180, 24)
    _frame(L, 23)
    L.zone(0, 72, "cour", "La Cour Intérieure", "cour")
    L.zone(72, 112, "chambres", "Les Chambres des Nobles", "chambres")
    L.zone(112, 180, "salle_manger", "La Salle à Manger", "salle_manger")
    L.floor(1, 179)
    L.spawn = (3, 3)

    # --- Cour : à ciel ouvert, remparts, fontaine, tours ---
    L.clear(1, 20, 71, 22)                              # le ciel est ouvert (plafond haut)
    L.ceil(1, 71, 22)
    L.block(12, 3, 14, 4)                               # fontaine (marche)
    L.plat(20, 25, 7)
    L.plat(28, 33, 10)
    L.plat(36, 41, 13)
    L.block(44, 3, 52, 6)                               # rempart
    L.stairs(41, 3, 3)
    L.plat(54, 60, 9)
    L.pit(60, 63)
    L.plat(58, 66, 7)
    L.chest(46, 7, "mana")
    L.bonfire(5)
    L.bonfire(68)
    for kind, x, y in [("sauteur", 10, 3), ("givre", 17, 3), ("givre", 24, 7), ("gluant", 30, 3),
                       ("sauteur", 36, 3), ("givre", 46, 7), ("spectre", 38, 11), ("givre", 56, 3),
                       ("sauteur", 66, 3)]:
        L.mob(kind, x, y)
    for x in (8, 22, 34, 50, 64):
        L.deco("torch", x, 9)
    L.deco("tower", 18, 3)
    L.deco("tower", 48, 3)
    L.deco("fountain", 13, 3)
    L.deco("moon", 30, 18)

    # --- Chambres : étage de passage + deux chambres verrouillées en bas ---
    L.ceil(72, 111, 17)
    L.plat(74, 77, 5)
    L.plat(78, 81, 7)
    L.fill(83, 8, 104, 8)                               # étage
    L.stairs(110, 3, 6, -1)                             # escalier de sortie (vers la salle à manger)
    L.fill(86, 3, 86, 7)                                # grande chambre noble (bas) : porte verrouillée
    L.fill(102, 3, 102, 7)
    L.lock(86, 3, 5)
    L.chest(89, 3, "mixte")                             # salle de loot (derrière la porte)
    L.chest(99, 3, "soin")
    L.chest(98, 9, "mana")                              # 2e chambre : sur l'étage, sans clé
    L.chest(73, 3, "mana")
    L.plat(88, 94, 12)
    L.npc("servante", 85, 9)
    for kind, x, y in [("givre", 84, 3), ("braise", 94, 3),
                       ("braise", 90, 9), ("sauteur", 94, 9), ("cuirasse", 100, 9)]:
        L.mob(kind, x, y)
    for x in (80, 92, 100, 108):
        L.deco("torch", x, 6)
    for x in (88, 94, 100):
        L.deco("drape", x, 15)

    # --- Salle à manger : longue table, lustres, arène ---
    L.ceil(112, 179, 19)
    L.ceil(112, 126, 12)
    L.plat(138, 150, 6)                                 # la longue table
    L.plat(130, 135, 10)
    L.plat(153, 158, 10)
    L.plat(142, 148, 13)
    L.arena_zone(130, 178, gate_top=10)
    L.bonfire(116)
    L.boss("gouvernante", 160, 3)
    L.boss("cuisinier", 168, 3)
    L.door(176, 3)
    for kind, x, y in [("braise", 118, 3), ("sauteur", 122, 3)]:
        L.mob(kind, x, y)
    L.deco("table", 138, 6)
    for x in (134, 146, 156, 166):
        L.deco("chandelier", x, 17)
    for x in (116, 124, 132, 172):
        L.deco("torch", x, 8)
    return L.finish()


# =====================================================================
# NIVEAU 3 : bibliothèque (camp) -> salle de guerre (Connétable)
# =====================================================================
def build_level3():
    L = Level(3, "La Citadelle", 190, 26)
    _frame(L, 24)
    L.zone(0, 100, "biblio", "La Bibliothèque", "biblio")
    L.zone(100, 190, "guerre", "La Salle de Guerre", "guerre")
    L.floor(1, 189)
    L.spawn = (3, 3)

    # --- Bibliothèque : étagères = plateformes sur plusieurs étages ---
    L.plat(8, 14, 7)
    L.plat(16, 22, 11)
    L.plat(8, 14, 15)
    L.plat(24, 30, 15)
    L.plat(32, 38, 11)
    L.plat(32, 38, 19)
    L.block(42, 3, 50, 5)
    L.stairs(51, 3, 3)
    L.plat(54, 60, 9)
    L.plat(62, 68, 12)
    L.plat(70, 76, 9)
    L.plat(78, 84, 13)
    L.block(86, 3, 94, 6)
    L.stairs(94, 3, 4, -1)
    L.pit(66, 69)
    L.bonfire(40)                                       # camp avec 2 PNJ
    L.npc("erudit", 36, 3)
    L.npc("mercenaire", 44, 6)
    L.chest(12, 8, "mixte")
    L.chest(35, 20, "soin")
    L.chest(80, 14, "mana")
    L.bonfire(5)
    for kind, x, y in [("spectre", 12, 9), ("foudre", 18, 3), ("cuirasse", 26, 3), ("spectre", 28, 17),
                       ("foudre", 56, 3), ("braise", 58, 9), ("givre", 72, 3), ("spectre", 64, 14),
                       ("foudre", 80, 3), ("cuirasse", 90, 7)]:
        L.mob(kind, x, y)
    for x in range(6, 98, 8):
        L.deco("shelf", x, 3)
    for x in (10, 30, 56, 76, 92):
        L.deco("candle", x, 9)
    L.deco("globe", 46, 3)

    # --- Salle de guerre : grande arène avec table-carte ---
    L.ceil(100, 189, 20)
    L.ceil(100, 118, 12)
    L.bonfire(104)
    L.plat(130, 138, 7)
    L.plat(144, 152, 7)
    L.plat(136, 146, 12)
    L.plat(156, 162, 11)
    L.arena_zone(124, 188, gate_top=10)
    L.boss("connetable", 168, 3)
    L.door(186, 3)
    for kind, x, y in [("foudre", 108, 3), ("cuirasse", 112, 3), ("spectre", 116, 8), ("foudre", 120, 3)]:
        L.mob(kind, x, y)
    L.deco("maptable", 140, 7)
    for x in (110, 126, 150, 176):
        L.deco("banner", x, 15)
    for x in (106, 122, 134, 160, 180):
        L.deco("torch", x, 8)
    return L.finish()


# =====================================================================
# NIVEAU 4 : chapelle -> salle du trône (Roi puis Reine)
# =====================================================================
def build_level4():
    L = Level(4, "Le Sanctuaire Royal", 200, 26)
    _frame(L, 25)
    L.zone(0, 96, "chapelle", "La Chapelle", "chapelle")
    L.zone(96, 200, "trone", "La Salle du Trône", "trone")
    L.floor(1, 199)
    L.spawn = (3, 3)

    # --- Chapelle : bancs (1 tuile = marche), piliers, nef haute ---
    for x in range(10, 40, 6):
        L.block(x, 3, x + 3, 3)                         # bancs
    L.plat(14, 20, 9)
    L.plat(24, 30, 12)
    L.plat(34, 40, 15)
    L.stairs(44, 3, 3)
    L.block(47, 3, 56, 5)
    L.plat(50, 56, 10)
    L.pit(58, 61)
    L.plat(57, 62, 7)
    L.stairs(70, 3, 3)
    L.block(73, 3, 82, 5)
    L.plat(76, 82, 10)
    L.plat(84, 90, 13)
    L.bonfire(5)
    L.bonfire(66)
    L.npc("pretre", 68, 3)
    L.chest(55, 6, "mixte")
    L.chest(86, 14, "soin")
    for kind, x, y in [("foudre", 14, 3), ("braise", 22, 3), ("spectre", 28, 10), ("cuirasse", 34, 3),
                       ("givre", 48, 6), ("spectre", 54, 11), ("foudre", 62, 8), ("cuirasse", 78, 6),
                       ("braise", 86, 3), ("givre", 90, 3)]:
        L.mob(kind, x, y)
    for x in (12, 28, 44, 60, 76, 90):
        L.deco("stained", x, 12)
    for x in range(8, 94, 10):
        L.deco("pillar", x, 3)
    for x in (18, 36, 52, 72):
        L.deco("candle", x, 4)

    # --- Salle du trône : long couloir puis arène royale ---
    L.ceil(96, 199, 21)
    L.ceil(96, 118, 13)
    L.bonfire(100)
    L.plat(132, 140, 7)
    L.plat(146, 154, 7)
    L.plat(138, 148, 12)
    L.plat(160, 168, 9)
    L.arena_zone(126, 198, gate_top=10)
    L.boss("roi", 178, 3)
    L.door(196, 3)
    for kind, x, y in [("cuirasse", 104, 3), ("foudre", 108, 3), ("braise", 112, 3), ("spectre", 116, 8)]:
        L.mob(kind, x, y)
    L.deco("throne", 188, 3)
    for x in (102, 120, 142, 164, 184):
        L.deco("banner", x, 16)
    for x in (106, 124, 150, 172, 192):
        L.deco("torch", x, 8)
    for x in (110, 130, 156, 176):
        L.deco("pillar", x, 3)
    return L.finish()


LEVEL_BUILDERS = {1: build_level1, 2: build_level2, 3: build_level3, 4: build_level4}


def build_level(index):
    return LEVEL_BUILDERS[index]()
