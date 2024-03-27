#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate openai
# python -m debugpy --listen localhost:15678 -m evaluators.eval \
python -m evaluators.eval \
	--user_agent llama-7b-chat \
	--assistant_agent codellama13b_oasst \
	--user_prompt_path prompts/prompt_eng_user_v3.txt \
	--assistant_prompt_path prompts/prompt_eng_system_llama_v2_static.txt \
	--api_excel_file API_list.xlsx \
	--eval_data_file datasets/data_v1_2.jsonl \
	--save_file_path results/a_codellama13b_oasst_static_force_5rounds.jsonl \
	--user_agent_url http://127.0.0.1:11007/generate \
	--assistant_agent_url http://127.0.0.1:11013/generate \
	--user_sleep 0 \
	--assistant_sleep 0 \
	--static_test True \
	--num_trials 5