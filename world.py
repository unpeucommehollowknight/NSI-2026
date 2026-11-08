"""
world.py : physique side-scroller, IA des mobs et des boss, état d'un niveau.

Aucune dépendance à arcade : tout peut être testé sans fenêtre.
main.py ne fait qu'appeler ces fonctions et dessiner le résultat.
"""
import math
import random

from levels import (
    TILE, AIR, SOLID, ONEWAY, SPIKE, LOCKED, GATE, SOLID_KINDS,
    MOB_TYPES, BOSSES, LEVEL_SCALE, build_level,
)

GRAVITY = 2400.0
MAX_FALL = 1300.0
JUMP_V = 1100.0          # hauteur de saut ~ 5 tuiles
JUMP_CUT = 300.0         # relâcher SPACE coupe le saut

PLAYER_HW = 20           # demi-largeur du joueur
PLAYER_FEET = 35         # distance centre -> pieds (le centre est y du Player)
PLAYER_H = 80            # hauteur totale (pieds -> sommet de la tête)

# Quand ce boss meurt, un autre apparaît (phase 2 du boss final)
BOSS_FOLLOWUP = {"roi": "reine"}


# ---------------------------------------------------------------------
# PHYSIQUE
# ---------------------------------------------------------------------
def box_hits_solid(level, x, bottom, hw, h):
    x0 = int(math.floor((x - hw) / TILE))
    x1 = int(math.floor((x + hw - 0.01) / TILE))
    y0 = int(math.floor(bottom / TILE))
    y1 = int(math.floor((bottom + h - 0.01) / TILE))
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            if level.kind_at(tx, ty) in SOLID_KINDS:
                return True
    return False


def box_touches_kind(level, x, bottom, hw, h, kind):
    x0 = int(math.floor((x - hw) / TILE))
    x1 = int(math.floor((x + hw - 0.01) / TILE))
    y0 = int(math.floor(bottom / TILE))
    y1 = int(math.floor((bottom + h - 0.01) / TILE))
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            if level.kind_at(tx, ty) == kind and 0 <= ty < level.h:
                return True
    return False


def move_box(level, x, bottom, hw, h, vx, vy, dt, on_ground=False, drop=False):
    """Déplace une boîte (centre x, bas = bottom). Renvoie
    (x, bottom, vx, vy, on_ground, hit_wall)."""
    hit_wall = False

    # --- horizontal (avec montée automatique des marches d'1 tuile) ---
    nx = x + vx * dt
    if box_hits_solid(level, nx, bottom, hw, h):
        stepped = False
        if on_ground:
            nb = (math.floor(bottom / TILE) + 1) * TILE
            if nb - bottom <= TILE * 1.05 and not box_hits_solid(level, nx, nb + 0.02, hw, h):
                bottom = nb + 0.02
                stepped = True
        if not stepped:
            hit_wall = True
            if vx > 0:
                col = int(math.floor((nx + hw) / TILE))
                nx = col * TILE - hw - 0.02
            else:
                col = int(math.floor((nx - hw) / TILE))
                nx = (col + 1) * TILE + hw + 0.02
            vx = 0.0
            if box_hits_solid(level, nx, bottom, hw, h):
                nx = x
    x = nx

    # --- vertical ---
    old = bottom
    nb = bottom + vy * dt
    landed = False
    x0 = int(math.floor((x - hw) / TILE))
    x1 = int(math.floor((x + hw - 0.01) / TILE))
    if vy <= 0:
        start = int(math.floor((old + 0.01) / TILE)) - 1 if abs(old / TILE - round(old / TILE)) < 1e-6 \
            else int(math.floor(old / TILE))
        end = int(math.floor(nb / TILE))
        ty = start
        while ty >= end and not landed:
            top = (ty + 1) * TILE
            if top <= old + 0.6:
                for tx in range(x0, x1 + 1):
                    k = level.kind_at(tx, ty)
                    if k in SOLID_KINDS or (k == ONEWAY and not drop):
                        nb = float(top)
                        vy = 0.0
                        landed = True
                        break
            ty -= 1
    else:
        head_old = old + h
        head_new = nb + h
        r0 = int(math.floor(head_old / TILE))
        r1 = int(math.floor(head_new / TILE))
        for ty in range(r0, r1 + 1):
            hit = False
            for tx in range(x0, x1 + 1):
                if level.kind_at(tx, ty) in SOLID_KINDS:
                    hit = True
                    break
            if hit:
                nb = ty * TILE - h - 0.02
                vy = 0.0
                break
    return x, nb, vx, vy, landed, hit_wall


class PlayerBody:
    """État physique du joueur (la position reste dans Player.x / Player.y)."""

    def __init__(self):
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.coyote = 0.0
        self.jump_buf = 0.0
        self.drop_t = 0.0
        self.inv = 0.0              # invincibilité après un coup
        self.knock_t = 0.0
        self.knock_vx = 0.0
        self.last_safe = None
        self.safe_t = 0.0

    def reset(self):
        self.__init__()


def move_player(level, player, body, dirx, speed_mult, jump_held, down, dt):
    """Un pas de physique du joueur. dirx = -1 / 0 / 1."""
    body.inv = max(0.0, body.inv - dt)
    body.coyote = max(0.0, body.coyote - dt)
    body.jump_buf = max(0.0, body.jump_buf - dt)
    body.drop_t = max(0.0, body.drop_t - dt)
    body.knock_t = max(0.0, body.knock_t - dt)

    speed = player.get_speed() * 60.0 * speed_mult
    body.vx = body.knock_vx if body.knock_t > 0 else dirx * speed

    body.vy = max(body.vy - GRAVITY * dt, -MAX_FALL)

    if down and body.on_ground and body.drop_t <= 0:
        # traverser une plateforme fine
        x, bottom = player.get_x(), player.get_y() - PLAYER_FEET
        k = level.kind_at(int(x // TILE), int((bottom - 2) // TILE))
        if k == ONEWAY:
            body.drop_t = 0.25

    if body.jump_buf > 0 and body.coyote > 0:
        body.vy = JUMP_V
        body.coyote = 0.0
        body.jump_buf = 0.0
        body.on_ground = False
    if not jump_held and body.vy > JUMP_CUT:
        body.vy = JUMP_CUT

    x, bottom, vx, vy, landed, _ = move_box(
        level, player.get_x(), player.get_y() - PLAYER_FEET, PLAYER_HW, PLAYER_H,
        body.vx, body.vy, dt, body.on_ground, body.drop_t > 0)
    body.vy = vy
    body.on_ground = landed
    if landed:
        body.coyote = 0.1
    player.set_x(x)
    player.set_y(bottom + PLAYER_FEET)

    # mémorise le dernier sol sûr (pour revenir après des piques)
    body.safe_t -= dt
    if landed and body.safe_t <= 0:
        tx = int(x // TILE)
        ty = int(bottom // TILE) - 1
        if (level.kind_at(tx, ty) in (SOLID, ONEWAY)
                and not any(level.kind_at(tx + o, ty + 1) == SPIKE for o in (-1, 0, 1))
                and level.kind_at(tx - 1, ty) in (SOLID, ONEWAY) and level.kind_at(tx + 1, ty) in (SOLID, ONEWAY)):
            body.last_safe = (x, bottom + PLAYER_FEET)
            body.safe_t = 0.3
    return landed


def player_on_spikes(level, player):
    return box_touches_kind(level, player.get_x(), player.get_y() - PLAYER_FEET + 2,
                            PLAYER_HW - 4, PLAYER_H - 10, SPIKE)


# ---------------------------------------------------------------------
# PROJECTILES ENNEMIS
# ---------------------------------------------------------------------
def make_projectile(x, y, vx, vy, dmg, element="none", kind="orb", r=10, life=3.0, grav=0.0):
    return dict(x=x, y=y, vx=vx, vy=vy, dmg=dmg, element=element, kind=kind, r=r, life=life, grav=grav)


def update_projectiles(level, projs, dt, pbox):
    """Fait avancer les projectiles. Renvoie la liste de ceux qui touchent le joueur.
    pbox = (x_centre, bas, demi_largeur, hauteur)."""
    hits = []
    px, pb, phw, ph = pbox
    for p in projs[:]:
        p["life"] -= dt
        p["vy"] -= p["grav"] * dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        tx, ty = int(p["x"] // TILE), int(p["y"] // TILE)
        k = level.kind_at(tx, ty) if ty >= 0 else SOLID
        dead = p["life"] <= 0 or k in SOLID_KINDS or (p["kind"] == "drop" and k == ONEWAY)
        if not dead:
            cx = max(px - phw, min(p["x"], px + phw))
            cy = max(pb, min(p["y"], pb + ph))
            if (p["x"] - cx) ** 2 + (p["y"] - cy) ** 2 <= p["r"] ** 2:
                hits.append(p)
                dead = True
        if dead:
            projs.remove(p)
    return hits


# ---------------------------------------------------------------------
# MONSTRES
# ---------------------------------------------------------------------
class WorldCtx:
    """Ce que les mobs produisent : projectiles, mobs invoqués, secousses d'écran."""

    def __init__(self):
        self.projectiles = []
        self.spawns = []        # (kind, x, y)
        self.shake = 0.0


class Monster:
    """Même signature que ton ancienne classe Monster (x, y, hp, speed, damage...),
    avec en plus un type (kind) ou un boss (boss_id)."""

    def __init__(self, x, y, hp=150, speed=100, damage=12, respawn_time=120,
                 variant="contamine", kind=None, boss_id=None):
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
        self.respawn_time = respawn_time
        self.respawn_timer = 0
        self.attack_cooldown = 0
        self.dir_timer = 0
        self.dx = 0
        self.dy = 0

        self.kind = kind
        self.boss_id = boss_id
        self.is_boss = boss_id is not None
        self.summoned = False
        data = BOSSES[boss_id] if self.is_boss else MOB_TYPES.get(kind, MOB_TYPES["gluant"])
        self.data = data
        self.w = data["w"]
        self.h = data["h"]
        self.ai = "boss" if self.is_boss else data["ai"]
        self.element = data["element"]
        self.xp = data["xp"]
        self.label = data.get("label", data.get("name", "Slime"))
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = random.choice((-1, 1))
        self.state = "idle"
        self.state_t = random.uniform(0.3, 1.2)
        self.phase = 1
        self.pattern = None
        self.shots = 0
        self.shot_t = random.uniform(0.5, 2.0)
        self.hop_t = random.uniform(0.3, 1.5)
        self.hurt_t = 0.0
        self.stun = 0.0
        self.t = random.uniform(0, 6)       # animation
        self.vulnerable_t = 0.0

    # ---- utilitaires ----
    def reset(self):
        self.alive = True
        self.hp = self.max_hp
        self.x = self.start_x
        self.y = self.start_y
        self.vx = self.vy = 0.0
        self.attack_cooldown = 0
        self.respawn_timer = 0
        self.state = "idle"
        self.state_t = 1.0
        self.phase = 1
        self.stun = 0.0
        self.hurt_t = 0.0

    def bottom(self):
        return self.y - self.h / 2

    def on_hit(self, direction):
        """Appelé quand le joueur touche ce monstre (petit recul, clignotement)."""
        self.hurt_t = 0.18
        if not self.is_boss and self.ai != "tank":
            self.vx = direction * 260
            self.stun = 0.18
            self.vy = max(self.vy, 220)

    def _ground_ahead(self, level):
        xf = self.x + self.facing * (self.w / 2 + 6)
        ty = int(math.floor((self.bottom() - 4) / TILE))
        return level.kind_at(int(xf // TILE), ty) in (SOLID, ONEWAY, LOCKED, GATE)

    def _physics(self, level, dt, gravity=True):
        if gravity:
            self.vy = max(self.vy - GRAVITY * dt, -MAX_FALL)
        x, bottom, vx, vy, landed, hit = move_box(
            level, self.x, self.bottom(), self.w / 2, self.h, self.vx, self.vy, dt, self.on_ground)
        self.x, self.y = x, bottom + self.h / 2
        self.vx, self.vy, self.on_ground = vx, vy, landed
        return hit

    # ---- mise à jour ----
    def update(self, rt, px, pyc, dt):
        self.t += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.hurt_t = max(0.0, self.hurt_t - dt)
        level = rt.level

        if self.stun > 0:
            self.stun -= dt
            self.vx *= 0.9
            if self.ai == "fly":
                self.x += self.vx * dt
            else:
                self._physics(level, dt)
            return

        if self.is_boss:
            self._boss_ai(rt, px, pyc, dt)
        elif self.ai == "fly":
            self._fly_ai(rt, px, pyc, dt)
        else:
            self._ground_ai(rt, px, pyc, dt)

    # ---- mobs normaux ----
    def _ground_ai(self, rt, px, pyc, dt):
        level = rt.level
        dx = px - self.x
        dy = pyc - self.y
        adx = abs(dx)
        aggro = adx < 9 * TILE and abs(dy) < 3.5 * TILE
        if aggro:
            self.facing = 1 if dx > 0 else -1
        ai = self.ai

        if ai in ("patrol", "tank"):
            sp = self.speed if aggro else self.speed * 0.55
            if not self._ground_ahead(level) and self.on_ground:
                if aggro:
                    sp = 0
                else:
                    self.facing = -self.facing
            self.vx = self.facing * sp

        elif ai == "hop":
            self.hop_t -= dt
            if self.on_ground:
                self.vx = 0
                if self.hop_t <= 0:
                    if not aggro:
                        self.facing = random.choice((-1, 1))
                    self.vy = 640
                    self.vx = self.facing * self.speed * (1.5 if aggro else 0.8)
                    self.hop_t = random.uniform(0.7, 1.4)

        elif ai == "ranged":
            self.vx = 0
            if aggro:
                if adx < 4 * TILE and self._ground_ahead_dir(level, -self.facing):
                    self.vx = -self.facing * self.speed
                elif adx > 7.5 * TILE and self._ground_ahead(level):
                    self.vx = self.facing * self.speed
            self.shot_t -= dt
            if aggro and self.shot_t <= 0 and adx < 11 * TILE:
                self.shot_t = 2.2
                d = max(1.0, math.hypot(dx, dy))
                spd = 340
                rt.ctx.projectiles.append(make_projectile(
                    self.x + self.facing * 20, self.y + 4, dx / d * spd, dy / d * spd,
                    self.damage, self.element, "orb", 11, 3.0))

        elif ai == "charge":
            if self.state == "idle":
                self.vx = self.facing * self.speed * 0.4 if aggro else 0
                if aggro and self.on_ground and self._ground_ahead(level):
                    self.state_t -= dt
                    if self.state_t <= 0 and adx < 7 * TILE:
                        self.state, self.state_t = "tele", 0.55
                        self.vx = 0
            elif self.state == "tele":
                self.vx = 0
                self.state_t -= dt
                if self.state_t <= 0:
                    self.state, self.state_t = "dash", 0.55
            elif self.state == "dash":
                self.vx = self.facing * 520
                self.state_t -= dt
                if self.state_t <= 0 or not self._ground_ahead(level):
                    self.state, self.state_t = "rest", 0.9
            elif self.state == "rest":
                self.vx = 0
                self.state_t -= dt
                if self.state_t <= 0:
                    self.state, self.state_t = "idle", random.uniform(0.6, 1.4)

        self._physics(level, dt)

    def _ground_ahead_dir(self, level, direction):
        xf = self.x + direction * (self.w / 2 + 6)
        ty = int(math.floor((self.bottom() - 4) / TILE))
        return level.kind_at(int(xf // TILE), ty) in (SOLID, ONEWAY, LOCKED, GATE)

    def _fly_ai(self, rt, px, pyc, dt):
        level = rt.level
        dx, dy = px - self.x, (pyc + 25) - self.y
        dist = math.hypot(dx, dy)
        if dist < 10 * TILE:
            self.facing = 1 if dx > 0 else -1
            sp = self.speed
            vx, vy = dx / max(dist, 1) * sp, dy / max(dist, 1) * sp
        else:
            vx = math.cos(self.t * 0.8) * self.speed * 0.4
            vy = math.sin(self.t * 1.3) * self.speed * 0.3
        nx, ny = self.x + vx * dt, self.y + vy * dt
        if not box_hits_solid(level, nx, self.y - self.h / 2, self.w / 2, self.h):
            self.x = nx
        if not box_hits_solid(level, self.x, ny - self.h / 2, self.w / 2, self.h):
            self.y = ny
        self.vx = 0

    # ---- boss ----
    def _boss_ai(self, rt, px, pyc, dt):
        level = rt.level
        d = self.data
        dx = px - self.x
        adx = abs(dx)
        toward = 1 if dx > 0 else -1

        if not rt.boss_active:                    # endormi tant que le joueur n'est pas entré
            self.vx = 0
            self._physics(level, dt)
            return

        if self.phase == 1 and self.hp <= self.max_hp * 0.5 and self.state != "roar":
            self.phase = 2
            self.state, self.state_t = "roar", 0.9
            self.vx = 0
            rt.ctx.shake = 0.6
            if "summon" in d["patterns2"]:
                self._summon(rt, 2)

        spd = self.speed * (1.3 if self.phase == 2 else 1.0)
        patterns = d["patterns2"] if self.phase == 2 else d["patterns1"]
        self.state_t -= dt
        st = self.state

        if st == "roar":
            self.vx = 0
            if self.state_t <= 0:
                self.state, self.state_t = "idle", 0.6

        elif st == "idle":
            self.facing = toward
            self.vx = toward * spd * 0.6 if adx > 2.2 * TILE else 0
            if self.state_t <= 0:
                self.pattern = random.choice(patterns)
                self.state = "tele"
                self.state_t = 0.4 if self.phase == 2 else 0.55
                self.vx = 0

        elif st == "tele":
            self.facing = toward
            self.vx = 0
            if self.state_t <= 0:
                p = self.pattern
                if p == "charge":
                    self.state, self.state_t = "charge", 0.9
                elif p == "slam":
                    self.state, self.state_t = "slam", 3.0
                    self.vy = 1000
                    self.vx = max(-380, min(380, dx * 1.1))
                    self.on_ground = False
                elif p == "shoot":
                    self.state, self.state_t = "shoot", 3.0
                    self.shots = 5 if self.phase == 2 else 3
                    self.shot_t = 0
                elif p == "rain":
                    self.state, self.state_t = "rain", 1.6
                    self.shot_t = 0
                elif p == "summon":
                    self._summon(rt, 2)
                    self.state, self.state_t = "rest", 0.8
                else:
                    self.state, self.state_t = "rest", 0.5

        elif st == "charge":
            self.vx = self.facing * spd * 4.2
            if self.state_t <= 0:
                self.state, self.state_t = "rest", 0.8
            elif self.vx != 0 and not self._boss_floor_ahead(level):
                self.state, self.state_t = "rest", 0.6

        elif st == "slam":
            if self.on_ground and self.state_t < 2.8:
                self.vx = 0
                self._shockwave(rt)
                self.state, self.state_t = "rest", 0.7
                rt.ctx.shake = 0.35

        elif st == "shoot":
            self.vx = 0
            self.facing = toward
            self.shot_t -= dt
            if self.shot_t <= 0 and self.shots > 0:
                self._fire(rt, px, pyc)
                self.shots -= 1
                self.shot_t = 0.35
            if self.shots <= 0 and self.shot_t <= 0:
                self.state, self.state_t = "rest", 0.6

        elif st == "rain":
            self.vx = 0
            self.shot_t -= dt
            if self.shot_t <= 0:
                self.shot_t = 0.18
                top = min((level.h - 3) * TILE, pyc + 560)
                rt.ctx.projectiles.append(make_projectile(
                    px + random.uniform(-340, 340), top, 0, -430, self.damage * 0.8,
                    self.element, "drop", 12, 3.0))
            if self.state_t <= 0:
                self.state, self.state_t = "rest", 0.6

        elif st == "rest":
            self.vx = 0
            if self.state_t <= 0:
                self.state, self.state_t = "idle", random.uniform(0.6, 1.1)

        hit = self._physics(level, dt)
        if st == "charge" and hit:
            self.state, self.state_t = "rest", 1.2       # se cogne : reste vulnérable
            rt.ctx.shake = 0.4

    def _boss_floor_ahead(self, level):
        return self._ground_ahead(level) or not self.on_ground

    def _fire(self, rt, px, pyc):
        dx, dy = px - self.x, pyc - self.y
        d = max(1.0, math.hypot(dx, dy))
        spd = 430
        kind = {"poison": "poison", "fire": "fire", "ice": "ice", "lightning": "spark"}.get(self.element, "orb")
        rt.ctx.projectiles.append(make_projectile(
            self.x + self.facing * self.w * 0.4, self.y + 10, dx / d * spd, dy / d * spd,
            self.damage, self.element, kind, 14, 3.5))

    def _shockwave(self, rt):
        for direction in (-1, 1):
            rt.ctx.projectiles.append(make_projectile(
                self.x + direction * self.w * 0.5, self.bottom() + 22, direction * 400, 0,
                self.damage, self.element, "wave", 24, 1.8))

    def _summon(self, rt, n):
        alive = sum(1 for m in rt.monsters if m.alive and m.summoned)
        for i in range(n):
            if alive + i >= 3:
                break
            side = -1 if i % 2 == 0 else 1
            rt.ctx.spawns.append((self.data["summon"], self.x + side * (self.w * 0.7 + i * 30), self.y))


def make_mob(kind, tx, ty, scale=1.0):
    d = MOB_TYPES[kind]
    hp = int(d["hp"] * scale)
    dmg = int(d["dmg"] * scale)
    x = (tx + 0.5) * TILE
    y = ty * TILE + d["h"] / 2 + 1
    return Monster(x, y, hp=hp, speed=d["speed"], damage=dmg, respawn_time=10 ** 9,
                   variant=kind, kind=kind)


def make_mob_at(kind, x, y, scale=1.0):
    m = make_mob(kind, 0, 0, scale)
    m.x = m.start_x = x
    m.y = m.start_y = y
    m.summoned = True
    return m


def make_boss(bid, tx, ty):
    d = BOSSES[bid]
    x = (tx + 0.5) * TILE
    y = ty * TILE + d["h"] / 2 + 1
    return Monster(x, y, hp=d["hp"], speed=d["speed"], damage=d["dmg"], respawn_time=10 ** 9,
                   variant=bid, boss_id=bid)


# ---------------------------------------------------------------------
# ÉTAT D'UN NIVEAU
# ---------------------------------------------------------------------
class LevelRuntime:
    def __init__(self, index, defeated=(), chests=(), doors=()):
        self.index = index
        self.level = build_level(index)
        self.scale = LEVEL_SCALE[index]
        self.ctx = WorldCtx()
        self.defeated = set(defeated)           # boss déjà vaincus
        self.chests_open = set(chests)          # "tx:ty"
        self.doors_open = set(doors)            # "tx:ty" (portes verrouillées ouvertes)
        self.boss_active = False
        self.gates_closed = False
        self.monsters = []
        self._build_monsters()
        for key in self.doors_open:
            tx, ty = (int(v) for v in key.split(":"))
            self._open_lock_column(tx, ty, rebuild=False)
        self.door_open = self._arena_cleared()
        self.level.finish()

    # ---- construction ----
    def _build_monsters(self):
        L = self.level
        self.monsters = [make_mob(k, tx, ty, self.scale) for k, tx, ty in L.mobs]
        for bid, tx, ty in L.bosses:
            if bid not in self.defeated:
                self.monsters.append(make_boss(bid, tx, ty))
        # boss final : le Roi est mort mais pas la Reine
        for first, then in BOSS_FOLLOWUP.items():
            if first in self.defeated and then not in self.defeated and any(b[0] == first for b in L.bosses):
                tx, ty = next((b[1], b[2]) for b in L.bosses if b[0] == first)
                self.monsters.append(make_boss(then, tx, ty))

    def _arena_cleared(self):
        if not self.level.bosses:
            return True
        final = [b[0] for b in self.level.bosses]
        for first, then in BOSS_FOLLOWUP.items():
            if first in final:
                final.append(then)
        return all(b in self.defeated for b in final)

    def bosses_alive(self):
        return [m for m in self.monsters if m.is_boss and m.alive]

    # ---- herses / portes ----
    def _set_gates(self, closed):
        for tx, y0, y1 in self.level.gates:
            self.level.fill(tx, y0, tx, y1, GATE if closed else AIR)
        self.gates_closed = closed
        self.level.finish()

    def _open_lock_column(self, tx, ty, rebuild=True):
        L = self.level
        for y in range(L.h):
            if L.kind_at(tx, y) == LOCKED:
                L.grid[y][tx] = AIR
        if rebuild:
            L.finish()

    def locked_near(self, px, pyc):
        """Renvoie (tx, ty) d'une porte verrouillée proche du joueur, sinon None."""
        L = self.level
        cx, cy = int(px // TILE), int(pyc // TILE)
        for tx in range(cx - 2, cx + 3):
            for ty in range(cy - 2, cy + 3):
                if L.kind_at(tx, ty) == LOCKED:
                    return tx, ty
        return None

    def unlock(self, tx, ty):
        key = f"{tx}:{ty}"
        self.doors_open.add(key)
        self._open_lock_column(tx, ty)

    # ---- combat de boss ----
    def check_arena(self, px):
        """Appelé à chaque frame : ferme la herse quand le joueur entre dans l'arène."""
        L = self.level
        if L.arena is None or self.boss_active or not self.bosses_alive():
            return False
        if px > (L.arena[0] + 3) * TILE:
            self.boss_active = True
            self._set_gates(True)
            return True
        return False

    def on_monster_killed(self, m):
        """Renvoie un message à afficher (ou None)."""
        if not m.is_boss:
            return None
        then = BOSS_FOLLOWUP.get(m.boss_id)
        if then and then not in self.defeated:
            self.defeated.add(m.boss_id)
            nb = make_boss(then, 0, 0)
            nb.x = nb.start_x = m.x
            nb.y = nb.start_y = m.y + 20
            self.monsters.append(nb)
            nb.state, nb.state_t = "roar", 1.2
            return f"{BOSSES[then]['name']} se dresse !"
        if self.bosses_alive():
            return f"{m.label} est tombé..."
        # tous les boss de l'arène sont morts
        for b in self.level.bosses:
            self.defeated.add(b[0])
        for first, th in BOSS_FOLLOWUP.items():
            if m.boss_id in (first, th):
                self.defeated.update((first, th))
        self.boss_active = False
        self._set_gates(False)
        self.door_open = True
        return "Zone libérée ! La porte est ouverte."

    def reset_boss_fight(self):
        """Le joueur est mort : le combat de boss recommence."""
        self.monsters = [m for m in self.monsters if not m.summoned]
        for first, then in BOSS_FOLLOWUP.items():
            if then not in self.defeated and any(b[0] == first for b in self.level.bosses):
                self.defeated.discard(first)
                self.monsters = [m for m in self.monsters if m.boss_id != then]
                if not any(m.boss_id == first for m in self.monsters):
                    tx, ty = next((b[1], b[2]) for b in self.level.bosses if b[0] == first)
                    self.monsters.append(make_boss(first, tx, ty))
        self.boss_active = False
        if self.gates_closed:
            self._set_gates(False)
        for m in self.monsters:
            if m.is_boss:
                m.reset()

    def reset_mobs(self):
        """Repos au feu de camp : les mobs normaux réapparaissent."""
        self.monsters = [m for m in self.monsters if not m.summoned]
        for m in self.monsters:
            if not m.is_boss:
                m.reset()
                m.attack_cooldown = 1.0

    # ---- mise à jour ----
    def update(self, px, pyc, dt):
        for m in self.monsters:
            if m.alive:
                m.update(self, px, pyc, dt)
            if m.alive and m.y < -400:
                m.x, m.y, m.vy = m.start_x, m.start_y, 0.0
        for kind, x, y in self.ctx.spawns:
            self.monsters.append(make_mob_at(kind, x, y, self.scale))
        self.ctx.spawns = []
        self.ctx.shake = max(0.0, self.ctx.shake - dt)