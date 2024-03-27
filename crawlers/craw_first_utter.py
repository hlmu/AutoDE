import pandas as pd
import json
import openai
import time
import os
from utils.crawl_utils import chat_completion_with_backoff
from utils.utils import read_api_excel, OPENAI_INFO
from utils.ssl_utils import no_ssl_verification

DEBUG = False
PROFILE_FILE = "results/dialogue_profiles_v1.txt"
RESPONSE_FILE = "results/dialogue_api_calls.txt"
PROFILE_FILE_DUMMY = "results/dialogue_profiles_dummy.txt"
RESPONSE_FILE_DUMMY = "results/dialogue_api_calls_dummy.txt"
openai_info = OPENAI_INFO["gpt-4-0616"]
DEPLOYMENT_ID = openai_info["deployment_id"]
openai.api_key = openai_info["api_key"]
openai.api_base = openai_info["api_base"]
openai.api_version = openai_info["api_version"]
openai.api_type = openai_info["api_type"]

def is_start(s):
    return s[0] in "0123456789"

if DEBUG:
    with open(PROFILE_FILE_DUMMY, "r") as f:
        profiles = f.read()
    # gpt-4
    with no_ssl_verification():
        messages = [{"role": "system", "content": "You are a helpful AI assistant with the ability to call functions."},{"role": "user", "content": "Please construct the API calls based on the following use case scenarios and API documentation. The use case scenarios are:\n" + profiles + "\nThe API documentation is:\n" + '{"domain": "Device Control", "subdomain": "Navigation", "function": "Navigate", "api": "Navigate", "description": "On a device, use a navigation app to navigate from a departure location to a destination by a certain transportation method", "parameters": {"deviceType": "Supported device types, including phone, tablet, TV, speaker, watch", "appName": "Name of the app with navigation capabilities", "trafficType": "Transportation method, including walking, cycling, driving, subway, bus, etc", "departure": "Departure location", "destination": "Destination (required slot)", "estimateTime": "Whether to query the estimated travel time, including True and False", "estimateDistance": "Whether to query the estimated travel distance, including True and False"}}' + 'Please follow the following format:\n1.\nNavigate(deviceType = "phone", appName = "All Trails", trafficType = "walking", departure = "campsite", destination = "hiking trail start")\n...\n10.\nNavigate(deviceType = "tablet", appName = "Google Maps", trafficType = "cycling", departure = "home", destination = "work")'}]
        response = chat_completion_with_backoff(
            deployment_id=DEPLOYMENT_ID,
            messages=messages,
        )
    fmt_resp = response["choices"][0]["message"]["content"].replace("\n\n", "\n").strip()
    print(fmt_resp)
    with open(RESPONSE_FILE_DUMMY, "w") as f:
        f.write(fmt_resp)
else:
    data = read_api_excel("API_list.xlsx", "API list", "local")
    api_dict = {}
    for d in data:
        assert d['api'] not in api_dict
        api_dict[d['api']] = d

    cnt = 0
    with open(PROFILE_FILE, "r") as f:
        d = {}
        for idx, line in enumerate(f):
            if is_start(line):
                if d:
                    cnt += 1
                    # if cnt < 50:
                    #     d = {}
                    #     continue
                    assert "Character" in d
                    {"API": "Navigate", "deviceType": "phone", "appName": "All Trails", "trafficType": "walking", "departure": "campsite", "destination": "hiking trail start"}

                    assert "Background" in d
                    assert "Purpose" in d
                    assert "API" in d
                    assert d["API"] in api_dict
                    # gpt-4
                    profiles = f"Character: {d['Character']}\nBackground: {d['Background']}\nPurpose: {d['Purpose']}\nAPI: {d['API']}"
                    with no_ssl_verification():
                        user_msg = "Please construct the API call based on the following use case scenario and API documentation. The use case scenario is:\n" + profiles + "\n\nThe API documentation is:\n" + json.dumps(api_dict[d['API']], ensure_ascii=False) + '\n\nPlease output the API call using the following format:\n[Explanation]foo bar\n[API Call]\n{"API": "Navigate", "deviceType": "phone", "appName": "All Trails", "trafficType": "walking", "departure": "campsite", "destination": "hiking trail start"}\n\nNote that the values in the generated API call should be consistent with the aforementioned use case scenario. You should always refer the original value from the case description instead of rewriting them. All keys with (required slot) annotation and at least one key with (optional slot) annotation must appear. Only fabricate the absent value when the case description can not satisfy the previous restriction. It is okay to omit the key without (required slot) and (optional slot) annotation. The [API Call] should be exact one line.'
                        messages = [{"role": "system", "content": "You are a helpful AI assistant with the ability to call functions."},{"role": "user", "content": user_msg}]
                        print(user_msg)
                        response = chat_completion_with_backoff(
                            deployment_id=DEPLOYMENT_ID,
                            messages=messages,
                        )
                    fmt_resp = response["choices"][0]["message"]["content"].replace("\n\n", "\n").strip()
                    print(fmt_resp)
                    with open(RESPONSE_FILE, "a") as f:
                        f.write(profiles + f"\n{fmt_resp}\n-------------------\n")
                    d = {}
                    time.sleep(5)
            else:
                # try:
                k, v = line.split(": ", maxsplit=1)
                d[k] = v.strip()
                # except ValueError:
                #     k, v = line.split(":", maxsplit=1)
                #     d[k] = v.strip()
