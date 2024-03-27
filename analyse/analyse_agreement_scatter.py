from utils.data_utils import calc_metrics, get_trial_results
import seaborn as sns
from analyse.definitions import ASSISTANTS, AGENTS, PATH_MAPPINGS


AGENTS_MAP = {
    "gpt35": "GPT 3.5",
    "llama7b": "Llama 2 7B Chat",
    "static": "Static",
}

def main():
    trials = None
    assitant_f1_pd = []
    human_f1_pd = []
    agents_pd = []

    for assistant in ASSISTANTS:
        for agent in AGENTS:
            src_datapath = "datasets/data_v1_2.jsonl"
            assistant1_datapath = PATH_MAPPINGS[assistant][agent]
            human1_datapath = PATH_MAPPINGS[assistant]["human"]
            assistant1_results = get_trial_results(src_datapath, assistant1_datapath, trials=trials)
            human1_results = get_trial_results(src_datapath, human1_datapath, trials=trials)

            # assert len(assistant1_results["f1_list"]) == len(human1_results["f1_list"])

            assitant_f1_pd.append(assistant1_results["f1_avg"])
            human_f1_pd.append(human1_results["f1_avg"])
            agents_pd.append(AGENTS_MAP[agent])
            # agents_pd.append(agent)

    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    df = pd.DataFrame({
        "Automated Evaluation": assitant_f1_pd,
        "Human Evaluation": human_f1_pd,
        "Method": agents_pd,
    })
    fig_width_in_inches = 4.13
    aspect_ratio = 1.2  # 1.2 is a common aspect ratio for this kind of plot
    # Adjust the height accordingly based on the aspect ratio
    fig_height_in_inches = fig_width_in_inches / aspect_ratio
    g = sns.lmplot(
        data=df,
        x="Automated Evaluation", y="Human Evaluation", hue="Method",
        # ci=None,
        # markers = ['x', 'o', 's'],
        markers = ['x', 'x', 's'],
        fit_reg=False,  # Disable automatic regression lines
        line_kws={'linestyle': '--', 'linewidth': 1, 'alpha': 0.5},
        # aspect=1,   # makes height equals width
        height=fig_height_in_inches,
    )

    # Manually adding regression lines for methods excluding "Static"
    for method in df["Method"].unique():
        if method != "Static":
            sns.regplot(
                data=df[df["Method"] == method],  # Filter data for the specific method
                x="Automated Evaluation", y="Human Evaluation", scatter=False,
                ax=g.axes[0, 0],  # Plot on the same axes as the lmplot
                line_kws={'linestyle': '--', 'linewidth': 1, 'alpha': 0.5},
                ci=None,
                label=None  # This is to avoid adding the method name to the legend again
            )

    for ax in g.axes.flat:
        for spine in ax.spines.values():
            spine.set_visible(True)  # Ensure spine is visible


    g.set(xlim=(0, 1), ylim=(0, 1))
    g.savefig("figs/agreement_scatter.png", dpi=300)

                

if __name__ == "__main__":
    main()