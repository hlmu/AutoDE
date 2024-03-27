ASSISTANTS = [
    "gpt35",
    "claude",
    "codellama13b_oasst",
    "zephyr7b_alpha",
    "llama70b",
]

AGENTS = [
    "gpt35",
    "llama7b",
    "static",
]

PATH_MAPPINGS = {
    "gpt35": {
        "gpt35": "results/u_gpt35_a_gpt35_v2.jsonl",
        "llama7b": "results/u_llama7b_a_gpt35_complementary.jsonl",
        "static": "results/a_gpt35_static_v2.jsonl",
        "human": "results/u_human_a_gpt35_complementary.jsonl",
    },
    "claude": {
        "gpt35": "results/u_gpt35_a_claude_instant_1_2.jsonl",
        "llama7b": "results/u_llama7b_a_claude_instant_1_2_complementary.jsonl",
        "static": "results/a_claude_instant_1_2_static.jsonl",
        "human": "results/a_claude_instant_1_2_human.jsonl",
    },
    "codellama13b_oasst": {
        # "gpt35": "results/u_gpt35_a_codellama13b_oasst_1round.jsonl",
        # "llama7b": "results/u_llama7b_a_codellama13b_oasst_1round.jsonl",
        # "static": "results/a_codellama13b_oasst_static_1round.jsonl",
        "gpt35": "results/u_gpt35_a_codellama13b_oasst_5rounds.jsonl",
        "llama7b": "results/u_llama7b_a_codellama13b_oasst_5rounds.jsonl",
        # "static": "results/a_codellama13b_oasst_static_5rounds.jsonl",
        "static": "results/a_codellama13b_oasst_static_force_5rounds.jsonl",
        "human": "results/a_codellama13b_oasst_human_good_complementary.jsonl",
    },
    "zephyr7b_alpha": {
        "gpt35": "results/u_gpt35_a_zephyr_7b_alpha_5rounds.jsonl",
        "llama7b": "results/u_llama7b_a_zephyr_7b_alpha_5rounds.jsonl",
        "static": "results/a_zephyr_7b_alpha_substitute_static_5rounds.jsonl",
        "human": "results/a_zephyr_7b_alpha_human_1round_complementary.jsonl"
    },
    "llama70b": {
        # "gpt35": "results/u_gpt35_a_llama70b_1round.jsonl",
        # "llama7b": "results/u_llama7b_a_llama70b_1round.jsonl",
        # "static": "results/a_llama70b_static_1round.jsonl",
        "gpt35": "results/u_gpt35_a_llama70b_5rounds.jsonl",
        "llama7b": "results/u_llama7b_a_llama70b_5rounds.jsonl",
        # "static": "results/a_llama70b_static_5rounds.jsonl",
        "static": "results/a_llama70b_static_force_5rounds.jsonl",
        "human": "results/a_llama70b_human.jsonl",
    },
}
