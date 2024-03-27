import pandas as pd
import json
import openai
import time
import os
import sys
from utils.crawl_utils import chat_completion_with_backoff
from utils.utils import read_api_excel, OPENAI_INFO
from utils.ssl_utils import no_ssl_verification

DEBUG = False
SAVE_FILE = "results/dialogue_profiles.txt"
SAVE_FILE_DUMMY = "results/dialogue_profiles_dummy.txt"
openai_info = OPENAI_INFO["gpt-4-0616"]
DEPLOYMENT_ID = openai_info["deployment_id"]
openai.api_key = openai_info["api_key"]
openai.api_base = openai_info["api_base"]
openai.api_version = openai_info["api_version"]
openai.api_type = openai_info["api_type"]

if DEBUG:
    # gpt-4
    with no_ssl_verification():
        messages = [{"role": "system", "content": "You are an experienced prompt engineer."},{"role": "user", "content": "Please construct 10 different use case scenarios based on the following API documentation:\n" +'{"domain": "Device Control", "subdomain": "Navigation", "function": "Navigate", "api": "Navigate", "description": "On a device, use a navigation app to navigate from a departure location to a destination by a certain transportation method", "parameters": {"deviceType": "Supported device types, including phone, tablet, TV, speaker, watch", "appName": "Name of the app with navigation capabilities", "trafficType": "Transportation method, including walking, cycling, driving, subway, bus, etc", "departure": "Departure location", "destination": "Destination (required slot)", "estimateTime": "Whether to query the estimated travel time, including True and False", "estimateDistance": "Whether to query the estimated travel distance, including True and False"}}'+ "\nPlease follow the following format:\n1.\nCharacter: Emma, a college student\nBackground: Emma has a difficult time remembering her assignment due dates and exam preparation schedules.\nPurpose: Emma uses the CreateNotification API on her phone to notify her of her 'to-do' tasks related to assignments and exams.\n...\n10.\nCharacter: Frank, a senior citizen\nBackground: Frank needs to take medicine at certain time slots during the day.\nPurpose: Frank uses the CreateNotification API on his smart speaker to remind him to take his medication.\n" }]
        response = chat_completion_with_backoff(
            deployment_id=DEPLOYMENT_ID,
            messages=messages,
        )
    fmt_resp = response["choices"][0]["message"]["content"].replace("\n\n", "\n").strip()
    print(fmt_resp)
    with open(SAVE_FILE_DUMMY, "w") as f:
        f.write(fmt_resp)
    sys.exit()

data = read_api_excel("API_list.xlsx", "API list", "local")
for idx, d in enumerate(data):
    # if idx >= 15:
    #     continue
    for _ in range(1):
        with no_ssl_verification():
            messages = [{"role": "system", "content": "You are an experienced prompt engineer."},{"role": "user", "content": "Please construct 5 different use case scenarios based on the following API documentation:\n" + json.dumps(d, ensure_ascii=False) + "\nPlease follow the following format:\n1.\nCharacter: Emma, a college student\nBackground: Emma has a difficult time remembering her assignment due dates and exam preparation schedules.\nPurpose: Emma uses her phone to notify her of her 'to-do' tasks related to assignments and exams.\nAPI: CreateNotification\nParameters: {\"deviceType\": \"phone\", \"time\": \"tomorrow at 8:30 in the morning\", \"content\": \"Prepare for the exam\", \"type\": \"todo\"}\nFirstQuery: Hi, I'd like to create a todo.\n...\n5.\nCharacter: Frank, a senior citizen\nBackground: Frank needs to take medicine at certain time slots during the day.\nPurpose: Frank uses his smart speaker to remind him to take his medication.\nAPI: CreateNotification\nParameters: {\"deviceType\": \"speaker\", \"time\": \"2:30 in the afternoon\", \"content\": \"take medicine\", \"type\": \"reminder message\"}\nFirstQuery: Please remind me to take medicine.\n\nNote that the generated scenarios have exactly six attributes, i.e. Character, Background, Purpose, API, Parameters and FirstQuery. Do not create new attributes.\nThe values in the generated parameters should be consistent with the character, background, purpose and API. All keys with (required slot) annotation and at least one key with (optional slot) annotation in the doc must appear. It is okay to omit the key without (required slot) and (optional slot) annotation, in which case you should simply leave them blank. The parameters should be exact one line. When creating parameters, do not use placeholders or vague expressions like \"unknown\", \"Not Available\", \"Some horror movie\" or \"Original notification time\", create a specific name, position, time or other exact expressions consistent with the background and purpose description instead. FirstQuery is the first user utterance in a multi-round user-system dialogue. FirstQuery should use spoken English and only consists of information from one or two parameters. The information value existing in FirstQuery should be exact the same with the value in Parameters, instead of their paraphrase." }]
            response = chat_completion_with_backoff(
                deployment_id=DEPLOYMENT_ID,
                messages=messages,
            )
        fmt_resp = response["choices"][0]["message"]["content"].replace("\n\n", "\n").strip()
        print(fmt_resp)
        with open(SAVE_FILE, "a") as f:
            f.write(fmt_resp + "\n")
            time.sleep(1)
