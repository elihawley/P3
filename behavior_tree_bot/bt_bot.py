#!/usr/bin/env py
#

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check

from planet_wars import PlanetWars, finish_turn


# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots
def setup_behavior_tree():

    # Top-down construction of behavior tree
    root = Selector(name='High Level Ordering of Strategies')

    crush_plan = Sequence(name='Crush')
    check_crush = Check(if_crushed_opponent)
    perform_crush = Action(attack_weakest_enemy_planet_with_best_safe_planet)
    crush_plan.child_nodes = [check_crush, perform_crush]
    
    grow_plan = Sequence(name='Grow')
    check_grow = Check(if_at_growth_advantage)
    perform_grow = Action(wait_and_grow)
    grow_plan.child_nodes = [check_grow, perform_grow]

    invade_plan = Sequence(name='Invade')
    check_invade = Check(time_to_invade_mvp)
    perform_invade = Action(strike_mvp)
    invade_plan.child_nodes = [check_invade, perform_invade]
    
    reinforce = Action(reinforce_base_with_best_other)


    root.child_nodes = [
        crush_plan,
        grow_plan,
        invade_plan,
        reinforce.copy()
    ]

    logging.info('\n' + root.tree_to_string())
    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")
