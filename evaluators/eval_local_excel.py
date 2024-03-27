from utils.data_utils import calc_metrics, get_trial_results
import seaborn as sns
from analyse.definitions import ASSISTANTS, AGENTS, PATH_MAPPINGS



def main():
    trials = None
    # assitant_f1_pd = []
    # human_f1_pd = []
    sheet_results = {
        agent: {
            "assistant": [],
            "precision_avg": [],
            "recall_avg": [],
            "f1_avg": [],
            "trials": [],
            "f1_var": [],
            "f1_var_unbiased": [],
            "f1_std_unbiased": [],
        }
    for agent in AGENTS}
    lines = []
    line = []
    for agent in AGENTS + ["human"]:
        line.append(agent)
    lines.append(line)

    for assistant in ASSISTANTS:
        for agent in AGENTS:
            src_datapath = "datasets/data_v1_2.jsonl"
            assistant1_datapath = PATH_MAPPINGS[assistant][agent]
            assistant1_results = get_trial_results(src_datapath, assistant1_datapath, trials=trials)
            sheet_results[agent]["assistant"].append(assistant)
            sheet_results[agent]["precision_avg"].append(round(assistant1_results["precision_avg"] * 100, 2))
            sheet_results[agent]["recall_avg"].append(round(assistant1_results["recall_avg"] * 100, 2))
            sheet_results[agent]["f1_avg"].append(round(assistant1_results["f1_avg"] * 100, 2))
            sheet_results[agent]["trials"].append(assistant1_results["trials"])
            sheet_results[agent]["f1_var"].append(round(assistant1_results["f1_var"] * 10000, 2))
            sheet_results[agent]["f1_var_unbiased"].append(round(assistant1_results["f1_var_unbiased"] * 10000, 2))
            sheet_results[agent]["f1_std_unbiased"].append(round(assistant1_results["f1_std_unbiased"] * 100, 2))
        
        line = []
        line.append(assistant)
        for agent in AGENTS + ["human"]:
            src_datapath = "datasets/data_v1_2.jsonl"
            assistant1_datapath = PATH_MAPPINGS[assistant][agent]
            assistant1_results = get_trial_results(src_datapath, assistant1_datapath, trials=trials)
            line.append("{:.2f}".format(assistant1_results["precision_avg"] * 100))
            line.append("{:.2f}".format(assistant1_results["recall_avg"] * 100))
            if agent != "human":
                line.append("{:.2f}".format(assistant1_results["f1_avg"] * 100)+ "_{\pm " +"{:.2f}".format(assistant1_results["f1_std_unbiased"] * 100) +"}")
            else:
                line.append("{:.2f}".format(assistant1_results["f1_avg"] * 100))
        lines.append(line)
    
    assert len(lines) == len(ASSISTANTS) + 1
    for j in range(1, len(lines[1])):
        max_idx = -1
        max_val = -1
        for i in range(1, len(ASSISTANTS)+1):
            current_val = float(lines[i][j].split("_")[0])
            if current_val > max_val:
                max_val = current_val
                max_idx = i
        lines[max_idx][j] = "\\boldsymbol{" + lines[max_idx][j] + "}"
    
    for i in range(1, len(lines)):
        for j in range(1, len(lines[i])):
            lines[i][j] = f"${lines[i][j]}$"
    
    with open("eval_local_latex.txt", "w") as f:
        for line in lines:
            f.write(" & ".join(line) + " \\\\\n")


    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    with pd.ExcelWriter('multi_sheet_file.xlsx') as writer:
        for agent in AGENTS:
            df = pd.DataFrame(sheet_results[agent])
            df.to_excel(writer, sheet_name=agent, index=False)



if __name__ == "__main__":
    main()