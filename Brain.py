import numpy as np
import pygame
import random as rand
import neat 
import os

from collections import namedtuple
from pygame import Vector2
from Car import Car
from Line import Line
from math import sqrt


class NeatManager():
	def __init__(self, gd, size, start_position, number):
		self.generation = []
		self.gameDisplay = gd
		self.displaySize = size
		self.number_dead = 0
		self.all_dead = False
		self.start_position = start_position
		self.generation_size = number
		self.generation_number = 0
		self.nets = []
		self.ge = []
		local_dir = os.path.dirname(__file__)
		config_path = os.path.join(local_dir, 'neat_config.txt')
		self.config_file = config_path
		self.last_checkpoint = None

	def createGeneration(self,angle, genome=None,config=None):
		# print("Generation: ", self.generation_number)
		self.all_dead = False
		self.number_dead = 0
		self.generation = []
		generation = []
		nets = []
		ge = []
		for genome_id, g in genome:
			g.fitness = 0
			net = neat.nn.feed_forward.FeedForwardNetwork.create(g, config)
			nets.append(net)
			br = Brain(Car(self.gameDisplay, self.displaySize))
			br.car.position.update(self.start_position)
			br.car.angle = angle
			br.setGenomeNet(g, net)
			generation.append(br)
			ge.append(g)
		self.generation = generation
		self.nets = nets
		self.ge = ge

	def makeMoves(self, walls, checkpoints,time):
		def distance(p1, p2):
			return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
		if self.number_dead >= len(self.generation):
			return
		i = 0
		for c in self.generation:
			if not c.car.crashed:
				move = c.move(walls=walls,checkpoints=checkpoints)
				if move:
					c.car.update(move, walls,
						   checkpoints,time)
				if time - c.car.time > 1500 and distance(c.car.prev_pos, c.car.getCarPos()) < 50:
					c.car.crashed = True
					c.genome.fitness -= 1000
				if c.car.crashed:
					c.genome.fitness += c.car.getScore(time)
					self.nets.pop(self.nets.index(c.neural_network))
					self.generation.pop(self.generation.index(c))
					self.ge.pop(self.ge.index(c.genome))
				if c.car.prev_pos != c.car.getCarPos():
					c.car.prev_pos = c.car.getCarPos()
					c.car.time = time
				i+=1

		if self.number_dead >= len(self.generation):
			# print("Everyone dead boy")
			self.all_dead = True



	def cullTheWeak(self):
		self.generation_number += 1
		# for c in self.generation:
		#     # print(c.car.score)
		self.all_dead = False
		self.number_dead = 0
		while(len(self.generation) > 0):
				self.nets.pop()
				self.generation.pop()
				self.ge.pop()

class Brain():

	def __init__(self, car, brain_file=None,):
		self.car = car
		self.neural_network = None
		self.move_dict = {pygame.K_LEFT:False, pygame.K_UP:False, pygame.K_DOWN: False, pygame.K_RIGHT: False}
		self.move_labels = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_UP]
		self.genome = None 
		self.ge = None
		
	def __repr__(self):
		return str(self.car.score)

	def setGenomeNet(self,genome, nn):
		self.neural_network = nn
		self.genome = genome

	def reset_available(self):
		self.move_dict = {pygame.K_LEFT:False, pygame.K_UP:False, pygame.K_DOWN: False, pygame.K_RIGHT: False}

	def availableMoves(self, choice):
		if choice == 1:
			return {pygame.K_LEFT:True, pygame.K_UP:True, pygame.K_DOWN: False, pygame.K_RIGHT: False}
		elif choice == 2:
			return {pygame.K_LEFT:False, pygame.K_UP:True, pygame.K_DOWN: False, pygame.K_RIGHT: True}
		elif choice == 0:
			return {pygame.K_LEFT:False, pygame.K_UP:True, pygame.K_DOWN: False, pygame.K_RIGHT: False}
		elif choice == 3:
			return {pygame.K_LEFT:False, pygame.K_UP:False, pygame.K_DOWN: True, pygame.K_RIGHT: False}

	def createAgent(self):
		pass

	def getScore(self,time):
		return self.car.getScore(time)

	def move(self, walls=None, checkpoints=None):
		
		def distance(p1,p2):
			return sqrt((p1[0]-p2[0])**2 + 	(p1[1]-p2[1])**2)			
		# Load wall positions and checkpoints
		collision_points = self.see(walls)
		car_corners = self.car.getCornerPos()

		network_input = np.full(len(car_corners)+1,np.inf)
		network_input[-1]=self.car.angle
		for c in collision_points:
			for corner in range(len(car_corners)):
				dist = distance(c,[car_corners[corner][0], car_corners[corner][1]])
				if dist < network_input[corner]:
					network_input[corner] = dist	
		output = 0
		if collision_points:
			output = self.neural_network.activate(network_input)
			output = output.index(max(output))
		
		if not self.car.crashed:
			return self.availableMoves(output)


	def checkStatus(self):
		if self.car.crashed:
			print("IM A BAD BOI :C")

	def see(self, walls, checkpoint=False):
		def distance(p1, p2):
			return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

		car_points = self.car.getCarLines()
		closest_points = []

		# Look at the walls/checkpoints and see the point where the car and the wall collide
		for point in car_points:
			line = Line(Vector2(point[0]), Vector2(point[1]))
			for w in walls:
				col_point = line.intersect(w)
				if col_point and distance(self.car.position, col_point) < 200:
					if checkpoint:
						# Draw the checkpoints as a red dot
						pygame.draw.circle(self.car.game, (0, 255, 0), col_point, 5)

					else:
						# Draw the checkpoints as a green dot
						# pygame.draw.circle(self.car.game, (255, 0, 0), col_point, 5)
						# pygame.draw.line(self.car.game,(255,0,0) ,point[0],col_point,4)
						closest_points.append((col_point.x, col_point.y))

		return closest_points
