from haas.class_resolver import *


class Food(object):
    pass


class Apple(Food):
    api_name = 'apple'


class Orange(Food):
    api_name = 'orange'


class Drink(object):
    pass


class Juice(Drink):
    pass


class OrangeJuice(Juice):
    api_name = 'orange'


class _AppleJuice(Juice):
    # _AppleJuice is an implementation detail; we don't give it
    # an ``api_name`` because we don't want to expose it to users... for some
    # reason.
    pass


class GrapeJuice(Juice):
    api_name = 'grape'


build_class_map_for(Food)
build_class_map_for(Drink)

assert concrete_class_for(Food, 'apple') is Apple
assert concrete_class_for(Food, 'orange') is Orange
assert concrete_class_for(Food, 'grape') is None
assert concrete_class_for(Drink, 'apple') is None
assert concrete_class_for(Drink, 'orange') is OrangeJuice
assert concrete_class_for(Drink, 'grape') is GrapeJuice
