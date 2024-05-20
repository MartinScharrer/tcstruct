import unittest
import tcstruct
import array
import struct
import sys


class TestCstruct(unittest.TestCase):
    def test_littleendianstruct(self):
        class MyStruct(tcstruct.LittleEndianStruct):
            magicnumber: tcstruct.uint32_t
            version: tcstruct.Array[tcstruct.uint8_t[4]]
            value: tcstruct.uint16_t
            fvalue: tcstruct.float32_t
            dvalue: tcstruct.float64_t

        ti = MyStruct(0xDEADBEEF, (1, 2, 3, 4000), -2, 1.0, 2.0)
        self.assertEqual(ti.magicnumber, 0xDEADBEEF)
        self.assertEqual(ti.version[0], 1)
        self.assertEqual(ti.version[1], 2)
        self.assertEqual(ti.version[2], 3)
        self.assertEqual(ti.version[3], 4000 & 0xFF)
        self.assertEqual(ti.value, 0xFFFE)
        self.assertEqual(ti.fvalue, 1.0)
        self.assertEqual(ti.dvalue, 2.0)

        fb = array.array('f', (1.0,)).tobytes()
        db = array.array('d', (2.0,)).tobytes()
        if sys.byteorder != 'little':
            fb = bytes(reversed(fb))
            db = bytes(reversed(db))
        self.assertEqual(len(fb), 4)
        self.assertEqual(len(db), 8)
        expb = bytes.fromhex('EFBEADDE010203A0FEFF0000') + fb + db
        self.assertSequenceEqual(bytes(ti), expb)

    def test_littleendianstruct_packed(self):
        class MyStruct(tcstruct.LittleEndianStruct):
            _pack_ = 1
            magicnumber: tcstruct.uint32_t
            version: tcstruct.Array[tcstruct.uint8_t[4]]
            value: tcstruct.uint16_t
            fvalue: tcstruct.float32_t
            dvalue: tcstruct.float64_t

        ti = MyStruct(0xDEADBEEF, (1, 2, 3, 4000), -2, 1.0, 2.0)
        self.assertEqual(ti.magicnumber, 0xDEADBEEF)
        self.assertEqual(ti.version[0], 1)
        self.assertEqual(ti.version[1], 2)
        self.assertEqual(ti.version[2], 3)
        self.assertEqual(ti.version[3], 4000 & 0xFF)
        self.assertEqual(ti.value, 0xFFFE)
        self.assertEqual(ti.fvalue, 1.0)
        self.assertEqual(ti.dvalue, 2.0)

        fb = array.array('f', (1.0,)).tobytes()
        db = array.array('d', (2.0,)).tobytes()
        if sys.byteorder != 'little':
            fb = bytes(reversed(fb))
            db = bytes(reversed(db))
        self.assertEqual(len(fb), 4)
        self.assertEqual(len(db), 8)
        expb = bytes.fromhex('EFBEADDE010203A0FEFF') + fb + db
        self.assertSequenceEqual(bytes(ti), expb)

    def test_derivation(self):
        class MyBaseStruct(tcstruct.LittleEndianStruct):
            common1:  tcstruct.uint32_t
            common2:  tcstruct.uint32_t

        class MyStruct(MyBaseStruct):
            special1: tcstruct.uint32_t

        ti = MyStruct(common1=1, common2=2, special1=3)
        self.assertEqual(ti.common1, 1)
        self.assertEqual(ti.common2, 2)
        self.assertEqual(ti.special1, 3)

        ti2 = MyStruct(1, 2, 3)
        self.assertEqual(ti2.common1, 1)
        self.assertEqual(ti2.common2, 2)
        self.assertEqual(ti2.special1, 3)

    def test_bytes(self):
        class MyStruct(tcstruct.BigEndianStruct):
            magicnumber: tcstruct.uint32_t
            version: tcstruct.Array[tcstruct.uint8_t[4]]
            value: tcstruct.uint16_t
            fvalue: tcstruct.float32_t
            dvalue: tcstruct.float64_t

        fb = array.array('f', (1.0,)).tobytes()
        db = array.array('d', (2.0,)).tobytes()
        if sys.byteorder != MyStruct._byteorder:
            fb = bytes(reversed(fb))
            db = bytes(reversed(db))
        self.assertEqual(len(fb), 4)
        self.assertEqual(len(db), 8)
        expb = bytes.fromhex('DEADBEEF010203A0FFFE0000') + fb + db

        print(MyStruct.__mro__)
        print(MyStruct._swappedbytes_)
        ti = MyStruct.from_bytes(expb)
        self.assertEqual(ti.magicnumber, 0xDEADBEEF)
        self.assertEqual(ti.version[0], 1)
        self.assertEqual(ti.version[1], 2)
        self.assertEqual(ti.version[2], 3)
        self.assertEqual(ti.version[3], 4000 & 0xFF)
        self.assertEqual(ti.value, 0xFFFE)
        self.assertEqual(ti.fvalue, 1.0)
        self.assertEqual(ti.dvalue, 2.0)

        b = ti.to_bytes()
        self.assertSequenceEqual(ti.to_bytes(), expb)

    def test_endian(self):
        for ctype in (tcstruct.uint16_t, tcstruct.uint32_t, tcstruct.uint64_t, tcstruct.sint16_t, tcstruct.sint32_t, tcstruct.sint64_t, tcstruct.float32_t, tcstruct.float64_t):
            if ctype._bitwidth <= 8:
                continue
            with self.subTest(ctype=ctype):
                bytewidth = ctype._bitwidth // 8
                class MyBigEndianStruct(tcstruct.BigEndianStruct):
                    value: ctype

                class MyLittleEndianStruct(tcstruct.LittleEndianStruct):
                    value: ctype

                class MyStruct(tcstruct.Struct):
                    value: ctype

                if issubclass(ctype, int):
                    testvalue = 0x1122334455667788 & ((1 << ctype._bitwidth) - 1)
                    testseq_little = testvalue.to_bytes(bytewidth, byteorder='little')
                    testseq_big = testvalue.to_bytes(bytewidth, byteorder='big')
                    testseq_sys = testseq_little if sys.byteorder == 'little' else testseq_big
                    assertEqual = self.assertEqual
                else:
                    testvalue = -1.234
                    testseq_sys = struct.pack(ctype._char, testvalue)
                    testseq_little = struct.pack('<' + ctype._char, testvalue)
                    testseq_big = struct.pack('>' + ctype._char, testvalue)
                    assertEqual = self.assertAlmostEqual
                self.assertNotEqual(testseq_little, testseq_big)  # Verify suitability of testvalue

                self.assertSequenceEqual(MyBigEndianStruct.from_bytes(testseq_sys).to_bytes(), testseq_sys)
                self.assertSequenceEqual(MyLittleEndianStruct.from_bytes(testseq_sys).to_bytes(), testseq_sys)
                self.assertSequenceEqual(MyStruct.from_bytes(testseq_sys).to_bytes(), testseq_sys)

                assertEqual(MyBigEndianStruct.from_bytes(testseq_big).value, testvalue)
                assertEqual(MyLittleEndianStruct.from_bytes(testseq_little).value, testvalue)
                assertEqual(MyStruct.from_bytes(testseq_sys).value, testvalue)

                self.assertSequenceEqual(MyBigEndianStruct(testvalue).to_bytes(), testseq_big)
                self.assertSequenceEqual(MyLittleEndianStruct(testvalue).to_bytes(), testseq_little)
                self.assertSequenceEqual(MyStruct(testvalue).to_bytes(), testseq_sys)


if __name__ == '__main__':
    unittest.main()
