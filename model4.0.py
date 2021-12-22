from mesa import Agent, Model, agent
from mesa.space import SingleGrid
from mesa.time import RandomActivation
import math
import random
from mesa.visualization.modules.CanvasGridVisualization import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import numpy as np
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import average, percentile
from mesa.visualization.modules import ChartModule
from mesa.datacollection import DataCollector
from matplotlib import pyplot as plt
from numpy.random.mtrand import normal, rand

expected_monthly_appreciation = 0.02


def sigma(x):
    return 1 / (1 + math.exp(-x))


def income_randomizer():
    inkomen_dist = []

    for i in range(0, 100, 2):
        a = i * 1000
        b = (i + 2) * 1000
        inkomen_dist.append(random.randint(a, b))

    return inkomen_dist


def vermogen_randomizer():
    vermogen_verdeling_huishouden = [1451 + 1240.1, 872.3, 1421.1, 2163, 365.2, 179.1]
    vermogen_verdeling_huishouden = np.asarray(vermogen_verdeling_huishouden) / sum(
        vermogen_verdeling_huishouden
    )

    # source: cbs
    vermogen_dist = [
        random.randint(0, 5000),
        random.randint(5000, 20000),
        random.randint(20000, 100000),
        random.randint(100000, 500000),
        random.randint(500000, 1000000),
        random.randint(1000000, 3000000),
    ]

    return random.choices(vermogen_dist, vermogen_verdeling_huishouden)


class Household(Agent):
    def __init__(self, unique_id: int, model: Model, type, init_wealth, income) -> None:
        super().__init__(unique_id, model)
        self.type = type
        self.wealth = init_wealth
        self.income = income
        self.owned_houses = []
        self.offers = {}
        self.offers_rent = {}

    def step(self):
        if self.type[0] == 'social':

            # desired housing expenditure p
            p = min(
                self.income
                * math.exp(np.random.random() / (1 - expected_monthly_appreciation)),
                self.max_available_mortgage(),
            )

            # rent or buy?
            # cost of renting
            # check if houses of type ABCDEF are avaible and if so try to buy them

            list_of_potential_buy = self.house_buy_checker()

            if list_of_potential_buy != None:

                quality = list_of_potential_buy[0].quality

                cost_rent = self.model.annual_rent(quality) * (1 + 0.1)

                cost_buy = 12 * (self.mortgage_payment(list_of_potential_buy[0]) - p * expected_monthly_appreciation)
                
                x = cost_rent - cost_buy
                beta = 0.00001
                prob_buy = sigma(beta * x)

                if prob_buy > random.random():
                    # person will buy a house
                    self.make_offer_house(house=list_of_potential_buy[0], price = self.get_price(list_of_potential_buy[0]))
                else:
                    cheapest_option = 100000000
                    for house in self.model.rent_market:
                        for rent in house.rent:
                            if rent < cheapest_option:
                                cheapest_option = rent
                                cheapest_house = house
                    if cheapest_option != 100000000:
                        self.rent(cheapest_house, cheapest_option)

        elif self.type == "owner_occ":
            prob_sell = 1 / 12 * max(1 / 11 * (1 + len(self.model.sell_market)), 0)

            if prob_sell > random.random():
                mark_up = 1
                sell_price = math.exp(
                    mark_up
                    + math.log(self.average_sell_price())
                    - math.log(1 + self.avg_day_on_market())
                )
                self.offer_house(self.owned_houses[0], sell_price)
        elif self.type == "investor":
            delta = 0.7

            exp_total_yield = self.max_yield()

            prob_buy = 1 - (1 - sigma(exp_total_yield)) ** (1 / 12)

            if prob_buy > random.random():
                self.make_offer_house()
            # Only if the houses are not rented out yet

            self.rent_house()

            true_exp_yield = self.max_yield_star()

            prob_sell = 1 - sigma(true_exp_yield) ** (1 / 12)

            if prob_sell > random.random():
                sell_price = math.exp(
                    math.log(self.average_sell_price())
                    - math.log(1 + self.avg_day_on_market())
                )

        if self.offers > 0:
            self.accept_sell_offer()

        if self.offers_rent > 0:
            self.accept_rent_offer()


        # change the number of days a house has been on the market

    def get_price(self, house):
        for selling_house in self.model.sell_market:
            if house == selling_house:
                value = self.model.sell_market[selling_house][1]
        return value

    def mortgage_payment(self, house):
        for selling_house in self.model.sell_market:
            if house == selling_house:
                value = self.model.sell_market[selling_house][1]
        return value /(30*12)

    def max_yield_star(self):
        pass

    def avg_day_on_market(self):
        total_days = 0
        total_houses = 0

        for cell in self.model.cells:
            for house in cell.houses:
                total_days += house.days_on_market
                total_houses += 1
        return total_days / total_houses

    def max_yield(self):
        delta = 0.6
        for house in self.model.sale_market:
            price = self.get_price(house)
            quality = house.quality
            exp_total_yield = (price*( delta * expected_monthly_appreciation + (1 - delta) * self.average_rental_yield(quality, price)  - price / (30*12)))



    def average_rental_yield(self, quality, price):
        annual_rent = self.model.annual_rent(quality)
        return annual_rent / price


    def average_sell_price(self):
        if len(self.model.prev_sale_prices) == 0:
            return 300000
        else:
            return sum(self.model.prev_sale_prices) / len(self.model.prev_sale_prices)

    def make_offer_rent(self, house, rent):
        if rent > self.income:
            pass
        else:
            tentant_id = house.owner_id
            self.find_agent(tentant_id).offers_rent[house] = [self.unique_id, rent]

    def set_rent(self, house, rent):
        self.model.rent_market[house] = [self.unique_id, rent]

    def accept_rent_offer(self):
        choice = random.choice(self.offers_rent)
        house = choice.keys()
        renter_id = choice[house][0]
        rent = choice[house][1]
        self.find_agent(renter_id).status == "renter"
        house.status = "renting"

        del self.model.rent_market[house]

    def house_buy_checker(self):
        potential_buy = []
        counterA = 0
        counterB = 0
        counterC = 0
        counterD = 0
        counterE = 0

        for house in self.model.sell_market:
            if house.quality == "A":
                counterA += 1
            if house.quality == "B":
                counterB += 1
            if house.quality == "C":
                counterC += 1
            if house.quality == "D":
                counterD += 1
            if house.quality == "E":
                counterE += 1

        if counterA != 0:
            for house in self.model.sell_market:
                if house.quality == "A":
                    potential_buy.append(house)
            return potential_buy
        elif counterA == 0 and counterB != 0:
            for house in self.model.sell_market:
                if house.quality == "B":
                    potential_buy.append(house)
            return potential_buy
        elif counterA == 0 and counterB == 0 and counterC != 0:
            for house in self.model.sell_market:
                if house.quality == "C":
                    potential_buy.append(house)
            return potential_buy
        elif counterA == 0 and counterB == 0 and counterC == 0 and counterD != 0:
            for house in self.model.sell_market:
                if house.quality == "D":
                    potential_buy.append(house)
            return potential_buy
        elif (
            counterA == 0
            and counterB == 0
            and counterC == 0
            and counterD == 0
            and counterE != 0
        ):
            for house in self.model.sell_market:
                if house.quality == "E":
                    potential_buy.append(house)
            return potential_buy

    def max_available_mortgage(self):
        return 0.28 * self.income + self.wealth

    def offer_house(self, house, sell_price):
        self.model.sell_market[house] = [self.unique_id, sell_price]

    def make_offer_house(self, house, price):
        id = house.owner_id
        for agent in self.model.household_agents:
            if agent.unique_id == id:
                agent.offers[house] = [self.unique_id, price]

    def find_agent(self, id):
        for agent in self.model.household_agents:
            if agent.unique_id == id:
                return agent

    def accept_sell_offer(self):

        choice = random.choice(self.offers)
        house = choice.keys()
        offer_id = choice[house][0]
        sell_price = choice[house][1]
        self.find_agent(offer_id).owned_houses.append(house)
        self.owned_houses.remove(house)
        self.wealth = self.wealth + sell_price
        self.find_agent(offer_id).wealth = self.find_agent(offer_id).wealth - sell_price
        house.owner_id = offer_id

        if len(self.model.prev_sale_prices) == 0:
            self.model.prev_sale_prices[house.quality] = []

        self.model.prev_sale_prices[house.quality].append(sell_price)

        if self.type == "owner_occ":
            self.type = "social"

        del self.model.sell_market[house]


class House:
    def __init__(self, size) -> None:
        self.size = size
        self.owner_id = -1
        self.status = ""
        self.rent = 0
        self.location = ""
        self.quality = ""
        self.days_on_market = 0

    def change_status(self, status):
        self.status = status

    def change_rent(self, rent_value):
        self.rent = rent_value


def housemaker(self, amount_houses):
    house_list = []
    for i in range(amount_houses):
        house_list.append(
            House(
                size=random.choices(
                    [
                        random.randint(20, 49),
                        random.randint(50, 74),
                        random.randint(75, 100),
                        random.randint(101, 149),
                        random.randint(149, 250),
                        random.randint(250, 500),
                    ],
                    weights=[0.038, 0.41, 0.29, 0.18, 0.07, 0.02],
                )[0]
            )
        )
    return house_list


class Cell_agent(Agent):
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        # list/dict  containing house objects
        self.houses = []
        self.location = ""
        self.wealth = np.NAN


class Housemarket(Model):
    def __init__(self, N, M, width, height):
        self.num_household = N
        self.num_houses = M
        self.grid = SingleGrid(width=width, height=height, torus=False)
        self.schedule = RandomActivation(self)

        self.cells = []
        self.household_agents = []
        self.current_id = 0

        # create M houses
        self.houses = housemaker(self, M)
        self.empty_houses = self.houses
        self.sell_market = {}
        self.rent_market = {}
        self.prev_sale_prices = {}

        # create N households
        for i in range(N):
            income_dist = income_randomizer()
            agent_income = random.choices(
                income_dist,
                weights=[
                    0.006195147,
                    0.007356737,
                    0.007485803,
                    0.008389262,
                    0.009163655,
                    0.013164688,
                    0.026587506,
                    0.054852865,
                    0.056659783,
                    0.066855963,
                    0.07188952,
                    0.063242127,
                    0.062338668,
                    0.061822406,
                    0.059628291,
                    0.056788849,
                    0.052658751,
                    0.047883325,
                    0.041946309,
                    0.035880227,
                    0.030330408,
                    0.025425916,
                    0.021166753,
                    0.017552917,
                    0.014584409,
                    0.012003098,
                    0.009808983,
                    0.008131131,
                    0.006711409,
                    0.005549819,
                    0.00464636,
                    0.003871967,
                    0.003355705,
                    0.002968508,
                    0.002452246,
                    0.002194115,
                    0.001935983,
                    0.001677852,
                    0.001419721,
                    0.001290656,
                    0.00116159,
                    0.001032525,
                    0.000903459,
                    0.000774393,
                    0.000774393,
                    0.000645328,
                    0.000645328,
                    0.000516262,
                    0.000516262,
                    0.000516262,
                ],
            )

            agent_income = agent_income[0] / 12
            vermogen = vermogen_randomizer()[0]

            agent_type = ""

            if vermogen >= 500000:
                if random.random() > 0.93:
                    agent_type = "investor"
                else:
                    agent_type = "owner_occ"
            else:
                agent_type = random.choices(["owner_occ", "social"], weights=[0.4, 0.6])

            a = Household(
                self.next_id(),
                self,
                type=agent_type,
                init_wealth=vermogen,
                income=agent_income,
            )

            self.schedule.add(a)
            self.household_agents.append(a)

        # Create cells to put houses in
        for i in range(width * height):
            a = Cell_agent(self.next_id(), self)

            self.schedule.add(a)
            self.grid.position_agent(a)
            x = a.pos[0]
            y = a.pos[1]

            a.location = self.location_finder(x, y)

            self.cells.append(a)

        # Put houses inside the cells randomly
        self.house_placer()

        self.house_assign()
        self.owner_assign()

        for cell in self.cells:
            for house in cell.houses:
                house.location = cell.location

        for cell in self.cells:
            for house in cell.houses:
                if house.location == "Centrum" and house.size >= 100:
                    house.quality = "A"
                elif house.location == "Centrum" and house.size < 100:
                    house.quality = "B"
                elif house.location == "Noord" and house.size >= 100:
                    house.quality = "B"
                elif house.location == "Noord" and house.size < 100:
                    house.quality = "C"
                elif house.location == "West" and house.size >= 100:
                    house.quality = "C"
                elif house.location == "West" and house.size < 100:
                    house.quality = "D"
                elif house.location == "South" and house.size > 100:
                    house.quality = "B"
                elif (
                    house.location == "South" and house.size < 100 and house.size >= 75
                ):
                    house.quality = "C"
                elif house.location == "South" and house.size < 75:
                    house.quality = "C"
                elif house.location == "East" and house.size > 150:
                    house.quality = "B"
                elif house.location == "East" and house.size < 150 and house.size > 75:
                    house.quality = "C"
                elif house.location == "East" and house.size < 75:
                    house.quality = "D"

        self.datacollector = DataCollector(model_reporters={"avg": average_sale_price}, agent_reporters={"Wealth": "wealth"})

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

    def house_placer(self):
        for house in self.houses:
            random.choice(self.cells).houses.append(house)

    def location_finder(self, x, y):
        if (x - width / 2) ** 2 + (y - width / 2) ** 2 < width / 4:
            return "Centrum"
        elif abs(x - width / 2) <= y - width / 2:
            return "Noord"
        elif abs(y - width / 2) <= x - width / 2:
            return "East"
        elif abs(y - width / 2) <= -x + width / 2:
            return "West"
        elif abs(x - width / 2) < -y + width / 2:
            return "South"

    def house_assign(self):
        for agent in self.household_agents:
            house = self.empty_houses.pop(0)
            agent.owned_houses.append(house)

    def owner_assign(self):
        for agent in self.household_agents:
            for owned_house in agent.owned_houses:
                owned_house.owner_id = agent.unique_id

    def annual_rent(self, quality):
        counter = 0
        total_rent = 0
        for cell in self.cells:
            for house in cell.houses:
                if house.status == "renting" and house.quality == quality:
                    total_rent == house.rent + total_rent
                    counter += 1

        total_rent = total_rent * 12
        
        if counter == 0:
            return 12000
        else:
            return total_rent / counter
    
def average_sale_price(model):
    total_price = 0
    total_sales = 0
    for quality, prices in model.prev_sale_prices.items():
        total_price += prices
        total_sales += 1
    if total_sales != 0:
        return total_price/total_sales
    else:
        return 0


def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Color": "red",
        "Filled": "true",
        "Layer": "0",
        "r": "1",
    }

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


if __name__ in "__main__":
    width = 5
    height = 5
    model = Housemarket(150, 2000, 5, 5)
    for i in range(100):
        model.step()

    agent_wealth = model.datacollector.get_agent_vars_dataframe()
    avg_sell_price = model.datacollector.get_model_vars_dataframe()
    agent_wealth = agent_wealth["Wealth"].dropna()
    print(avg_sell_price)

    



    # grid = CanvasGrid(agent_portrayal, width, height, 500, 500)
    # chart = ChartModule([{"Label": "Average house prices", "Color" : "Black"}], data_collector_name='datacollector')
    # server = ModularServer(
    #     Housemarket,
    #     [grid],
    #     "Housemarket",
    #     {"N": 100, "M": 100, "width": width, "height": height},
    # )
    # server.port = 8521  # The default
    # server.launch()
