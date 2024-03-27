from utils.data_utils import calc_metrics, get_icc, get_pearsonr, get_trial_results
import seaborn as sns
from analyse.definitions import ASSISTANTS, AGENTS, PATH_MAPPINGS



def main():
    trials = None

    for agent in AGENTS:
        assitant_f1_pd = []
        human_f1_pd = []

        for assistant in ASSISTANTS:
            src_datapath = "datasets/data_v1_2.jsonl"
            assistant1_datapath = PATH_MAPPINGS[assistant][agent]
            human1_datapath = PATH_MAPPINGS[assistant]["human"]
            assistant1_results = get_trial_results(src_datapath, assistant1_datapath, trials=trials)
            human1_results = get_trial_results(src_datapath, human1_datapath, trials=trials)

            assitant_f1_pd.append(assistant1_results["f1_avg"])
            human_f1_pd.append(human1_results["f1_avg"])
        
        pearsonr = get_pearsonr(human_f1_pd, assitant_f1_pd)
        print(f"pearsonr of {agent}: {pearsonr}")
        # print(get_icc(human_f1_pd, assitant_f1_pd))
        get_icc(human_f1_pd, assitant_f1_pd)
            # agents_pd.append(agent)


if __name__ == "__main__":
    main()