from re import L
from typing import Sequence
from mesa import Agent, Model
from mesa.space import SingleGrid
from mesa.time import RandomActivation
import math
import random
from mesa.visualization.modules.CanvasGridVisualization import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import numpy as np
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import average
import statistics

class Household(Agent):
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        self.type = ""
        self.wealth = 0
        self.income = 0
        self.age = 0
        self.owned_houses = []

        def step(self):
            if self.type == "renter":
                # p could also be just maximum mortgage
                alpha = 0
                p = min(alpha * self.income * math.exp(np.random.normal(0,1,100)) / 1 - beta * g, self.max_mortgage())

                tao = 0.02
                r = model.annual_rent()

                cost_rent = r (1 + tao)
                
                g = 0.035
                # m is monthly mortgage payment per house how do we calculate that
                m = 2000
                cost_buying = 12(m - p*g)

                beta = 1

                prob_buy = 1 / (1 + math.exp(-1* (beta(cost_rent - cost_buying))))

                if prob_buy > random.random():
                    self.buy_house()


            elif self.type == "owner_occ":
                house_stock = 0
                alpha = 1
                prob_sell = 1/12 * max(1/11 * (1 + alpha *(house_stock)), 0)

                if prob_sell > random.random():
                    beta = 1
                    sell_price = math.exp(alpha + math.log(average_sale_price) - beta * math.log(y* (1+f) ) + np.random.random(0,1,100))
                    self.sell_house(sell_price)

            elif self.type == "investor":
                delta = 0.7
                g = 0.035
                average_rental_yield = 500
                mortgage_costs = 200000
                buy_price = 1500000

                total_exp_yield = buy_price (delta * g + (1 - delta) * average_rental_yield) - mortgage_costs

                beta = 1
                prob_buy = 1 - (1 - (1/1 + math.exp(-(beta * total_exp_yield))))^(1/12)

                alpha = 400
                price_rent = math.exp(alpha + math.log(average_rent_price) - beta * math.log(y (1 + f)))

                if prob_buy > random.random():
                    self.buy_house()
                    self.rent_house()


                
                

                prob_sell = 1 - (1/1+math.exp(-(beta* total_exp_yield)))^(1/12)

                y = 1
                sell_price_investor = math.exp(alpha + math.log(average_sale_price) - beta * math.log(y* (1 + avg_num_days_onmarket)) + np.random.random(0,1,100))
                
                if prob_sell > random.random():
                    self.sell_house()

                



        def max_mortgage(self):
            monthly_PITI = self.income * 0.28 
            return monthly_PITI


        def sell_house(sale_price, house):
            

        def buy_house(house_id):
            pass

        def rent_house(house_id, rent):
            pass


def average_sale_price(model, quality_house):
    return statistics.mean(model.prev_sale[quality_house])

        



class cellContents(Agent):
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        # list/dict  containing house objects
        self.houses = []
        self.location = ""


class House():
    def __init__(self, size) -> None:
        self.size = size
        self.initial_value = 0
        self.market_value = 0
        self.owner_id = ""
        self.status = ""
        self.rent = 0

class Market():
    def __init__(self) -> None:
        self.sale_offers = {}
        self.rent_offers = {}

    def add_house(self, house, price, type):
        if type == "rent":
            self.sale_offers[house] = price
        elif type == "sale":
            self.rent_offers[house] = price
        

class Housemarket(Model):
    def __init__(self, N, M,width, height) -> None:
        self.num_household = N
        self.grid = SingleGrid(width = width, height = height, torus = False)
        self.schedule = RandomActivation(self)
        self.num_houses = M
        self.cell_agents = []
        self.household_agents = []
        self.current_id = 0
        self.sale_market = []
        self.rent_market = []
        self.prev_sales = {}


        # Creating households
        for i in range(N):
            inkomen_dist = income_randomizer()
            inkomen = random.choices(inkomen_dist, weights=[0.006195147,0.007356737,0.007485803,0.008389262,0.009163655,0.013164688,0.026587506,0.054852865,0.056659783,0.066855963,0.07188952,0.063242127,0.062338668,0.061822406,0.059628291,0.056788849,0.052658751,0.047883325,0.041946309,0.035880227,0.030330408,0.025425916,0.021166753,0.017552917,0.014584409,0.012003098,0.009808983,0.008131131,0.006711409,0.005549819,0.00464636,0.003871967,0.003355705,0.002968508,0.002452246,0.002194115,0.001935983,0.001677852,0.001419721,0.001290656,0.00116159,0.001032525,0.000903459,0.000774393,0.000774393,0.000645328,0.000645328,0.000516262,0.000516262,0.000516262])
            
            vermogen = vermogen_randomizer()[0]
            a = Household(i, self)

            self.schedule.add(a)

            a.income = inkomen / 12
            a.wealth = vermogen

            a.type = random.choices(["owner_occ", "renter", "investor"], weights = [0.7, 0.15, 0.15])
            self.household_agents.append(a)
            self.current_id = i


        # Creating houses and placing them on the grid
        self.houses = []
        for i in range(self.num_houses):
            self.houses.append(House(size=random.choices([random.randint(20,49),  random.randint(50,74),  random.randint(75,100),  random.randint(101,149),  random.randint(149,250), random.randint(250,500)] , 
                                    weights = [0.038, 0.41, 0.29, 0.18, 0.07, 0.02])))



        # Creating cell agents and placing houses inside these cell agents
        for i in range(width*height):
            a = cellContents(self.next_id(), self)
            self.schedule.add(a)
            self.grid.position_agent(a)
            x = a.pos[0]
            y = a.pos[1]

            # Assign area for every house that is placed
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
            random_num = random.randint(0,3)

            
            self.total_houses = 0

            for i in range(random_num):
                a.houses.append(self.houses[random.randint(0,len(self.houses) - 10)])
                self.total_houses += 1

            self.cell_agents.append(a)


        # loop through all agents that are households and give them houses depending on the status
        
        c1 = 0
        for household in self.household_agents:
            if household.wealth >= 500000:
                if random.random() > 0.95:
                    household.type = "investor"
                else:
                    household.type = "owner_occ"
            else:
                household.type = random.choices(["owner_occ", "renter"], weights = [0.7, 0.3])
            
        if household.type != "renter":
            self.cell_agents[c1].owner_id = household.unique_id
            c1 += 1

        

        def step(self):
            self.schedule.step()
        

        def annual_rent(self, quality_house):
            for house in self.cell_agents:
                if house.status == "rented_out":
                    if house.quality == quality_house:
                        cost_of_renting = 12 * house.rent
            return cost_of_renting




def income_randomizer():
    inkomen_dist = []

    for i in range(0, 100, 2):
        a = i * 1000
        b = (i+2) *1000
        inkomen_dist.append(random.randint( a , b ))

    return inkomen_dist

def vermogen_randomizer():
    vermogen_verdeling_huishouden = [1451 + 1240.1, 872.3, 1421.1, 2163, 365.2, 179.1]
    vermogen_verdeling_huishouden = np.asarray(vermogen_verdeling_huishouden)/ sum(vermogen_verdeling_huishouden)
    
    #source: cbs
    vermogen_dist = [random.randint(0, 5000), random.randint(5000, 20000), random.randint(20000, 100000), random.randint(100000, 500000), random.randint(500000, 1000000), random.randint(1000000, 3000000)]

    return random.choices(vermogen_dist, vermogen_verdeling_huishouden)


def agent_portrayal(agent):
    portrayal = {"Shape":"circle", "Color": "red", "Filled" : "true", "Layer": "0", "r": "1"}

    if agent.location == "Centrum":
        portrayal["Color"] = "red"
        portrayal["Layer"] = "0"
        if len(agent.houses) < 2:
            portrayal["r"] = "0.2"
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

if __name__ in '__main__':
    width = 25
    height = 25
    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)
    server = ModularServer(Housemarket,
                       [grid],
                       "Housemarket",
                       {"N":100, "M" : 100 ,"width":width, "height":height})
server.port = 8521 # The default
server.launch()
