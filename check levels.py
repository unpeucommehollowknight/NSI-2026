"""Vérifie que chaque niveau est faisable : spawn -> feux de camp, coffres, boss, porte."""
import sys, math, time
from levels import *
from world import move_box, JUMP_V, JUMP_CUT, GRAVITY, MAX_FALL, PLAYER_HW, PLAYER_H

DT = 1/60
SPEED = 300

class FakeLevel:
    """Copie du niveau où les portes verrouillées sont considérées ouvertes (on a la clé)."""
    def __init__(self, L):
        self.L = L
        self.w, self.h = L.w, L.h
        self.grid = [[(AIR if k == LOCKED else k) for k in row] for row in L.grid]
    def kind_at(self, tx, ty):
        if tx < 0 or tx >= self.w: return SOLID
        if ty < 0: return AIR
        if ty >= self.h: return SOLID
        return self.grid[ty][tx]

def sim(level, x, bottom, d, jump, cut, walk_steps=None):
    """Renvoie la liste des états (tx, row, x, bottom) où l'on se pose pendant la simulation."""
    vy = JUMP_V if jump else 0.0
    on_ground = not jump
    out = []
    t = 0.0
    last_col = None
    stuck = 0
    for i in range(240):
        t += DT
        vy = max(vy - GRAVITY*DT, -MAX_FALL)
        if cut is not None and t > cut and vy > JUMP_CUT:
            vy = JUMP_CUT
        ox = x
        x, bottom, _, vy, landed, hit = move_box(level, x, bottom, PLAYER_HW, PLAYER_H, d*SPEED, vy, DT, on_ground)
        on_ground = landed
        if landed:
            tx = int(x // TILE); row = int(round(bottom / TILE))
            out.append((tx, row, x, bottom))
            if jump or walk_steps is None:
                break
            if last_col is None or tx != last_col:
                last_col = tx
        if bottom < -300:
            break
        if walk_steps and abs(x - ox) < 0.01 and landed:
            stuck += 1
            if stuck > 10: break
        if walk_steps is not None and i > walk_steps: break
    return out

def explore(L):
    lv = FakeLevel(L)
    sx = (L.spawn[0] + 0.5) * TILE
    start = (L.spawn[0], L.spawn[1], sx, L.spawn[1]*TILE)
    seen = {(start[0], start[1])}
    queue = [start]
    while queue:
        tx, row, x0, b0 = queue.pop()
        for off in (0.15, 0.5, 0.85):
            x = (tx + off) * TILE
            for d in (-1, 0, 1):
                variants = [(False, None)] if d != 0 else []
                variants += [(True, None), (True, 0.2), (True, 0.35)]
                for jump, cut in variants:
                    res = sim(lv, x, b0, d, jump, cut, walk_steps=(40 if not jump else None))
                    for (ntx, nrow, nx, nb) in res:
                        if (ntx, nrow) not in seen and nrow >= 0:
                            seen.add((ntx, nrow))
                            queue.append((ntx, nrow, nx, nb))
    return seen

def check(L):
    seen = explore(L)
    ok = True
    def reach(tx, ty, label):
        nonlocal ok
        # on accepte une position debout dans la même colonne, à 0..1 tuile de la cible (ty = rangée du sol libre)
        good = any((tx + dx, ty + dy) in seen for dx in (-1, 0, 1) for dy in (0, 1))
        if not good:
            ok = False
            print(f"  !! INATTEIGNABLE : {label} en ({tx},{ty})")
    for (tx, ty) in L.bonfires: reach(tx, ty, "feu de camp")
    for (tx, ty, loot) in L.chests: reach(tx, ty, f"coffre {loot}")
    for (nid, tx, ty) in L.npcs: reach(tx, ty, f"PNJ {nid}")
    for (bid, tx, ty) in L.bosses: reach(tx, ty, f"boss {bid}")
    for (tx, ty) in L.doors: reach(tx, ty, "porte de sortie")
    for (k, tx, ty) in L.mobs:
        if MOB_TYPES[k]['ai'] != 'fly': reach(tx, ty, f"mob {k}")
    return ok, len(seen)

if __name__ == "__main__":
    allok = True
    for i in (1, 2, 3, 4):
        t = time.time()
        L = build_level(i)
        ok, n = check(L)
        print(f"Niveau {i} ({L.name}) : {'OK' if ok else 'PROBLEMES'} - {n} positions atteignables - {time.time()-t:.1f}s")
        allok &= ok
    sys.exit(0 if allok else 1)