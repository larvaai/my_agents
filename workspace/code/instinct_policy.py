def should_act(urgency, control_ratio, leap_risk):
    # Rule 1: If leap_risk > 0.7 then return False
    if leap_risk > 0.7:
        return False
    
    # Rule 2: If urgency > 0.5 AND control_ratio >= 0.5 then return True
    if urgency > 0.5 and control_ratio >= 0.5:
        return True
    
    # Rule 3: Otherwise return False
    return False

if __name__ == "__main__":
    assert should_act(0.9, 0.2, 0.9) is False
    assert should_act(0.9, 0.8, 0.1) is True
    print("INSTINCT_POLICY_OK")