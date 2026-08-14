import unittest
from datetime import datetime, timedelta

from photobooth.services.kiosk_credit import apply_bill, partial_credit_expired


class KioskCreditTest(unittest.TestCase):
    def test_credit_sequences(self):
        cases = [([50, 50, 50, 50], 200, 0), ([100, 100], 200, 0), ([200], 200, 0), ([50, 100, 50], 200, 0), ([100, 200], 300, 100)]
        for sequence, credit, overpayment in cases:
            bills: list[int] = []
            for denomination in sequence:
                bills, current, excess, paid = apply_bill(bills, denomination, 200, [50, 100, 200])
            self.assertEqual((current, excess, paid), (credit, overpayment, True))

    def test_rejects_noise_or_unconfigured_bill(self):
        with self.assertRaises(ValueError):
            apply_bill([], 20, 200, [50, 100, 200])

    def test_partial_credit_deadline(self):
        now = datetime.now()
        self.assertFalse(partial_credit_expired(now + timedelta(seconds=1), now))
        self.assertTrue(partial_credit_expired(now, now))
