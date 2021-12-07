
from math import inf
import random
import json
import copy

from douzero.dmc.utils import act
from . import util
from ..env.game import InfoSet

MCTS_DATA_FILE_NAME = 'C:\\Users\\Genevieve\\Desktop\\NEU\\Fall_2021\\ai\\DouZero\\douzero\\evaluation\\mcts_agent_data.txt'  # TODO
VERBOSE = True
TREE_TARGET_DEPTH = 5


def debug(*msgs):
    global VERBOSE
    if VERBOSE:
        result = ""
        for msg in msgs:
            result += str(msg)
        print(result)

# Represents a node of mcts including all children nodes


class MctsState:
    def __init__(self, position, last_two_moves, all_handcards):
        self.position = position
        self.last_two_moves = last_two_moves
        self.all_handcards = all_handcards

    def getScore(self):
        if self.position == 'landlord':
            return len(self.all_handcards['landlord'])
        else:
            min_cards = len(self.all_handcards['landlord_down']) \
                if len(self.all_handcards['landlord_down']) < len(self.all_handcards['landlord_up']) \
                else len(self.all_handcards['landlord_up'])

            return min_cards


class Node:
    def __init__(self, state):
        self.state = state  # MCTS Object
        self.children = {}  # action: resulting node

    def getScore(self):
        return self.state.getScore()

# **Modified** MCTS Agent:
# This agent is called upon each time an action is to be selected.
# Each time it is called upon, it is trained with MCTS a certain number of times
# Each game this agent is used, it will update the saved mcts data to be used


class MctsAgent:
    ######################################################################
    ########################## UTILITIES #################################
    ######################################################################
    def __init__(self, position):
        self.name = 'MCTS'
        self.position = 'position'

    # Runs the given number of iterations PER action taken
    # Saves the updated data to the save file
    # Returns the best action
    def act(self, infoset, num_iterations=10):
        curr_hand = infoset.player_hand_cards

        card_str_list = util.env_arr2real_card_str(curr_hand)
        # print('last_two_moves', infoset.last_two_moves)
        best_action_tuples = util.get_best_actions(
            card_str_list, infoset.last_two_moves)

        # print('bestactiontuple', list(map(lambda x: x[0], best_action_tuple)))
        # print('legal actions', infoset.legal_actions)
        tree = self.create_tree(infoset, best_action_tuples)

        action = self.choose_best_action_from_children(tree, infoset)

        if action not in infoset.legal_actions:
            print("ILLEGAL ACTION", action)
            print(infoset.last_two_moves)
            print(infoset.legal_actions)

            # print(curr_hand)
            # print(infoset.all_handcards)
            # print(infoset.num_cards_left_dict)

        assert action in infoset.legal_actions

        return action

    # New state = our cards after playing the action, the opponents' cards after playing their next best action
    # The opponents right now choose the first action from the heuritic narrowed-down list
    def build_child_node(self, action_tuple, parent_state):
        new_state = copy.deepcopy(parent_state)

        last_move, player_hand = action_tuple

        # update the last two moves now that we have taken another action
        updated_last_two_moves = [last_move, new_state.last_two_moves[0]]

        # Update the players hand in all_handcards
        new_state.all_handcards[new_state.position] = player_hand

        for i in range(2):
            # increment to the next player
            next_player_position = util.next_player(parent_state.position)

            best_action_tuples = util.get_best_actions(
                util.env_arr2real_card_str(
                    parent_state.all_handcards[next_player_position]),
                updated_last_two_moves)

            # make a random choice for the next player based on their best actions
            action, next_hand = random.choice(best_action_tuples)

            # update last moves
            updated_last_two_moves = [action, updated_last_two_moves[0]]

            # update the players hand at this position
            new_state.all_handcards[next_player_position] = next_hand

        new_state.last_two_moves = updated_last_two_moves

        node = Node(new_state)

        return node

    # def fill_node(self, root_node, depth):
    #     pass
    #     # if depth == 0:
    #     #   return root_node
    #     # BROKEN
    #     # for action_child_pair in root_node.children:
    #     #
    #     #   self.fill_node(action_child_pair[1], depth - 1)

    def create_tree(self, infoset, best_action_tuples):
        global TREE_TARGET_DEPTH
        state = MctsState(infoset.player_position,
                          infoset.last_two_moves, infoset.all_handcards)
        root_node = Node(state)

        # create a node for each action from the hand
        for action_tuple in best_action_tuples:
            child_node = self.build_child_node(action_tuple, state)
            root_node.children[tuple(action_tuple[0])] = child_node

        # self.fill_node(root_node, TREE_TARGET_DEPTH)
        return root_node

    def choose_best_action_from_children(self, tree, infoset):
        lowest_num_cards_left = float('inf')
        best_action = None
        for action in tree.children:
            child_node = tree.children[action]
            if child_node.getScore() < lowest_num_cards_left:
                lowest_num_cards_left = child_node.getScore()
                best_action = action
        if best_action == None:
            return random.choice(infoset.legal_actions)
        result = list(best_action)

        return result

    # def traverse_round_tree(self, infoset):
    #   target_leaf_hand = None  # TODO
    #
    #   # while fully_expanded(node):
    #   #   node = best_uct(node)
    #   #
    #   # # in case no children are present / node is terminal
    #   # return pick_univisted(node.children) or node
    #
    #   return target_leaf_hand
    #
    # def round_rollout_policy(self, legal_actions_from_hand):
    #   return random.choice(legal_actions_from_hand)
    #
    # def rollout_round(self, target_leaf_hand):
    #   simulation_result = None  # TODO
    #   #   while non_terminal(node):
    #   #     node = rollout_policy(node)
    #   #   return result(node)
    #   return simulation_result
    #
    # def backpropagate(self, target_leaf_hand, simulation_result):
    #   # TODO update the mcts data??
    #
    #   #   if is_root(node) return
    #   #   node.stats = update_stats(node, result)
    #   #   backpropagate(node.parent)
    #   return None  # TODO nothing to return
