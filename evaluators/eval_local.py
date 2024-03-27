from utils.data_utils import calc_metrics

def main():
    trials = None
    src_datapath = "datasets/data_v1_2.jsonl"
    # pred_datapath = "results/u_gpt35_a_gpt35_v2.jsonl"
    # pred_datapath = "results/u_llama7b_a_gpt35_complementary.jsonl"
    # pred_datapath = "results/a_gpt35_static_v2.jsonl"
    # human_datapath = "results/u_human_a_gpt35_complementary.jsonl"

    # pred_datapath = "results/u_gpt35_a_claude_instant_1_2.jsonl"
    # pred_datapath = "results/u_llama7b_a_claude_instant_1_2.jsonl"
    # pred_datapath = "results/a_claude_instant_1_2_static.jsonl"
    # human_datapath = "results/a_claude_instant_1_2_human.jsonl"

    # pred_datapath = "results/u_gpt35_a_codellama13b_oasst_5rounds.jsonl"
    # pred_datapath = "results/u_llama7b_a_codellama13b_oasst_5rounds.jsonl"
    # pred_datapath = "results/a_codellama13b_oasst_static_5rounds.jsonl"
    # pred_datapath = "results/a_codellama13b_oasst_human.jsonl"
    # human_datapath = "results/a_codellama13b_oasst_human_good_complementary.jsonl"

    pred_datapath = "results/u_gpt35_a_llama70b_5rounds.jsonl"
    # pred_datapath = "results/u_llama7b_a_llama70b_5rounds.jsonl"
    # pred_datapath = "results/a_llama70b_static_5rounds.jsonl"
    # pred_datapath = "results/a_llama70b_human.jsonl"
    human_datapath = "results/a_llama70b_human.jsonl"

    # human_datapath = None
    calc_metrics(src_datapath, pred_datapath, human_datapath, trials=trials)

if __name__ == "__main__":
    main()