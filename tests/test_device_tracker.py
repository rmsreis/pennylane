# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the DeviceTracker and constructor
"""
import pytest

import pennylane as qml
from pennylane import track
from pennylane.device_tracker import DefaultTracker


class TestTrackerCoreBehaviour:
    def test_default_initialization(self):
        """Tests default initializalition"""

        tracker = DefaultTracker()

        assert tracker.persistent == False
        assert tracker.callback is None

        assert tracker.history == dict()
        assert tracker.totals == dict()
        assert tracker.latest == dict()

        assert tracker.tracking == False

    def test_device_assignment(self):
        """Assert gets assigned to device"""
        dev = qml.device("default.qubit", wires=2)

        tracker = DefaultTracker(dev=dev)

        assert id(dev.tracker) == id(tracker)

    def test_incompatible_device_assignment(self):
        """Assert exception raised when `supports_tracker` not True"""

        class TempDevice:
            short_name = "temp"

            def capabilities(self):
                return dict()

        temp = TempDevice()

        with pytest.raises(Exception, match=r"Device 'temp' does not support device tracking"):
            DefaultTracker(dev=temp)

    def test_reset(self):
        """Assert reset empties totals and history"""

        tracker = DefaultTracker()

        tracker.totals = {"a": 1}
        tracker.history = {"a": [1]}
        tracker.latest = {"a": 1}

        tracker.reset()

        assert tracker.totals == dict()
        assert tracker.history == dict()
        assert tracker.latest == dict()

    def test_enter_and_exit(self):
        """Assert entering and exit work as expected"""

        tracker = DefaultTracker()
        tracker.totals = {"a": 1}
        tracker.history = {"a": [1]}
        tracker.latest = {"a": 1}

        returned = tracker.__enter__()

        assert id(tracker) == id(returned)
        assert tracker.tracking == True

        assert tracker.totals == dict()
        assert tracker.history == dict()
        assert tracker.latest == dict()

        tracker.__exit__(1, 1, 1)

        assert tracker.tracking == False

    def test_context(self):
        """Assert works with runtime context"""

        with DefaultTracker() as tracker:
            assert isinstance(tracker, DefaultTracker)
            assert tracker.tracking == True

        assert tracker.tracking == False

    def test_update(self):
        """Checks update stores to history and totals"""

        tracker = DefaultTracker()

        tracker.update(a=1, b="b", c=None)
        tracker.update(a=2, c=1)

        assert tracker.history == {"a": [1, 2], "b": ["b"], "c": [None, 1]}

        assert tracker.totals == {"a": 3, "c": 1}

        assert tracker.latest == {"a": 2, "c": 1}

    def test_record_callback(self, mocker):
        class callback_wrapper:
            @staticmethod
            def callback(totals=dict(), history=dict(), latest=dict()):
                pass

        wrapper = callback_wrapper()
        spy = mocker.spy(wrapper, "callback")

        tracker = DefaultTracker(callback=wrapper.callback)

        tracker.totals = {"a": 1, "b": 2}
        tracker.history = {"a": [1], "b": [1, 1]}
        tracker.latest = {"a": 1, "b": 1}

        tracker.record()

        _, kwargs_called = spy.call_args_list[-1]

        assert kwargs_called["totals"] == tracker.totals
        assert kwargs_called["history"] == tracker.history
        assert kwargs_called["latest"] == tracker.latest


class TestDefaultTrackerIntegration:
    def test_single_execution_default(self, mocker):
        """Test correct behavior with single circuit execution"""

        class callback_wrapper:
            @staticmethod
            def callback(totals=dict(), history=dict(), latest=dict()):
                pass

        wrapper = callback_wrapper()
        spy = mocker.spy(wrapper, "callback")

        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def circuit():
            return qml.expval(qml.PauliZ(0))

        with DefaultTracker(circuit.device, callback=wrapper.callback) as tracker:
            circuit()

        assert tracker.totals == {"executions": 1}
        assert tracker.history == {"executions": [1], "shots": [None]}
        assert tracker.latest == {"executions": 1, "shots": None}

        _, kwargs_called = spy.call_args_list[-1]

        assert kwargs_called["totals"] == {"executions": 1}
        assert kwargs_called["history"] == {"executions": [1], "shots": [None]}
        assert kwargs_called["latest"] == {"executions": 1, "shots": None}

    def test_shots_execution_default(self, mocker):
        """Test correct tracks shots as well."""

        class callback_wrapper:
            @staticmethod
            def callback(totals=dict(), history=dict(), latest=dict()):
                pass

        wrapper = callback_wrapper()
        spy = mocker.spy(wrapper, "callback")

        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def circuit():
            return qml.expval(qml.PauliZ(0))

        with DefaultTracker(circuit.device, callback=wrapper.callback) as tracker:
            circuit(shots=10)
            circuit(shots=20)

        assert tracker.totals == {"executions": 2, "shots": 30}
        assert tracker.history == {"executions": [1, 1], "shots": [10, 20]}
        assert tracker.latest == {"executions": 1, "shots": 20}

        assert spy.call_count == 2

        _, kwargs_called = spy.call_args_list[-1]
        assert kwargs_called["totals"] == {"executions": 2, "shots": 30}
        assert kwargs_called["history"] == {"executions": [1, 1], "shots": [10, 20]}
        assert kwargs_called["latest"] == {"executions": 1, "shots": 20}
