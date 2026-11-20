#!/usr/bin/env python3
import random
import unittest

from panda import Panda, pack_can_buffer, unpack_can_buffer, DLC_TO_LEN
from unittest.mock import Mock

class PandaTestPackUnpack(unittest.TestCase):
  def test_lateral_heartbeat_is_independent_of_cruise(self):
    panda = Panda.__new__(Panda)
    panda._handle = Mock()
    for engaged in (False, True):
      for requested in (False, True):
        for enabled in (False, True):
          for fault in (False, True):
            panda.send_heartbeat(engaged, requested, enabled, fault)
            panda._handle.controlWrite.assert_called_with(Panda.REQUEST_OUT, 0xf3, engaged,
                                                         int(requested) | (int(enabled) << 1) | (int(fault) << 2), b'')
    panda.send_heartbeat(False)
    panda._handle.controlWrite.assert_called_with(Panda.REQUEST_OUT, 0xf3, False, 0, b'')
    # Avoid the device-close destructor on an intentionally unconnected instance.
    panda._handle = None

  def test_lateral_health_flags_do_not_imply_cruise(self):
    panda = Panda.__new__(Panda)
    panda._handle = Mock()
    panda.health_version = Panda.HEALTH_PACKET_VERSION
    for flags in (0, Panda.HEALTH_FLAG_LATERAL_ALLOWED, Panda.HEALTH_FLAG_LATERAL_SUPPORTED,
                  Panda.HEALTH_FLAG_LATERAL_SUSPENDED,
                  Panda.HEALTH_FLAG_LATERAL_ALLOWED | Panda.HEALTH_FLAG_LATERAL_SUPPORTED):
      fields = list(Panda.HEALTH_STRUCT.unpack(bytes(Panda.HEALTH_STRUCT.size)))
      fields[8] = flags
      panda._handle.controlRead.return_value = Panda.HEALTH_STRUCT.pack(*fields)
      health = panda.health()
      self.assertFalse(health['controls_allowed'])
      self.assertEqual(health['lateral_allowed'], bool(flags & Panda.HEALTH_FLAG_LATERAL_ALLOWED))
      self.assertEqual(health['lateral_supported'], bool(flags & Panda.HEALTH_FLAG_LATERAL_SUPPORTED))
      self.assertEqual(health['lateral_suspended'], bool(flags & Panda.HEALTH_FLAG_LATERAL_SUSPENDED))
    panda._handle = None

  def test_panda_lib_pack_unpack(self):
    overflow_buf = b''

    to_pack = []
    for _ in range(10000):
      address = random.randint(1, (1 << 29) - 1)
      data = bytes([random.getrandbits(8) for _ in range(DLC_TO_LEN[random.randrange(0, len(DLC_TO_LEN))])])
      to_pack.append((address, data, 0))

    packed = pack_can_buffer(to_pack)
    unpacked = []
    for dat in packed:
      msgs, overflow_buf = unpack_can_buffer(overflow_buf + dat)
      unpacked.extend(msgs)

    self.assertEqual(unpacked, to_pack)

if __name__ == "__main__":
  unittest.main()
