import json
from django.test import TestCase, Client

from rest_framework import status

from pprint import pprint
import datetime

from api import fake_api_calls

# Credit Trade Statuses
STATUS_DRAFT = 1
STATUS_PROPOSED = 2
STATUS_ACCEPTED = 3
STATUS_APPROVED = 6
STATUS_COMPLETED = 7
STATUS_CANCELLED = 8


class TestCreditTradeAPI(TestCase):
    fixtures = ['credit_trade_statuses.json', 'credit_trade_types.json',
                'fuel_supplier_actions_types.json',
                'fuel_supplier_statuses.json',
                'fuel_suppliers.json', 'fuel_supplier_balances.json',
                'users.json']

    def setUp(self):

        # Initialize Foreign keys
        # self.ct_status_id = fake_api_calls?.create_credit_trade_status()
        self.ct_type_id = fake_api_calls.create_credit_trade_type()
        self.fs1_id, self.fs1_status_id, self.fs1_action_type_id = (
            fake_api_calls.create_fuel_supplier())
        self.user_id = fake_api_calls.create_user(self.fs1_id)

        self.credit_trade = fake_api_calls.create_credit_trade(
            initiatorFK=self.fs1_id,
            respondentFK=self.fs1_id,
            creditTradeTypeFK=self.ct_type_id,
            creditTradeStatusFK=STATUS_DRAFT,
            user_id=self.user_id,
        )
        # self.credit_trade_id = fake_api_calls.create_credit_trade(
        #     self.fs1_id,
        #     self.user_id
        # )[0]

        self.client = Client(HTTP_SM_USER_ID=self.user_id)
        self.test_url = "/api/credit_trades"

        self.test_data_fail = [{
            'data': {'numberOfCredits': 1},
            'response': {
                "creditTradeStatusFK": ["This field is required."],
                "respondentFK": ["This field is required."],
                "creditTradeTypeFK": ["This field is required."]
            }
        }, {
            'data': {'numberOfCredits': 1,
                     'creditTradeStatusFK': STATUS_DRAFT},
            'response': {
                "respondentFK": ["This field is required."],
                "creditTradeTypeFK": ["This field is required."],
            }
        }, {
            'data': {'numberOfCredits': 1,
                     'creditTradeStatusFK': STATUS_DRAFT,
                     'respondentFK': self.fs1_id},
            'response': {
                "creditTradeTypeFK": ["This field is required."]
            }
        }]

        self.test_data_success = [{
            'data': {'numberOfCredits': 1,
                     'creditTradeStatusFK': STATUS_DRAFT,
                     'respondentFK': self.fs1_id,
                     'creditTradeTypeFK': self.ct_type_id},
        }]

    def test_create_fail(self):
        credit_trades = self.test_data_fail

        for tests in credit_trades:
            response = self.client.post(
                self.test_url,
                content_type='application/json',
                data=json.dumps(tests['data']))

            self.assertJSONEqual(
                response.content.decode("utf-8"),
                tests['response'])
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_success(self):
        credit_trades = self.test_data_success

        for tests in credit_trades:
            response = self.client.post(
                self.test_url,
                content_type='application/json',
                data=json.dumps(tests['data']))

            assert status.HTTP_201_CREATED == response.status_code

    def test_create_and_create_trade_history(self):
        credit_trades = self.test_data_success

        for tests in credit_trades:
            response = self.client.post(
                self.test_url,
                content_type='application/json',
                data=json.dumps(tests['data']))

            ct_id = response.data['id']
            response = self.client.get(
                "{}/{}/history".format(self.test_url, ct_id),
                content_type='application/json')

            assert status.HTTP_200_OK == response.status_code

    def test_update(self, **kwargs):
        credit_trade_id = kwargs.get("credit_trade_id", self.credit_trade['id'])
        num_of_credits = kwargs.get("num_of_credits", 4)
        credit_trade_status = kwargs.get("credit_trade_status", STATUS_DRAFT)
        fair_market_value = kwargs.get("fair_market_value", 1)
        #
        # if not credit_trade_id:
        #     credit_trade_id = self.credit_trade_id

        data = {
            'numberOfCredits': num_of_credits,
            'creditTradeStatusFK': credit_trade_status,
            'respondentFK': self.fs1_id,
            'creditTradeTypeFK': self.ct_type_id,
            'fairMarketValuePerCredit': fair_market_value
        }

        response = self.client.put(
            "{}/{}".format(self.test_url, credit_trade_id),
            content_type='application/json',
            data=json.dumps(data))

        assert status.HTTP_200_OK == response.status_code

    def test_update_create_trade_history(self):
        self.test_update(num_of_credits=1)
        self.test_update(num_of_credits=2)

        response = self.client.get(
            "{}/{}/history".format(self.test_url, self.credit_trade['id']),
            content_type='application/json')

        response_data = json.loads(response.content.decode("utf-8"))

        self.assertEqual(3, len(response_data))

        assert status.HTTP_200_OK == response.status_code

    def test_is_internal_history_false(self):
        data = [STATUS_PROPOSED, STATUS_ACCEPTED]
        for ct_status in data:
            self.test_update(credit_trade_status=ct_status)
            response = self.client.get(
                "{}/{}/history".format(self.test_url, self.credit_trade['id']),
                content_type='application/json')
            response_data = json.loads(response.content.decode("utf-8"))
            self.assertFalse(response_data[0]['isInternalHistoryRecord'])

    def test_is_internal_history_draft(self):
        # Initially created credit trade is "Draft"
        response = self.client.get(
            "{}/{}/history".format(self.test_url, self.credit_trade['id']),
            content_type='application/json')

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertTrue(response_data[0]['isInternalHistoryRecord'])

    def test_is_internal_history_draft_then_cancelled(self):
        # Initially created credit trade is "Draft"

        # Update the status to "Cancelled"
        self.test_update(credit_trade_status=STATUS_CANCELLED)
        response = self.client.get(
            "{}/{}/history".format(self.test_url, self.credit_trade['id']),
            content_type='application/json')

        response_data = json.loads(response.content.decode("utf-8"))
        self.assertTrue(response_data[0]['isInternalHistoryRecord'])

    def test_nested_credit_trade(self):
        response = self.client.get(
            "{}/{}".format(self.test_url, self.credit_trade['id']),
            content_type='application/json')
        response_data = json.loads(response.content.decode("utf-8"))

        credit_trade_status = {
            "id": STATUS_DRAFT,
            "status": "Draft"
        }
        self.assertTrue(
            set(credit_trade_status).issubset(
                response_data['creditTradeStatusFK']))

    def test_nested_credit_trade_history(self):
        response = self.client.get(
            "{}/{}/history".format(self.test_url, self.credit_trade['id']),
            content_type='application/json')
        response_data = json.loads(response.content.decode("utf-8"))[0]

        credit_trade_status = {
            "id": STATUS_DRAFT,
            "status": "Draft"
        }
        self.assertTrue(
            set(credit_trade_status).issubset(
                response_data['creditTradeStatusFK']))

    # def test_approved_buy(self, **kwargs):
    #     # get fuel supplier balance for fs 1
    #     initiator_bal = fake_api_calls.get_fuel_supplier_balances(id=1)
    #     respondent_bal = fake_api_calls.get_fuel_supplier_balances(id=2)
    #
    #     # balance = initiator_balance['validatedCredits']
    #     print("initiator & respondent")
    #     print(initiator_bal['validatedCredits'])
    #     print(respondent_bal['validatedCredits'])
    #     # get fuel supplier balance for fs 2
    #
    #     num_of_credits = 50
    #
    #     credit_trade = fake_api_calls.create_credit_trade(
    #         user_id=self.user_id,
    #         creditTradeStatusFK=STATUS_PROPOSED,
    #         fairMarketValuePerCredit=1000,
    #         initiatorFK=1,
    #         respondentFK=2,
    #         numberOfCredits=num_of_credits
    #     )
    #
    #     pprint(credit_trade)
    #
    #     response = self.client.put(
    #         "{}/{}/approve".format(self.test_url, credit_trade['id']),
    #         content_type='application/json')
    #
    #     response_data = json.loads(response.content.decode("utf-8"))
    #     print(response)
    #     print(response_data)
    #     assert status.HTTP_200_OK == response.status_code
    #
    #     # TODO: Make sure two credit histories are created
    #
    #     pprint(response_data)
    #
    #     print("After approval")
    #     initiator_bal_after = fake_api_calls.get_fuel_supplier_balances(id=1)
    #     respondent_bal_after = fake_api_calls.get_fuel_supplier_balances(id=2)
    #     print(initiator_bal['validatedCredits'])
    #     print(respondent_bal['validatedCredits'])
    #
    #     init_final_bal = initiator_bal['validatedCredits'] + num_of_credits
    #     resp_final_bal = respondent_bal['validatedCredits'] - num_of_credits
    #
    #     ct_completed = self.client.get(
    #         "{}/{}".format(self.test_url, credit_trade['id']),
    #         content_type='application/json')
    #
    #     completed_response = json.loads(
    #         ct_completed.content.decode("utf-8"))
    #
    #     # response_data should have status == completed
    #     print(completed_response)
    #     today = datetime.datetime.today().strftime('%Y-%m-%d')
    #
    #     # Status of Credit Trade should be 'completed'
    #     self.assertEqual(completed_response['creditTradeStatusFK']['id'],
    #                      STATUS_COMPLETED)
    #
    #     # Effective date should be today
    #     self.assertEqual(initiator_bal_after['tradeEffectiveDate'], today)
    #     self.assertEqual(respondent_bal_after['tradeEffectiveDate'], today)
    #
    #     # Credits should be subtracted/added
    #     self.assertEqual(init_final_bal,
    #                      initiator_bal_after['validatedCredits'])
    #     self.assertEqual(resp_final_bal,
    #                      respondent_bal_after['validatedCredits'])

    def test_approved_sell(self, **kwargs):
        pass

    def test_approved_credit_validation(self, **kwargs):
        pass

    def test_approved_retirement(self, **kwargs):
        pass

    def test_approved_part_3_award(self, **kwargs):
        pass

        #
        # def test_director_approved(self):
        #     """Execute and complete a trade when an "On Director's Approval" Trade
        #     is approved"""
        #     tests = [{
        #         'data': {
        #             'credit_trade_status': STATUS_APPROVED,
        #             'number_of_credits': 2
        #         },
        #         'response': {
        #             ''
        #         }
        #     }, {
        #         'data': {
        #             'credit_trade_status': STATUS_DRAFT,
        #             'number_of_credits': 10,
        #             'fair_market_value': "Value"
        #         },
        #         'response': {
        #             ''
        #         }
        #     }]
        #     for test in tests:
        #         self.test_update(**test['data'])

        # self.test_update(credit_trade_status=STATUS_APPROVED)
        """Test that no other fields are changed, except for notes, 
        effective date & status"""


        # don't care where it comes from (ignore previous status)
        # status is "Approved"
        # no other fields can change, unless from getting a new note

        # effective date is None or past
        # Set effective date on director's approval

        # fuel supplier receives credits
        # fuel supplier loses credits
        # FuelSupplierBalance record created, effective data = transaction create time
        #   end data is None


        # pass