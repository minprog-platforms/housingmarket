from typing import Sequence
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import math
import random
from mesa.visualization.modules.CanvasGridVisualization import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


# class Household(Agent):
#     def __init__(self, unique_id: int, model: Model):
#         super().__init__(unique_id, model)
#         self.age = 0
#         self.income_percentile
#         self.initial_wealth
#         self.death_probability
#         self.owned_houses

# class Construction(Agent):
#     def __init__(self, unique_id: int, model: Model):
#         super().__init__(unique_id, model)

class House(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.value = 0
        self.location = ""
        self.size = 0
    


class HouseMarket(Model):
    def __init__(self, N, M, width, height):
        self.num_households = N
        self.num_houses = M
        self.grid = MultiGrid(width, height, torus= False)
        self.schedule = RandomActivation(self)

        for i in range(self.num_houses):
            a = House(i, self)
            self.schedule.add(a)

            #Place the households on a grid
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)

            if (x - width/2)**2 + (y - width/2 )**2 < width/4:
                a.location = "Centrum"
            elif abs(x-width/2) <= y - width/2:
                a.location = "Noord"
            elif abs(y - width/2) <= x - width /2:
                a.location = "East"
            elif abs(y - width / 2) <= - x + width /2 :
                a.location = "West"
            elif abs(x - width/2) <  - y + width/2:
                a.location = "South"

               
            a.size = random.choices([random.randint(20,49),  random.randint(50,74),  random.randint(75,100),  random.randint(101,149),  random.randint(149,250), random.randint(250,500)] , 
                                    weights = [0.038, 0.41, 0.29, 0.18, 0.07, 0.02])


            self.grid.place_agent(a,(x,y))
    
    def step(self):
        self.schedule.step()


def agent_portrayal(agent):
    portrayal = {"Shape":"circle", "Color": "red", "Filled" : "true", "Layer": "0", "r": "0.5", "text": 1 + len(agent.model.grid.get_cell_list_contents([agent.pos]))}
    if agent.location == "Centrum":
        portrayal["Color"] = "red"
        portrayal["Layer"] = "0"
    elif agent.location == "Noord":
        portrayal["Color"] = "blue"
        portrayal["Layer"] = "0"
    elif agent.location == "East":
        portrayal["Color"] = "yellow"
        portrayal["Layer"] = "0"
    elif agent.location == "West":
        portrayal["Color"] = "green"
        portrayal["Layer"] = "0"
    elif agent.location == "South":
        portrayal["Color"] = "black"
        portrayal["Layer"] = "0"
    
    return portrayal

if __name__ == '__main__':
    width = 22
    height = 22
    canvas =  CanvasGrid(agent_portrayal, width, height , 1000, 1000)
    server = ModularServer(HouseMarket,[canvas], "House Market", {"N": 0, "M": 10000, "width": width, "height": height})
    server.port = 8521
    server.launch()