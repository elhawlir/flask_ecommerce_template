# functions for cleaning uploaded mobile numbers
from pprint import pprint
import numpy as np
import time
import json

# ensures all Australian numbers are in suitable format to receive twilio messages
def number_clean(series):
    empty_list = []
    for i in series:
        if (i[:2] == "61") or (i[:3] == "+61"):
            empty_list.append(i)
        else:
            i = "+61" + i
            empty_list.append(i)
    return empty_list


def clean_mobile_input(mobile_list):
    for i in range(len(mobile_list)):
        if mobile_list[i][0] != "+":
            mobile_list[i] = "+" + mobile_list[i]
    else:
        pass

    return mobile_list

# function that sends test message to mobile number user enters
def test_msg(receiving_number, text, client, msg_service_id):
    message = client.messages.create(
        body = text,
        messaging_service_sid = msg_service_id,
        to = receiving_number
    )


# function that sends final message to members list
def final_text(numbers_list, text, client, notify_id, sender, msg_service_id):
    count = 0
    # list of numbers not to be sent messages
    leave_out = ["+61412345678", "+61400000000"]
    # filtering out the above numbers
    final_list = [number for number in numbers_list if number not in leave_out]
    # print(final_list)
    # length of total numbers to be sent messges
    # print("There are", len(final_list), "total mobile numbers")
    # removing duplicate numbers
    unique_numbers = list(set(final_list))
    # displaying number of unique numbers
    print('There are', len(unique_numbers), 'unique mobile numbers')
    # returns number of duplicate numbers
    # print('There are', len(final_list) - len(unique_numbers), 'duplicate mobile numbers')
    bindings = list(map(lambda number: json.dumps({'binding_type': 'sms', 'address': number}), unique_numbers))
    print(bindings)

    # create alpha sender
    alpha_sender = client.messaging.services(msg_service_id).alpha_senders.create(alpha_sender=sender)
    alpha_sid = alpha_sender.sid
    print(f"Newly created alpha_sid: {alpha_sid}")

    # send msg to each number individually
    start_np = time.time()
    print('starting now')
    try:
        notification = client.notify.services(notify_id).notifications.create(
        to_binding=bindings,
        body=text)
        print(f"body: {notification.body}")
    except Exception as e:
        # pass
        print(e)
        pass

    # print(client.notify.services(notify_id).list(limit=10))

    # delete temporary alpha sender
    # client.messaging.services(msg_service_id).alpha_senders(alpha_sid).delete()
    print(client.messaging.services(msg_service_id).alpha_senders.list())
    
    end_np = time.time()
    print(f"Dictionary run time: {end_np - start_np}")

    print(f"Notification SID retrieval: {client.notify.services(notify_id).notifications('NTbdbfbd85485447c67241ff7128bdb134').fetch()}")

    print(f"Expected Number of messages: {len(unique_numbers)}")
    if count == 1:
        msg = f"You successfully sent {count} message"
        final_list.clear()
        return msg
    else:
        msg = f"You successfully sent {count} messages"
        final_list.clear()
        return msg
    
    


