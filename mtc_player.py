#!/usr/bin/env python3
"""
Quoridor agent.
Copyright (C) 2013, <<<<<<<<<<< YOUR NAMES HERE >>>>>>>>>>>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

"""

from collections import deque
import math
from quoridor import *


class MTCAgent(Agent):

    """My Quoridor agent."""

    def play(self, percepts, player, step, time_left):
        """
        This function is used to play a move according
        to the percepts, player and time left provided as input.
        It must return an action representing the move the player
        will perform.
        :param percepts: dictionary representing the current board
            in a form that can be fed to `dict_to_board()` in quoridor.py.
        :param player: the player to control in this step (0 or 1)
        :param step: the current step number, starting from 1
        :param time_left: a float giving the number of seconds left from the time
            credit. If the game is not time-limited, time_left is None.
        :return: an action
          eg: ('P', 5, 2) to move your pawn to cell (5,2)
          eg: ('WH', 5, 2) to put a horizontal wall on corridor (5,2)
          for more details, see `Board.get_actions()` in quoridor.py
        """
        # print("percept:", percepts)
        # print("player:", player)
        # print("step:", step)
        # print("time left:", time_left if time_left else '+inf')

        # TODO: implement your agent and return an action for the current step.
        node = self.mtc_search(percepts, player, 10)

        return node.action

    def mtc_search(self, percepts, player, limit):

        board = dict_to_board(percepts)
        node = MTCNode(score=0, visit=0, action=None, board=board, player=player, parent=None)

        for i in range(limit):
            leaf  = self.selection(node)
            child = self.expansion(leaf)
            score = self.simulation(child)
            node  = self.backpropagate(score, child)

        return node.get_most_visited_child()




    def selection(self, root):
        if not root.hasChild():
            return root

        node = root
        while node.hasChild():
            maxS = random.choice(node.children).get_average_score()
            selected_child = None

            for child in node.children:
                if child.get_average_score() >= maxS:
                    maxS = child.get_average_score()
                    selected_child = child

            node = selected_child
        
        return node

    def expansion(self, node):
        if node.visit == 0:
            return node

        clone_board = node.board.clone()

        actions = self.select_move_actions(clone_board, node.player) + self.select_wall_actions(clone_board, node.player)
        
        for action in actions:
            cloned = clone_board.clone()
            opponent = 1 if node.player == 0 else 0
            child = MTCNode(score=0, visit=0, action=action, board=cloned.play_action(action, node.player), player=opponent, parent=node)
            node.addChild(child)

        print(actions)

        if not node.hasChild():
            return node

        return node.firstChild()

    def simulation(self, node):

        node.visit += 1
        player = node.player
        board = node.board.clone()

        while not board.is_finished():
            action = self.choose_next_action(board, player)
            board.play_action(action, player)
            player = PLAYER1 if node.player == PLAYER2 else PLAYER2

        score = board.get_score(PLAYER1)
        node.score += score
        # print(score)
        return score
    
    def backpropagate(self, score, child):
        node = child
        while node.hasParent():
            parent = node.parent
            parent.score += score
            parent.visit += 1
            node = parent

        return node


    def select_wall_actions(self, board, player):
        opponent = 1-player
        # oppo_y, oppo_x = board.pawns[opponent]
        # oppo_goal_y = board.goals[opponent]
        wall_actions = board.get_legal_wall_moves(player)
        wall_dict_wh = dict()
        wall_dict_wv = dict()

        for wall_action in wall_actions:
            if wall_action[0] == 'WH':
                wall_dict_wh[wall_action[1], wall_action[2]] = wall_action[0] 
            else:
                wall_dict_wv[wall_action[1], wall_action[2]] = wall_action[0] 

        candidate_walls = []
    
        moves = board.get_shortest_path(opponent)
        
        for move in moves: 
            if move in wall_dict_wh:
                candidate_walls.append((wall_dict_wh[move], move[0], move[1]))

        # if oppo_goal_y < oppo_y:
        #     for wall_action in wall_actions:
        #         wall_dir, wall_y, wall_x = wall_action
        #         if wall_dir == 'WH' and wall_y == oppo_y - 1 and wall_x in (oppo_x, oppo_x - 1):
        #             candidate_walls.append(wall_action)
        #         if wall_dir == 'WV' and wall_y == oppo_y and wall_x in (oppo_x, oppo_x + 1):
        #             candidate_walls.append(wall_action)
        # else:
        #     for wall_action in wall_actions:
        #         wall_dir, wall_y, wall_x = wall_action
        #         if wall_dir == 'WH' and wall_y == oppo_y - 1 and wall_x in (oppo_x, oppo_x - 1):
        #             candidate_walls.append(wall_action)
        #         if wall_dir == 'WV' and wall_y == oppo_y and wall_x in (oppo_x, oppo_x + 1):
        #             candidate_walls.append(wall_action)
        # print(candidate_walls)
        return candidate_walls

    def select_move_actions(self, board, player):
        # actions = []
        # for move in board.get_shortest_path(player):
        #     actions.append(('P', move[0], move[1]))
        
        return board.get_legal_pawn_moves(player)

    def choose_next_action(self, board, player):
        my_moves  = board.get_shortest_path(player)
        opp_moves = board.get_shortest_path(1 - player)

        if len(my_moves) > len(opp_moves):
            wall_actions = self.select_wall_actions(board, player)
            if len(wall_actions) > 0:
                choice = random.choice(wall_actions)
                return choice
            
        # next_moves = self.select_move_actions(board, player)
        # print(f"Moving : {next_moves[0]}")
        # return random.choice(next_moves)
        
        move = my_moves[0]
        # print(f"Shortest path : {moves}")
        return ('P', move[0], move[1])



class MTCNode():
    def __init__(self, score=0, visit=0, actions=[], action=None, board=None, player=None, parent=None) -> None:
        self.score = score
        self.visit = visit
        self.parent = parent
        self.actions = actions
        self.action = action
        self.player = player
        self.board = board
        self.children = []

    def get_average_score(self):
        if self.visit > 0:
            c = 0
            explore =  c * math.sqrt(math.log(self.parent.visit) / self.visit) if self.hasParent() else 0
            return (self.score / self.visit) + explore
        return 0

    def hasChild(self):
        return len(self.children) > 0

    def addChild(self, child):
        self.children.append(child)

    def firstChild(self):
        return self.children[0]

    def hasParent(self):
        return self.parent != None

    def get_most_visited_child(self):
        max_v = 0
        most_visited = None
        for child in self.children:
            if child.visit > max_v:
                max_v = child.visit
                most_visited = child

        return most_visited


def printTree(node):
    queue = deque()
    queue.append(node)
    while len(queue) > 0:
        current = queue.popleft()
        s = '\n'
        for child in current.children:
            queue.append(child)
            s += f"({child.visit}) "
        print(s)


if __name__ == "__main__":
    agent_main(MTCAgent())
