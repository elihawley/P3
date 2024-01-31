import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
from heapq import nlargest
from math import ceil, sqrt

from behavior_tree_bot.checks import *


def attack_weakest_enemy_planet_with_best_safe_planet(state):
    target_planet = min(state.enemy_planets(), key=lambda p: p.num_ships + sum(f.num_ships for f in state.enemy_fleets() if f.destination_planet == p.ID), default=None)
    if (not target_planet):
        return False
    AGGRESSION_SCALE = .6
    best_safe_planet = min([p for p in state.my_planets() if not any(f for f in state.enemy_fleets() if f.destination_planet == p.ID)], key=lambda p: (state.distance(target_planet.ID, p.ID) / (1+p.num_ships)), default=None)
    if (not best_safe_planet):
        return False
    return issue_order(state, best_safe_planet.ID, target_planet.ID, best_safe_planet.num_ships * AGGRESSION_SCALE)

def wait_and_grow(state):
    return True

def strike_mvp(state):
    _p_base = p_base(state)
    _p_other = p_other(state)
    if not _p_base and not _p_other:
        return False
    mvp = max(state.not_my_planets(), key=lambda p: invade_value(state, p))
    if not mvp:
        return False
    attacking_p, fleet_size = my_available_offense_ships(state, mvp)
    if not attacking_p:
        return False
    return issue_order(state, attacking_p.ID, mvp.ID, fleet_size)

def reinforce_base_with_best_other(state):
    _p_base = p_base(state)
    _p_other = p_other(state)
    if not _p_base or not _p_other:
        return False
    lowest_pb = min(_p_base, key=lambda p: p.num_ships + sum(f.num_ships for f in state.my_fleets() if f.destination_planet == p.ID) - sum(f.num_ships for f in state.enemy_fleets() if f.destination_planet == p.ID))
    highest_po = max(_p_other, key=lambda p: (p.num_ships + sum(f.num_ships for f in state.my_fleets() if f.destination_planet == p.ID) - sum(f.num_ships for f in state.enemy_fleets() if f.destination_planet == p.ID)) / state.distance(lowest_pb.ID, p.ID))
    REINFORCEMENT_RATIO = .2
    ships_to_send = max(min(highest_po.num_ships*REINFORCEMENT_RATIO, highest_po.num_ships - incoming_enemy_ships(state, highest_po)), 0)
    return issue_order(state, highest_po.ID, lowest_pb.ID, ships_to_send)
