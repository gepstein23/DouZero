import random
import json

MCTS_DATA_FILE_NAME = 'C:\\Users\\Genevieve\\Desktop\\NEU\\Fall_2021\\ai\\DouZero\\douzero\\evaluation\\mcts_agent_data.txt' #TODO
VERBOSE = True

def debug(*msgs):
    global VERBOSE
    if VERBOSE:
        result = ""
        for msg in msgs:
            result += str(msg)
        print(result)

# **Modified** MCTS Agent:
# This agent is called upon each time an action is to be selected.
# Each time it is called upon, it is trained with MCTS a certain number of times
# Each game this agent is used, it will update the saved mcts data to be used
class MctsAgent:

    ######################################################################
    ########################## UTILITIES #################################
    ######################################################################

    def __init__(self, mcts_data_file_name=MCTS_DATA_FILE_NAME):
        self.name = 'MCTS'
        self.mcts_data_file_name = mcts_data_file_name

        # Stores data about each node and the quality of each possible action
        self.mcts_data = self.load_mcts_data()

    # Loads stores MCTS data from the save file and stores in self.mcts_data as a dictionary
    def load_mcts_data(self):
        with open(self.mcts_data_file_name, 'r') as file:
            mcts_data = file.read()
        mcts_data_dict = json.loads(mcts_data)
        return mcts_data_dict

    # Updates the MCTS Data file with the updated contents of self.mcts_data
    def save_mcts_data(self):
        with open(self.mcts_data_file_name, 'w') as file:
            file.write(json.dumps(self.mcts_data))

    ######################################################################
    ########################## ALGORITHM #################################
    ######################################################################
    ### Follwing pseudo code from https://www.geeksforgeeks.org/ml-monte-carlo-tree-search-mcts/

    # Returns the best action from the curr_hand based on self.mcts_data
    # (The action that will lead to the child with the highest number of visits)
    def get_best_action(self, curr_hand):
        return None # TODO

    def traverse_round_tree(self, infoset):
        target_leaf_hand = None # TODO

        # while fully_expanded(node):
        #     node = best_uct(node)
        #
        # # in case no children are present / node is terminal
        # return pick_univisted(node.children) or node

        return target_leaf_hand

    def round_rollout_policy(self, legal_actions_from_hand):
        return random.choice(legal_actions_from_hand)

    def rollout_round(self, target_leaf_hand):
        simulation_result = None # TODO
        #     while non_terminal(node):
        #         node = rollout_policy(node)
        #     return result(node)
        return simulation_result

    def backpropagate(self, target_leaf_hand, simulation_result):
        # TODO update the mcts data??

        #     if is_root(node) return
        #     node.stats = update_stats(node, result)
        #     backpropagate(node.parent)
        return None # TODO nothing to return

    # Runs the given number of iterations PER action taken
    # Saves the updated data to the save file
    # Returns the best action
    def act(self, infoset, num_iterations=10):
        curr_hand = infoset.player_hand_cards
        curr_legal_actions = infoset.legal_actions

        if len(curr_legal_actions) == 0:
            debug("No actions to take with hand: ", curr_hand)
            return None

        # Run the current number of iterations
        while num_iterations != 0:
            target_leaf_hand = self.traverse_round_tree(infoset)
            simulation_result = self.rollout_round(target_leaf_hand)
            self.backpropagate(target_leaf_hand, simulation_result)
            num_iterations -= 1

        self.save_mcts_data()
        return self.get_best_action(curr_hand)