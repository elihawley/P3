from statistics import mean
from math import ceil, sqrt
from heapq import nlargest
from random import random
import logging


BASE_SIZE_PCT = .5
GROWTH_RATE_IMPORTANCE = 1.1
GROWTH_RATE_IMPORTANCE_FOR_ENEMY = 4

def base_size(state):
    return ceil(BASE_SIZE_PCT * len(state.my_planets()))
def enemy_base_size(state):
    return ceil(BASE_SIZE_PCT * len(state.enemy_planets()))

def p_base(state):
    if not state.my_planets():
        return []
    return nlargest(base_size(state), state.my_planets(), key=lambda p: p.num_ships * p.growth_rate * GROWTH_RATE_IMPORTANCE)
def p_other(state):
    if not state.my_planets():
        return []
    return sorted([p for p in state.my_planets() if p not in p_base(state)], key=lambda p: p.num_ships * p.growth_rate * GROWTH_RATE_IMPORTANCE, reverse=True)
def distance_from_base_center(state, p):
    _p_base = p_base(state)
    if not _p_base:
        return 0
    c = (mean(p.x for p in _p_base), mean(p.y for p in _p_base)) if _p_base else (0,0)
    return sqrt((p.x - c[0])**2 + (p.y - c[1])**2)
def available_ships_base(state):
    return sum(p.num_ships for p in p_base(state))
def available_ships_other(state):
    return sum(p.num_ships for p in p_other(state))

def enemy_p_base(state):
    if not state.enemy_planets():
        return []
    return nlargest(enemy_base_size, state.enemy_planets(), key=lambda p: p.num_ships * p.growth_rate * GROWTH_RATE_IMPORTANCE_FOR_ENEMY)
def enemy_p_other(state):
    if not state.enemy_planets():
        return []
    return sorted([p for p in state.enemy_planets() if p not in enemy_p_base(state)], key=lambda p: p.num_ships * p.growth_rate * GROWTH_RATE_IMPORTANCE_FOR_ENEMY, reverse=True)
def distance_from_enemy_base_center(state, p):
    _enemy_p_base = enemy_p_base(state)
    if not _enemy_p_base:
        return 0
    c = (mean(p.x for p in _enemy_p_base), mean(p.y for p in _enemy_p_base)) if _enemy_p_base else (1,1)
    return sqrt((p.x - c[0])**2 + (p.y - c[1])**2) 
def enemy_available_ships_base(state):
    return sum(p.num_ships for p in enemy_p_base(state))
def enemy_available_ships_other(state):
    return sum(p.num_ships for p in enemy_p_other(state))

DEFENSIVENESS = 2
AGGRESSION = 3
INVADE_BONUS = .25 # Lower is more aggressive
def incoming_enemy_ships(state, p):
    if not state.enemy_fleets():
        return 0
    return sum(f.num_ships * (1 - (f.turns_remaining / f.total_trip_length)) for f in state.enemy_fleets() if f.destination_planet == p.ID)

def my_available_offense_ships(state, p):
    _p_base = p_base(state)
    _p_other = p_other(state)
    BIAS_TOWARDS_OTHER_FLEET = 1.5
    AVAILABLE_SHIPS_BASE_RATIO = 0.6
    AVAILABLE_SHIPS_OTHER_RATIO = 0.6
    pb = sorted(_p_base, key=lambda _p: _p.num_ships * _p.growth_rate * GROWTH_RATE_IMPORTANCE / state.distance(p.ID, _p.ID), reverse=True)[0] if _p_base else None
    po = sorted(_p_other, key=lambda _p: _p.num_ships * _p.growth_rate * GROWTH_RATE_IMPORTANCE / state.distance(p.ID, _p.ID), reverse=True)[0] if _p_other else None
    base_fleet = pb.num_ships * AVAILABLE_SHIPS_BASE_RATIO if pb else 0
    other_fleet = po.num_ships * AVAILABLE_SHIPS_OTHER_RATIO if po else 0
    return (pb, base_fleet) if (base_fleet > (BIAS_TOWARDS_OTHER_FLEET * other_fleet)) else (po, other_fleet)

def invade_value(state, p):
    ship_advantage = my_available_offense_ships(state, p)[1] - ((p.num_ships if p.owner == 0 else p.num_ships*INVADE_BONUS) + incoming_enemy_ships(state, p))
    return (AGGRESSION * p.growth_rate * GROWTH_RATE_IMPORTANCE_FOR_ENEMY) * (ship_advantage - distance_from_base_center(state, p))

def not_my_mvp(state):
    return max(state.not_my_planets(), key=lambda p: invade_value(state, p), default=None)

# def my_available_defense_ships(state, p):
#     _p_base = p_base(state)
#     _p_other = p_other(state)
#     BIAS_TOWARDS_OTHER_FLEET = 1.2
#     AVAILABLE_SHIPS_BASE_RATIO = 0.4
#     AVAILABLE_SHIPS_OTHER_RATIO = 0.6
# def defend_value(state, p):
#     return DEFENSIVENESS * (my_available_defense_ships(state, p) - incoming_enemy_ships(state, p))                                                                 * p.growth_rate * GROWTH_RATE_IMPORTANCE / distance_from_base_center(state, p)


def if_crushed_opponent(state):
    num_ships_at_my_smallest_planet = min([p.num_ships for p in state.my_planets()], default=0)
    return len(state.neutral_planets()) == 0 and num_ships_at_my_smallest_planet > max([p.num_ships for p in state.enemy_planets()], default=0) and num_ships_at_my_smallest_planet > max([f.num_ships for f in state.enemy_fleets()], default=0)

def if_at_growth_advantage(state):
    my_total_growth_rate = sum(p.growth_rate for p in state.my_planets())
    enemy_total_growth_rate = sum(p.growth_rate for p in state.enemy_planets())
    my_total_num_ships = sum(f.num_ships for f in state.my_fleets()) + sum(p.num_ships for p in state.my_planets())
    enemy_total_num_ships = sum(f.num_ships for f in state.enemy_fleets()) + sum(p.num_ships for p in state.enemy_planets())

    ADVANTAGE_MAXIMUM_RATIO = 1.1

    return my_total_growth_rate > enemy_total_growth_rate and \
        my_total_num_ships < (enemy_total_num_ships * ADVANTAGE_MAXIMUM_RATIO)

def time_to_invade_mvp(state):
    mvp = not_my_mvp(state)
    if not mvp or invade_value(state, mvp) < 0:
        return False
    ATTACK_PCT = .8
    return my_available_offense_ships(state, mvp)[1] > (mvp.num_ships * ATTACK_PCT)
