import logging
import os
import requests
import time
import uuid
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client


http_client.HTTPConnection.debuglevel = 1

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
bank_base_uri = os.getenv('BANK_BASE_URI')

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def get_account_summary(token, group):
    headers = generate_headers(token)
    r = requests.get(bank_base_uri + "/accounts",
                     headers=headers)

    if r.status_code != 200:
        logger.error("Unable to get account summary, status={}, error={}".format(r.status_code, r.text))
        return None

    summary = r.json()
    logger.debug(summary)
    for a in summary['accountGroupSummary']:
        if a['accountGroup'] == group:
            return a


def retrieve_dest_src_acct(token):
    headers = generate_headers(token)
    r = requests.get(bank_base_uri + "/transfer",
                     headers=headers)

    if r.status_code != 200:
        logger.error("Unable to get account summary, status={}, error={}".format(r.status_code, r.text))
        return None

    resp = r.json()
    logger.debug(resp)
    return resp


def create_transfer(token, source_account_id, amount, destination_account_id):
    request = {
        "sourceAccountId": source_account_id,
        "transactionAmount": amount,
        "transferCurrencyIndicator": "SOURCE_ACCOUNT_CURRENCY",
        "destinationAccountId": destination_account_id,
        "chargeBearer": "BENEFICIARY",
        "fxDealReferenceNumber": "FB%d" % int(time.time()),
        "remarks": "",
        "transferPurpose": "CASH_DISBURSEMENT"
    }

    headers = generate_headers(token)
    r = requests.post('https://sandbox.apihub.citi.com/gcp/api/v1/moneyMovement/personalDomesticTransfers/preprocess',
                      json=request,
                      headers=headers)

    if r.status_code != 200:
        logger.error("Unable to create transfer request, status={}, error={}".format(r.status_code, r.text))
        return None

    j = r.json()
    return j['controlFlowId']


def make_transfer(token, control_flow_id):
    request = {"controlFlowId": control_flow_id}
    headers = generate_headers(token)
    r = requests.post('https://sandbox.apihub.citi.com/gcb/api/v1/moneyMovement/personalDomesticTransfers',
                      json=request,
                      headers=headers)

    if r.status_code != 200:
        logger.error("Unable to create transfer request, status={}, error={}".format(r.status_code, r.text))
        return None

    return r.json()


def generate_headers(token):
    return {
        "Authorization": "Bearer %s" % token,
        "uuid": str(uuid.uuid4()),
        "client_id": client_id,
        "Accept": "application/json"
    }
