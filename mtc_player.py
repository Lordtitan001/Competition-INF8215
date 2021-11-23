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
import time
import sys


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
        self.player = player
        self.step = step
        self.time_left = time_left
        self.iteration = 300

        node = self.mtc_search(percepts, player, self.iteration)
        return node.action


    def mtc_search(self, percepts, player, limit):

        board = dict_to_board(percepts)
        node = MTCNode(score=0, visit=0, action=None,
                       board=board, player=player, parent=None)
        start = time.time()
        while limit > 0 and time.time() - start < 8:
            leaf = self.selection(node)
            child = self.expansion(leaf)
            score = self.simulation(child)
            node = self.backpropagate(score, child)
            limit -= 1

        return node.get_most_visited_child()

    def selection(self, root):
        if not root.hasChild():
            return root

        node = root
        while node.hasChild():
            selected_child = random.choice(node.children)
            maxS = selected_child.get_average_score()

            for child in node.children:
                if child.get_average_score() > maxS:
                    maxS = child.get_average_score()
                    selected_child = child

            node = selected_child

        return node

    def expansion(self, node):
        if node.visit == 0:
            return node

        clone_board = node.board.clone()

        if clone_board.is_finished():
            return node

        actions = self.select_actions(clone_board, node.player)

        for action in actions:
            cloned = clone_board.clone()
            opponent = 1 - node.player
            child = MTCNode(score=0, visit=0, action=action, board=cloned.play_action(
                action, node.player), player=opponent, parent=node)
            node.addChild(child)

        if not node.hasChild():
            return node

        return node.randomChild()

    def simulation(self, node):

        node.visit += 1
        player = node.player
        board = node.board.clone()

        score = 0

        if 1 - player == self.player:
            player_steps = board.min_steps_before_victory_safe(self.player)
            oppo_steps = board.min_steps_before_victory_safe(1 - self.player)

            score = oppo_steps - player_steps

        node.score += score
        return score

    def backpropagate(self, score, child):
        node = child
        while node.hasParent():
            parent = node.parent
            parent.score += score
            parent.visit += 1
            node = parent

        return node

    def select_actions(self, board, player):
        try:
            opp_moves = board.get_shortest_path(1 - player)
            my_moves = board.get_shortest_path(player)

            return self.select_move_actions(board, player, opp_moves, my_moves) + \
                self.select_wall_actions(
                board, player, opp_moves, my_moves)
        except NoPath:
            print("No path exception")
            temp = board.pawns[1 - player]
            board.pawns[1 - player] = board.pawns[player]
            my_moves = board.get_shortest_path(player)
            board.pawns[1 - player] = temp

            temp = board.pawns[player]
            board.pawns[player] = board.pawns[1 - player]
            opp_moves = board.get_shortest_path(1 - player)
            board.pawns[player] = temp

            return self.select_move_actions(board, player, opp_moves, my_moves) + \
                self.select_wall_actions(
                board, player, opp_moves, my_moves)

    def select_wall_actions(self, board, player, opp_moves, my_moves):
        opponent = 1-player
        oppo_y, oppo_x = board.pawns[opponent]
        oppo_goal_y = board.goals[opponent]
        candidate_walls = []

        if board.nb_walls[player] == 0:
            return []

        if len(my_moves) < len(opp_moves):
            return []

        actions = []

        for (wall_y, wall_x) in board.horiz_walls:
            actions += [('WV', wall_y + 1, wall_x - 1), ('WV', wall_y + 1, wall_x - 1), ('WV', wall_y + 1, wall_x + 1),
                        ('WV', wall_y, wall_x - 1), ('WV', wall_y, wall_x - 1), ('WV', wall_y, wall_x + 1)]

        for (wall_y, wall_x) in board.verti_walls:
            actions += [('WH', wall_y + 2, wall_x + 1), ('WH', wall_y + 2, wall_x - 1),
                        ('WH', wall_y - 1, wall_x +
                         1), ('WH', wall_y - 1, wall_x - 1),
                        ('WH', wall_y + 1, wall_x +
                         1), ('WH', wall_y + 1, wall_x - 1),
                        ]

        for move in opp_moves:
            actions += [('WH', move[0], move[1]), ('WH', move[0], move[1] - 1), 
                        ('WV', move[0], move[1] - 1), ('WV', move[0] + 1, move[1] - 1)]

        if oppo_goal_y < oppo_y:  # Opponent moving North
            actions += [('WH', oppo_y - 1, oppo_x),
                        ('WH', oppo_y - 1, oppo_x - 1)]

        else:
            actions += [('WH', oppo_y, oppo_x), ('WH', oppo_y, oppo_x - 1)]

        for action in actions:
            if board.is_action_valid(action, player):
                candidate_walls.append(action)

        return candidate_walls

    def select_move_actions(self, board, player, opp_moves, my_moves):

        if len(my_moves) == 0:
            return []
        # if len(my_moves) <= len(opp_moves):
        #     move = my_moves[0]
        #     return [('P', move[0], move[1])]
        # else:
        #     return board.get_legal_pawn_moves(player)

        move = my_moves[0]
        return [('P', move[0], move[1])]


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
            c = math.sqrt(2)
            explore = c * \
                math.sqrt(math.log(self.parent.visit) /
                          self.visit) if self.hasParent() else 0
            return (self.score / self.visit) + explore
        return sys.maxsize

    def hasChild(self):
        return len(self.children) > 0

    def addChild(self, child):
        self.children.append(child)

    def randomChild(self):
        return random.choice(self.children)

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


# def printTree(node):
#     queue = deque()
#     queue.append(node)
#     while len(queue) > 0:
#         current = queue.popleft()
#         s = '\n'
#         for child in current.children:
#             queue.append(child)
#             s += f"({child.visit}) "
#         print(s)


if __name__ == "__main__":
    agent_main(MTCAgent())
