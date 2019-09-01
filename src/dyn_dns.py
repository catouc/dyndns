import requests
import sys
import logging
import urllib3
import time
import boto3
import os
from retrying import retry

# I know I'm doing insecure requests I'll fix it.. promise
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGLEVEL = os.environ.get('LOGLEVEL')

# create logger with 'spam_application'
logger = logging.getLogger('__name__')
if LOGLEVEL:
    logger.setLevel(LOGLEVEL)
else:
    logger.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
logger = logging.getLogger('__name__')
if LOGLEVEL:
    ch.setLevel(LOGLEVEL)
else:
    ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=requests.exceptions.Timeout)
def get_public_ip():
    open_dns_url = 'https://diagnostic.opendns.com/myip'
    # somehow the handshake errors out
    logger.debug(f'Making GET request to {open_dns_url} ...')
    response = requests.get(open_dns_url, verify=False)
    logger.debug(f'Request succeded with code: {response}')
    public_ip = response.text
    logger.info(f'The public IP is {public_ip}')
    return public_ip

# just so on the first run we actually update the DNS record
public_ip = '127.0.0.1/32'

while True:
    n_public_ip = get_public_ip()
    logger.debug(f'Matching {public_ip} against {n_public_ip}')
    if public_ip == n_public_ip:
        logger.info(f'IPs match no action required!')
        time.sleep(120)
    else:
        client = boto3.client('route53')
        response = client.change_resource_record_sets(
            HostedZoneId=os.environ.get('HOSTED_ZONE_ID'),
            ChangeBatch={
                'Comment': 'Updating public ip for dyn dns service',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': 'home.deichindianer.de',
                            'Type': 'A',
                            'TTL': 120,
                            'ResourceRecords': [
                                {
                                    'Value': n_public_ip 
                                }
                            ]
                        }
                    }
                ]
            }
        )
        logger.debug(f'R53 response: {response}')
    public_ip = n_public_ip

