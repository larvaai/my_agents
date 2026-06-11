# Society Sim Complex - Domain Constants
# All domain constants for the life simulation engine.

from typing import Final

# Population and Household Defaults
DEFAULT_POPULATION: Final[int] = 10
DEFAULT_HOUSEHOLDS: Final[int] = 3
DEFAULT_HOMES: Final[int] = 4
DEFAULT_JOBS: Final[int] = 6
DEFAULT_LOCATIONS: Final[int] = 6
DEFAULT_ACTION_TYPES: Final[int] = 12
DEFAULT_RANDOM_EVENTS: Final[int] = 6
DEFAULT_DAILY_EVENTS: Final[int] = 6

# Time Constants (in simulation ticks)
TICKS_PER_DAY: Final[int] = 240
TICKS_PER_HOUR: Final[int] = 10
TICKS_PER_MINUTE: Final[int] = 1
DAY_LENGTH_TICKS: Final[int] = TICKS_PER_DAY

# Resource Constants (base units)
BASE_MONEY: Final[float] = 100.0
BASE_FOOD: Final[int] = 50
BASE_HYGIENE: Final[int] = 30
BASE_ENERGY: Final[int] = 100
BASE_SATISFACTION: Final[int] = 70

# Health and Vitality Ranges
HEALTH_CRITICAL_LOW: Final[int] = 20
HEALTH_CRITICAL_HIGH: Final[int] = 80
ENERGY_MIN: Final[int] = 0
ENERGY_MAX: Final[int] = 100
SATISFACTION_MIN: Final[int] = 0
SATISFACTION_MAX: Final[int] = 100

# Simulation Control Constants
SIMULATION_TICKS_PER_RUN: Final[int] = 365 * TICKS_PER_DAY  # One year default
DEFAULT_SEED: Final[int] = 42
MAX_SIMULATION_DAYS: Final[int] = 7300  # 20 years max