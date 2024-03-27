#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate openai
# python -m debugpy --listen localhost:15678 -m evaluators.eval \
python -m evaluators.eval \
	--user_agent llama-7b-chat \
	--assistant_agent claude_instant_1_2 \
	--user_prompt_path prompts/prompt_eng_user_v3.txt \
	--assistant_prompt_path prompts/prompt_eng_system_claude_v1.txt \
	--api_excel_file API_list.xlsx \
	--eval_data_file datasets/data_v1_2.jsonl \
	--save_file_path results/u_llama7b_a_claude_instant_1_2.jsonl \
	--user_agent_url http://127.0.0.1:11007/generate \
	--assistant_agent_url http://127.0.0.1:11013/generate \
	--user_sleep 0 \
	--assistant_sleep 0 \
	--num_trials 5 \
	--complementary True