"""
game_world.py : tout ce qui transforme ton jeu en side-scroller à 4 niveaux.

WorldMixin est ajouté à ta classe Game (class Game(WorldMixin, arcade.Window)).
Il utilise tes helpers existants : self.box, self.outline, self.text, self.shadow_text.
La logique (physique, IA) est dans world.py, les maps dans levels.py.
"""
import math
import random

import arcade

from levels import TILE, SOLID, ONEWAY, SPIKE, LOCKED, GATE, THEMES, NPCS, CHEST_LOOT, BOSSES
from world import (
    LevelRuntime, PlayerBody, move_player, player_on_spikes, update_projectiles,
    PLAYER_HW, PLAYER_FEET, PLAYER_H,
)

INTERACT_RANGE = 85
LAST_LEVEL = 4

ELEMENT_COLORS = {
    "none": (230, 230, 230), "fire": (255, 140, 50), "ice": (150, 220, 255),
    "lightning": (255, 235, 90), "poison": (170, 90, 210),
}
GOLD_LIGHT_C = (230, 181, 88)
GOLD_DARK_C = (88, 63, 35)


def shade(c, f, a=None):
    r, g, b = (max(0, min(255, int(v * f))) for v in c[:3])
    return (r, g, b) if a is None else (r, g, b, a)


def lerp_c(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class WorldMixin:
    # =================================================================
    # INITIALISATION
    # =================================================================
    def init_world(self):
        self.level_index = 1
        self.rt = None
        self.body = PlayerBody()
        self.cam_x, self.cam_y = 640.0, 360.0
        self.progress = {}                  # niveau -> {"defeated": [...], "chests": [...], "doors": [...]}
        self.checkpoint = None              # (niveau, x, y) du dernier feu de camp
        self.status = {"burn": 0.0, "poison": 0.0, "slow": 0.0, "stun": 0.0}
        self.dot_t = 0.0
        self.dialog = None
        self.zone_id = None
        self.zone_name = ""
        self.zone_timer = 0.0
        self.victory = False
        self.world_time = 0.0
        self.prompt = ""
        self.theme_cur = dict(THEMES["oubliettes"])
        self.stars = [(random.random(), random.random(), random.randint(1, 2)) for _ in range(50)]

    @property
    def monsters(self):
        return self.rt.monsters if self.rt is not None else []

    def make_item_by_name(self, name):
        for it in self.item_catalog():
            if it.get_name().strip() == name.strip():
                return self.clone_item(it)
        return None

    # =================================================================
    # NIVEAUX, PROGRESSION, SAUVEGARDE
    # =================================================================
    def level_progress(self, index):
        return self.progress.setdefault(index, {"defeated": [], "chests": [], "doors": []})

    def sync_progress(self):
        if self.rt is None:
            return
        p = self.level_progress(self.level_index)
        p["defeated"] = sorted(self.rt.defeated)
        p["chests"] = sorted(self.rt.chests_open)
        p["doors"] = sorted(self.rt.doors_open)

    def start_level(self, index, at_checkpoint=False):
        """Charge un niveau et place le joueur."""
        self.sync_progress()
        self.level_index = index
        p = self.level_progress(index)
        self.rt = LevelRuntime(index, p["defeated"], p["chests"], p["doors"])
        L = self.rt.level
        sx, sy = (L.spawn[0] + 0.5) * TILE, L.spawn[1] * TILE + PLAYER_FEET
        if at_checkpoint and self.checkpoint and self.checkpoint[0] == index:
            sx, sy = self.checkpoint[1], self.checkpoint[2]
        self.player.set_x(sx)
        self.player.set_y(sy)
        self.body.reset()
        self.status = {"burn": 0.0, "poison": 0.0, "slow": 0.0, "stun": 0.0}
        self.dialog = None
        self.victory = False
        self.arrows.clear()
        self.zone_id = None
        self.cam_x, self.cam_y = sx, sy + 60
        self.theme_cur = dict(L.theme_at(int(sx // TILE)))
        if index == 1:
            self.objet_sol_x = 9.5 * TILE
            self.objet_sol_y = 3 * TILE + 16
        self.state = "game"
        self.inventory_open = False
        self.pause_open = False
        self.keys.clear()

    def world_save_data(self):
        self.sync_progress()
        return {
            "level": self.level_index,
            "checkpoint": list(self.checkpoint) if self.checkpoint else None,
            "progress": {str(k): v for k, v in self.progress.items()},
        }

    def world_load_data(self, data):
        self.level_index = int(data.get("level", 1))
        cp = data.get("checkpoint")
        self.checkpoint = tuple(cp) if cp else None
        self.progress = {int(k): v for k, v in data.get("progress", {}).items()}

    def world_new_game(self):
        self.level_index = 1
        self.checkpoint = None
        self.progress = {}
        self.rt = None

    def world_reset_mobs(self):
        if self.rt is not None:
            self.rt.reset_mobs()
            self.rt.reset_boss_fight()

    def respawn_player(self):
        """Après la mort : retour au dernier feu de camp (ou au début du niveau)."""
        self.player.revive()
        self.body.reset()
        self.status = {"burn": 0.0, "poison": 0.0, "slow": 0.0, "stun": 0.0}
        self.world_reset_mobs()
        L = self.rt.level
        sx, sy = (L.spawn[0] + 0.5) * TILE, L.spawn[1] * TILE + PLAYER_FEET
        if self.checkpoint and self.checkpoint[0] == self.level_index:
            sx, sy = self.checkpoint[1], self.checkpoint[2]
        self.player.set_x(sx)
        self.player.set_y(sy)
        self.cam_x, self.cam_y = sx, sy + 60
        for m in self.monsters:
            m.attack_cooldown = 2.0
        self.state = "game"
        self.inventory_open = False
        self.pause_open = False
        self.arrows.clear()
        self.keys.clear()

    # =================================================================
    # DÉGÂTS AU JOUEUR
    # =================================================================
    def hurt_player(self, raw, element="none", src_x=None):
        if self.body.inv > 0 or self.state != "game":
            return
        dealt = self.player.take_damage(int(raw))
        self.body.inv = 0.9
        px = self.player.get_x()
        direction = 1 if (src_x is None or px >= src_x) else -1
        self.body.knock_vx = direction * 330
        self.body.knock_t = 0.16
        self.body.vy = 420
        self.body.on_ground = False
        if element == "fire":
            self.status["burn"] = 3.0
        elif element == "poison":
            self.status["poison"] = 4.0
        elif element == "ice":
            self.status["slow"] = 2.5
        elif element == "lightning":
            self.status["stun"] = 0.45
        self.show_message(f"-{dealt} PV")
        self.check_death()

    def check_death(self):
        if self.player.get_hp() <= 0 and self.state == "game":
            self.death_count += 1
            self.state = "game_over"
            self.game_over_selection = 0
            self.keys.clear()
            self.inventory_open = False
            self.pause_open = False
            self.message = ""
            self.message_timer = 0
            self.dialog = None

    # =================================================================
    # MISE À JOUR (appelée par on_update)
    # =================================================================
    def update_world(self, dt):
        if self.rt is None:
            return
        self.world_time += dt
        if self.victory or self.dialog is not None:
            self.update_camera(dt)
            return

        rt = self.rt
        L = rt.level
        keys = self.keys

        # --- entrées ---
        dirx = (1 if arcade.key.D in keys else 0) - (1 if arcade.key.Q in keys else 0)
        if self.status["stun"] > 0:
            dirx = 0
        slow = 0.55 if self.status["slow"] > 0 else 1.0
        jump_held = arcade.key.SPACE in keys or arcade.key.Z in keys
        down = arcade.key.S in keys
        if dirx != 0:
            self.facing = dirx

        move_player(L, self.player, self.body, dirx, slow, jump_held, down, dt)
        px, py = self.player.get_x(), self.player.get_y()

        # --- pièges et chutes ---
        if player_on_spikes(L, self.player) or py < -200:
            self.spike_hit()
            px, py = self.player.get_x(), self.player.get_y()

        # --- ressources ---
        self.stamina = min(self.max_stamina, self.stamina + 18 * dt)
        self.player.regen_mana(3 * dt)
        self.message_timer = max(0, self.message_timer - dt)

        # --- effets de statut (brûlure / poison) ---
        for k in self.status:
            self.status[k] = max(0.0, self.status[k] - dt)
        if self.status["burn"] > 0 or self.status["poison"] > 0:
            self.dot_t -= dt
            if self.dot_t <= 0:
                self.dot_t = 0.6
                self.player.take_damage(int(3 * rt.scale))
                self.check_death()
                if self.state != "game":
                    return

        # --- combat du joueur ---
        self.update_combat(dt)

        # --- arène de boss, monstres, projectiles ---
        if rt.check_arena(px):
            self.show_message("Combat de boss !", 2.0)
        pyc = py + 5
        rt.update(px, pyc, dt)

        pbox = (px, py - PLAYER_FEET, PLAYER_HW - 4, PLAYER_H)
        for p in update_projectiles(L, rt.ctx.projectiles, dt, pbox):
            self.hurt_player(p["dmg"], p["element"], p["x"] - p["vx"] * 0.1)
            if self.state != "game":
                return

        for m in rt.monsters:
            if not m.alive:
                continue
            if (abs(m.x - px) < m.w / 2 + PLAYER_HW - 6 and abs(m.y - pyc) < m.h / 2 + PLAYER_H / 2 - 6
                    and m.attack_cooldown <= 0 and self.body.inv <= 0):
                m.attack_cooldown = 1.0
                self.hurt_player(m.damage, m.element, m.x)
                if self.state != "game":
                    return
        rt.monsters = [m for m in rt.monsters if m.alive or not m.summoned]

        # --- zone / caméra ---
        z = L.zone_at(int(px // TILE))
        if z[2] != self.zone_id:
            self.zone_id = z[2]
            self.zone_name = z[3]
            self.zone_timer = 3.2
        self.zone_timer = max(0.0, self.zone_timer - dt)
        target = L.theme_at(int(px // TILE))
        for k in ("sky_top", "sky_bottom", "wall", "floor", "far", "near", "light", "fog"):
            self.theme_cur[k] = lerp_c(self.theme_cur[k], target[k], min(1.0, dt * 2.5))
        self.update_camera(dt)
        self.update_prompt()

    def spike_hit(self):
        safe = self.body.last_safe
        L = self.rt.level
        if safe is None:
            safe = ((L.spawn[0] + 0.5) * TILE, L.spawn[1] * TILE + PLAYER_FEET)
        self.hurt_player(int(12 * self.rt.scale), "none", None)
        self.player.set_x(safe[0])
        self.player.set_y(safe[1] + 2)
        self.body.vx = self.body.vy = 0.0
        self.body.inv = 1.2

    def update_camera(self, dt):
        L = self.rt.level
        tx, ty = self.player.get_x(), self.player.get_y() + 70
        k = min(1.0, dt * 7)
        self.cam_x += (tx - self.cam_x) * k
        self.cam_y += (ty - self.cam_y) * k
        hw, hh = self.width / 2, self.height / 2
        lw, lh = L.w * TILE, L.h * TILE
        self.cam_x = lw / 2 if lw <= self.width else max(hw, min(lw - hw, self.cam_x))
        self.cam_y = lh / 2 if lh <= self.height else max(hh, min(lh - hh, self.cam_y))

    # =================================================================
    # INTERACTIONS (touche F)
    # =================================================================
    def interactables(self):
        """Liste de (distance, type, données, texte) des éléments utilisables à proximité."""
        rt = self.rt
        L = rt.level
        px, py = self.player.get_x(), self.player.get_y()
        out = []

        def add(kind, data, x, y, text, rng=INTERACT_RANGE):
            d = math.hypot(px - x, (py - 5) - y)
            if d <= rng:
                out.append((d, kind, data, text))

        if self.objet_sol is not None and self.level_index == 1:
            add("pickup", None, self.objet_sol_x, self.objet_sol_y, "F : ramasser", 60)
        for tx, ty in L.bonfires:
            add("bonfire", (tx, ty), (tx + 0.5) * TILE, ty * TILE + 30, "F : se reposer au feu de camp")
        for tx, ty, loot in L.chests:
            if f"{tx}:{ty}" not in rt.chests_open:
                add("chest", (tx, ty, loot), (tx + 0.5) * TILE, ty * TILE + 20, "F : ouvrir le coffre")
        for nid, tx, ty in L.npcs:
            add("npc", nid, (tx + 0.5) * TILE, ty * TILE + 40, f"F : parler ({NPCS[nid]['name']})")
        for tx, ty in L.doors:
            add("door", (tx, ty), (tx + 1.0) * TILE, ty * TILE + 70,
                "F : franchir la porte" if rt.door_open else "La porte est scellée...", 110)
        lk = rt.locked_near(px, py)
        if lk is not None:
            cx, cy = (lk[0] + 0.5) * TILE, (lk[1] + 0.5) * TILE
            out.append((math.hypot(px - cx, py - cy), "lock", lk,
                        "F : ouvrir avec la Clé" if self.find_key() else "Porte verrouillée (Clé requise)"))
        out.sort(key=lambda o: o[0])
        return out

    def update_prompt(self):
        items = self.interactables()
        self.prompt = items[0][3] if items else ""

    def find_key(self):
        for it in self.inventory.get_items():
            if it.get_name().strip() == "Cle":
                return it
        return None

    def interact(self):
        if self.rt is None:
            return
        if self.dialog is not None:
            self.advance_dialog()
            return
        items = self.interactables()
        if not items:
            return
        _, kind, data, _ = items[0]
        rt = self.rt
        if kind == "pickup":
            self.player.get_inventory().add_item(self.objet_sol)
            self.show_message(f"{self.objet_sol.get_name().strip()} récupéré !")
            self.objet_sol = None
        elif kind == "bonfire":
            self.rest_at_bonfire(data)
        elif kind == "chest":
            self.open_chest(data)
        elif kind == "npc":
            n = NPCS[data]
            self.dialog = {"name": n["name"], "lines": list(n["lines"]), "i": 0, "color": n["color"]}
        elif kind == "door":
            if rt.door_open:
                self.next_level()
            else:
                self.show_message("Vaincs le gardien de la zone pour ouvrir la porte", 2.2)
        elif kind == "lock":
            key = self.find_key()
            if key is None:
                self.show_message("Il te faut une Clé", 2.0)
            else:
                self.inventory.get_items().remove(key)
                self.hotbar = [None if h is key else h for h in self.hotbar]
                rt.unlock(*data)
                self.sync_progress()
                self.show_message("La porte s'ouvre (Clé utilisée)", 2.0)

    def advance_dialog(self):
        d = self.dialog
        if d is None:
            return
        d["i"] += 1
        if d["i"] >= len(d["lines"]):
            self.dialog = None

    def rest_at_bonfire(self, pos):
        tx, ty = pos
        self.player.heal(10 ** 6)
        self.player.regen_mana(10 ** 6)
        self.stamina = self.max_stamina
        self.status = {"burn": 0.0, "poison": 0.0, "slow": 0.0, "stun": 0.0}
        self.checkpoint = (self.level_index, (tx + 0.5) * TILE, ty * TILE + PLAYER_FEET)
        self.rt.reset_mobs()
        self.save_game()
        self.show_message("Feu de camp : partie sauvegardée", 2.2)

    def open_chest(self, data):
        tx, ty, loot = data
        names = CHEST_LOOT.get(loot, CHEST_LOOT["soin"])
        got = []
        for n in names:
            it = self.make_item_by_name(n)
            if it is not None:
                self.player.get_inventory().add_item(it)
                got.append(n)
        self.rt.chests_open.add(f"{tx}:{ty}")
        self.sync_progress()
        self.show_message("Coffre : " + ", ".join(got), 2.5)

    def next_level(self):
        self.sync_progress()
        if self.level_index >= LAST_LEVEL:
            self.victory = True
            self.keys.clear()
            self.save_game()
            return
        self.checkpoint = None
        self.start_level(self.level_index + 1)
        self.player.heal(10 ** 6)
        self.save_game()
        self.show_message(f"Niveau {self.level_index} : {self.rt.level.name}", 3.0)

    # =================================================================
    # DESSIN : FOND AVEC PARALLAXE (remplace ton draw_background)
    # =================================================================
    def draw_background(self):
        th = self.theme_cur
        w, h = self.width, self.height
        steps = 48
        bh = h / steps
        for i in range(steps):
            r = i / (steps - 1)
            c = lerp_c(th["sky_top"], th["sky_bottom"], r)
            self.box(0, w, h - (i + 1) * bh - 1, h - i * bh, c)
        if self.rt is None:
            return
        outdoor = self.zone_id == "cour"
        if outdoor:
            for sx, sy, s in self.stars:
                arcade.draw_circle_filled(sx * w, h * (0.45 + 0.55 * sy), s, (220, 225, 255, 150))
        # couches de parallaxe : colonnes + arches
        for layer, (factor, col, top_frac, width) in enumerate(((0.22, th["far"], 0.62, 190),
                                                                 (0.45, th["near"], 0.50, 150))):
            off = (self.cam_x * factor) % (width * 2)
            n = int(w / (width * 2)) + 3
            for i in range(-1, n):
                x = i * width * 2 - off + (width if layer else 0)
                ph = h * top_frac * (0.8 + 0.2 * ((i + int(self.cam_x * factor // (width * 2))) % 3) / 2)
                self.box(x, x + width * 0.45, 0, ph, col)
                if outdoor and layer == 0:
                    for k in range(3):
                        self.box(x + k * width * 0.18, x + k * width * 0.18 + width * 0.1, ph, ph + 14, col)
                else:
                    arcade.draw_circle_filled(x + width * 0.225, ph, width * 0.225, col)
        # brume basse
        for i in range(6):
            self.box(0, w, i * 14, (i + 1) * 14, (*th["fog"], 16))

    # =================================================================
    # DESSIN : LE MONDE (remplace ton draw_game)
    # =================================================================
    def draw_game(self):
        if self.rt is None:
            return
        rt = self.rt
        L = rt.level
        sh = rt.ctx.shake
        ox = random.uniform(-6, 6) * sh * 2 if sh > 0 else 0
        oy = random.uniform(-6, 6) * sh * 2 if sh > 0 else 0
        self.camera.position = (self.cam_x + ox, self.cam_y + oy)
        self.camera.use()

        vx0, vx1 = self.cam_x - self.width / 2 - 64, self.cam_x + self.width / 2 + 64
        vy0, vy1 = self.cam_y - self.height / 2 - 64, self.cam_y + self.height / 2 + 64

        self.draw_back_wall(vx0, vx1, vy0, vy1)
        self.draw_decor(vx0, vx1, vy0, vy1)
        self.draw_tiles(vx0, vx1, vy0, vy1)
        self.draw_entities(vx0, vx1)
        self.draw_mob()
        self.draw_projectiles()
        self.draw_player()
        self.draw_combat_effects()

    # ---- mur de fond ----
    def lines(self, pts, color, width=1):
        if not pts:
            return
        try:
            arcade.draw_lines(pts, color, width)
        except Exception:
            for i in range(0, len(pts) - 1, 2):
                arcade.draw_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, width)

    def zone_segments(self, x0, x1):
        """Découpe [x0, x1[ (pixels) en segments (début, fin, thème) selon les zones."""
        L = self.rt.level
        segs = []
        for z in L.zones:
            a, b = max(x0, z[0] * TILE), min(x1, z[1] * TILE)
            if b > a:
                segs.append((a, b, THEMES[z[4]], z[2]))
        return segs

    def draw_back_wall(self, vx0, vx1, vy0, vy1):
        L = self.rt.level
        y0, y1 = max(0, vy0), min(L.h * TILE, vy1)
        for a, b, th, zid in self.zone_segments(max(0, vx0), min(L.w * TILE, vx1)):
            if zid == "cour":
                continue
            self.box(a, b, y0, y1, (*th["near"], 175))
            pts = []
            r0 = int(y0 // TILE)
            r1 = int(y1 // TILE) + 1
            for r in range(r0, r1):
                y = r * TILE
                pts += [(a, y), (b, y)]
                start = int(a // TILE) - 1
                for c in range(start, int(b // TILE) + 2):
                    x = c * TILE + (TILE / 2 if r % 2 else 0)
                    if a <= x <= b:
                        pts += [(x, y), (x, y + TILE)]
            self.lines(pts, (*shade(th["wall"], 0.85), 70), 1)

    # ---- tuiles ----
    def draw_tiles(self, vx0, vx1, vy0, vy1):
        L = self.rt.level
        for (x0, y0, x1, y1, k) in L.rects:
            left, right = x0 * TILE, (x1 + 1) * TILE
            bottom, top = y0 * TILE, (y1 + 1) * TILE
            if right < vx0 or left > vx1 or top < vy0 or bottom > vy1:
                continue
            if k == SOLID:
                self.draw_solid(left, right, bottom, top, vx0, vx1, vy0, vy1, y1)
            elif k == ONEWAY:
                th = L.theme_at(x0)
                for tx in range(x0, x1 + 1):
                    px = tx * TILE
                    self.box(px, px + TILE, top - 12, top, shade(th["floor"], 1.15))
                    self.box(px, px + TILE, top - 16, top - 12, shade(th["wall"], 0.6))
                    self.box(px + 4, px + 9, top - 30, top - 16, shade(th["wall"], 0.7))
                    self.box(px + TILE - 9, px + TILE - 4, top - 30, top - 16, shade(th["wall"], 0.7))
            elif k == SPIKE:
                for tx in range(x0, x1 + 1):
                    for ty in range(y0, y1 + 1):
                        bx, by = tx * TILE, ty * TILE
                        for i in range(3):
                            arcade.draw_triangle_filled(bx + i * 16, by, bx + i * 16 + 16, by,
                                                        bx + i * 16 + 8, by + 30, (170, 175, 190))
                            arcade.draw_triangle_filled(bx + i * 16 + 8, by + 30, bx + i * 16 + 16, by,
                                                        bx + i * 16 + 8, by, (110, 114, 130))
            elif k == LOCKED:
                self.box(left, right, bottom, top, (62, 44, 30))
                self.outline(left, right, bottom, top, GOLD_DARK_C, 3)
                for i in range(y0, y1 + 1):
                    arcade.draw_line(left + 4, i * TILE + 8, right - 4, i * TILE + 8, (30, 22, 16), 2)
                cy = (bottom + top) / 2
                arcade.draw_circle_filled((left + right) / 2, cy, 9, GOLD_LIGHT_C)
                self.box((left + right) / 2 - 2, (left + right) / 2 + 2, cy - 12, cy - 2, (40, 30, 20))
            elif k == GATE:
                self.box(left, right, bottom, top, (20, 20, 26, 190))
                for i in range(int(bottom // 16), int(top // 16)):
                    pass
                for xx in range(int(left) + 6, int(right), 16):
                    arcade.draw_line(xx, bottom, xx, top, (110, 114, 124), 5)
                for yy in range(int(bottom) + 20, int(top), 70):
                    arcade.draw_line(left, yy, right, yy, (80, 84, 94), 4)

    def draw_solid(self, left, right, bottom, top, vx0, vx1, vy0, vy1, top_row):
        L = self.rt.level
        a0, b0 = max(left, vx0), min(right, vx1)
        for a, b, th, _ in self.zone_segments(a0, b0):
            self.box(a, b, bottom, top, th["wall"])
            pts = []
            r0 = int(max(bottom, vy0) // TILE)
            r1 = int(min(top, vy1) // TILE) + 1
            for r in range(r0, r1):
                y = r * TILE
                if bottom < y < top:
                    pts += [(a, y), (b, y)]
                for c in range(int(a // TILE), int(b // TILE) + 2):
                    x = c * TILE + (TILE / 2 if r % 2 else 0)
                    if a < x < b and y < top:
                        pts += [(x, y), (x, min(y + TILE, top))]
            self.lines(pts, shade(th["wall"], 0.72), 1)
            # arête haute éclairée si l'air est au-dessus
            if L.kind_at(int(a // TILE), top_row + 1) != SOLID:
                self.box(a, b, top - 8, top, th["floor"])
                self.box(a, b, top - 11, top - 8, shade(th["floor"], 0.7))
            # ombre sous les plafonds
            if L.kind_at(int(a // TILE), int(bottom // TILE) - 1) != SOLID and bottom > 0:
                self.box(a, b, bottom, bottom + 6, shade(th["wall"], 0.55))

    # ---- décors ----
    def draw_decor(self, vx0, vx1, vy0, vy1):
        L = self.rt.level
        t = self.world_time
        for kind, tx, ty in L.decor:
            x, y = tx * TILE, ty * TILE
            if x < vx0 - 250 or x > vx1 + 250:
                continue
            th = L.theme_at(tx)
            c = x + TILE / 2
            light = th["light"]
            if kind == "torch":
                fl = 1 + 0.18 * math.sin(t * 11 + tx)
                self.box(c - 3, c + 3, y - 4, y + 22, (60, 44, 32))
                self.box(c - 8, c + 8, y + 20, y + 26, (80, 80, 88))
                arcade.draw_circle_filled(c, y + 40, 90 * fl, (*light, 14))
                arcade.draw_circle_filled(c, y + 40, 55 * fl, (*light, 22))
                arcade.draw_triangle_filled(c - 9, y + 26, c + 9, y + 26, c, y + 54 * fl, (255, 150, 50))
                arcade.draw_triangle_filled(c - 5, y + 26, c + 5, y + 26, c, y + 42 * fl, (255, 225, 120))
            elif kind == "chain":
                for i in range(7):
                    arcade.draw_ellipse_outline(c, y - i * 16, 8, 14, (90, 94, 100), 2)
            elif kind == "bones":
                arcade.draw_circle_filled(c, y + 8, 9, (200, 195, 180))
                arcade.draw_line(c + 10, y + 4, c + 40, y + 2, (200, 195, 180), 4)
                arcade.draw_line(c - 30, y + 2, c - 10, y + 6, (190, 185, 170), 3)
            elif kind == "bars":
                self.box(x, x + 2 * TILE, y + 40, y + 190, (6, 8, 10, 220))
                for i in range(7):
                    arcade.draw_line(x + 6 + i * 14, y + 40, x + 6 + i * 14, y + 190, (90, 94, 104), 4)
                self.outline(x, x + 2 * TILE, y + 40, y + 190, (60, 62, 70), 4)
            elif kind == "rack":
                self.box(x, x + 3 * TILE, y + 40, y + 52, (84, 56, 32))
                for i in range(5):
                    bx = x + 14 + i * 28
                    arcade.draw_line(bx, y + 52, bx, y + 120 + (i % 2) * 20, (170, 176, 190), 5)
                    self.box(bx - 8, bx + 8, y + 52, y + 58, (130, 100, 50))
                self.box(x, x + 4, y, y + 52, (84, 56, 32))
                self.box(x + 3 * TILE - 4, x + 3 * TILE, y, y + 52, (84, 56, 32))
            elif kind == "banner":
                col = {"armes": (150, 30, 40), "salle_manger": (160, 110, 40), "guerre": (150, 30, 30),
                       "trone": (200, 150, 40), "chapelle": (90, 60, 160)}.get(self.rt.level.zone_at(tx)[4], (120, 30, 40))
                self.box(c - 24, c + 24, y - 110, y, col)
                arcade.draw_triangle_filled(c - 24, y - 110, c + 24, y - 110, c, y - 140, col)
                self.box(c - 30, c + 30, y, y + 6, (90, 70, 40))
                arcade.draw_circle_filled(c, y - 55, 10, GOLD_LIGHT_C)
            elif kind == "tower":
                self.box(x, x + 3 * TILE, y, y + 9 * TILE, shade(th["wall"], 0.75))
                for i in range(4):
                    self.box(x + i * 36, x + i * 36 + 22, y + 9 * TILE, y + 9 * TILE + 22, shade(th["wall"], 0.75))
                self.box(x + 60, x + 84, y + 5 * TILE, y + 5 * TILE + 70, (255, 200, 100, 190))
            elif kind == "fountain":
                arcade.draw_ellipse_filled(c + TILE, y + 12, 170, 40, (90, 98, 112))
                arcade.draw_ellipse_filled(c + TILE, y + 20, 150, 28, (60, 110, 160))
                self.box(c + TILE - 6, c + TILE + 6, y + 20, y + 70, (110, 116, 130))
                for i in range(4):
                    ph = (t * 1.6 + i * 0.25) % 1
                    arcade.draw_circle_filled(c + TILE + (i - 1.5) * 14 * ph, y + 70 - 40 * ph * ph + 14, 3, (160, 210, 255, 200))
            elif kind == "moon":
                arcade.draw_circle_filled(c, y, 54, (230, 232, 250, 230))
                arcade.draw_circle_filled(c + 16, y + 6, 46, (*self.theme_cur["sky_top"], 255))
            elif kind == "drape":
                col = (130, 30, 50)
                self.box(c - 40, c + 40, y - 150, y, col)
                for i in range(5):
                    arcade.draw_line(c - 40 + i * 20, y, c - 40 + i * 20, y - 150, shade(col, 0.7), 3)
                self.box(c - 46, c + 46, y, y + 8, GOLD_DARK_C)
            elif kind == "table":
                self.box(x, x + 13 * TILE, y + 2, y + 14, (110, 74, 42))
                self.box(x + 10, x + 22, y - TILE * 3, y + 2, (80, 52, 30))
                self.box(x + 13 * TILE - 22, x + 13 * TILE - 10, y - TILE * 3, y + 2, (80, 52, 30))
                for i in range(8):
                    arcade.draw_circle_filled(x + 40 + i * 74, y + 20, 9, (210, 210, 200))
                    arcade.draw_circle_filled(x + 70 + i * 74, y + 18, 6, (200, 150, 70))
            elif kind == "chandelier":
                self.lines([(c, y + 90), (c, y)], (90, 90, 96), 3)
                arcade.draw_ellipse_outline(c, y - 6, 120, 18, GOLD_LIGHT_C, 4)
                for i in range(5):
                    cx2 = c - 48 + i * 24
                    self.box(cx2 - 2, cx2 + 2, y - 4, y + 12, (230, 225, 200))
                    fl = 1 + 0.2 * math.sin(t * 10 + i)
                    arcade.draw_triangle_filled(cx2 - 4, y + 12, cx2 + 4, y + 12, cx2, y + 26 * fl, (255, 190, 80))
                arcade.draw_circle_filled(c, y, 130, (*light, 12))
            elif kind == "shelf":
                sh = 6 * TILE
                self.box(x, x + 3 * TILE, y, y + sh, shade(th["wall"], 0.65))
                self.outline(x, x + 3 * TILE, y, y + sh, (50, 34, 22), 4)
                for r in range(5):
                    by = y + 12 + r * 56
                    self.box(x, x + 3 * TILE, by + 44, by + 50, (50, 34, 22))
                    bx = x + 8
                    k = 0
                    while bx < x + 3 * TILE - 14:
                        bw = 8 + ((k * 7 + r * 3 + tx) % 3) * 3
                        bh = 28 + ((k * 5 + r + tx) % 4) * 4
                        colr = ((150, 50, 50), (60, 90, 140), (60, 120, 80), (150, 110, 50), (110, 70, 140))[(k + r + tx) % 5]
                        self.box(bx, bx + bw, by + 6, by + 6 + bh, colr)
                        bx += bw + 2
                        k += 1
            elif kind == "candle":
                self.box(c - 4, c + 4, y, y + 22, (230, 225, 205))
                fl = 1 + 0.2 * math.sin(t * 9 + tx)
                arcade.draw_triangle_filled(c - 5, y + 22, c + 5, y + 22, c, y + 38 * fl, (255, 190, 80))
                arcade.draw_circle_filled(c, y + 28, 60, (*light, 14))
            elif kind == "globe":
                arcade.draw_circle_filled(c, y + 52, 30, (70, 100, 140))
                arcade.draw_circle_outline(c, y + 52, 32, GOLD_LIGHT_C, 3)
                self.box(c - 4, c + 4, y, y + 22, GOLD_DARK_C)
            elif kind == "maptable":
                self.box(x, x + 9 * TILE, y + 2, y + 14, (110, 74, 42))
                self.box(x + 24, x + 9 * TILE - 24, y + 14, y + 18, (200, 180, 130))
                for i in range(6):
                    arcade.draw_circle_filled(x + 60 + i * 60, y + 24, 7, (200, 60, 50) if i % 2 else (60, 90, 190))
            elif kind == "stained":
                col = [(190, 70, 90), (80, 110, 210), (230, 190, 80), (110, 190, 130)]
                self.box(x, x + 2 * TILE, y, y + 6 * TILE, (14, 12, 26))
                for i in range(2):
                    for j in range(5):
                        self.box(x + 6 + i * 44, x + 6 + i * 44 + 40, y + 8 + j * 56, y + 8 + j * 56 + 50,
                                 (*col[(i + j + tx) % 4], 210))
                arcade.draw_circle_filled(x + TILE, y + 6 * TILE, TILE, (14, 12, 26))
                arcade.draw_circle_filled(x + TILE, y + 6 * TILE, TILE - 8, (*col[(tx) % 4], 210))
                self.outline(x, x + 2 * TILE, y, y + 6 * TILE, (60, 56, 86), 4)
                arcade.draw_triangle_filled(x + 10, y, x + 2 * TILE - 10, y, x + TILE, y - 90, (*light, 14))
            elif kind == "pillar":
                ph = 13 * TILE
                self.box(c - 24, c + 24, y, y + ph, shade(th["wall"], 1.0))
                self.box(c - 24, c - 14, y, y + ph, shade(th["wall"], 1.25))
                self.box(c - 34, c + 34, y, y + 16, shade(th["wall"], 0.8))
                self.box(c - 34, c + 34, y + ph - 16, y + ph, shade(th["wall"], 0.8))
            elif kind == "throne":
                self.box(x - 40, x + 3 * TILE, y, y + 30, (110, 30, 40))
                self.box(x, x + 2 * TILE, y + 30, y + 120, (150, 40, 50))
                self.box(x - 10, x + 2 * TILE + 10, y + 120, y + 300, (60, 20, 28))
                arcade.draw_triangle_filled(x - 10, y + 300, x + 2 * TILE + 10, y + 300, x + TILE, y + 380, GOLD_LIGHT_C)
                self.outline(x - 10, x + 2 * TILE + 10, y + 120, y + 300, GOLD_LIGHT_C, 4)

    # ---- objets du monde : feux, coffres, PNJ, porte ----
    def draw_entities(self, vx0, vx1):
        rt = self.rt
        L = rt.level
        t = self.world_time
        for tx, ty in L.bonfires:
            x, y = (tx + 0.5) * TILE, ty * TILE
            if abs(x - self.cam_x) > self.width:
                continue
            lit = self.checkpoint is not None and self.checkpoint[0] == self.level_index and \
                abs(self.checkpoint[1] - x) < 2
            arcade.draw_ellipse_filled(x, y + 6, 70, 16, (70, 72, 80))
            self.box(x - 22, x + 22, y + 4, y + 14, (60, 42, 30))
            fl = 1 + 0.2 * math.sin(t * 12 + tx)
            if lit:
                arcade.draw_circle_filled(x, y + 36, 120 * fl, (255, 170, 60, 16))
                arcade.draw_triangle_filled(x - 18, y + 12, x + 18, y + 12, x, y + 66 * fl, (255, 140, 40))
                arcade.draw_triangle_filled(x - 10, y + 12, x + 10, y + 12, x, y + 48 * fl, (255, 220, 110))
            else:
                arcade.draw_triangle_filled(x - 14, y + 12, x + 14, y + 12, x, y + 34, (90, 70, 60))
                arcade.draw_circle_filled(x, y + 22, 4, (255, 170, 60, 120))
        for tx, ty, loot in L.chests:
            x, y = tx * TILE, ty * TILE
            if abs(x - self.cam_x) > self.width:
                continue
            opened = f"{tx}:{ty}" in rt.chests_open
            self.box(x + 4, x + 44, y, y + 24, (96, 64, 34))
            self.outline(x + 4, x + 44, y, y + 24, GOLD_DARK_C, 2)
            if opened:
                self.box(x + 4, x + 44, y + 24, y + 30, (70, 46, 26))
                arcade.draw_circle_filled(x + 24, y + 32, 4, (255, 230, 140, 140))
            else:
                self.box(x + 4, x + 44, y + 24, y + 38, (116, 78, 40))
                self.outline(x + 4, x + 44, y + 24, y + 38, GOLD_DARK_C, 2)
                arcade.draw_circle_filled(x + 24, y + 24, 5, GOLD_LIGHT_C)
        for nid, tx, ty in L.npcs:
            n = NPCS[nid]
            x, y = (tx + 0.5) * TILE, ty * TILE
            if abs(x - self.cam_x) > self.width:
                continue
            col = n["color"]
            bob = math.sin(t * 2 + tx) * 1.5
            self.box(x - 15, x + 15, y, y + 44 + bob, col)
            arcade.draw_circle_filled(x, y + 56 + bob, 13, shade(col, 1.2))
            arcade.draw_triangle_filled(x - 16, y + 54 + bob, x + 16, y + 54 + bob, x, y + 78 + bob, shade(col, 0.7))
            arcade.draw_circle_filled(x + 4, y + 56 + bob, 2, (20, 20, 20))
            self.text(n["name"], x, y + 92, 11, (225, 218, 201), anchor_x="center")
        for tx, ty in L.doors:
            x, y = tx * TILE, ty * TILE
            if abs(x - self.cam_x) > self.width:
                continue
            w, h = 2 * TILE, 3 * TILE + 10
            if rt.door_open:
                self.box(x, x + w, y, y + h, (255, 235, 170, 120))
                arcade.draw_circle_filled(x + w / 2, y + h, w / 2, (255, 235, 170, 120))
                arcade.draw_circle_filled(x + w / 2, y + h / 2, 150, (255, 230, 150, int(18 + 8 * math.sin(t * 3))))
            else:
                self.box(x, x + w, y, y + h, (22, 18, 20))
                arcade.draw_circle_filled(x + w / 2, y + h, w / 2, (22, 18, 20))
                arcade.draw_circle_filled(x + w / 2, y + h * 0.55, 12, (160, 40, 50))
            self.outline(x, x + w, y, y + h, GOLD_DARK_C, 4)
        if self.objet_sol is not None and self.level_index == 1:
            arcade.draw_circle_filled(self.objet_sol_x, self.objet_sol_y, 14 + 2 * math.sin(t * 4), GOLD_LIGHT_C)
            arcade.draw_circle_filled(self.objet_sol_x, self.objet_sol_y, 34, (230, 181, 88, 30))
            self.text(self.objet_sol.get_name(), self.objet_sol_x, self.objet_sol_y + 30, 12, (225, 218, 201),
                      anchor_x="center")

    # ---- monstres ----
    def draw_mob(self):
        for m in self.monsters:
            if not m.alive:
                continue
            if abs(m.x - self.cam_x) > self.width / 2 + 250 or abs(m.y - self.cam_y) > self.height / 2 + 250:
                continue
            self.draw_slime(m)
            if not m.is_boss and m.hp < m.max_hp:
                ratio = max(0, m.hp / m.max_hp)
                bw = max(40, m.w * 0.9)
                bl, bb = m.x - bw / 2, m.y + m.h / 2 + 10
                self.box(bl, bl + bw, bb, bb + 5, (40, 10, 10))
                self.box(bl, bl + bw * ratio, bb, bb + 5,
                         (80, 165, 95) if ratio > 0.5 else (230, 181, 88) if ratio > 0.25 else (220, 68, 70))
                self.outline(bl, bl + bw, bb, bb + 5, GOLD_DARK_C, 1)

    def draw_slime(self, m):
        d = m.data
        body, edge = d["body"], d["edge"]
        w, h = m.w, m.h
        cx, cy = m.x, m.y
        t = m.t
        alpha = 200 if m.kind == "spectre" else 255
        flash = None
        if m.hurt_t > 0:
            flash = (255, 255, 255)
        elif m.state in ("tele", "roar") or (m.ai == "charge" and m.state == "tele"):
            flash = (255, 235, 130) if int(t * 14) % 2 == 0 else None
        col = flash or body
        squash = 1 + 0.06 * math.sin(t * 6)
        if not m.on_ground and m.ai not in ("fly",):
            squash = 1.15 if m.vy > 0 else 0.88
        bw, bh = w * (2 - squash) * 0.98, h * squash
        by = cy - (h - bh) / 2
        lw = 5 if m.is_boss else 3
        # ombre au sol
        if m.on_ground:
            arcade.draw_ellipse_filled(cx, m.bottom() + 3, w * 0.9, 10, (0, 0, 0, 70))
        # petits éléments derrière le corps
        el = m.element
        if m.ai == "fly":
            wing = 14 * math.sin(t * 14)
            arcade.draw_triangle_filled(cx - w * 0.4, by, cx - w * 0.95, by + 18 + wing, cx - w * 0.3, by + 14, (*shade(body, 0.8), 170))
            arcade.draw_triangle_filled(cx + w * 0.4, by, cx + w * 0.95, by + 18 + wing, cx + w * 0.3, by + 14, (*shade(body, 0.8), 170))
        arcade.draw_ellipse_filled(cx, by, bw, bh, (*col, alpha))
        arcade.draw_ellipse_outline(cx, by, bw, bh, edge, lw)
        arcade.draw_circle_filled(cx - bw * 0.22, by + bh * 0.25, max(4, w * 0.07), (*shade(col, 1.45), 190))
        # détails élémentaires
        top = by + bh / 2
        if el == "fire":
            for i in (-1, 0, 1):
                fl = 1 + 0.3 * math.sin(t * 10 + i)
                arcade.draw_triangle_filled(cx + i * w * 0.2 - 7, top - 2, cx + i * w * 0.2 + 7, top - 2,
                                            cx + i * w * 0.2, top + 16 * fl, (255, 200, 80))
        elif el == "ice" and m.ai != "fly":
            for i in (-1, 0, 1):
                arcade.draw_triangle_filled(cx + i * w * 0.22 - 6, top - 3, cx + i * w * 0.22 + 6, top - 3,
                                            cx + i * w * 0.22, top + 14, (220, 245, 255))
        elif el == "lightning":
            self.lines([(cx - 8, top + 12), (cx, top + 2), (cx, top + 2), (cx - 6, top - 6),
                        (cx - 6, top - 6), (cx + 4, top - 14)], (255, 245, 150), 3)
        elif el == "poison":
            for i in range(3):
                ph = (t * 0.8 + i * 0.33) % 1
                arcade.draw_circle_filled(cx + (i - 1) * w * 0.22, top + ph * 20, 4 - ph * 2, (190, 110, 230, int(220 * (1 - ph))))
        if m.ai == "tank":
            self.box(cx - bw * 0.42, cx + bw * 0.42, by - 2, by + 8, (80, 86, 98))
            self.box(cx - bw * 0.3, cx + bw * 0.3, top - 8, top + 2, (90, 96, 110))
        # yeux
        f = m.facing
        eye_r = max(4, w * 0.085)
        ex = w * 0.16
        ey = by + bh * 0.06
        for s in (-1, 1):
            arcade.draw_circle_filled(cx + s * ex + f * 3, ey, eye_r, (255, 255, 255))
            arcade.draw_circle_filled(cx + s * ex + f * (eye_r * 0.5 + 3), ey - 1, eye_r * 0.45, (0, 0, 0))
        if m.is_boss or m.damage > 0:
            for s in (-1, 1):
                arcade.draw_line(cx + s * ex - 8, ey + eye_r + 5 + (3 if s == f else 0),
                                 cx + s * ex + 8, ey + eye_r + 1 - (3 if s == f else 0), edge, 3)
        if m.is_boss:
            self.draw_boss_gear(m, cx, by, bw, bh, top)

    def draw_boss_gear(self, m, cx, by, bw, bh, top):
        acc = m.data["accent"]
        bid = m.boss_id
        if bid == "capitaine":                    # casque + panache
            self.box(cx - bw * 0.3, cx + bw * 0.3, top - 14, top + 10, (150, 156, 170))
            self.outline(cx - bw * 0.3, cx + bw * 0.3, top - 14, top + 10, (60, 64, 80), 3)
            arcade.draw_triangle_filled(cx - 12, top + 10, cx + 12, top + 10, cx + 30, top + 50, acc)
            arcade.draw_triangle_filled(cx - 12, top + 10, cx + 12, top + 10, cx + 4, top + 56, shade(acc, 0.8))
        elif bid == "gouvernante":                # coiffe blanche + trousseau de clés
            self.box(cx - bw * 0.28, cx + bw * 0.28, top - 6, top + 14, (240, 240, 245))
            arcade.draw_circle_filled(cx, top + 16, 16, (240, 240, 245))
            arcade.draw_circle_outline(cx + bw * 0.42, by - 10, 10, GOLD_LIGHT_C, 3)
            self.box(cx + bw * 0.42 - 2, cx + bw * 0.42 + 2, by - 36, by - 20, GOLD_LIGHT_C)
        elif bid == "cuisinier":                  # toque de cuisinier
            self.box(cx - bw * 0.22, cx + bw * 0.22, top - 6, top + 30, (250, 250, 245))
            for i in (-1, 0, 1):
                arcade.draw_circle_filled(cx + i * bw * 0.16, top + 38, 20, (250, 250, 245))
            arcade.draw_circle_filled(cx + bw * 0.5, by - 8, 14, (60, 60, 66))
            self.box(cx + bw * 0.5 - 3, cx + bw * 0.5 + 40, by - 12, by - 6, (60, 60, 66))
        elif bid == "connetable":                 # heaume sombre + cornes dorées
            self.box(cx - bw * 0.34, cx + bw * 0.34, top - 18, top + 14, (50, 52, 64))
            self.outline(cx - bw * 0.34, cx + bw * 0.34, top - 18, top + 14, (20, 20, 28), 4)
            arcade.draw_triangle_filled(cx - bw * 0.34, top, cx - bw * 0.34 - 10, top + 6, cx - bw * 0.42, top + 50, acc)
            arcade.draw_triangle_filled(cx + bw * 0.34, top, cx + bw * 0.34 + 10, top + 6, cx + bw * 0.42, top + 50, acc)
            self.box(cx - 2, cx + 2, top - 18, top - 2, (20, 20, 28))
        elif bid in ("roi", "reine"):             # couronne
            n = 5 if bid == "roi" else 7
            span = bw * 0.46
            self.box(cx - span, cx + span, top - 4, top + 14, acc)
            for i in range(n):
                px = cx - span + (2 * span) * i / (n - 1)
                arcade.draw_triangle_filled(px - 10, top + 14, px + 10, top + 14, px, top + 40, acc)
                arcade.draw_circle_filled(px, top + 42, 4, (230, 60, 70) if bid == "roi" else (120, 200, 255))
            if bid == "reine":
                arcade.draw_circle_filled(cx, by, bw * 0.75, (150, 90, 255, 18))

    # ---- projectiles ----
    def draw_projectiles(self):
        for p in self.rt.ctx.projectiles:
            col = ELEMENT_COLORS.get(p["element"], (230, 230, 230))
            x, y, r = p["x"], p["y"], p["r"]
            k = p["kind"]
            if k == "wave":
                arcade.draw_ellipse_filled(x, y, r * 1.3, r * 2.4, (*col, 200))
                arcade.draw_ellipse_outline(x, y, r * 1.3, r * 2.4, (255, 255, 255, 200), 2)
            elif k == "drop":
                arcade.draw_line(x, y + 30, x, y, (*col, 150), 3)
                arcade.draw_circle_filled(x, y, r, col)
            elif k == "spark":
                self.lines([(x - r, y - r), (x, y), (x, y), (x + r, y - r), (x + r, y - r), (x + r * 1.6, y + r)], col, 3)
                arcade.draw_circle_filled(x, y, r * 0.7, (255, 255, 200))
            else:
                arcade.draw_circle_filled(x, y, r * 1.8, (*col, 40))
                arcade.draw_circle_filled(x, y, r, col)
                arcade.draw_circle_filled(x, y, r * 0.5, (255, 255, 230))

    # ---- joueur (ton ancien code, sans l'offset du saut) ----
    def draw_player(self):
        player_x = self.player.get_x()
        player_y = self.player.get_y()
        visual_y = player_y
        if self.body.inv > 0 and int(self.world_time * 18) % 2 == 0:
            return_flicker = True
        else:
            return_flicker = False

        arcade.draw_ellipse_filled(player_x, player_y - 33, 48, 12, (0, 0, 0, 90))
        if not return_flicker:
            arcade.draw_circle_filled(player_x, visual_y + 25, 20, (190, 190, 195))
            self.box(player_x - 23, player_x + 23, visual_y - 35, visual_y + 20, (85, 88, 95))
            # petit regard dans la direction du déplacement
            arcade.draw_circle_filled(player_x + self.facing * 8, visual_y + 28, 3, (30, 30, 36))
        if self.equipped_weapon:
            icon = self.equipped_weapon.get_icon()
            wx = player_x + 75 * self.facing
            if icon in ("sword", "sword_bas"):
                self.draw_sword(wx, visual_y + 5, self.character_sword_width, icon == "sword_bas")
            elif icon == "arcleg":
                self.draw_arcleg(wx, visual_y + 5, self.character_arcleg_width)
            elif icon == "arcbas":
                arcade.draw_arc_outline(wx, visual_y + 5, 55, 75, GOLD_LIGHT_C, 250, 70, 4)
        if self.equipped_shield:
            self.draw_shield(player_x - 38 * self.facing, visual_y + 5)
        # effets de statut
        if self.status["burn"] > 0:
            arcade.draw_triangle_filled(player_x - 8, visual_y + 40, player_x + 8, visual_y + 40,
                                        player_x, visual_y + 66, (255, 150, 50, 200))
        if self.status["poison"] > 0:
            arcade.draw_circle_filled(player_x + 14, visual_y + 52, 5, (170, 90, 210, 200))
        if self.status["slow"] > 0:
            arcade.draw_circle_outline(player_x, visual_y + 5, 40, (150, 220, 255, 140), 3)
        if self.status["stun"] > 0:
            arcade.draw_circle_outline(player_x, visual_y + 62, 12, (255, 235, 90), 3)

    # =================================================================
    # DESSIN : INTERFACE PAR-DESSUS LE HUD
    # =================================================================
    def draw_world_ui(self):
        if self.rt is None:
            return
        w, h = self.width, self.height
        cx = w / 2

        # bannière de zone
        if self.zone_timer > 0 and self.zone_name:
            a = int(255 * min(1.0, self.zone_timer / 0.8, (3.2 - self.zone_timer) / 0.6 + 0.01))
            a = max(0, min(255, a))
            self.shadow_text(self.zone_name, cx, h * 0.80, 34, (236, 214, 160, a))
            self.box(cx - 220, cx + 220, h * 0.80 - 28, h * 0.80 - 26, (184, 135, 61, a))

        # barre(s) de boss
        bosses = [m for m in self.rt.monsters if m.is_boss and m.alive] if self.rt.boss_active else []
        for i, m in enumerate(bosses):
            bw = min(640, w * 0.5)
            bl, bb = cx - bw / 2, h - 46 - i * 48
            ratio = max(0.0, m.hp / m.max_hp)
            self.shadow_text(m.label, cx, bb + 20, 17, (236, 214, 160))
            self.box(bl, bl + bw, bb, bb + 14, (40, 10, 14))
            self.box(bl, bl + bw * ratio, bb, bb + 14, (170, 40, 48))
            self.box(bl, bl + bw * ratio, bb + 8, bb + 14, (205, 70, 76))
            self.box(bl + bw * 0.5 - 1, bl + bw * 0.5 + 1, bb, bb + 14, (20, 8, 10))
            self.outline(bl, bl + bw, bb, bb + 14, (184, 135, 61), 2)

        # statuts
        y = h - 168
        for name, col, label in (("burn", (255, 150, 50), "BRÛLURE"), ("poison", (190, 110, 230), "POISON"),
                                 ("slow", (150, 220, 255), "RALENTI"), ("stun", (255, 235, 90), "ÉTOURDI")):
            if self.status[name] > 0:
                self.text(f"{label} {self.status[name]:.0f}s", 22, y, 12, col)
                y -= 18

        # invite d'interaction
        if self.prompt and self.dialog is None and not self.victory:
            self.shadow_text(self.prompt, cx, 215, 16, (230, 181, 88))

        # niveau en cours (discret, en haut à droite)
        self.text(f"Niveau {self.level_index} · {self.rt.level.name}", w - 20, h - 24, 12,
                  (140, 136, 126), anchor_x="right")

        # dialogue
        if self.dialog is not None:
            d = self.dialog
            left, right, bottom, top = w * 0.12, w * 0.88, 150, 290
            self.box(left, right, bottom, top, (12, 13, 18, 238))
            self.outline(left, right, bottom, top, (184, 135, 61), 2)
            self.box(left + 20, left + 84, top - 96, top - 24, shade(d["color"], 0.6))
            arcade.draw_circle_filled(left + 52, top - 42, 14, d["color"])
            self.text(d["name"], left + 110, top - 30, 17, (230, 181, 88), bold=True)
            self.text(d["lines"][d["i"]], left + 110, top - 70, 18, (225, 218, 201))
            self.text(f"{d['i'] + 1}/{len(d['lines'])}   F / ENTRÉE : continuer", right - 20, bottom + 18, 11,
                      (140, 136, 126), anchor_x="right")

        # victoire
        if self.victory:
            self.box(0, w, 0, h, (0, 0, 0, 205))
            self.shadow_text("LE ROYAUME EST LIBÉRÉ", cx, h * 0.58, 48, (236, 214, 160))
            self.shadow_text("à suivre...", cx, h * 0.46, 22, (140, 150, 170), italic=True)
            self.text("ENTRÉE : retour au menu", cx, h * 0.30, 14, (140, 136, 126), anchor_x="center")