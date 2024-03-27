import json 
file_path = "results/u_llama7b_a_gpt35_legacy.jsonl"
tgt_path = "results/u_llama7b_a_gpt35.jsonl"

dialogs = []
with open(file_path, "r") as f:
	for line in f:
		if line.strip() == "":
			continue
		dialog = json.loads(line.strip())
		dialog["content"] = [
			{
				"role": c["role"],
				"message": c["content"]
			}
			for c in dialog["content"]
		]
		dialogs.append(dialog)

with open(tgt_path, "w") as f:
	for dialog in dialogs:
		f.write(json.dumps(dialog, ensure_ascii=False) + "\n")
	