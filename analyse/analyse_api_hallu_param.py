from utils.data_utils import calc_metrics, get_trial_results
import seaborn as sns
from analyse.definitions import ASSISTANTS, AGENTS, PATH_MAPPINGS
from utils.parse_records import get_dialogs
from utils.utils import ENUM_MAP_ENG, SPECIAL_TYPES, read_api_excel
import json

def get_dialogs_aligned(src_datapath, pred_datapath, trials=None):
    dialogs_gold = get_dialogs(src_datapath)
    _keys_d = {}
    keys = []
    for d in dialogs_gold:
        if d['uuid'] in _keys_d:
            raise ValueError("duplicate uuid in test labels")
        _keys_d[d['uuid']] = True
        keys.append(d['uuid'])
    dialogs_pred = get_dialogs(pred_datapath)
    dialogs_pred_dict = {}
    for d in dialogs_pred:
        if d['uuid'] not in dialogs_pred_dict:
            dialogs_pred_dict[d['uuid']] = [d]
        else:
            dialogs_pred_dict[d['uuid']].append(d)
    max_trials = 1000000000
    for _, v in dialogs_pred_dict.items():
        max_trials = min(max_trials, len(v))
    if trials is None:
        trials = max_trials
    else:
        if trials > max_trials:
            raise ValueError("trials > max_trials")
    dialogs_pred_aligned = [dialogs_pred_dict[k][trial] for k in keys for trial in range(trials)]
    return dialogs_pred_aligned


data_filter = read_api_excel('API_list.xlsx', sheet_name="API list_2", return_format="filter")
def is_param_exist(dialog):
    global data_filter
    name = dialog["api"].strip()
    argument_constraints = data_filter[name]
    arguments = dialog["slots"]
    for k, v in arguments.items():
        if k not in argument_constraints["parameters_all"]:
            return False
        # if k in SPECIAL_TYPES:
        #     assert isinstance(v, bool)
        # if k in ENUM_MAP_ENG:
        #     assert v in ENUM_MAP_ENG[k], (k, v)
    return True


def main():
    trials = None

    for assistant in ASSISTANTS:
        src_datapath = "datasets/data_v1_2.jsonl"
        assistant1_datapath = PATH_MAPPINGS[assistant]["llama7b"]
        assistant2_datapath = PATH_MAPPINGS[assistant]["static"]
        assistant1_dialogs = get_dialogs_aligned(src_datapath, assistant1_datapath, trials=trials)
        assistant2_dialogs = get_dialogs_aligned(src_datapath, assistant2_datapath, trials=trials)

        print("assistant:", assistant)
        assert len(assistant1_dialogs) == len(assistant2_dialogs), (len(assistant1_dialogs), len(assistant2_dialogs))
        # print(len(assistant1_dialogs), len(assistant2_dialogs))

        cnt_1 = 0
        cnt_exceed_1 = 0
        for dialog in assistant1_dialogs:
            cnt_1 += 1
            if dialog["state"] == 'success' and not is_param_exist(dialog):
                if len(dialog["content"]) < 4 and assistant != "llama70b":
                    print(json.dumps(dialog["content"], indent=4, ensure_ascii=False))
                    print(dialog["api"])
                    print(data_filter[dialog["api"]])
                    print(json.dumps(dialog["slots"], indent=4, ensure_ascii=False))
                    cnt_1
                cnt_exceed_1 += 1
        cnt_2 = 0
        cnt_exceed_2 = 0
        for dialog in assistant2_dialogs:
            cnt_2 += 1
            if dialog["state"] == 'success' and not is_param_exist(dialog):
                cnt_exceed_2 += 1
        print(cnt_1, cnt_exceed_1)
        print(cnt_2, cnt_exceed_2)
        print("API hallu ratio Dynamic - static ", cnt_exceed_1/cnt_1 - cnt_exceed_2/cnt_2)


if __name__ == "__main__":
    main()