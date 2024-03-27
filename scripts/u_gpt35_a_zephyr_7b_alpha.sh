#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate openai
# python -m debugpy --listen localhost:15678 -m evaluators.eval \
python -m evaluators.eval \
	--user_agent gpt-35-turbo-azure \
	--assistant_agent zephyr-7b-alpha \
	--user_prompt_path prompts/prompt_eng_user_v3.txt \
	--assistant_prompt_path prompts/prompt_eng_system_zephyr_v2.txt \
	--api_excel_file API_list.xlsx \
	--eval_data_file datasets/data_v1_2.jsonl \
	--save_file_path results/u_gpt35_a_zephyr_7b_alpha_5rounds.jsonl \
	--user_agent_url http://127.0.0.1:11008/generate \
	--assistant_agent_url http://127.0.0.1:12008/generate \
	--user_sleep 0 \
	--assistant_sleep 0 \
	--num_trials 5