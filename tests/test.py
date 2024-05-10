import unittest
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
from xian_py.wallet import Wallet
import datetime

class TestCurrencyContract(unittest.TestCase):
    def setUp(self):
        # Called before every test, bootstraps the environment.
        self.client = ContractingClient()
        self.client.flush()

        with open("token_xst002.py") as f:
            code = f.read()
            self.client.submit(code, name="currency")

        self.currency = self.client.get_contract("currency")

    def tearDown(self):
        # Called after every test, ensures each test starts with a clean slate and is isolated from others
        self.client.flush()

    def test_initial_balance(self):
        # Check initial balance set by constructor
        sys_balance = self.currency.balances["sys"]
        self.assertEqual(sys_balance, 1_000_000)

    def test_transfer(self):
        # Setup
        self.currency.transfer(amount=100, to="bob", signer="sys")
        self.assertEqual(self.currency.balances["bob"], 100)
        self.assertEqual(self.currency.balances["sys"], 999_900)

    def test_change_metadata(self):
        # Only the operator should be able to change metadata
        with self.assertRaises(Exception):
            self.currency.change_metadata(
                key="token_name", value="NEW TOKEN", signer="bob"
            )
        # Operator changes metadata
        self.currency.change_metadata(key="token_name", value="NEW TOKEN", signer="sys")
        new_name = self.currency.metadata["token_name"]
        self.assertEqual(new_name, "NEW TOKEN")

    def test_approve_and_allowance(self):
        # Test approve
        self.currency.approve(amount=500, to="eve", signer="sys")
        # Test allowance
        allowance = self.currency.balances["sys", "eve"]
        self.assertEqual(allowance, 500)

    def test_transfer_from_without_approval(self):
        # Attempt to transfer without approval should fail
        with self.assertRaises(Exception):
            self.currency.transfer_from(
                amount=100, to="bob", main_account="sys", signer="bob"
            )

    def test_transfer_from_with_approval(self):
        # Setup - approve first
        self.currency.approve(amount=200, to="bob", signer="sys")
        # Now transfer
        self.currency.transfer_from(
            amount=100, to="bob", main_account="sys", signer="bob"
        )
        self.assertEqual(self.currency.balances["bob"], 100)
        self.assertEqual(self.currency.balances["sys"], 999_900)
        remaining_allowance = self.currency.balances["sys", "bob"]
        self.assertEqual(remaining_allowance, 100)


    # XST002 / Permit Tests


    # Helper Functions

    def fund_wallet(self, funder, spender, amount):
        self.currency.transfer(amount=100, to=spender, signer=funder)


    def construct_permit_msg(self, owner: str, spender: str, value: float, deadline: dict):
        return f"{owner}:{spender}:{value}:{deadline}:currency"


    def create_deadline(self, minutes=1):
        d = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        return Datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute)
    

    # Permit Tests

    def test_permit_valid(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg)
        # WHEN
        response = self.currency.permit(owner=public_key, spender=spender, value=value, deadline=deadline, signature=signature)
        # THEN
        self.assertIn("Permit granted", response)


    def test_permit_expired(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline(minutes=-1)  # Past deadline
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg)
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=deadline, signature=signature)
        # THEN
        self.assertIn('Permit has expired', str(context.exception))


    def test_permit_invalid_signature(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg + "tampered")
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=deadline, signature=signature)
        # THEN
        self.assertIn('Invalid signature', str(context.exception))


    def test_permit_double_spending(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg)
        self.currency.permit(owner=public_key, spender=spender, value=value, deadline=deadline, signature=signature)
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=deadline, signature=signature)
        # THEN
        self.assertIn('Permit can only be used once', str(context.exception))


if __name__ == "__main__":
    unittest.main()
