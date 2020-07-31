# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import paddle
import os


class TestFleetMetaOptimizer(unittest.TestCase):
    def setUp(self):
        os.environ["PADDLE_TRAINER_ENDPOINTS"] = "127.0.0.1:36001"

    def test_pipeline_optimizer(self):
        import paddle.fleet as fleet
        import paddle.fluid.incubate.fleet.base.role_maker as role_maker
        role = role_maker.PaddleCloudRoleMaker(is_collective=True)
        fleet.init(role)
        with paddle.fluid.device_guard("cpu"):
            input_x = paddle.fluid.layers.data(
                name="x", shape=[32], dtype='float32')
            input_y = paddle.fluid.layers.data(
                name="y", shape=[1], dtype='int64')
            data_loader = paddle.fluid.io.DataLoader.from_generator(
                feed_list=[input_x, input_y],
                capacity=64,
                use_double_buffer=True,
                iterable=False)
            fc_1 = paddle.fluid.layers.fc(input=input_x, size=64, act='tanh')

        with paddle.fluid.device_guard("gpu:0"):
            fc_2 = paddle.fluid.layers.fc(input=fc_1, size=64, act='tanh')
            prediction = paddle.fluid.layers.fc(input=[fc_2],
                                                size=2,
                                                act='softmax')
            cost = paddle.fluid.layers.cross_entropy(
                input=prediction, label=input_y)
            avg_cost = paddle.fluid.layers.mean(x=cost)

        strategy = paddle.fleet.DistributedStrategy()
        strategy.pipeline = True
        strategy.pipeline_configs = {'micro_batch': 2}

        optimizer = paddle.optimizer.SGD(learning_rate=0.01)
        optimizer = fleet.distributed_optimizer(optimizer, strategy=strategy)
        optimizer.minimize(avg_cost)


if __name__ == "__main__":
    unittest.main()