from utils.utils import parse_profile, read_api_excel, SPECIAL_TYPES, ENUM_MAP_ENG
import json

def get_dialogs(datapath):
    """
    [
        {
            "uuid": "example_uuid",
            "content": [
                {"role": "User", "message": "Turn up the volume on the Smart TV."}
                {"role": "Assistant", "message": '{"name": "TurnUpVolume", "arguments": "{\n  \"deviceType\": \"TV\"\n}"}'}
            ],
        },
    ]
    or
    [
        {
            "uuid": "example_uuid",
            "content": [
                {"role": "User", "message": "Turn up the volume on the Smart TV."}
                {"role": "Assistant", "message": '{"name": "TurnUpVolume", "arguments": "{\n  \"deviceType\": \"TV\"\n}"}'}
            ],
            "api": "TurnUpVolume",
            "slots": {
                "deviceType": "TV"
            }
        },
    ]
    """
    dialogs = []
    if datapath.endswith(".jsonl"):
        with open(datapath, "r") as f:
            for line in f:
                line = line.strip()
                if line == "":
                    continue
                dialog = json.loads(line)
                if "uuid" not in dialog or "content" not in dialog:
                    raise ValueError
                dialogs.append(dialog)
    elif datapath.endswith(".txt"):
        with open(datapath, "r") as f:
            uuid = None
            rounds = []
            last_role = None
            for line in f:
                # assert "```" not in line
                if "-------------------" in line:
                    dialogs.append({ "uuid": uuid, "content": rounds })
                    uuid = None
                    rounds = []
                    last_role = None
                elif "User:" == line[:5] or "Assistant:" == line[:10] or "uuid:" == line[:5]:
                    k, v = line.split(": ", maxsplit=1)
                    if k=="uuid":
                        uuid = v.strip()
                        rounds = []
                        last_role = None
                    elif k=="User" or k=="Assistant":
                        if k=="User":
                            assert last_role is None or last_role=="Assistant"
                        if k=="Assistant":
                            assert last_role is None or last_role == "User"
                        last_role = k
                        r = {"role": k, "message": v.strip()}
                        rounds.append(r)
                    else:
                        raise ValueError
                elif "precision:" == line[:len("precision:")] or "avg precision:" == line[:len("avg precision:")]:
                    pass

                else:
                    assert uuid is not None
                    rounds[-1]["message"] += "\n"+line.strip()
    return dialogs

def get_profiles(datapath):
    profiles = parse_profile(datapath)
    profiles_dict = {p['uuid']:p for p in profiles}
    return profiles_dict

def get_background(dialogs, profiles_dict, data_filter, strict=True):
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
    records = []
    for dialog in dialogs:
        assert dialog["content"][-1]["role"] == "Assistant"

        try:
            api_json = json.loads(dialog["content"][-1]["message"])

        except json.decoder.JSONDecodeError:
            print(dialog["content"][-1]["message"])
            continue
        name = api_json["name"].strip()
        assert name in data_filter
        argument_constraints = data_filter[name]
        arguments = json.loads(api_json["arguments"])
        if strict:
            for k, v in arguments.items():
                assert k in argument_constraints["parameters_all"]
                if k in SPECIAL_TYPES:
                    assert isinstance(v, bool)
                if k in ENUM_MAP_ENG:
                    assert v in ENUM_MAP_ENG[k], (k, v)
        arguments = {k:v for k,v in arguments.items() if isinstance(v, bool) or v is not None and isinstance(v, str) and v.lower()!='null' and v.strip()!=''}
        background = profiles_dict[dialog["uuid"]]
        background_trimmed = f"Character: {background['Character']}\nBackground: {background['Background']}\nPurpose: {background['Purpose']}"
        record = {
            "uuid": dialog["uuid"],
            "background": background_trimmed,
            "content": dialog["content"][:-1],
            "api": name,
            "slots": arguments
        }
        records.append(record)
    return records

def get_labels(dialogs_gold, dialogs_pred, return_uuid=False):
    dialogs_pred_dict = {}
    for d in dialogs_pred:
        if d['uuid'] not in dialogs_pred_dict:
            dialogs_pred_dict[d['uuid']] = d
        else:
            raise ValueError("duplicate uuid")

    preds = []
    golds = []
    uuids = []
    for dialog in dialogs_gold:
        uuid = dialog['uuid']
        if "slots" in dialog:
            label = dialog["slots"]
            if uuid in dialogs_pred_dict:
                pred = dialogs_pred_dict[uuid]["slots"]
            else:
                pred = {}
        else:
            assert dialog['content'][-1]['role'] == "Assistant"
            try:
                label = json.loads(json.loads(dialog['content'][-1]['message'])['arguments'])
            except json.decoder.JSONDecodeError:
                print(dialog['content'][-1]['message'])
                continue
            try:
                if uuid in dialogs_pred_dict:
                    pred = json.loads(json.loads(dialogs_pred_dict[uuid]['content'][-1]['message'])['arguments'])
                else:
                    pred = {}
            except json.decoder.JSONDecodeError:
                print(dialog['content'][-1]['message'])
                pred = {}
        preds.append(pred)
        golds.append(label)
        uuids.append(uuid)
    if return_uuid:
        return preds, golds, uuids
    else:
        return preds, golds

def get_records(src_datapath, profile_datapath, api_list_path, strict=True):
    data_filter = read_api_excel(api_list_path, sheet_name="API list_2", return_format="filter")
    dialogs = get_dialogs(src_datapath)
    profiles = get_profiles(profile_datapath)
    records = get_background(dialogs, profiles, data_filter, strict=strict)
    return records

def write_records(records, path):
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False).strip() + "\n")

def main():
    src_datapath = "results/results_eng_v01_2.txt"
    profile_datapath = "results/dialogue_profiles_v2_2_uuid.txt"
    records = get_records(src_datapath, profile_datapath, 'API_list.xlsx', strict=False)
    write_records(records, "datasets/data.jsonl")
    # src_datapath = "results/results_eng_eval_v1_2.txt"
    # profile_datapath = "results/dialogue_profiles_v2_2_uuid.txt"
    # records = get_records(src_datapath, profile_datapath, 'API_list.xlsx', strict=False)
    # write_records(records, "results/u_gpt35_a_gpt35.jsonl")

    # # pred_datapath = "results/results_eng_eval_v1.txt"
    # # pred_datapath = "results/results_eng_eval_single_shot_v1.txt"
    # pred_datapath = "results/results_eng_human_eval_v1.txt"
    # preds, golds = get_labels(src_datapath, pred_datapath)
    # get_scores(preds, golds)

if __name__ == "__main__":
    main()