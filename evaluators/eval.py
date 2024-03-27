from utils.crawl_utils import chat_completion_with_backoff, get_agent, llama_chat_completion, openai_chat_completion
from utils.data_utils import get_precision_recall_f1, load_data, calc_metrics
import json
import openai
import time
import os
from utils.utils import parse_profile, read_api_excel, OPENAI_INFO
from utils.ssl_utils import no_ssl_verification
import argparse
import traceback
import uuid
from tqdm import tqdm
import copy

parser = argparse.ArgumentParser(description="Start the Flask server with custom paths.")
parser.add_argument('--user_agent', default="gpt-35-turbo-16k", type=str, required=True, help='User agent')
parser.add_argument('--assistant_agent', default="gpt-35-turbo-16k", type=str, required=True, help='Assistant agent')
parser.add_argument('--user_prompt_path', default="prompts/prompt_eng_user_v3.txt", type=str, required=True, help='User system message path')
parser.add_argument('--assistant_prompt_path', default="prompts/prompt_eng_system.txt", type=str, required=True, help='Assistant system message path')
parser.add_argument('--api_excel_file', default="API_list.xlsx", type=str, required=True, help='File with api reference')
parser.add_argument('--eval_data_file', default="datasets/data_v1.jsonl", type=str, required=True, help='Benchmark dataset file')
parser.add_argument('--human_data_file', type=str, required=False, help='Human evaluation results')
parser.add_argument('--save_file_path', default="results/test.jsonl", type=str, required=True, help='Path to save the result file')
parser.add_argument('--user_agent_url', default="http://192.168.1.115:12315/generate", type=str, required=False, help='User agent url, if user agent is not gpt')
parser.add_argument('--assistant_agent_url', type=str, required=False, help='Assistant agent url, if system agent is not gpt')
parser.add_argument('--user_sleep', default=0, type=int, required=False, help='Sleep time after fetching of user agent')
parser.add_argument('--assistant_sleep', default=0, type=int, required=False, help='Sleep time after fetching of assistant agent')
parser.add_argument('--num_trials', type=int, required=True, help='Trials')
parser.add_argument('--static_test', type=bool, default=False, required=False, help='Do static test')
parser.add_argument('--human_test', type=bool, default=False, required=False, help='Do human test')
parser.add_argument('--max_rounds', default=8, type=int, required=False, help='Max rounds of dialogues')
parser.add_argument('--complementary', default=False, type=bool, required=False, help='Whether to complete save file')
args = parser.parse_args()

if "llama" in args.assistant_agent or "zephyr" in args.assistant_agent or "mistral" in args.assistant_agent:
    assitant_chat_completion = get_agent(args.assistant_agent, url=args.assistant_agent_url)
else:
    assitant_chat_completion = get_agent(args.assistant_agent)

if "llama" in args.user_agent or "zephyr" in args.user_agent or "mistral" in args.user_agent:
    user_chat_completion = get_agent(args.user_agent, url=args.user_agent_url)
else:
    user_chat_completion = get_agent(args.user_agent)


with open(args.user_prompt_path, "r") as f:
    user_system_message = f.read()
with open(args.assistant_prompt_path, "r") as f:
    assistant_system_message = f.read()

if args.static_test and "static" not in args.assistant_prompt_path:
    raise ValueError("Wrong assistant_prompt_path file provided")

if "gpt" in args.assistant_agent:
    if "[Openai]" not in assistant_system_message:
        raise ValueError("Wrong assistant_prompt_path file provided")
    assistant_system_message = assistant_system_message.strip("[Openai]")
elif "llama" in args.assistant_agent:
    if "[Llama]" not in assistant_system_message:
        raise ValueError("Wrong assistant_prompt_path file provided")
    assistant_system_message = assistant_system_message.strip("[Llama]")
elif "zephyr" in args.assistant_agent:
    if "[Zephyr]" not in assistant_system_message:
        raise ValueError("Wrong assistant_prompt_path file provided")
    assistant_system_message = assistant_system_message.strip("[Zephyr]")
elif "mistral" in args.assistant_agent:
    if "[Mistral]" not in assistant_system_message:
        raise ValueError("Wrong assistant_prompt_path file provided")
    assistant_system_message = assistant_system_message.strip("[Mistral]")
elif "claude" in args.assistant_agent:
    if "[Claude]" not in assistant_system_message:
        raise ValueError("Wrong assistant_prompt_path file provided")
    assistant_system_message = assistant_system_message.strip("[Claude]")
else:
    raise NotImplementedError

api_data = read_api_excel(args.api_excel_file, "API list_2", "openai_eng")
api_dict = { function['name']:function for function in api_data}

"""
[
    {
        "uuid": "example_uuid",
        "background": "Character: ...\nBackground: ...\nPurpose: ...",
        "content": [
            {"role": "User", "message": "Turn up the volume on the Smart TV."},
        ],
        "api": "UpdateApp",
        "slots": {
            "deviceType": "tablet",
            "appName": "Fitness Pro"
        }
    },
]
"""
records = load_data(args.eval_data_file)
# print(records[:5])
trial_uuid = str(uuid.uuid4())

assert args.save_file_path.endswith(".jsonl")
if not args.complementary:
    save_file = args.save_file_path
    ckpt_path = save_file.replace(".jsonl", ".save")
    save_file_debug = save_file.replace(".jsonl", ".debug")
else:
    save_file = args.save_file_path.replace(".jsonl", "_complementary.jsonl")
    ckpt_path = save_file.replace(".jsonl", ".save")
    save_file_debug = save_file.replace(".jsonl", ".debug")
    complementary_src_file = load_data(args.save_file_path)
    complementary_src_dict = {}
    for r in complementary_src_file:
        if r["uuid"] not in complementary_src_dict:
            complementary_src_dict[r["uuid"]] = [r]
        else:
            complementary_src_dict[r["uuid"]].append(r)

ckpt = -1
if os.path.exists(ckpt_path):
    with open(ckpt_path, "r") as f:
        ckpt = int(f.read())
    print("Starting from " + str(ckpt))


precision_accu = 0.0
recall_accu = 0.0
f1_accu = 0.0
instance_cnt = 0

# for index, d in enumerate(profile_data):

def fetch_assistant(current_dialogue, assistant_messages, user_messages, functions, function_call='auto', sleep=5):
    response_message = assitant_chat_completion(assistant_messages, functions=functions, function_call=function_call, sleep=sleep)
    if "error" in response_message:
        if "Context length exceeded" in response_message["error"] or "Generation format error" in response_message["error"]:
            current_dialogue["reason"] = response_message["error"]
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            with open(save_file_debug, "a") as f:
                f.write("Fail: " + response_message["error"])
            return {"state": "failure"}
        else:
            raise Exception(response_message["error"])

    elif "arguments" in response_message:
        try:
            pred_slot_label = json.loads(response_message["arguments"])
            pred_slot_label.pop("functionName", None)
            pred_slot_label = {k:v for k,v in pred_slot_label.items() if isinstance(v, bool) or v is not None and isinstance(v, str) and v.lower()!='null' and v.strip()!=''}
        except json.decoder.JSONDecodeError as e:
            traceback.print_exc()
            print(response_message["arguments"])
            current_dialogue["reason"] = f"Arguments parse failed: {response_message['arguments']}"
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            with open(save_file_debug, "a") as f:
                f.write("Fail: " + f"Arguments parse failed: {response_message['arguments']}")
            return {"state": "failure"}
        except AttributeError as e:
            traceback.print_exc()
            print(response_message["arguments"])
            current_dialogue["reason"] = f"Arguments parse failed: {response_message['arguments']}"
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            with open(save_file_debug, "a") as f:
                f.write("Fail: " + f"Arguments parse failed: {response_message['arguments']}")
            return {"state": "failure"}

        current_dialogue["slots"] = pred_slot_label
        current_dialogue["state"] = "success"
        with open(save_file, "a") as f:
            f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")

        print("Assistant: " + json.dumps(response_message["arguments"], ensure_ascii=False))
        with open(save_file_debug, "a") as f:
            f.write("Assistant: " + json.dumps(response_message["arguments"], ensure_ascii=False))
        # print("-------------------")
        return {"state": "success", "label": pred_slot_label}
    else:
        print("Assistant: " + response_message["content"])
        if "end" in response_message and response_message["end"]:
            with open(save_file_debug, "a") as f:
                f.write("Assistant: " + response_message["content"] + "\n-------------------\n")
            current_dialogue["content"].append({"role": "Assistant", "message": response_message["content"]})
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            return {"state": "failure"}
        else:
            with open(save_file_debug, "a") as f:
                f.write("Assistant: " + response_message["content"] + "\n")
            assistant_messages.append({"role": "assistant", "content": response_message["content"]})
            user_messages.append({"role": "user", "content": response_message["content"]})
            current_dialogue["content"].append({"role": "Assistant", "message": response_message["content"]})
    return {"state": "running"}


def fetch_user(current_dialogue, assistant_messages, user_messages, sleep=5):
    response = user_chat_completion(user_messages, sleep=sleep)
    if "error" in response:
        if "Context length exceeded" in response["error"] or "Generation format error" in response["error"]:
            current_dialogue["reason"] = response["error"]
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            with open(save_file_debug, "a") as f:
                f.write("Fail: " + response["error"])
            return {"state": "failure"}
        else:
            raise Exception(response["error"])

    resp = response["content"].strip()

    print("User: ", resp)
    with open(save_file_debug, "a") as f:
        f.write("User: " + resp + "\n")
    assistant_messages.append({"role": "user", "content": resp})
    user_messages.append({"role": "assistant", "content": resp})
    current_dialogue["content"].append({"role": "User", "message": resp})
    return {"state": "running"}

def fetch_user_manual(current_dialogue, assistant_messages, user_messages, sleep=5):
    response = user_chat_completion(user_messages, sleep=sleep)
    if "error" in response:
        if "Context length exceeded" in response["error"] or "Generation format error" in response["error"]:
            current_dialogue["reason"] = response["error"]
            with open(save_file, "a") as f:
                f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
            with open(save_file_debug, "a") as f:
                f.write("Fail: " + response["error"])
            return {"state": "failure"}
        else:
            raise Exception(response["error"])

    default_resp = response["content"].strip()
    resp = input(f"User (default: {default_resp}):")
    if resp.strip() == "":
        resp = default_resp
    if resp.strip() == "[fail]":
        current_dialogue["reason"] = "Annotator thought the dialogue is failed"
        with open(save_file, "a") as f:
            f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
        with open(save_file_debug, "a") as f:
            f.write("Fail: Annotator thought the dialogue is failed")
        return {"state": "failure"}

    print("User: ", resp)
    with open(save_file_debug, "a") as f:
        f.write("User: " + resp + "\n")
    assistant_messages.append({"role": "user", "content": resp})
    user_messages.append({"role": "assistant", "content": resp})
    current_dialogue["content"].append({"role": "User", "message": resp})
    return {"state": "running"}


def run_metric(gold_slot_label, pred_slot_label):
    global instance_cnt
    global precision_accu
    global recall_accu
    global f1_accu
    precision, recall, f1 = get_precision_recall_f1(gold_slot_label, pred_slot_label)
    precision_accu += precision
    recall_accu += recall
    f1_accu += f1
    print(f"precision: {precision}, recall: {recall}, f1: {f1}")
    print(f"avg precision: {precision_accu/instance_cnt}, avg recall: {recall_accu/instance_cnt}, avg f1: {f1_accu/instance_cnt}" + "\n-------------------\n")

    with open(save_file_debug, "a") as f:
        f.write(f"\nprecision: {precision}, recall: {recall}, f1: {f1}" + f"\navg precision: {precision_accu/instance_cnt}, avg recall: {recall_accu/instance_cnt}, avg f1: {f1_accu/instance_cnt}" + "\n-------------------\n")


def main():
    global instance_cnt
    for index, record in enumerate(tqdm(records, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}')):
        function = copy.deepcopy(api_dict[record["api"]])
        record_uuid = record["uuid"]

        if index <= ckpt:
            continue
        if "gpt" not in args.assistant_agent:
            required = function["parameters"]["required"]
            function["parameters"] = function["parameters"]["properties"]
            function["requiredParameters"] = required
        functions = [function]
        user_content = f"{record['background'].strip()}\nAPI: {record['api']}\nParameters: {json.dumps(record['slots'], ensure_ascii=False)}"
        print("\n-----------------\n")
        if "llama" in args.assistant_agent or "claude" in args.assistant_agent or "zephyr" in args.assistant_agent or "mistral" in args.assistant_agent:
            print("Assistant Instruction: " + assistant_system_message.replace("{{api_doc}}", json.dumps(function, ensure_ascii=False)) + "\n")
        else:
            print("Assistant Instruction: " + assistant_system_message + "\n" + json.dumps(function, ensure_ascii=False, indent=4))
        print("\n-----------------\n")
        print("User Instruction: " + user_system_message + user_content)
        print("===================")

        with open(save_file_debug, "a") as f:
            f.write("uuid: " + record_uuid + "\n")

        rep = args.num_trials
        if args.complementary:
            if record_uuid in complementary_src_dict:
                for r in complementary_src_dict[record_uuid]:
                    with open(save_file, "a") as f:
                        f.write(json.dumps(r, ensure_ascii=False).strip() + "\n")
                rep = max(0, rep - len(complementary_src_dict[record_uuid]))

        for _ in range(rep):
            if not args.static_test:
                current_dialogue = {
                    "uuid": record_uuid,
                    "content": [{"role": "User", "message": record['content'][0]['message']}],
                    "background": record['background'].strip(),
                    "api": record['api'],
                    "slots": {},
                    "state": "failure",
                    "reason": "",
                    "trial_uuid": trial_uuid
                }
                assert record['content'][0]['role'] == "User"
                user_messages = [{"role": "system", "content": user_system_message + user_content}, {"role": "user", "content": "Now let's start the chat."}, {"role": "assistant", "content": record['content'][0]['message']}]
                if "claude" in args.assistant_agent or "mistral" in args.assistant_agent:
                    # Claude has no system message
                    assistant_messages = [{"role": "user", "content": assistant_system_message.replace("{{question}}", record['content'][0]['message'])}]
                else:
                    assistant_messages = [{"role": "system", "content": assistant_system_message}, {"role": "user", "content": record['content'][0]['message']}]
                print("First Round User: ", record['content'][0]['message'])
                with open(save_file_debug, "a") as f:
                    f.write("First Round User: " + str(record['content'][0]['message']))
            else:
                l = len(record['content'])
                ENTITY_MAP_0 = {
                    "User": "user",
                    "Assistant": "assistant"
                }
                ENTITY_MAP_1 = {
                    "User": "assistant",
                    "Assistant": "user"
                }
                current_dialogue = {
                    "uuid": record_uuid,
                    "content": copy.deepcopy(record['content'][:l]),
                    "background": record['background'].strip(),
                    "api": record['api'],
                    "slots": {},
                    "state": "failure",
                    "reason": "",
                    "trial_uuid": trial_uuid
                }
                assert record['content'][0]['role'] == "User"
                user_messages = [{"role": "system", "content": user_system_message + user_content}, {"role": "user", "content": "Now let's start the chat."}] + [{"role": ENTITY_MAP_1[r["role"]], "content": r["message"]} for r in record["content"][:l]]
                if "claude" in args.assistant_agent or "mistral" in args.assistant_agent:
                    # Claude has no system message
                    assistant_messages = [{"role": "user", "content": assistant_system_message.replace("{{question}}", record['content'][0]['message'])}] + [{"role": ENTITY_MAP_0[r["role"]], "content": r["message"]} for r in record["content"][1:l]]
                else:
                    assistant_messages = [{"role": "system", "content": assistant_system_message}] + [{"role": ENTITY_MAP_0[r["role"]], "content": r["message"]} for r in record["content"][:l]]
                assert assistant_messages[-1]["role"] == "user"
                print("First Round User: ", record['content'][0]['message'])
                with open(save_file_debug, "a") as f:
                    f.write("First Round User: " + str(record['content'][0]['message']))


            instance_cnt += 1
            gold_slot_label = record['slots']
            round_ended = False
            if not args.static_test:
                for r in range(args.max_rounds):
                    result = fetch_assistant(current_dialogue, assistant_messages, user_messages, functions, sleep=args.assistant_sleep)

                    if result["state"] == "success":
                        run_metric(gold_slot_label, result["label"])
                        round_ended = True
                        break
                    elif result["state"] == "failure":
                        round_ended = True
                        break
                    if args.human_test:
                        user_result = fetch_user_manual(current_dialogue, assistant_messages, user_messages, args.user_sleep)
                    else:
                        user_result = fetch_user(current_dialogue, assistant_messages, user_messages, args.user_sleep)

                    if user_result["state"] == "failure":
                        round_ended = True
                        break
            else:
                result = fetch_assistant(current_dialogue, assistant_messages, user_messages, functions, function_call={"name": function['name']}, sleep=args.assistant_sleep)
                if result["state"] == "success":
                    run_metric(gold_slot_label, result["label"])
                    round_ended = True
                elif result["state"] == "failure":
                    round_ended = True
            if not round_ended:
                print("Round limit reached")
                current_dialogue["reason"] = f"Round limit reached"
                with open(save_file, "a") as f:
                    f.write(json.dumps(current_dialogue, ensure_ascii=False).strip() + "\n")
                with open(save_file_debug, "a") as f:
                    f.write("Fail: Round limit reached")

        with open(ckpt_path, 'w') as f:
            f.write(str(index))

    eval_results = calc_metrics(src_datapath=args.eval_data_file, pred_datapath=save_file, human_datapath = args.human_data_file, trials=None)
    with open(save_file_debug, "a") as f:
        f.write("agent results:" + "\n")
        f.write("trials: " + str(eval_results["trials"]) + "\n")
        f.write("precision_avg: " + str(eval_results["precision_avg"]) + "\n")
        f.write("recall_avg: " + str(eval_results["recall_avg"]) + "\n")
        f.write("f1_avg: " + str(eval_results["f1_avg"]) + "\n")
        f.write("precision_var: " + str(eval_results["precision_var"]) + "\n")
        f.write("recall_var: " + str(eval_results["recall_var"]) + "\n")
        f.write("f1_var: " + str(eval_results["f1_var"]) + "\n")
        f.write("f1_var_unbiased: " + str(eval_results["f1_var_unbiased"]) + "\n")
        f.write("f1_std_unbiased: " + str(eval_results["f1_std_unbiased"]) + "\n")
    
        if "icc" in eval_results:
            f.write(str(eval_results["icc"]) + "\n")

    # with open(save_file_debug, "a") as f:
    #     f.write(f"avg precision: {precision_accu/instance_cnt}, avg recall: {recall_accu/instance_cnt}, avg f1: {f1_accu/instance_cnt}")

if __name__ == "__main__":
    main()