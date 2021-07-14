# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

import pennylane as qml


class TestTracker:
    def test_tracker_initialization(self, device):
        """Tests a tracker instance is assigned at initialization."""

        dev = device(1)

        if not dev.capabilities().get("supports_tracker", False):
            pytest.skip("Device does not support a tracker")

        dev = qml.device("default.qubit.autograd", wires=1)

        assert isinstance(dev.tracker, qml.device_tracker.DefaultTracker)

    def test_tracker_updated_in_execution_mode(self, device, mocker):
        """Tests that device update and records during tracking mode"""

        dev = device(1)

        if not dev.capabilities().get("supports_tracker", False):
            pytest.skip("Device does not support a tracker")

        @qml.qnode(dev, diff_method="parameter-shift")
        def circ():
            return qml.expval(qml.PauliX(wires=[0]))

        spy_update = mocker.spy(dev.tracker, "update")
        spy_record = mocker.spy(dev.tracker, "record")

        dev.tracker.tracking = False
        circ()

        assert spy_update.call_count == 0
        assert spy_record.call_count == 0

        dev.tracker.tracking = True
        circ()

        assert spy_update.call_count == 1
        assert spy_record.call_count == 1
