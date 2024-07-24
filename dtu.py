# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
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

"""A DTU sample"""


import ql_fs
import checkNet
import utime
from usr.serial import Serial
from usr.logging import getLogger
from usr.threading import Thread
from aLiYun import aLiYun
from queue import Queue

logger = getLogger(__name__)
productKey = "igiyOVruVsh"  # 产品标识(参照阿里 IoT 平台应用开发指导)
productSecret = None  # 产品密钥（使用一机一密认证时此参数传入None，参照阿里 IoT 平台应用开发指导)
DeviceName = "s3FfKHJ2hxn9jOc0tR90"  # 设备名称(参照阿里 IoT 平台应用开发指导)
DeviceSecret = "c4f832cb993d89c02e126aab53d6c3fc"  # 设备密钥（使用一型一密认证此参数传入None，免预注册暂不支持，需先在 IoT 平台创建设备，参照阿里 IoT 平台应用开发指导)
clientID = "8848" # 自定义字符（不超过64）
topic = "/igiyOVruVsh/s3FfKHJ2hxn9jOc0tR90/user/000001"  # IoT 平台自定义或自拥有的Topic

class Configure(dict):
    """Configure for DTU

    actually it is a dict, but add `from_json` and `save` method.
    - `from_json`: read json file and update to self
    - `save`: save self to `path` json file
    """

    def __init__(self, path=None):
        super().__init__()
        self.path = path

    def __repr__(self):
        return 'Configure(path=\'{}\')'.format(self.path)

    def from_json(self, path):
        self.path = path
        if not ql_fs.path_exists(path):
            raise ValueError('\"{}\" not exists!'.format(path))
        self.update(ql_fs.read_json(path))

    def save(self):
        ql_fs.touch(self.path, self)


class DTU(object):
    """DTU Class with simple features:
        - tcp transparent transmission
        - serial read/write
    """

    def __init__(self, name):
        self.name = name
        self.config = Configure()
        self.serial = None
        self.cloud = None
        self.queue = Queue()
        

    def __str__(self):
        return 'DTU(name=\"{}\")'.format(self.name)

    def open_serial(self):
        try:
            self.serial = Serial(**self.config['UART'])
            self.serial.open()
        except Exception as e:
            logger.error('open serial failed: {}'.format(e))
        else:
            logger.info('open serial successfully.')

    def connect_cloud(self):
        try:
            self.cloud = aLiYun(productKey, productSecret, DeviceName, DeviceSecret) 
            self.cloud.setMqtt(clientID, clean_session=False, keepAlive=300)
            self.cloud.setCallback(self.callback)
            self.cloud.subscribe(topic)
            self.cloud.start()
        except Exception as e:
            logger.error('connect cloud failed: {}'.format(e))
        else:
            logger.info('conect cloud successfully.')
    
    def callback(self, topic, msg):
        self.queue.put((topic, msg))


    def recv(self):
        print('ok2!')
        return self.queue.get()

    def run(self):
        logger.info('{} run...'.format(self))
        self.open_serial()
        self.connect_cloud()
        self.start_uplink_transaction()
        self.start_downlink_transaction()

    def down_transaction_handler(self):
        while True:
            try:
                Topic,msg = self.recv()
                logger.info("Recv: Topic={},Msg={}".format(Topic.decode(), msg.decode()))
                self.serial.write(msg)
            except Exception as e:
                logger.error('down transfer error: {}'.format(e))

    def up_transaction_handler(self):
        while True:
            try:
                msg = self.serial.read(1024)
                if msg:
                    self.cloud.publish(topic,msg)
            except Exception as e:
                logger.error('up transfer error: {}'.format(e))
            else:
                logger.info("Send: Topic={},Msg={}".format(topic.decode(),msg.decode()))

    def start_uplink_transaction(self):
        logger.info('start up transaction worker thread {}.'.format(Thread.get_current_thread_ident()))
        Thread(target=self.up_transaction_handler).start()

    def start_downlink_transaction(self):
        logger.info('start down transaction worker thread {}.'.format(Thread.get_current_thread_ident()))
        Thread(target=self.down_transaction_handler).start()


if __name__ == '__main__':
    # initialize DTU Object
    dtu = DTU('Quectel')

    # read json configure from json file
    dtu.config.from_json('/usr/DTU_config.json')

    # poweron print once
    checknet = checkNet.CheckNetwork(
        dtu.config['PROJECT_NAME'],
        dtu.config['PROJECT_VERSION'],
    )
    checknet.poweron_print_once()

    # check network until ready
    while True:
        rv = checkNet.waitNetworkReady()
        if rv == (3, 1):
            print('network ready.')
            break
        else:
            print('network not ready, error code is {}.'.format(rv))

    # dtu application run forever
    dtu.run()