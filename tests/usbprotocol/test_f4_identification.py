import unittest
from unittest.mock import Mock

from panda import Panda, McuType
from panda.python.usb import PandaUsbHandle


class TestF4Identification(unittest.TestCase):
  def panda(self, response, bcd=None, bootstub=True):
    p = Panda.__new__(Panda)
    p.bootstub = bootstub
    p._handle_open = False
    p._handle = PandaUsbHandle(Mock(controlRead=Mock(return_value=response)), bcd)
    return p

  def test_application_and_current_bootstub(self):
    for bootstub in (False, True):
      p = self.panda(Panda.HW_TYPE_DOS, bootstub=bootstub)
      self.assertEqual(p.get_mcu_type(), McuType.F4)
      self.assertTrue(p.is_internal())
      self.assertEqual(p.get_mcu_type().config.app_fn, 'panda.bin.signed')

  def test_legacy_bootstubs(self):
    legacy = b'\xff\x00\xc1\x3e\xde\xad\xd0\x0d'
    for bcd in (None, 0x2300, 0x0600):
      self.assertEqual(self.panda(legacy, bcd).get_mcu_type(), McuType.F4)
    self.assertEqual(self.panda(legacy, 0x0900).get_mcu_type(), McuType.H7)
    with self.assertRaises(ValueError):
      self.panda(legacy, 0xFF00).get_mcu_type()
    with self.assertRaises(ValueError):
      self.panda(legacy, bootstub=False).get_mcu_type()

  def test_unknown_hardware_is_not_flashed_as_f4(self):
    for response in (b'', b'\xff', b'\x00', b'bad bootstub'):
      with self.assertRaises(ValueError):
        self.panda(response).get_mcu_type()


if __name__ == '__main__':
  unittest.main()
