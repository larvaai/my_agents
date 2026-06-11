import sys
sys.path.insert(0, '.')

from society_sim_complex import (
    Person,
    Household,
    Home,
    Job,
    Location,
    ActionType,
    RandomEvent,
    DailyEvent,
    Rule,
    Action,
    AutonomyPlanner,
    Relationship,
    Event as SimEvent,
    Economy,
    World,
    Simulation
)

# Minimal test to verify package loads and basic imports work

def test_package_imports():
    # Verify all core types are importable
    assert Person is not None
    assert Household is not None
    assert Home is not None
    assert Job is not None
    assert Location is not None
    assert ActionType is not None
    assert RandomEvent is not None
    assert DailyEvent is not None
    assert Rule is not None
    assert Action is not None
    assert AutonomyPlanner is not None
    assert Relationship is not None
    assert SimEvent is not None
    assert Economy is not None
    assert World is not None
    assert Simulation is not None

def test_person_basic():
    p = Person(name='Test', age=25, gender='F')
    assert p.name == 'Test'
    assert p.age == 25
    assert p.gender == 'F'

if __name__ == '__main__':
    test_package_imports()
    test_person_basic()
    print('All minimal tests passed!')
