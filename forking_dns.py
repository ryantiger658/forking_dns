import requests, toml, boto3
from datetime import datetime

# Global Vars
dynamic_sub_domain = 'wtf'
domains = ['whatthefork.wtf']
record_set = {}
hosted_zones = {}
external_ip = ''
wtf_results = {}
line_break = "\n----------------------------------------------------------\n"

r53 = boto3.client('route53')

def get_ip(url = 'https://myip.wtf/json', refresh=False):
    global external_ip
    if external_ip == '' or refresh:
        wtf = requests.get(url).json()
        wtf['TimeLastFuckingChecked'] = datetime.now()
        global wtf_results
        wtf_results = wtf
        external_ip = wtf['YourFuckingIPAddress']
        write_to_file(wtf, url)
        print("I think your forking IP is " + external_ip)

    return external_ip

def write_to_file(wtf, url, file='wtf.toml'):
    wtf = {
        url: wtf
    }
    with open(file, "w") as wtf_file:
        toml.dump(wtf, wtf_file)

def get_hosted_zones():
    global hosted_zones
    if hosted_zones == {}:
        hosted_zones = r53.list_hosted_zones()['HostedZones']
    return hosted_zones

def get_records(HostedZoneId):
    global record_set

    if record_set == {}:
        record_set[HostedZoneId] = {} 
    elif not HostedZoneId in record_set:
        record_set[HostedZoneId] = {} 

    if record_set[HostedZoneId] == {}:
        record_set[HostedZoneId] = r53.list_resource_record_sets(HostedZoneId=HostedZoneId)['ResourceRecordSets']
    
    return record_set[HostedZoneId]

def check_for_record(dyn_record, HostedZoneId):
    records=get_records(HostedZoneId)
    for record in records:
        if record['Name'] == dyn_record + '.':
            print(dyn_record + ' already exists... Will UPSERT')
            # TODO; CHECK TO SEE IF RECORD IS CORRECT
            return "UPSERT"

    print(dyn_record + ' does not exist... Will CREATE')
    return "CREATE"

def create_record(dyn_record, HostedZoneId, ip, action, comment="created by wtf" ):
    r53.change_resource_record_sets(
        ChangeBatch={
            'Changes': [
                {
                    'Action': action,
                    'ResourceRecordSet': {
                        'Name': dyn_record,
                        'ResourceRecords': [
                            {
                                'Value': ip,
                            },
                        ],
                        'TTL': 300,
                        'Type': 'A',
                    },
                },
            ],
            'Comment': comment,
        },
        HostedZoneId=HostedZoneId,
    )
    print(action + "D A Record " + dyn_record + " ==> " + ip)

def check_domains(domains):
    validated_domains = []
    zones = get_hosted_zones()
    for domain in domains:
        print("\n----------- Checking Ownership of " + domain + ' -----------\n')
        found = 0
        for zone in zones:
            if zone['Name'] == domain + '.':
                validated_domains.append({
                    'ZoneName': domain,
                    'HostedZoneId': zone['Id']
                })
                found = 1
                break
        if found == 1:
            print(domain + ' is in this account')
        else:
            print('You do not have permissions to forking update ' + domain)
    return(validated_domains)

domains_to_process = check_domains(domains)

if len(domains_to_process) == 0:
    print("Don't forking make me update records that you don't forking own.")
    print(line_break)
    print("ABORTING")
    exit()

print(line_break)

get_ip()

print(line_break)

print("Checking for existing records...")

for domain in domains_to_process:
    try:
        print("\n----------- Operating on " + domain['ZoneName'] + ' -----------')

        record_name = dynamic_sub_domain+'.'+domain['ZoneName']

        domain['update_action'] = check_for_record(record_name, domain['HostedZoneId'])
        
        create_record(record_name, domain['HostedZoneId'], external_ip, domain['update_action'])
        
        print(domain['ZoneName'] + " updated sucessfully")
    except:
        print(domain['ZoneName'] + " FAILED")

print(line_break)