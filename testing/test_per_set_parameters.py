"""
Test suite for per-set parameter isolation feature

Tests that each motor set can have independent parameters
and that editing one set doesn't affect other sets.

Author: Per-Set Parameter Feature Tests
Date: 2025-11-14
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Motor import Motor


class MockModel:
    """Mock Model class to avoid hardware dependencies"""
    IP_ADDRESS = '192.168.1.1'
    PROCESSOR_SLOT = 1
    CONNECTED = False
    live_motors = {}
    live_motors_sets = []
    motdict = {}


class TestPerSetParameterIsolation:
    """Test suite for per-set parameter isolation"""

    def test_different_sets_have_independent_parameters(self):
        """Test that different sets can have different parameter values"""
        model = MockModel()

        # Create Set 1: Motors 0, 1, 2 with Speed=500
        motor0 = Motor(0, CONNECTED=False)
        motor1 = Motor(1, CONNECTED=False)
        motor2 = Motor(2, CONNECTED=False)

        for motor in [motor0, motor1, motor2]:
            motor.write_params['Speed 1'] = 500
            motor.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        set1 = {0: motor0, 1: motor1, 2: motor2}

        # Create Set 2: Motors 3, 4, 5 with Speed=750
        motor3 = Motor(3, CONNECTED=False)
        motor4 = Motor(4, CONNECTED=False)
        motor5 = Motor(5, CONNECTED=False)

        for motor in [motor3, motor4, motor5]:
            motor.write_params['Speed 1'] = 750
            motor.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        set2 = {3: motor3, 4: motor4, 5: motor5}

        model.live_motors_sets = [set1, set2]

        # Verify Set 1 has Speed=500
        for motor in set1.values():
            assert motor.current_params['Speed 1'] == 500, \
                f"Set 1 motor should have Speed=500, got {motor.current_params['Speed 1']}"

        # Verify Set 2 has Speed=750
        for motor in set2.values():
            assert motor.current_params['Speed 1'] == 750, \
                f"Set 2 motor should have Speed=750, got {motor.current_params['Speed 1']}"

    def test_editing_one_set_does_not_affect_other_sets(self):
        """Test that parameter changes to one set don't affect other sets"""
        model = MockModel()

        # Create two sets with initial Speed=500
        set1_motors = [Motor(i, CONNECTED=False) for i in range(3)]
        set2_motors = [Motor(i + 3, CONNECTED=False) for i in range(3)]

        for motor in set1_motors + set2_motors:
            motor.write_params['Speed 1'] = 500
            motor.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        set1 = {i: set1_motors[i] for i in range(3)}
        set2 = {i + 3: set2_motors[i] for i in range(3)}
        model.live_motors_sets = [set1, set2]

        # Simulate editing Set 1 only (change Speed to 600)
        # This mimics what DefineMotors.update_motor_write_params does
        # when currently_editing_set_index = 0
        for motor in model.live_motors_sets[0].values():
            motor.write_params['Speed 1'] = 600
            motor.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        # Verify Set 1 changed to 600
        for motor in set1.values():
            assert motor.current_params['Speed 1'] == 600, \
                "Set 1 should be updated to 600"

        # Verify Set 2 still has 500 (unchanged)
        for motor in set2.values():
            assert motor.current_params['Speed 1'] == 500, \
                f"Set 2 should remain at 500, but got {motor.current_params['Speed 1']}"

    def test_multiple_parameters_independent_across_sets(self):
        """Test that multiple different parameters can vary independently across sets"""
        model = MockModel()

        # Create Set 1 with specific parameters
        motor0 = Motor(0, CONNECTED=False)
        motor0.write_params['Speed 1'] = 500
        motor0.write_params['Accel 1'] = 10000
        motor0.write_params['Position 2'] = 300
        motor0.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        # Create Set 2 with different parameters
        motor1 = Motor(1, CONNECTED=False)
        motor1.write_params['Speed 1'] = 700
        motor1.write_params['Accel 1'] = 15000
        motor1.write_params['Position 2'] = 350
        motor1.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)

        model.live_motors_sets = [{0: motor0}, {1: motor1}]

        # Verify Set 1 parameters
        assert motor0.current_params['Speed 1'] == 500
        assert motor0.current_params['Accel 1'] == 10000
        assert motor0.current_params['Position 2'] == 300

        # Verify Set 2 parameters
        assert motor1.current_params['Speed 1'] == 700
        assert motor1.current_params['Accel 1'] == 15000
        assert motor1.current_params['Position 2'] == 350

    def test_new_motors_dont_overwrite_confirmed_sets(self):
        """Test that adding new motors with parameters doesn't affect existing sets"""
        model = MockModel()

        # Create and confirm Set 1
        motor0 = Motor(0, CONNECTED=False)
        motor0.write_params['Speed 1'] = 500
        motor0.write_to_motor(model.IP_ADDRESS, model.PROCESSOR_SLOT)
        model.live_motors_sets = [{0: motor0}]

        # Now create new motors (not yet confirmed) with different parameters
        motor1 = Motor(1, CONNECTED=False)
        motor1.write_params['Speed 1'] = 800
        model.live_motors = {1: motor1}

        # Simulate what happens when updating new motor parameters
        # (should NOT affect confirmed Set 1)
        for motor in model.live_motors.values():
            motor.write_params['Speed 1'] = 800

        # Verify Set 1 is unchanged
        assert motor0.current_params['Speed 1'] == 500, \
            "Confirmed set should not be affected by new motor parameters"

        # Verify new motor has its own parameters
        assert motor1.write_params['Speed 1'] == 800, \
            "New motor should have its own parameters"


class TestSetSelection:
    """Test suite for set selection UI logic"""

    def test_selecting_set_loads_correct_parameters(self):
        """Test that selecting a set populates UI with that set's parameters"""
        model = MockModel()

        # Create two sets with different parameters
        motor0 = Motor(0, CONNECTED=False)
        motor0.write_params['Speed 1'] = 500
        motor0.write_params['Position 2'] = 300

        motor1 = Motor(1, CONNECTED=False)
        motor1.write_params['Speed 1'] = 750
        motor1.write_params['Position 2'] = 350

        model.live_motors_sets = [{0: motor0}, {1: motor1}]

        # Simulate selecting Set 1 (index 0)
        selected_set_index = 0
        selected_motors = list(model.live_motors_sets[selected_set_index].values())

        # Verify we got the right motor
        assert len(selected_motors) == 1
        assert selected_motors[0].write_params['Speed 1'] == 500
        assert selected_motors[0].write_params['Position 2'] == 300

        # Simulate selecting Set 2 (index 1)
        selected_set_index = 1
        selected_motors = list(model.live_motors_sets[selected_set_index].values())

        # Verify we got the right motor
        assert len(selected_motors) == 1
        assert selected_motors[0].write_params['Speed 1'] == 750
        assert selected_motors[0].write_params['Position 2'] == 350


if __name__ == "__main__":
    # Allow running this file directly
    pytest.main([__file__, "-v"])
