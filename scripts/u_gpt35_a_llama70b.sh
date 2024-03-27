#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate openai
# python -m debugpy --listen localhost:15679 -m evaluators.eval \
python -m evaluators.eval \
	--user_agent gpt-35-turbo-16k \
	--assistant_agent llama-70b-chat \
	--user_prompt_path prompts/prompt_eng_user_v3.txt \
	--assistant_prompt_path prompts/prompt_eng_system_llama_v2.txt \
	--api_excel_file API_list.xlsx \
	--eval_data_file datasets/data_v1_2.jsonl \
	--save_file_path results/u_gpt35_a_llama70b_4rounds.jsonl \
	--user_agent_url http://127.0.0.1:11007/generate \
	--assistant_agent_url http://172.16.1.76:11071/generate \
	--num_trials 4
