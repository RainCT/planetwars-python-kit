#! /usr/bin/env python
# By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>

from planetwars import BaseBot, Game, ME, ENEMIES
from planetwars.planet2 import Planet2
from logging import getLogger

log = getLogger(__name__)

class MyBot(BaseBot):
    
    def do_turn(self):
        fighters_available = {}
        reinforcements_needed = []
        
        # Calculate current ship balance
        for planet in self.universe.my_planets:
            dispensable_ships = planet.dispensable_ships
            if dispensable_ships > 0:
                fighters_available[planet] = dispensable_ships
            elif dispensable_ships < 0:
                reinforcements_needed.append((planet, -dispensable_ships))
        
        # Send out reinforcements, if needed
        for target, required_ships in sorted(reinforcements_needed, key=lambda x: x[0].score_defensive, reverse=True):
            if reduce(lambda x, a: x + a, fighters_available.itervalues(), 0) < required_ships:
                continue # no useless deaths
            for base, available_ships in dict(fighters_available).iteritems():
                base.send_fleet(target, min(available_ships, required_ships))
                if available_ships > required_ships:
                    fighters_available[base] = available_ships - required_ships
                else:
                    del fighters_available[base]
        
        # Pown the universe!
        for planet in sorted(self.universe.not_my_planets, key=lambda planet: planet.score_aggresive, reverse=True):
            if planet.growth_rate < 1:
            	continue # why, this is crap. unless some day we get the concept of support bases
            for base, available_ships in dict(fighters_available).iteritems():
                distance = planet.distance(base)
                future_planet = planet.in_future(distance)
                if (future_planet.owner == ME):
                    break
                required_ships = future_planet.ship_count + 1
                if available_ships > future_planet.ship_count:
                    base.send_fleet(planet, required_ships)
                    fighters_available[base] = min(0, available_ships - required_ships)
                    break

class MyPlanet(Planet2):

    def friendly_planets_in_radius(self, radius):
        for planet in self.universe.find_planets(owner=planet.owner):
            if self.distance(planet) <= radius:
                yield planet
    
    @property
    def dispensable_ships(self):
        """Returns the number of ships the planet can send out without risking
        the user's ownership of this planet.
        
        If this is an enemy or neutral planet, then it returns a negative
        number indicating how many ships are required to take it over."""
        planet = self.in_future()
        if planet.owner == ME:
            if planet.owner == self.owner:
                return planet.ship_count
            else:
                return -planet.ship_count
        else:
            return -planet.ship_count
    
    @property
    def score_defensive(self):
        score = self.growth_rate * 50 - (-self.dispensable_ships)
        return score
    
    @property
    def score_aggresive(self):
        score = self.growth_rate * 50 - (-self.dispensable_ships)
        if self.owner in ENEMIES:
            score += 120
        return score

Game(MyBot, planet_class=MyPlanet)
