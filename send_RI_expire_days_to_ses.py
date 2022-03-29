import botocore
import boto3
import datetime 
import json

def main():
    p_n="test"
    r_n="ap-northeast-2"

    session = boto3.session.Session(profile_name=p_n)
    ec2_cli = session.client('ec2', region_name=r_n)
    account_id = session.client('sts').get_caller_identity().get('Account')

    alert_to_expire_days = 7
    alert_to_emails = ['ahchim.lee@bespinglobal.com', 'AhchimLeee@gmail.com']
    sender_email = 'ahchim.lee@bespinglobal.com'
    ses_verified_emails = []
    ses_not_verified_emails = []

    head,exp_list = get_reservation_expires(ec2_cli, alert_to_expire_days)

    #print(head)
    #print(exp_list)

    title = "[AWS: " + account_id + "] Reserved Instance Experation in " + str(alert_to_expire_days) + " days"
    message = account_id + """ AWS Account: EC2 Reserved Instance Experation: <b>""" + str(alert_to_expire_days) + """</b> days <br/>
    """ + head + exp_list

    ses_verified_emails = get_verified_email_addresses(ses_cli)

    for email in alert_to_emails:
        if ses_verified_emails:
            if email not in ses_verified_emails:
                verify_email_identity(ses_cli, email)
                ses_not_verified_emails.append(email)
        else:
            verify_email_identity(ses_cli, email)
            ses_not_verified_emails.append(email)

    if exp_list:
        alert_to_emails = list(set(alert_to_emails) - set(ses_not_verified_emails))

        for email in alert_to_emails:
            send_html_email(ses_cli, title, message, email, sender_email)

def get_reservation_expires(ec2_cli, days):
    ris = ec2_cli.describe_reserved_instances().get(
        'ReservedInstances', []
    )

    ri = [ r for r in ris if r['State']=='active' ]

    th = ['Instance Type', 'Scope', 'Count', 'Start', 'Expires', 'Term', 'Payment', 'Offering class', 'Charge', 'Plaform', 'State']
    table_head = '<table width="100%" border="0.5"><thead><tr>' + ''.join(['<th>'+t+'</th>' for t in th]) + '</tr></thead>'

    table_content = ''

    to_kst = datetime.timedelta(hours=9)
    
    for r in ri:
        start = (r['Start'] + to_kst).strftime('%Y-%m-%d %H:%M')
        end = (r['End'] + to_kst).strftime('%Y-%m-%d %H:%M')
        term = (r['End']-(datetime.datetime.now(datetime.timezone.utc) + to_kst)).days
        charge = r['RecurringCharges'][0]['Amount']
        charge_unit = r['RecurringCharges'][0]['Frequency']

        if term == days:
            if not table_content:
                table_content += '<tbody><tr>'

            td = [r['InstanceType'], r['Scope'], str(r['InstanceCount']), start, end, str(term) + ' days', r['OfferingType'], r['OfferingClass'], '$' + str(charge) + ' (' + charge_unit + ')', r['ProductDescription'], r['State']]
            table_content += ''.join(['<td>'+t+'</td>' for t in td])
            table_content += '</tr><tr>'

    if table_content:
        table_content = table_content[:-4]
        table_content += '</tbody></table>'

    return table_head,table_content


def get_verified_email_addresses(ses_cli):
    return ses_cli.list_verified_email_addresses().get(
        'VerifiedEmailAddresses', []
    )

def verify_email_identity(ses_cli, email):
    response = ses_cli.verify_email_identity(
        EmailAddress=email
    )

def send_html_email(ses_cli, title, message, email, s_email):
    CHARSET = "UTF-8"
    HTML_EMAIL_CONTENT = message

    response = ses_cli.send_email(
        Destination={
            "ToAddresses": [
                email,
            ],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": CHARSET,
                    "Data": HTML_EMAIL_CONTENT,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": title,
            },
        },
        Source=s_email,
    )


if __name__ == '__main__':
    main()
