import json
import pandas as pd
import numpy as np
import pingouin as pg
import scipy
from utils.parse_records import get_dialogs, get_labels

def load_data(datapath):
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
    with open(datapath, "r") as f:
        for line in f:
            records.append(json.loads(line))
    
    return records

def get_precision_recall_f1(gold_slot_labels, pred_slot_labels):
    """
    {
        "deviceType": "tablet",
        "appName": "Fitness Pro"
    }
    """
    gold_slot_cnt = len(gold_slot_labels.keys())
    pred_slot_cnt = len(pred_slot_labels.keys())
    if gold_slot_cnt == 0 and pred_slot_cnt == 0:
        return 1.0, 1.0, 1.0
    elif gold_slot_cnt == 0 or pred_slot_cnt == 0:
        return 0.0, 0.0, 0.0
    correct_num = 0
    for pred_k, pred_v in pred_slot_labels.items():
        if pred_k in gold_slot_labels and pred_v == gold_slot_labels[pred_k]:
            correct_num += 1
    precision = (correct_num+0.0) / pred_slot_cnt
    recall = (correct_num+0.0) / gold_slot_cnt
    try:
        f1 = (2.0 * precision * recall) / (precision + recall)
    except ZeroDivisionError:
        f1 = 0.0
    return precision, recall, f1

def get_scores(preds, golds):
    precision_accu = 0.0
    recall_accu = 0.0
    f1_accu = 0.0
    assert len(preds) == len(golds)
    precision_list = []
    recall_list = []
    f1_list = []
    for pred, gold in zip(preds, golds):
        precision, recall, f1 = get_precision_recall_f1(gold, pred)
        precision_accu += precision
        recall_accu += recall
        f1_accu += f1
        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)

    precision_avg = precision_accu / len(preds)
    recall_avg = recall_accu / len(preds)
    f1_avg = f1_accu / len(preds)
    return precision_avg, recall_avg, f1_avg, precision_list, recall_list, f1_list

def get_icc(scores_a, scores_b):
    """
    scores_a: [0.2, 0.3, 0.4, 0.5, 0.6]
    scores_b: [0.3, 0.4, 0.5, 0.6, 0.7]
    """
    assert len(scores_a) == len(scores_b)
    targets = [str(i) for i in range(len(scores_a))] * 2
    scores = scores_a + scores_b
    raters = ['a'] * len(scores_a) + ['b'] * len(scores_b)
    df = pd.DataFrame({"targets": targets, "raters": raters, "scores": scores})
    icc = pg.intraclass_corr(data=df, targets="targets", raters="raters", ratings="scores")
    print(icc)

def get_icc_multicase(targets, raters, scores):
    """
    targets: ['1', '2', '1', '2']
    scores: [0.2, 0.3, 0.5, 0.6]
    raters: ['a', 'a', 'b', 'b']
    """
    df = pd.DataFrame({"targets": targets, "raters": raters, "scores": scores})
    icc = pg.intraclass_corr(data=df, targets="targets", raters="raters", ratings="scores")
    return icc

def get_pearsonr(scores_a, scores_b):
    """
    scores_a: [0.2, 0.3, 0.4, 0.5, 0.6]
    scores_b: [0.3, 0.4, 0.5, 0.6, 0.7]
    """
    assert len(scores_a) == len(scores_b)
    return scipy.stats.pearsonr(scores_a, scores_b)

def get_spearmanr(scores_a, scores_b):
    """
    scores_a: [0.2, 0.3, 0.4, 0.5, 0.6]
    scores_b: [0.3, 0.4, 0.5, 0.6, 0.7]
    """
    assert len(scores_a) == len(scores_b)
    return scipy.stats.spearmanr(scores_a, scores_b)

def get_trial_results(src_datapath, pred_datapath, trials=None):
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
    precision_accu = 0.0
    recall_accu = 0.0
    f1_accu = 0.0
    uuid_list = []
    precision_list = []
    recall_list = []
    f1_list = []
    precision_macro_list = []
    recall_macro_list = []
    f1_macro_list = []
    f1_list_trials = []
    for trial in range(trials):
        dialogs_pred_single = [dialogs_pred_dict[k][trial] for k in keys]
        # if max_trials == 5:
        #     dialogs_pred_single = [dialogs_pred_dict[k][trial+4] for k in keys]
        preds, golds, uuids = get_labels(dialogs_gold, dialogs_pred_single, return_uuid=True)
        precision, recall, f1, precision_l, recall_l, f1_l = get_scores(preds, golds)
        precision_accu += precision
        recall_accu += recall
        f1_accu += f1
        precision_macro_list.append(precision)
        recall_macro_list.append(recall)
        f1_macro_list.append(f1)
        uuid_list.extend(uuids)
        precision_list.extend(precision_l)
        recall_list.extend(recall_l)
        f1_list.extend(f1_l)
        f1_list_trials.append(f1_l)
    
    for f1_l in f1_list_trials:
        assert len(f1_l) == len(f1_list_trials[0])
    
    f1_list_avg = list(np.mean(f1_list_trials, axis=0))

    precision_avg = precision_accu / trials
    recall_avg = recall_accu / trials
    f1_avg = f1_accu / trials
    # return trials, precision_avg, recall_avg, f1_avg, precision_list, recall_list, f1_list
    return {
        "trials": trials,
        "precision_avg": precision_avg,
        "recall_avg": recall_avg,
        "f1_avg": f1_avg,
        "precision_var": np.var(precision_macro_list),
        "recall_var": np.var(recall_macro_list),
        "f1_var": np.var(f1_macro_list),
        "f1_var_unbiased": np.var(f1_macro_list, ddof=1),
        "f1_std_unbiased": np.std(f1_macro_list, ddof=1),
        "uuid_list": uuid_list,
        "precision_list": precision_list,
        "recall_list": recall_list,
        "f1_list": f1_list,
        "f1_list_avg": f1_list_avg,
    }

def calc_metrics(src_datapath, pred_datapath, human_datapath=None, trials=None):
    # agent_results = get_trial_results(src_datapath, pred_datapath, trials=4)
    # human_results = get_trial_results(src_datapath, human_datapath, trials=1)
    agent_results = get_trial_results(src_datapath, pred_datapath, trials=trials)
    print("agent results:")
    print("trials:", agent_results["trials"])
    print("precision_avg:", agent_results["precision_avg"])
    print("recall_avg:", agent_results["recall_avg"])
    print("f1_avg:", agent_results["f1_avg"])
    print("precision_var:", agent_results["precision_var"])
    print("recall_var:", agent_results["recall_var"])
    print("f1_var:", agent_results["f1_var"])
    print("f1_var_unbiased:", agent_results["f1_var_unbiased"])
    print("f1_std_unbiased:", agent_results["f1_std_unbiased"])
    result =  {
        "trials": agent_results["trials"],
        "precision_avg": agent_results["precision_avg"],
        "recall_avg": agent_results["recall_avg"],
        "f1_avg": agent_results["f1_avg"],
        "precision_var": agent_results["precision_var"],
        "recall_var": agent_results["recall_var"],
        "f1_var": agent_results["f1_var"],
        "f1_var_unbiased": agent_results["f1_var_unbiased"],
        "f1_std_unbiased": agent_results["f1_std_unbiased"]
    }

    if human_datapath:
        human_results = get_trial_results(src_datapath, human_datapath)
        targets = agent_results["uuid_list"] + human_results["uuid_list"]
        raters = ['agent'] * len(agent_results["uuid_list"]) + ['human'] * len(human_results["uuid_list"])
        scores = agent_results["f1_list"] + human_results["f1_list"]
        icc = get_icc_multicase(targets, raters, scores)
        print(icc)
        result["icc"] = icc
        human_f1_extended = human_results["f1_list"] * (agent_results["trials"] // human_results["trials"])
        assert len(human_f1_extended) == len(agent_results["f1_list"])
        statistic, p_value = get_pearsonr(human_f1_extended, agent_results["f1_list"])
        print("pearsonr:", statistic)
        result["pearsonr"] = statistic
        statistic, p_value = get_spearmanr(human_f1_extended, agent_results["f1_list"])
        print("spearmanr:", statistic)
        result["spearmanr"] = statistic

        h_trimmed = []
        a_trimmed = []
        bad_cnt = 0
        good_cnt = 0
        for h, a in zip(human_f1_extended, agent_results["f1_list"]):
            # if not (h<1e-6 and a>1e-6 or h>1e-6 and a<1e-6):
            if not (h<1e-6 and a>1e-6):
                h_trimmed.append(h)
                a_trimmed.append(a)
                good_cnt += 1
            else:
                bad_cnt += 1
        print("good_cnt:", good_cnt)
        print("bad_cnt:", bad_cnt)
        statistic, p_value = get_pearsonr(h_trimmed, a_trimmed)
        print("pearsonr trimmed:", statistic)


    return result

if __name__ == "__main__":
    # print(load_data("datasets/data_v1.jsonl")[:5])
    test_data = pg.read_dataset('icc')
    get_icc([0.2, 0.3, 0.4, 0.5, 0.6], [0.3, 0.4, 0.5, 0.6, 0.7])