import enum

__all__ = ("ElementType", "Specialty")


class ElementType(enum.IntEnum):
    PHYSICAL = 200
    FIRE = 201
    ICE = 202
    ELECTRIC = 203
    ETHER = 205


class Specialty(enum.IntEnum):
    ATTACK = 1
    STUN = 2
    ANOMALY = 3
    SUPPORT = 4
    DEFENSE = 5
    RUPTURE = 6
