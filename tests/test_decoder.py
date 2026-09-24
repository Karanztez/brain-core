import base64
import gzip
import unittest

from brain_core.tools.builtins.decoder import analyze_ctf_data, decode_inspect_data


class DecoderTests(unittest.TestCase):
    def test_hex_is_backward_compatible(self):
        result = decode_inspect_data("464c41477b6865787d")
        self.assertTrue(result["success"])
        self.assertEqual(result["decoded"], "FLAG{hex}")
        self.assertEqual(result["path"], ["hex"])

    def test_recursive_base64_hex(self):
        value = base64.b64encode("FLAG{layered}".encode().hex().encode()).decode()
        report = analyze_ctf_data(value)
        self.assertIn("FLAG{layered}", report["flags"])
        item = next(item for item in report["candidates"] if "FLAG{layered}" in item["flags"])
        self.assertEqual(item["path"], ["base64", "hex"])

    def test_gzip_after_base64(self):
        value = base64.b64encode(gzip.compress(b"CTF{compressed}")).decode()
        report = analyze_ctf_data(value)
        self.assertIn("CTF{compressed}", report["flags"])
        self.assertTrue(any(item["path"] == ["base64", "gzip"] for item in report["candidates"]))

    def test_binary_ascii(self):
        bits = " ".join(f"{value:08b}" for value in b"FLAG{bin}")
        self.assertEqual(decode_inspect_data(bits)["decoded"], "FLAG{bin}")

    def test_single_byte_xor(self):
        encrypted = bytes(value ^ 0x23 for value in b"FLAG{xor}")
        report = analyze_ctf_data(encrypted.hex())
        self.assertIn("FLAG{xor}", report["flags"])

    def test_input_limit(self):
        report = analyze_ctf_data("A" * (64 * 1024 + 1))
        self.assertFalse(report["success"])
        self.assertIn("safety limit", report["error"])

    def test_never_opens_url_or_executes(self):
        report = analyze_ctf_data(base64.b64encode(b"https://example.invalid/payload").decode())
        self.assertTrue(report["success"])
        self.assertIn("nothing was executed or opened", report["warnings"][0])


if __name__ == "__main__":
    unittest.main()
