#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate openai
# python -m debugpy --listen localhost:15678 -m evaluators.eval \
python -m evaluators.eval \
	--user_agent gpt-35-turbo-16k \
	--assistant_agent gpt-35-turbo-16k \
	--user_prompt_path prompts/prompt_eng_user_v3.txt \
	--assistant_prompt_path prompts/prompt_eng_system_v1.txt \
	--api_excel_file API_list.xlsx \
	--eval_data_file datasets/data_v1_2.jsonl \
	--save_file_path results/u_gpt35_a_gpt35_v2.jsonl \
	--user_agent_url http://127.0.0.1:11007/generate \
	--assistant_agent_url http://127.0.0.1:11070/generate \
	--num_trials 5