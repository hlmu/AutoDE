import pandas as pd
import json
import openai
import time
import os
from utils.crawl_utils import chat_completion_with_backoff
from utils.utils import parse_profile, read_api_excel, OPENAI_INFO
from utils.ssl_utils import no_ssl_verification

openai_info = OPENAI_INFO["gpt-35-turbo-16k"]
openai.api_key = openai_info["api_key"]
openai.api_version = openai_info["api_version"]


with open("prompts/prompt_eng_user_v3.txt", "r") as f:
    user_system_message = f.read()
with open("prompts/prompt_eng_user_first_round_v2.txt", "r") as f:
    user_system_message_first_round = f.read()
with open("prompts/prompt_eng_system.txt", "r") as f:
    assistant_system_message = f.read()


save_file = 'results/results_eng.txt'
save_file_debug = 'results/results_eng_debug.txt'
ckpt_path = save_file.replace(".txt", ".save")
ckpt = -1
if os.path.exists(ckpt_path):
    with open(ckpt_path, "r") as f:
        ckpt = int(f.read())
    print("Starting from " + str(ckpt))

api_data = read_api_excel("API_list.xlsx", "API list", "openai_eng")
profile_data = parse_profile("results/dialogue_profiles_v2_uuid.txt")

api_dict = { function['name']:function for function in api_data}

rep = 1

for index, d in enumerate(profile_data):
    function = api_dict[d["API"]]
    uuid = d["uuid"]
    if index <= ckpt:
        continue
    # if len(function["parameters"]["required"]) == 0 and "The call must contain at least one of the following parameters" not in function["description"]:
    #     continue
    functions = [function]
    user_content_first_round = f"Output your utterance as the following format, you may random choose one parameter at most, and you may only use the exact choosed parameter without paraphrase to construct your query. You should try to choose the parameter randomly. If no parameters choosed, output \"None\" in the [Random Parameter].\n[Random Parameter] deviceType\n[Thought] I should ask using the deviceType parameter.\n[Query] Turn down the volume on my phone.\n\nThe conversation information is given as:\nCharacter: {d['Character']}\nBackground: {d['Background']}\nPurpose: {d['Purpose']}\nAPI: {d['API']}\nParameters: {d['Parameters']}\n\nAlways act as {d['Character']}. You can chat with me now." 
    user_content = f"Character: {d['Character']}\nBackground: {d['Background']}\nPurpose: {d['Purpose']}\nAPI: {d['API']}\nParameters: {d['Parameters']}"
    print("\n-----------------\n")
    print("User First Round Instruction: " + user_system_message_first_round + "\n\n" + user_content_first_round)
    print("\n-----------------\n")
    print("User Instruction: " + user_system_message + user_content)
    print("\n-----------------\n")
    print("Assistant Instruction: " + assistant_system_message + "\n" + json.dumps(function, ensure_ascii=False, indent=4))
    print("===================")
    for _ in range(rep):

        user_messages_first_round = [{"role": "system", "content": user_system_message_first_round}, {"role": "user", "content": user_content_first_round}]
        user_messages = [{"role": "system", "content": user_system_message + user_content}]
        assistant_messages = [{"role": "system", "content": assistant_system_message}]
        
        success_flag = False
        with open(save_file, "a") as f:
            f.write("uuid: " + uuid + "\n")
        with open(save_file_debug, "a") as f:
            f.write("uuid: " + uuid + "\n")
        for r in range(8):
            flag = False
            while not flag:
                with no_ssl_verification():
                    response = chat_completion_with_backoff(
                        model=openai_info["model"],
                        messages=user_messages if r!=0 else user_messages_first_round,
                    )
                time.sleep(5)
                try:
                    resp = response["choices"][0]["message"]["content"]
                except KeyError as e:
                    print(e)
                    print("Retrying...")
                    time.sleep(60)
                    continue
                if r!=0:
                    flag = True
                else:
                    print("First round query: ", resp)
                    for line in resp.split("\n"):
                        if "[Query]" in line:
                            flag = True
                            resp_debug = resp
                            resp = line.replace("[Query]", "").strip()
                            break
                    if not flag:
                        print("\n***********First round format error, regenerate now\n")

            print("User: ", resp)
            with open(save_file, "a") as f:
                f.write("User: " + resp + "\n")
            with open(save_file_debug, "a") as f:
                f.write("User: " + resp_debug + "\n")
            assistant_messages.append({"role": "user", "content": resp})
            user_messages.append({"role": "assistant", "content": resp})

            with no_ssl_verification():
                response = chat_completion_with_backoff(
                    model=openai_info["model"],
                    messages=assistant_messages,
                    functions=functions,
                    function_call='auto',  # auto is default, but we'll be explicit
                    # function_call={"name": function['name']},  # auto is default, but we'll be explicit
                )
            try:
                response_message = response["choices"][0]["message"]
            except KeyError as e:
                print(e)
                print("Retrying...")
                time.sleep(60)
                continue
            if response_message.get("function_call"):
                res = json.dumps(response_message["function_call"], ensure_ascii=False)
                print("Assistant: " + res)
                success_flag = True
                with open(save_file, "a") as f:
                    f.write("Assistant: " + res + "\n-------------------\n")
                with open(save_file_debug, "a") as f:
                    f.write("Assistant: " + res + "\n-------------------\n")
                print("-------------------")
                break
            else:
                print("Assistant: " + response_message["content"])
                if "[DONE]" in response_message["content"]:
                    msg = response_message["content"].replace("[DONE]", "").strip()
                    with open(save_file, "a") as f:
                        f.write("Assistant: " + msg + "\n-------------------\n")
                    with open(save_file_debug, "a") as f:
                        f.write("Assistant: " + msg + "\n-------------------\n")
                        break
                else:
                    with open(save_file, "a") as f:
                        f.write("Assistant: " + response_message["content"] + "\n")
                    with open(save_file_debug, "a") as f:
                        f.write("Assistant: " + response_message["content"] + "\n")
                    assistant_messages.append({"role": "assistant", "content": response_message["content"]})
                    user_messages.append({"role": "user", "content": response_message["content"]})
            time.sleep(5)
    with open(ckpt_path, 'w') as f:
        f.write(str(index))
